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
        msg = await self.bot.say(f"Warning: <@!{user.id}>. Is this correct?")

        await self.bot.add_reaction(msg, '✅')
        await self.bot.add_reaction(msg, '🛑')

        def check(reaction, user):
            if user.id == msg.author.id:
                pass
            else:
                return user.id == mod.id and str(reaction.emoji) == '✅' or str(reaction.emoji) == '🛑'

        react = await self.bot.wait_for_reaction(timeout=60.0, message=msg, check=check)
        if react:
            return str(react.reaction.emoji) == '✅'
        return False


    async def _get_reason(self, mod):
        msg = await self.bot.say(f"Please provide a reason for the warning. Type 'stop' to cancel.")

        def check(message):
            if message.content == 'stop':
                return True
            if len(message.content) < 5:
                self.bot.say('Provide a valid reason.')
            if len(message.content) > 500:
                self.bot.say('Given reason is too long.')
            return len(message.content) > 5 and len(message.content) < 500

        msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)
        
        resp = msg.clean_content if msg else False

        if resp == 'stop':
            return False

        return resp


    async def _get_notes(self, mod):
        msg = await self.bot.say(f"Optional: provide any notes or attachments (such as screenshots) or reply with 'done' to skip the wait.")

        def check(message):
            if message.content.lower() == 'done':
                return True
            if len(message.content) > 500:
                self.bot.say('Note is too long.')
            return len(message.content) < 500

        msg = await self.bot.wait_for_message(timeout=120.0, author=mod)

        resp = msg.clean_content if msg else False

        if resp == 'done':
            return False

        if msg.attachments:
            for attachment in msg.attachments:
                resp += f' << attachment: {attachment["url"]} >>'

        return resp


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

            user = user[0]
            mod = ctx.message.author
            date = datetime.datetime.now()
        
        except Exception as e:
            await self.bot.say(content=None, embed=create_error(f"Error creating warning: {e}"))
            return False

        if await self._check_user(user, mod):
            reason = await self._get_reason(mod)
            if not reason:
                await self.bot.say("Cancelled.")
                return False
            notes = await self._get_notes(mod)
        else:
            await self.bot.say("Cancelled.")
            return False

        warning = Warning_Table(
            user_id=user.id,
            created_by=mod.id,
            created_on=date,
            reason=reason,
            notes=notes
        )
        session.add(warning)

        try:
            session.commit()
        except Exception as e:
            print(e)
            await self.bot.say(content=None, embed=create_error("entering warning into database: {e}"))

        count = session.query(Warning_Table).filter_by(user_id=user.id).count()
        await self.bot.say(f"<@!{mod.id}>, you have warned user <@!{user.id}>.\n\n**Reason:** {reason}\n**Notes:** {notes}\n\nUser has **{count} {'warnings' if count > 1 else 'warning'}**.")

        try:
            await self.bot.send_message(user, content=f"Hi {user.name},\n\nYou have received a warning in Eggserver Alpha.\n\n**Reason:** {reason}.\nYou have **{count} {'warnings' if count > 1 else 'warning'}**.\n\nIf you have any further questions or concerns, please ask the mods.")
        except:
            await self.bot.say(f"Error DMing <@!{user.id}>. Please follow up.")


    @commands.command()
    @is_mod()
    async def removewarning(self, ctx):
        """Remove warning from user"""
        pass


    @commands.command(pass_context=True, invoke_without_command=True)
    async def warnings(self, ctx):
        """Check warnings of user or self"""
        user = ctx.message.mentions
        if len(user) > 1:
            await self.bot.say(content=None, embed=create_error("Too many users specified"))
            return False

        if len(user) == 1:
            user = user[0]

        else:
            user = ctx.message.author

        warnings = session.query(Warning_Table).filter_by(user_id=user.id).all()

        if ctx.message.author.id == user.id:
            await self.bot.send_message(user, content=warnings)
        else:
            mod_role = discord.utils.get(ctx.message.author.server.roles, name=config["roles"]["mod"])
            if mod_role in ctx.message.author.roles:
                await self.bot.send_message(author, content=warnings)
            else:
                await self.bot.say(content=None, embed=create_error("You can only view your own warnings."))
        

def setup(bot):
    bot.add_cog(Warning(bot))
    