import os, urllib.request, json
token = os.environ['GITHUB_PAT']
req = urllib.request.Request(
    'https://api.github.com/repos/ArindamBanerji/copilot-sdk/contents/copilot_sdk/scoring',
    headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'}
)
data = json.loads(urllib.request.urlopen(req).read())
for item in data:
    print(item['type'] + '  ' + item['name'])
