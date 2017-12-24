import asyncio
import datetime
import discord
import os
from discord.ext import commands
from config import config
from cogs.utils.create_error import create_error
from cogs.utils.checks import channels_allowed
from cogs.utils.checks import is_owner
from cogs.utils.checks import is_mod
from sqlalchemy import create_engine  
from sqlalchemy import Column, String, Integer, DateTime 
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker


"""
Keeps track of warnings
"""

db   = create_engine(os.environ['DATABASE_URL'])
Base = declarative_base()


class Warning_Table(Base):  
    __tablename__ = "warning_table"
    index = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    created_by = Column(String)
    created_on = Column(DateTime)
    reason = Column(String)
    notes = Column(String)


Session = sessionmaker(db)  
session = Session()
Base.metadata.create_all(db)


class Warning:
    """Keep track of user warnings"""
    def __init__(self, bot):
        self.bot = bot


    async def _check_user(self, user, mod):
        msg = await self.bot.say(f"Warning: <@!{user}>. Is this correct?")

        await self.bot.add_reaction(msg, '✅')
        await self.bot.add_reaction(msg, '🛑')

        def check(reaction, user):
            print('1234')
            valid = user.id == mod.id and str(reaction.emoji) == '✅'
            print(f'{reaction.message.author.id}, {mod.id}: {str(reaction.emoji)}: {valid}')
            return valid

        react = await self.bot.wait_for_reaction(timeout=60.0, message=msg, check=check)

        if react:
            return True
        return False



    async def _get_reason(self, user, mod):
        msg = await self.bot.say(f"Warning: <@!{user}>.")
        await client.wait_for_message(timeout=120.0, author=mod)


    async def _get_notes(self, user, mod):
        msg = await self.bot.say(f"Warning: <@!{user}>.")
        await client.wait_for_message(timeout=120.0, author=mod)


    @commands.command(pass_context=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def warn(self, ctx):
        """Add a warning to the database"""
        try:
            user = ctx.message.mentions
            if len(user) != 1:
                await self.bot.say(content=None, embed=create_error("Invalid user specified"))
                return False

            user = user[0].id
            mod = ctx.message.author
            date = datetime.datetime.now()
        
        except Exception as e:
            await self.bot.say(content=None, embed=create_error(f"Error creating warning: {e}"))
            return False

        if await self._check_user(user, mod):
            await self.bot.say("Gucci")
            reason = await self._get_reason(user, mod)
            note = await self._get_notes(mod)
        else:
            await self.bot.say("Cancelled.")


    @commands.command()
    @is_mod()
    async def removewarning(self, uid):
        """Remove warning from user"""
        pass


    @commands.command(invoke_without_command=True)
    async def warnings(self, ctx):
        """Check warnings of user or self"""
        pass

def setup(bot):
    bot.add_cog(Warning(bot))
    