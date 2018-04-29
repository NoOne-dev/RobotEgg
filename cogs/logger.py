import discord
from discord.ext import commands
from config import config

"""
Log message deletes, edits, member joins/leaves...
"""


class Logger:
    """Log events"""

    def __init__(self, bot):
        self.bot = bot
        self.logging_channel = bot.get_channel(config["channels"]["logging"])
        print(config["channels"]["logging"])
        print(self.logging_channel)

    async def create_embed(self, title, content, color, author):
        name = author.nick if author.nick else author.name
        
        emb = discord.Embed(title=title, description=content, color=color)
        emb.set_author(name=name, icon_url=author.avatar_url)
        emb.set_footer(text=f"ID: {author.id}")
    
        return emb


    async def on_message_delete(self, message):
        """Fires when somebody deletes a message"""

        emb = await self.create_embed("🗑️ Message deleted", message.content, 
                                       0xd33751, message.author)

        await self.bot.send_message(self.logging_channel, embed=emb)

    
    async def on_message_edit(self, before, after):
        """Fires when somebody edits a message"""

        content = f"**Before**\n```{before.content}```\n\n**After**\n```{after.content}```"

        emb = await self.create_embed("✏️ Message edited", content, 
                                       0x37a4d3, before.author)

        await self.bot.send_message(self.logging_channel, embed=emb)

    
    async def on_member_join(self, member):
        """Fires when somebody joins"""

        emb = await self.create_embed("✨ Member joined", None, 
                                       0x2acc4d, member)

        await self.bot.send_message(self.logging_channel, embed=emb)


    async def on_member_remove(self, member):
        """Fires when somebody joins"""

        emb = await self.create_embed("😔 Member left", None, 
                                       0x6b8ea3, member)

        await self.bot.send_message(self.logging_channel, embed=emb)


def setup(bot):
    bot.add_cog(Logger(bot))
