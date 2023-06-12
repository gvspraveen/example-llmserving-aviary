import requests

resp = requests.get(
    "http://localhost:8000/query/amazon--LightGPT", params={"prompt": "Where is a good place to eat in San Francisco?","use_prompt_format":"true"}
)
print(resp.json())


