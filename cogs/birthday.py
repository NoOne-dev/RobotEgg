import asyncio
import datetime
import discord
import os
from discord.ext import commands
from config import config
from cogs.utils.create_error import create_error
from cogs.utils.checks import channels_allowed
from cogs.utils.checks import is_owner
from sqlalchemy import create_engine  
from sqlalchemy import Column, String, Integer, Date  
from sqlalchemy import func
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


class Notified(Base):  
    __tablename__ = "notified_today"
    uid = Column(String, primary_key=True)
    date = Column(Date)


Session = sessionmaker(db)  
session = Session()
Base.metadata.create_all(db)


class Birthday:
    """Keep track of people's birthdays"""
    def __init__(self, bot):
        self.bot = bot
        self.notifier_bg_task = bot.loop.create_task(self.notifier_task())


    def _parse_birthday(self, birthday_str):
        try:
            date = datetime.datetime.strptime(birthday_str, "%Y-%m-%d").date()
            return date
        except Exception as e:
            print(e)
            return False


    def _ordinal(self, n):
        return str(n)+("th" if 4 <= n%100 <= 20 else {1:"st", 2:"nd", 3:"rd"}.get(n%10, "th"))


    def _check_today(self):
        date = datetime.datetime.now().date()
        return session.query(Birthday_Table)\
                .filter(func.extract('day', Birthday_Table.birthday) == date.day)\
                .filter(func.extract('month', Birthday_Table.birthday) == date.month)\
                .all()


    async def notifier_task(self):
        """Runs a birthday notifier background task."""
        await self.bot.wait_until_ready()

        date = datetime.datetime.now().date()
        users = self._check_today()

        notified = session.query(Notified.uid).scalar()
        print(notified)

        session.query(Notified).filter(Notified.date < date).delete()

        for user in users:
            if notified is None or user.uid not in notified :
                channel = self.bot.get_channel('346251033527320577')
                emb = discord.Embed(color=0x76cef1)
                age = self._ordinal(date.year - user.birthday.year)
                emb.description = f":tada: Happy {age} birthday to <@!{user.uid}>! :tada:"
                await self.bot.send_message(channel, embed=emb)

                notif = Notified(uid=user.uid, date=date)
                session.add(notif)

        session.commit()
        print("notified")
        await asyncio.sleep(600)


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
                birthday = Birthday_Table(uid=uid, birthday=birthday, times_changed=1)
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
            
            emb = discord.Embed(color=0x76f2ac)
            emb.set_author(name=f"{author.nick if author.nick else author.name}")
            emb.description = f"Birthday set. Changed {user.times_changed if user else 1}/3 times."
            await self.bot.say(content=None, embed=emb)

        elif user:
            year = user.birthday.year
            month = user.birthday.month
            day = user.birthday.day
            emb = discord.Embed(color=0xffffff)
            emb.set_author(name=f"{author.nick if author.nick else author.name}")
            emb.description = f"Birthday set to {year}-{month}-{day}."
            emb.description += f"\n_You have changed your birthday {user.times_changed} times ({3-user.times_changed} times left)._"
            await self.bot.say(content=None, embed=emb)

        else:
            await self.bot.say(content=None, embed=create_error("- use -birthday `YYYY-MM-DD` to enter your birthday."))


    @commands.command(invoke_without_command=True)
    async def today(self):
        users = self._check_today()
        if users:
            for user in users:
                emb = discord.Embed(color=0x76cef1)
                age = self._ordinal(date.year - user.birthday.year)
                emb.description = f":tada: Happy {age} birthday to <@!{user.uid}>! :tada:"
                await self.bot.say(content=None, embed=emb)

        else:
            emb = discord.Embed(color=0xffffff)
            emb.description = f"No birthday boys today. :slight_frown:"
            await self.bot.say(content=None, embed=emb)


    @commands.command()
    @is_owner()
    async def addchange(self, uid):
        user = session.query(Birthday_Table).filter_by(uid=uid).first()
        user.times_changed -= 1
        session.commit()


    @commands.command()
    @is_owner()
    async def rollback(self):
        session.rollback()
        await self.bot.say(":thinking:")


    @commands.command()
    @is_owner()
    async def clear_notif(self):
        session.query(Notified).delete()
        session.commit()
        await self.bot.say("ok i have done what you asked of me")


def setup(bot):
    bot.add_cog(Birthday(bot))
    