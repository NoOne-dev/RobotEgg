import aiohttp
import discord
import json
from cogs.utils.fetch import fetch
from discord.ext import commands
from config import config


class OCR:
    """Finds @Mod in images"""

    def __init__(self, bot):
        self.bot = bot
        self.image_mimes = ['image/png', 'image/pjpeg', 'image/jpeg', 'image/x-icon']
        self.session = aiohttp.ClientSession()
        self.ocr_token = config["tokens"]["ocr"]
        

    async def _is_image(self, url):
        try:
            with aiohttp.Timeout(4):
                async with self.session.head(url) as resp:
                    if resp.status == 200:
                        mime = resp.headers.get('Content-type', '').lower()
                        if any([mime == x for x in self.image_mimes]):
                            return True
                        else:
                            return False

        except Exception as e:
            print(f"Error checking for image type: {e}")
            return False



    async def _get_ocr(self, url):
        try:
            with aiohttp.Timeout(5):
                api_url = "https://api.ocr.space/parse/imageurl"
                params = dict(apikey=self.ocr_token,
                              url=url)
                text = await fetch(api_url, params=params)
                text = json.loads(text)

                print(f"{api_url}?{params['apikey']}&{params['url']}")

                if text["ParsedResults"]:
                    text = text["ParsedResults"][0]
                else:
                    return False
                
                if text["FileParseExitCode"] == 1:
                    print(text["ParsedText"])
                    return text["ParsedText"]
                else:
                    print(text["FileParseExitCode"])

            return False

        except Exception as e:
            print(f"Error getting OCR: {e}")
            return False



    async def on_message(self, message):
        if not message.attachments:
            return

        for attachment in message.attachments:
            if attachment["size"] > 5000:
                continue

            if await self._is_image(attachment["url"]):
                text = await self._get_ocr(attachment["url"])
                if text and "@mod" in text.lower():
                    emoji = discord.utils.get(self.bot.get_all_emojis(), name='BeAdvised')
                    await self.bot.say(message.channel, emoji)

            

# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(OCR(bot))
    