import aiohttp

async def fetch(url: str, params=None, headers=None):
    async with aiohttp.get(url, params=params, headers=headers) as r:
        if r.status == 200:    
            return await r.text()
        return False
