import urllib, json
author = 'Youtube_Username'
inp = urllib.urlopen("UCmeHX75iiqezgdKgYfrFKSA")
resp = json.load(inp)
inp.close()
first = resp['feed']['entry'][0]
print (first['title']) # video title
print (first['link'][0]['href']) #url