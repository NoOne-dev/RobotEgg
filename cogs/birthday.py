import datetime
import discord
import os
from discord.ext import commands
from config import config
from cogs.utils.create_error import create_error
from cogs.utils.checks import channels_allowed
from sqlalchemy import create_engine  
from sqlalchemy import Column, String, Integer, Date  
from sqlalchemy import func.extract
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker


"""
Keep track of people's birthdays
"""

db   = create_engine(os.environ['DATABASE_URL'])
Base = declarative_base()

class Birthday_Table(Base):  
    __tablename__ = "birthday_table"
    uid = Column(String, primary_key=True)
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
        except Exception as e:
            print(e)
            return False


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["circlejerk"])
    async def birthday(self, ctx, birthday_str = None):
        author = ctx.message.author
        uid = author.id
        user = session.query(Birthday_Table).filter_by(uid=uid).first()

        # Try to enter args into db
        if birthday_str:
            birthday = self._parse_birthday(birthday_str)

            if not birthday:
                await self.bot.say(content=None, embed=create_error("creating birthday. Format: `YYYY-MM-DD`"))
                return False

            if not user:
                birthday = Birthday_Table(uid=uid, birthday=birthday, times_changed=0)
                session.add(birthday)
            else:
                user.birthday = birthday
                if uid != config["owner_ids"]:
                    user.times_changed = user.times_changed+1

            try:
                session.commit()
            except Exception as e:
                print(e)
                await self.bot.say(content=None, embed=create_error("entering into database."))
                return False
            
            emb = discord.Embed(color=0xffffff)
            emb.set_author(name=f"{author.nick if author.nick else author.name}")
            emb.description = "Birthday set."
            await self.bot.say(content=None, embed=emb)

        elif user:
            year = user.birthday.year
            month = user.birthday.month
            day = user.birthday.day
            emb = discord.Embed(color=0xffffff)
            emb.set_author(name=f"{author.nick if author.nick else author.name}")
            emb.description = f"Birthday set to {year}-{month}-{day}."
            if user.times_changed < 2:
                emb.description += f"\n_You have changed your birthday {user.times_changed} times ({2-user.times_changed} times left)._"
            await self.bot.say(content=None, embed=emb)

        else:
            await self.bot.say(content=None, embed=create_error("- use -birthday `YYYY-MM-DD` to enter your birthday."))


    @commands.command(pass_context=True, invoke_without_command=True)
    async def today(self, ctx):
        date = datetime.datetime.now().date()
        users = session.query(Birthday_Table)\
                .filter(extract('day', Birthday_Table.birthday) == date.day)\
                .filter(extract('month', Birthday_Table.birthday) == date.month)\
                .all()

        if users:
            for user in users:
                emb = discord.Embed(color=0xffffff)
                emb.description = f"Happy birthday to <@!{user.uid}>"
                await self.bot.say(content=None, embed=emb)

        else:
            emb = discord.Embed(color=0xffffff)
            emb.description = f"No birthday bois today."


def setup(bot):
    bot.add_cog(Birthday(bot))
    