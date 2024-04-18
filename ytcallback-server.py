#!/usr/bin/env python3
"""Send telegrams about new videos on subscribed YouTube channels.

To try it, install dependencies:

  $ python3 -mpip install aiohttp feedparser werkzeug

run the callback server:

  $ env TELEBOT_TOKEN=<token> TELEBOT_CHAT_ID=<chat_id> python3 ytcallback-server.py
  $ ngrok 8080  # expose localhost as <id>.ngrok.io

Subscribe to receive push-notifications for a YouTube channel:

  $ python3 -mpip install httpie
  $ http PUT https://<id>.ngrok.io/subscription/<channel_id>

Now, for each new video on https://youtube.com/channel/<channel_id>,
you (<chat_id>) get a telegram from the bot identified by <token>.

To unsubscribe:

  $ http DELETE https://<id>.ngrok.io/subscription/<channel_id>

https://developers.google.com/youtube/v3/guides/push_notifications
https://core.telegram.org/bots/api#sendmessage

"""
import asyncio
import logging
import os
import posixpath
import sys
from functools import partial
from urllib.parse import urljoin, urlparse

import feedparser
from aiohttp import ClientSession, web
from werkzeug.contrib import cache as cache_mod


async def subscribe_youtube_channel(channel_id, callback_url, *,
                                    lease_time=86400, subscribe=True):
    """Subscribe to receive push-notifications via PubSubHubbub."""
    subscribe_url = 'https://pubsubhubbub.appspot.com/subscribe'
    topic_url = ('https://www.youtube.com/xml/feeds/videos.xml?channel_id='
                 + channel_id)
    data = {
        'hub.mode': 'subscribe' if subscribe else 'unsubscribe',
        'hub.callback': callback_url,
        'hub.lease_seconds': lease_time,
        'hub.topic': topic_url
    }
    async with ClientSession() as session:
        async with session.post(subscribe_url, data=data) as r:
            log('url: %s, channel_id: %s status: %s',
                subscribe_url, channel_id, r.status)
            return r.status


def hub_challenge(request):
    """Echo challenge on GET"""
    return web.Response(text=request.query['hub.challenge'])


async def send_telegram(text):
    """Send *text* to a telegram chat ($TELEBOT_CHAT_ID) from $TELEBOT_TOKEN bot."""
    token = os.environ['TELEBOT_TOKEN']
    chat_id = os.environ['TELEBOT_CHAT_ID']
    api_url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = dict(chat_id=chat_id, text=text)
    async with ClientSession() as session:
        async with session.post(api_url, data=data) as r:
            log('text: %s, status: %s', text, r.status)


async def feed_callback(request):
    """Handle callback: send a telegram for each new YouTube video."""
    log('channel %s', request.match_info['channel_id'])
    xml = await request.text()
    feed = feedparser.parse(xml)
    for e in feed.entries:
        log('channel_id: %s, video_id: %s', e.yt_channelid, e.yt_videoid)
        text = (f'channel: {e.yt_channelid}\n'
                f'video_url: {e.link}\n'
                f'title: {e.title}')
        if cache.inc(e.yt_videoid) == 1:  # don't send duplicate updates
            asyncio.ensure_future(send_telegram(text))
    return web.HTTPCreated()  # 201


async def _subscribe(channel_id, base_url, subscribe):
    path = app.router['callback'].url(parts=dict(channel_id=channel_id))
    callback_url = urljoin(str(base_url), path)
    return web.Response(status=await subscribe_youtube_channel(
        channel_id, callback_url, subscribe=subscribe))


async def subscribe(request, subscribe=True):
    """Subscribe to receive push-notifications for a given channel_id."""
    channel_id = request.match_info['channel_id']
    return await _subscribe(channel_id, request.url, subscribe)


async def subscribe_via_url(request, subscribe=True):
    """Subscribe to receive push-notifications for a given channel url."""
    data = await request.post()
    channel_id = posixpath.basename(urlparse(data['youtube_channel_url']).path)
    return await _subscribe(channel_id, request.url, subscribe)


def setup_routes(app):
    """Setup routes for the web app."""
    resource = app.router.add_resource(
        '/callback/{channel_id}', name='callback')
    resource.add_route('GET',  hub_challenge)
    resource.add_route('POST', feed_callback)
    app.router.add_route('POST', '/subscription/', subscribe_via_url)
    app.middlewares.append(web.normalize_path_middleware(  # append trailing /
        merge_slashes=False,
        redirect_class=web.HTTPPermanentRedirect))  # don't change POST to GET
    resource = app.router.add_resource('/subscription/{channel_id}')
    resource.add_route('PUT', subscribe)
    resource.add_route('DELETE', partial(subscribe, subscribe=False))
    return app


log = logging.getLogger(__name__).debug
app = setup_routes(web.Application())
cache = cache_mod.FileSystemCache('.cachedir',
                                  threshold=100000,       # nitems
                                  default_timeout=86400)  # a day

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)-15s %(message)s",
                        datefmt="%F %T",
                        level=logging.DEBUG)
    web.run_app(app,
                host='localhost',
                ssl_context=None,
                port=int(sys.argv[1]) if len(sys.argv) > 1 else None)
