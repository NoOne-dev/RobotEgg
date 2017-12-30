import aiohttp
import discord
import pytesseract
import os
from discord.ext import commands
from config import config
from PIL import Image


class OCR:
    """Finds @Mod in images"""

    def __init__(self, bot):
        self.bot = bot
        self.image_mimes = ['image/png', 'image/pjpeg', 'image/jpeg', 'image/x-icon']
        self.session = aiohttp.ClientSession()
        self.image_counter = 0
        

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
            print(e)
            return False



    async def _get_image(self, url, image_name):
        try:
            with aiohttp.Timeout(4):
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        image = await resp.read()
                        filename = f"{self.image_counter}_{image_name}"
                        self.image_counter += 1

                        with open(filename, "wb") as f:
                            f.write(image)

                        image = Image.open(filename)
                        image = image.convert('1')
                        image.save(filename)
                        image.close()
                        print(f"saving as {filename}")
                        return filename

            return False

        except Exception as e:
            print(e)
            return False



    async def on_message(self, message):
        if not message.attachments:
            return

        for attachment in message.attachments:
            if attachment["size"] > 5000:
                continue

            if await self._is_image(attachment["url"]):
                try:
                    filename = await self._get_image(attachment["url"], attachment["name"])
                    if not filename:
                        return False

                    print ('opening image')
                    image = Image.open(filename)
                    text = pytesseract.image_to_string(image)
                    image.close()
                    print("removing image")
                    os.remove(filename)
                    self.image_counter -= 1
                    print(f"text: {text}")
                except Exception as e:
                    print(e)
                    return False

            

# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(OCR(bot))
    