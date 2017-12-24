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


    @commands.command(pass_context=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def warn(self, ctx):
        """Add a warning to the database"""
        user = ctx.message.mentions
        if len(user) != 1:
            return False

        user = user[0].id
        mod = ctx.message.author.id
        date = datetime.datetime.now()

        print(f'warning {user} by {mod} on {date}')


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
    