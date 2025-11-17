import httpx

BASE_URL = "https://www.googleapis.com/youtube/v3"

class YouTubeClient:
    def __init__(self, api_key: str):
        self._key = api_key
        self._http = httpx.Client(timeout=10)

    def search_live(self, channel_id: str):
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "eventType": "live",
            "type": "video",
            "key": self._key,
        }
        r = self._http.get(f"{BASE_URL}/search", params=params)
        if r.status_code == 403:
            raise OSError("YouTube API quota exceeded")
        r.raise_for_status()
        data = r.json()
        return data.get("items", [])