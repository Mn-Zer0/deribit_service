import aiohttp
from app.config import get_settings

class DeribitClient:
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self._session = session
        self._base_url = base_url

    async def get_index_price(self, index_name: str) -> float:
        url = f"{self._base_url}/public/get_index_price"
        params = {"index_name": index_name}
        async with self._session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["result"]["index_price"]