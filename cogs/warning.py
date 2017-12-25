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
        self.queue = []

    
    async def _deletion_queue(self, message=None, delete=False):
        """Set messages to delete"""
        if message:
            self.queue.append(message)

        if delete:
            for message in self.queue:
                await self.bot.delete_message(message)
        
        return True


    def _get_warning_message(self, user_id, ids=False):
        """Generate message showing warnings"""
        warnings = session.query(Warning_Table).filter_by(user_id=user_id).all()

        id_list = []
        message = f"**Warnings for <@!{user_id}>**\n"
        if len(warnings) == 0:
            message = "There are no warnings for this user."
        else:
            count = 1
            for warning in warnings:
                if ids:
                    id_list.append(warning.index)
                    message += f"\n**Warning ID {warning.index}:**\n"
                else:
                    message += f"\n**Warning {count}:** \n"
                message += f"    _Date:_ {warning.created_on.year}-{warning.created_on.month}-{warning.created_on.day}\n"
                message += f"    _By:_ <@!{warning.created_by}>\n"
                message += f"    _Reason:_ {warning.reason}\n"
                if warning.notes:
                    message += f"    _Notes:_ {warning.notes}\n\n"       
                count += 1

        if ids:
            return message, id_list
        return message


    async def _get_more_info(self, id_dict):
        """Waits for user to provide a number to generate a warning list for"""
        def check(message):
            """Checks if the given user was present in the list"""
            if message.content in id_dict:
                return True
            return False

        msg = await self.bot.wait_for_message(timeout=30.0, check=check)

        if msg:
            user_id = id_dict[msg.content]
            msg = self._get_warning_message(user_id)
            await self.bot.say(msg)


    async def _check_user(self, user, mod):
        """Check if the correct user is being warned"""
        msg = await self.bot.say(f"Warning: <@!{user.id}>. Is this correct?")

        await self.bot.add_reaction(msg, '✅')
        await self.bot.add_reaction(msg, '🛑')

        def check(reaction, user):
            """Check if the reaction is by the bot and then if it's an OK or a not OK"""
            if user.id == msg.author.id:
                pass
            else:
                return user.id == mod.id and str(reaction.emoji) == '✅' or str(reaction.emoji) == '🛑'

        react = await self.bot.wait_for_reaction(timeout=60.0, message=msg, check=check)
        if react:
            return str(react.reaction.emoji) == '✅'
        return False


    async def _get_reason(self, mod):
        """Gets a reason from the reporting party"""

        reason_msg = "Please provide a reason. Enter a message or choose a premade warning. Type 'stop' to cancel.\n"
        premade = {"1": "NSFW content",
                   "2": "Very disturbing content",
                   "3": "Use of slurs",
                   "4": "Harassment / personal attacks",
                   "5": "Spam",
                   "6": "Posting links to other Discord servers",
                   "7": "Breaking Discord ToS"}
        for key in premade:
            reason_msg += f"\n{key}: {premade[key]}"

        msg = await self.bot.say(reason_msg) #Ask user to enter a reason

        def check(message):
            """Check if the reason is valid: either stop, premade or with a given length."""
            if message.content == 'stop' or message.content in premade:
                return True
            if len(message.content) < 5:
                self.bot.say('Provide a valid reason.')
            if len(message.content) > 500:
                self.bot.say('Given reason is too long.')
            return len(message.content) > 5 and len(message.content) < 500

        #Wait for the user to enter a reason
        await self._deletion_queue(msg)
        user_msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)

        #If no reason was given then return false
        resp = user_msg.clean_content if user_msg else False

        if user_msg.content in premade:
            resp = premade[user_msg.content]

        await self._deletion_queue(user_msg)

        if resp == 'stop':
            return False

        return resp


    async def _get_notes(self, mod):
        """Gets any notes from the reporting party"""
        msg = await self.bot.say(f"Optional: provide any notes or attachments (such as screenshots) or reply with 'done' to skip the wait.")

        def check(message):
            """Check if a note should be entered and if the length is valid"""
            if message.content.lower() == 'done':
                return True
            if len(message.content) > 500:
                self.bot.say('Note is too long.')
            return len(message.content) < 500

        await self._deletion_queue(msg)
        user_msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)

        resp = user_msg.clean_content if user_msg else False

        await self._deletion_queue(user_msg)

        if resp == 'done':
            return False

        # Attach the link of any attachment to the note
        if user_msg.attachments:
            for attachment in user_msg.attachments:
                resp += f' << attachment: {attachment["url"]} >>'

        return resp


    @commands.command(pass_context=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def warn(self, ctx):
        """Add a warning to the database"""
        try:
            # Find the user to warn in message mentions
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

        if await self._check_user(user, mod): #Correct user confirmation
            reason = await self._get_reason(mod) #Get a reason
            if not reason:
                msg = await self.bot.say("Cancelled.")
                await self._deletion_queue(delete=True)
                return False
            notes = await self._get_notes(mod) #Get any further notes
        else:
            msg = await self.bot.say("Cancelled.")
            await self._deletion_queue(delete=True)
            return False

        notes = '' if not notes else notes

        warning = Warning_Table(
            user_id=user.id,
            created_by=mod.id,
            created_on=date,
            reason=reason,
            notes=notes
        )
        session.add(warning) 

        try:
            session.commit() # Add it to the DB
        except Exception as e:
            print(e)
            await self.bot.say(content=None, embed=create_error("entering warning into database: {e}"))

        # Tell the mod and the user about the warning
        count = session.query(Warning_Table).filter_by(user_id=user.id).count()

        mod_message = f"<@!{mod.id}>, you have warned user <@!{user.id}>.\n\n"
        mod_message += f"**Reason:** {reason}\n"
        if notes:
            mod_message += f"**Notes:** {notes}\n"
        mod_message += f"\nUser has **{count} {'warnings' if count > 1 else 'warning'}**."
        await self.bot.say(mod_message)


        user_message = f"Hi {user.name},\n\nYou have received a warning in Eggserver Alpha.\n\n"
        user_message += f"**Reason:** {reason}.\n"
        user_message += f"You have **{count} {'warnings' if count > 1 else 'warning'}**.\n\n"
        user_message += f"If you have any further questions or concerns, please ask the mods."
        try:
            await self.bot.send_message(user, content=user_message)
        except Exception as e:
            await self.bot.say(f"<@!{mod.id}>: error DMing <@!{user.id}>. Please follow up. ({e})")


    @commands.command(pass_context=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def removewarning(self, ctx):
        """Remove warning from user"""
        user = ctx.message.mentions
        mod = ctx.message.author
        if len(user) != 1:
            await self.bot.say(content=None, embed=create_error("Please specify exactly one user."))
            return False

        user = user[0]

        # Get the warnings and the warning IDs for the specified user
        message, ids = self._get_warning_message(user.id, ids=True)
        await self.bot.say(message)
        prompt_msg = await self.bot.say(content="Enter the ID of the warning to remove.")
        self._deletion_queue(msg)

        def check(message):
            """Check if the warning to remove is indeed valid"""
            try:
                return int(message.content) in ids
            except:
                self.bot.say(content=None, embed=create_error("Enter a valid warning ID"))
                return False

        msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)
        await self._deletion_queue(msg)

        if not msg.content:
            return False

        try:
            index = int(msg.content)
            record = session.query(Warning_Table).get(index)
            session.delete(record)
            session.commit()
        except Exception as e:
            await self.bot.say(content=None, embed=create_error(f"Error deleting from DB: {e}"))
            return False

        await self._deletion_queue(delete=True)
        await self.bot.say(f"Removed warning with ID {index}.")


    @commands.command(invoke_without_command=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def warninglist(self):
        """Generate complete list of warnings"""
        message = '`,-------------------------------------------------------------.`\n'
        message += '`| #   | Amount  | User                                        |`\n'
        id_dict = {}
        count = 1
        for row in session.query(Warning_Table.user_id).distinct():
            row = row[0]
            id_dict[str(count)] = row
            warnings = session.query(Warning_Table).filter_by(user_id=row).count()
            warnings = f"`| {count}{((4-len(str(count)))*' ')}| {warnings}{((8-len(str(warnings)))*' ')}|`  <@!{row}>\n"
            if len(message) + len(warnings) < 1000:
                message += warnings
            else:
                await self.bot.say(message)
                message = warnings
            count += 1

        message += "`'-------------------------------------------------------------'`"
        await self.bot.say(message)

        # If a mod enters a number give more info about the warnings of that user
        await self._get_more_info(id_dict)


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

        message = self._get_warning_message(user.id)

        if ctx.message.channel.id == config["channels"]["mod-commands"]:
            await self.bot.say(message)
        else:
            if ctx.message.author.id == user.id:
                await self.bot.send_message(user, content=message)
            else:
                await self.bot.say(content=None, embed=create_error("You may only view your own warnings."))


def setup(bot):
    bot.add_cog(Warning(bot))
    