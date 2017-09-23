import discord
import asyncio
import aiohttp
import datetime
from discord.ext import commands
from config import config


# Bot description
description = config["description"]

# Current time can be used for uptime
startup_time = datetime.datetime.now()

# Load these modules
extensions = config["active_extensions"]


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discord_token = config["tokens"]["discord"]


    async def on_ready(self):
        """Run this when the bot starts up"""
        print(f"Logged in as {self.user.name} - {self.user.id}\nVersion: {discord.__version__}")
        await self.change_presence(game=discord.Game(name="Isaac, probably"))

        print(f"Successfully logged in and booted")


# Initialize bot with parameters
bot = Bot(command_prefix=config["prefix"], description=description)


if __name__ == '__main__':
    """Run the bot"""
    for extension in extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

    bot.run(bot.discord_token, bot=True, reconnect=True)
