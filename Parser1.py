import requests
import json
from bs4 import BeautifulSoup

URL = "https://www.youtube.com/c/AntropogenezRu/videos"

page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
print(page)
#print(soup)

#results = soup.find(id="page-manager")
 
body = soup.find_all("body")[0]
scripts = body.find_all("script")

result = {}
tt=result["title"] = soup.find("meta", itemprop="name")['content']
tt1=result["description"] = soup.find("meta", itemprop="description")['content']

print(tt1)

#tt=soup.select('div#contents.style-scope ytd-rich-grid-renderer')

#print(tt)

#post = post.find_all("article", class_="tm-articles-list__item", id=True)
#post_id = post["id"]

#result = json.loads(scripts[0].string[30:-1])
#result.keys()

#result['streamingData'].keys()
#result['streamingData']['formats']

#print(result)

#title = post.find("h3", class_="style-scope ytd-rich-grid-media").text.strip()
#description = post.find("div", class_="style-scope ytd-rich-grid-media").text.strip()
#url = post.find("a", class_="tm-article-snippet__readmore", href=True)

#print(title, description, url)
#print(title)