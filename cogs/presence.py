import discord
import json
from discord.ext import commands
from config import config


"""
Tells you the status of given twitch streamers
"""


class Presence:
    """Stream status listings"""

    def __init__(self, bot):
        self.bot = bot

    pass


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(Presence(bot))