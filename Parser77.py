from googleapiclient.discovery import build

api_key = "AIzaSyBMoHlzVntxs91vr_ZwXru5thGMh-ylJQU"
youtube = build("youtube", "v3", developerKey=api_key)

channel_id = "UCmeHX75iiqezgdKgYfrFKSA"
request = youtube.search().list(part="snippet", channelId=channel_id, maxResults=10, type="video")
response = request.execute()
 
for item in response["items"]:
    print(item["snippet"]["title"])