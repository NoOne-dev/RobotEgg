import discord
from discord.ext import commands
from config import config
from cogs.utils.fetch import fetch
from cogs.utils.create_error import create_error
from cogs.utils.checks import channels_allowed


class Help:
    """Lists commands"""

    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["nlss-chat", "circlejerk"])
    async def joke(self, ctx):
        await self.bot.send_typing(ctx.message.channel)
        
        commands = "`-status [others]`: NLSS status\n\n`-joke`: random joke\n\n`-random`: random bible verse\n`-verse [book] [x:x]`: specific bible verse\n`-daily`: daily bible verse"
        
        await self.bot.say(commands)


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(Help(bot))
    