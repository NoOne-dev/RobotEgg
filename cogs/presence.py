import discord
import json
from discord.ext import commands
from config import config
from cogs.utils.checks import is_owner


"""
Tells you the status of given twitch streamers
"""


class Presence:
    """Stream status listings"""

    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True, invoke_without_command=True)
    @is_owner()
    async def presence(self, ctx, *args):
        await self.change_presence(game=discord.Game(name=''.join(args)))
        await self.bot.say(f"Changed to {''.join(args)}.")


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(Presence(bot))