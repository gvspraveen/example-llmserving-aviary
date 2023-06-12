import requests

resp = requests.post(
    "http://127.0.0.1:8000/query/amazon--LightGPT", json={"prompt": "Where is a good place to eat in San Francisco?","use_prompt_format":"true"}
)
print(resp.json())


