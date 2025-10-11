import requests
class TTSClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.xiangyinge.com"
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def synthesize(self, text, voice_id):
        payload = {
            'text': text,
            'voice_id': voice_id
        }
        response = requests.post(
            f"{self.base_url}/public/api/tts",
            headers=self.headers,
            json=payload
        )
        return response.json()
# Usage
client = TTSClient('YOUR_API_KEY')
result = client.synthesize("你好世界", "sunny_sichuan")
if result['success']:
    print(f"Audio URL: {result['data']['audio_url']}")