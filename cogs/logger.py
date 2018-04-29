import discord
import requests
import os
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
        self.filecounter = 0
        self.sizecounter = 0
        self.files = {}

    
    def check(self, author):
        return author.id != self.bot.user.id


    async def on_ready(self):
        if not self.logging_channel:
            self.logging_channel = self.bot.get_channel(config["channels"]["logging"])

    
    async def on_message(self, message):
        if len(message.attachments) != 0:
            for att in message.attachments:
                if att["size"] >= 5000000:
                    continue
                data = requests.get(att["url"]).content
                with open(att["filename"], 'wb') as handler:
                    handler.write(data)
                    self.sizecounter += att["size"]
                    self.filecounter += 1
                    self.files[message.id] = att["filename"]
            
            while self.filecounter >= 20 or self.sizecounter >= 100000000:
                os.remove(self.files.pop(list(self.files.keys())[0], None))
                


    async def create_embed(self, title, content, channel, color, author):
        name = author.nick if author.nick else author.name 
        name += f" ({author.id})"
        
        emb = discord.Embed(title=title, description=f"\n{content}", color=color)
        emb.set_author(name=name, icon_url=author.avatar_url)
        
        if channel:
            emb.set_footer(text=f"\nin #{channel}")
    
        return emb


    async def on_message_delete(self, message):
        """Fires when somebody deletes a message"""

        if self.check(message.author):
            emb = await self.create_embed("🗑️ Message deleted", message.content, 
                                        message.channel.name, 0xd33751, message.author)

            await self.bot.send_message(self.logging_channel, embed=emb)

            if message.id in self.files:
                self.bot.send_file(self.logging_channel, self.files["id"])
                os.remove(self.files.pop(message.id, None)

    
    async def on_message_edit(self, before, after):
        """Fires when somebody edits a message"""

        if not before.embeds and after.embeds:
            return False

        if before.pinned != after.pinned:
            emb = await self.create_embed("📌 Message changed pin state", before.content, 
                                        before.channel.name, 0x37a4d3, before.author)

            await self.bot.send_message(self.logging_channel, embed=emb)
            return True

        if self.check(before.author) and before.content != after.content:
            before_clean = before.clean_content.replace("```", "<code>")
            after_clean = after.clean_content.replace("```", "<code>")
            content = f"```{before_clean}```\n```{after_clean}```"

            emb = await self.create_embed("✏️ Message edited", content, 
                                        before.channel.name, 0x37a4d3, before.author)

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
