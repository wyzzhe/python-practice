import requests
import json

getPromptUrl = "https://screen.aibee.cn/guide/get_prompt?place_id=801&name=intentionPrompt"
print("?????")
res = requests.get(getPromptUrl)
resDict = json.loads(res.text)
print(resDict)