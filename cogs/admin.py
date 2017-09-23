import discord
from discord.ext import commands
from config import config


"""
Some administration commands:::WIP
"""


class Admin:
    """Several admin commands (doubtlessly useless)"""

    @bot.command()
    async def load(extension_name : str):
        """Loads an extension."""
        try:
            bot.load_extension(extension_name)
        except (AttributeError, ImportError) as e:
            await bot.say(f"Error loading extension: {type(e).__name__}, {str(e)}")
            return
        await bot.say(f"Loaded extension {extension_name}")

    @bot.command()
    async def unload(extension_name : str):
        """Unloads an extension."""
        bot.unload_extension(extension_name)
        await bot.say(f"Unloaded {extension_name}.")

    @bot.command()
    async def uptime(extension_name : str):
        """Unloads an extension."""
        bot.unload_extension(extension_name)
        await bot.say(f"Unloaded {extension_name}.")


def setup(bot):
    bot.add_cog(Admin(bot))