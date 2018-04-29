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

    
    def check(self, author):
        return author.id != self.bot.user.id


    async def on_ready(self):
        if not self.logging_channel:
            self.logging_channel = self.bot.get_channel(config["channels"]["logging"])


    async def create_embed(self, title, content, channel, color, author):
        name = author.nick if author.nick else author.name 
        name += f" ({author.id})"
        
        emb = discord.Embed(title=title, description=f"\n{content}", color=color)
        emb.set_author(name=name, icon_url=author.avatar_url)
        
        if channel:
            emb.set_footer(text=f"\nin {channel}")
    
        return emb


    async def on_message_delete(self, message):
        """Fires when somebody deletes a message"""

        if self.check(message.author):
            emb = await self.create_embed("🗑️ Message deleted", message.content, 
                                        message.channel.name, 0xd33751, message.author)

            await self.bot.send_message(self.logging_channel, embed=emb)

    
    async def on_message_edit(self, before, after):
        """Fires when somebody edits a message"""

        if not before.embeds and after.embeds:
            return false

        if not before.pinned and after.pinned:
            emb = await self.create_embed("📌 Message pinned", before.content, 
                                        before.channel.name, 0x37a4d3, before.author)

            await self.bot.send_message(self.logging_channel, embed=emb)
            return True

        if self.check(before.author) and before.content != after.content:
            content = f"```{before.content}```\n```{after.content}```"

            emb = await self.create_embed("✏️ Message edited", content, 
                                        before.channel.nam, e0x37a4d3, before.author)

            await self.bot.send_message(self.logging_channel, embed=emb)

    
    async def on_member_join(self, member):
        """Fires when somebody joins"""

        emb = await self.create_embed("✨ Member joined", None, 
                                        None, 0x2acc4d, member)

        await self.bot.send_message(self.logging_channel, embed=emb)


    async def on_member_remove(self, member):
        """Fires when somebody joins"""

        emb = await self.create_embed("😔 Member left", None, 
                                        None, 0x6b8ea3, member)

        await self.bot.send_message(self.logging_channel, embed=emb)


def setup(bot):
    bot.add_cog(Logger(bot))
