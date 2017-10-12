import discord
from discord.ext import commands
from config import config
from cogs.utils.fetch import fetch
from cogs.utils.create_error import create_error
from cogs.utils.checks import channels_allowed


class Joke:
    """Gets a joke"""

    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["circlejerk"])
    async def joke(self, ctx):
        """Gets you a random, HILARIOUS joke."""
        await self.bot.send_typing(ctx.message.channel)
        try:
            url = "https://icanhazdadjoke.com/"
            header = dict(Accept="text/plain")

            msg = await fetch(url, headers=header)

            emb = discord.Embed(title=f"😂😂 WHO DID THIS? 😂😂", description=msg, color=0xf4f142)          #Create the embed object
            emb.set_footer(text=f"like share subscribe")
            await self.bot.say(content=None, embed=emb)

        except:
            await self.bot.say(content=None, embed=create_error("fetching joke"))


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(Joke(bot))
    