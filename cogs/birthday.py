import datetime
import discord
import os
from discord.ext import commands
from config import config
from cogs.utils.checks import create_error
from sqlalchemy import create_engine  
from sqlalchemy import Column, Integer, Date  
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker


"""
Keep track of people's birthdays
"""

db   = create_engine(os.environ['DATABASE_URL'])
Base = declarative_base()

class Birthday_Table(Base):  
    __tablename__ = "birthday_table"
    uid = Column(Integer, primary_key=True)
    birthday = Column(Date)
    times_changed = Column(Integer)

Session = sessionmaker(db)  
session = Session()
Base.metadata.create_all(db)


class Birthday:
    """Keep track of people's birthdays"""
    def __init__(self, bot):
        self.bot = bot


    def _parse_birthday(self, birthday_str):
        try:
            year = int(birthday_str[0:4])
            month = int(birthday_str[5:7])
            day = int(birthday_str[8:10])
            date = datetime.datetime(year, month, day).date()
            return date
        except:
            await self.bot.say(content=None, embed=create_error("creating birthday. Make sure to enter it as `YYYY-MM-DD` (example: `1969-04-20`)"))
            return False


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["circlejerk"])
    async def birthday(self, ctx, *args):
        uid = ctx.message.author.id
        user = session.query(Birthday_Table).filter_by(uid=uid).first()

        birthday_str = ""
        try:
            birthday_str = args[0]
        except:
            pass

        # Try to enter args into db
        if birthday_str:
            birthday = self._parse_birthday(birthday_str)

            if not birthday:
                await self.bot.say(content=None, embed=create_error("Use -birthday `YYYY-MM-DD` to enter your birthday."))
                return False

            if not user:
                birthday = Birthday_Table(uid=uid, birthday=birthday, times_changed=0)
                session.add(birthday)
            else:
                user.birthday = birthday
                user.times_changed = user.times_changed+1

            try:
                session.commit()
            except:
                await self.bot.say(content=None, embed=create_error("entering into database."))
                return False
            
            emb = discord.Embed(color=0xffffff) 
            emb.set_author(name=f"{author.nick if author.nick else author.name}") 
            emb.description = "Birthday set."
            self.bot.say(content=None, embed=emb)

        elif user:
            author = ctx.message.author
            year = user.birthday.year
            month = user.birthday.month
            day = user.birthday.day
            emb = discord.Embed(color=0xffffff) 
            emb.set_author(name=f"{author.nick if author.nick else author.name}") 
            emb.description = f"Birthday set to {year}-{month}-{day}. \
            You have changed your birthday {user.times_changed} times ({2-user.times_changed} times left).") 
            await self.bot.say(content=None, embed=emb)   

        else:
            await self.bot.say(content=None, embed=create_error("Use -birthday `YYYY-MM-DD` to enter your birthday."))



def setup(bot):
    bot.add_cog(Birthday(bot))
    