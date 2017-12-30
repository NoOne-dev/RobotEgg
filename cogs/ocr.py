import discord
from discord.ext import commands
from config import config
from PIL import Image
import pytesseract
import cv2 


class OCR:
    """Finds @Mod in images"""

    def __init__(self, bot):
        self.bot = bot


    async def on_message(self, message):
        if not message.attachments:
            return

        for attachment in message.attachments:
            print(attachment)
            

# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(Ocr(bot))
    