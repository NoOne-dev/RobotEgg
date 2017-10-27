import datetime
import discord
from discord.ext import commands
from config import config
from cogs.utils.checks import is_owner


"""
Some administration commands:::WIP
"""


class Admin:
    """Several admin commands (doubtlessly useless)"""
    def __init__(self, bot):
        self.bot = bot
        self.startup = datetime.datetime.now()

    def timedelta_str(self, dt):
        days = dt.days
        hours, r = divmod(dt.seconds, 3600)
        minutes, sec = divmod(r, 60)

        if minutes == 1 and sec == 1:
            return f"{days} days, {hours} hours, {minutes} minute and {sec} second."
        elif minutes > 1 and sec == 1:
            return f"{days} days, {hours} hours, {minutes} minutes and {sec} second."
        elif minutes == 1 and sec > 1:
            return f"{days} days, {hours} hours, {minutes} minute and {sec} seconds."
        else:
            return f"{days} days, {hours} hours, {minutes} minutes and {sec} seconds."


    @commands.command()
    @is_owner()
    async def load(self, extension_name: str):
        """Loads an extension."""
        try:
            self.bot.load_extension(extension_name)
        except (AttributeError, ImportError) as e:
            await self.bot.say(f"Error loading extension: {type(e).__name__}, {str(e)}")
            return
        await self.bot.say(f"Loaded extension {extension_name}")

    @commands.command()
    @is_owner()
    async def unload(self, extension_name: str):
        """Unloads an extension."""
        self.bot.unload_extension(extension_name)
        await self.bot.say(f"Unloaded {extension_name}.")

    @commands.command()
    @is_owner()
    async def active(self):
        """lists active extensions."""
        active_ext = ""
        try:
            for extension in tuple(self.bot.extensions):
                active_ext += f"{extension}\n"
            for cog in tuple(self.bot.cogs):
                active_ext += f"{cog}\n"
        except:
            pass
        await self.bot.say(active_ext)

    @commands.command()
    async def uptime(self):
        """Prints bot uptime."""
        delta = datetime.datetime.now()-self.startup
        delta_str = self.timedelta_str(delta)
        await self.bot.say(f"Uptime: {delta_str}")


    @commands.command()
    @is_owner()
    async def say_this(self, *args):
        channel = self.bot.get_channel(args[0])
        msg = ' '.join(args[1:])
        await self.bot.send_message(channel, msg)


def setup(bot):
    bot.add_cog(Admin(bot))
    