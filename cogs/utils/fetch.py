import aiohttp

async def fetch(url: str, params=None, headers=None):
    async with aiohttp.get(url, params=params, headers=headers) as r:
        return await r.text()
