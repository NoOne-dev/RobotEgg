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
Keeps track of strikes
"""

db = create_engine(os.environ['DATABASE_URL'])
Base = declarative_base()


class Strike_Table(Base):
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


class Strike:
    """Keep track of user strikes"""
    def __init__(self, bot):
        self.bot = bot
        self.queue = []



    async def _deletion_queue(self, message=None, delete=False):
        """Set messages to delete"""
        if message != None:
            self.queue.append(message)

        if delete:
            try:
                await self.bot.delete_messages(self.queue)
                self.queue = []
            except discord.ClientException: #try deleting them one by one
                try:
                    while self.queue:
                        await self.bot.delete_message(self.queue.pop())
                except:
                    return
            except Exception as e:
                print(e)



    def _get_strike_message(self, user_id, ids=False):
        """Generate message showing strikes"""
        strikes = session.query(Strike_Table).filter_by(user_id=user_id).all()
        id_list = []
        
        message = f"**Strikes for <@!{user_id}>**\n"
        
        if len(strikes) == 0:
            message = "There are no strikes for this user."
        else:
            count = 1
            for strike in strikes:
                if ids:
                    id_list.append(strike.index)
                    message += f"\n**Strike ID {strike.index}:**\n"
                else:
                    message += f"\n**Strike {count}:** \n"
                message += f"    _Date:_ {strike.created_on.year}-{strike.created_on.month}-{strike.created_on.day}\n"
                message += f"    _By:_ <@!{strike.created_by}>\n"
                message += f"    _Reason:_ {strike.reason}\n"
                if strike.notes:
                    message += f"    _Notes:_ {strike.notes}\n\n"
                count += 1

        if ids:
            return message, id_list
        return message



    async def _get_more_info(self, id_dict):
        """Waits for user to provide a number to generate a strike list for"""

        def check(message):
            """Checks if the given user was present in the list"""
            if message.content in id_dict:
                return True
            return False

        msg = await self.bot.wait_for_message(timeout=30.0, check=check)

        if msg:
            user_id = id_dict[msg.content]
            await self._deletion_queue(msg)
            msg = self._get_strike_message(user_id)
            await self.bot.say(msg)



    async def _check_user(self, user, mod):
        """Check if the correct user is being strikeed"""
        def check(reaction, user):
            """Check if the reaction is by the bot and then if it's an OK or a not OK"""
            if user.id == msg.author.id:
                pass
            else:
                return user.id == mod.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '🛑')

        msg = await self.bot.say(f"Strike: <@!{user.id}>. Is this correct?")

        await self.bot.add_reaction(msg, '✅')
        await self.bot.add_reaction(msg, '🛑')
        await self._deletion_queue(msg)

        react = await self.bot.wait_for_reaction(timeout=60.0, message=msg, check=check)
        if react:
            return str(react.reaction.emoji) == '✅'
        return False



    async def _get_reason(self, mod):
        """Gets a reason from the reporting party"""

        def check(message):
            """Check if the reason is valid: either stop, premade or with a given length."""
            if message.content.lower() == 'stop' or message.content in premade:
                return True
            if len(message.content) < 5:
                self.bot.say('Provide a valid reason.')
            if len(message.content) > 500:
                self.bot.say('Given reason is too long.')
            return len(message.content) > 5 and len(message.content) < 500

        reason_msg = "Please provide a reason. Enter a message or choose a premade one. Type 'stop' to cancel.\n"
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
        await self._deletion_queue(msg)

        #Wait for the user to enter a reason
        user_msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)
        if user_msg:
            await self._deletion_queue(user_msg)

        #If no reason was given then return false
        resp = user_msg.clean_content if user_msg else False

        if resp in premade:
            resp = premade[user_msg.content]

        if resp:
            if resp.lower() == 'stop':
                return False

        return resp



    async def _get_notes(self, mod):
        """Gets any notes from the reporting party"""

        def check(message):
            """Check if a note should be entered and if the length is valid"""
            if message.content.lower() == 'done':
                return True
            if len(message.content) > 500:
                self.bot.say('Note is too long.')
            return len(message.content) < 500

        msg = await self.bot.say(f"Optional: provide any notes or attachments (such as screenshots) or reply with 'done' to skip.")
        await self._deletion_queue(msg)

        user_msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)
        if user_msg and not user_msg.attachments:
            await self._deletion_queue(user_msg)

        resp = user_msg.clean_content if user_msg else False

        if resp:
            if resp.lower() == 'done':
                return False

        # Attach the link of any attachment to the note
        if user_msg.attachments:
            for attachment in user_msg.attachments:
                resp += f' [ attachment: {attachment["url"]} ]'

        return resp



    async def _parse_user(self, ctx, author=False):
        """Parse user from message"""
        user = ctx.message.mentions
        mentions = len(user)

        if mentions > 1:
            await self.bot.say(content=None, embed=create_error("- too many users specified"))
            return False

        elif mentions == 1:
            return user[0]

        elif mentions == 0 and not author:
            try:
                members = ctx.message.server.members
                query = ' '.join(ctx.message.content.lower().split(' ')[1:]) #get command outta there
                if not query:
                    return False

                for member in members:
                    if query == member.id:
                        return member
                    elif query == f"{member.name}#{str(member.discriminator)}".lower():
                        return member
                    elif query == member.name.lower():
                        return member
                    elif member.nick:
                        if query == member.nick.lower():
                            return member
            except Exception as e:
                await self.bot.say(content=None, embed=create_error(f"getting user: {e}"))
                return False

        elif mentions == 0 and author:
            return ctx.message.author

        await self.bot.say(content=None, embed=create_error("no user found in your message"))
        return False



    @commands.command(pass_context=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def strike(self, ctx):
        """Add a strike to the database"""
        user = await self._parse_user(ctx)
        if not user:
            return False

        mod = ctx.message.author
        await self._deletion_queue(ctx.message)
        date = datetime.datetime.now()

        if await self._check_user(user, mod): #Correct user confirmation
            reason = await self._get_reason(mod) #Get a reason
            if not reason:
                await self.bot.say("Cancelled.")
                await self._deletion_queue(None, delete=True)
                return False
            notes = await self._get_notes(mod) #Get any further notes
        else:
            await self.bot.say("Cancelled.")
            await self._deletion_queue(None, delete=True)
            return False

        notes = '' if not notes else notes

        strike = Strike_Table(
            user_id=user.id,
            created_by=mod.id,
            created_on=date,
            reason=reason,
            notes=notes
        )
        session.add(strike)

        try:
            session.commit() # Add it to the DB
        except Exception as e:
            print(e)
            await self.bot.say(content=None, embed=create_error("entering strike into database: {e}"))

        # Tell the mod and the user about the strike
        count = session.query(Strike_Table).filter_by(user_id=user.id).count()

        mod_message = f"<@!{mod.id}> has given user <@!{user.id}> a strike.\n\n"
        mod_message += f"**Reason:** {reason}\n"
        if notes:
            mod_message += f"**Notes:** {notes}\n"
        mod_message += f"\nUser has **{count} {'strikes' if count > 1 else 'strike'}**."
        await self.bot.say(mod_message)
        await self._deletion_queue(None, delete=True)


        user_message = f"Hi {user.name},\n\nYou have received a strike in Eggserver Alpha.\n\n"
        user_message += f"**Reason:** {reason}.\n"
        user_message += f"You have **{count} {'strikes' if count > 1 else 'strike'}**.\n\n"
        user_message += f"If you have any further questions or concerns, please ask the mods."
        try:
            await self.bot.send_message(user, content=user_message)
        except Exception as e:
            await self.bot.say(content=None, embed=create_error(f"DMing <@!{user.id}>. Please follow up. <@!{mod.id}>, ({e})"))



    @commands.command(pass_context=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def removestrike(self, ctx):
        """Remove strike from user"""
        def check(message):
            """Check if the strike to remove is indeed valid"""
            try:
                return int(message.content) in ids
            except:
                self.bot.say(content=None, embed=create_error("- enter a valid strike ID"))
                return False

        user = await self._parse_user(ctx)
        if not user:
            return False

        mod = ctx.message.author
        await self._deletion_queue(ctx.message)

        # Get the strikes and the strike IDs for the specified user
        message, ids = self._get_strike_message(user.id, ids=True)

        strike_msg = await self.bot.say(message)
        await self._deletion_queue(strike_msg)
        prompt_msg = await self.bot.say(content="Enter the ID of the strike to remove.")
        await self._deletion_queue(prompt_msg)

        user_msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)
        if user_msg:
            await self._deletion_queue(user_msg)

        if not user_msg.content:
            return False

        removal_message = ''
        try:
            index = int(user_msg.content)
            record = session.query(Strike_Table).get(index)
            session.delete(record)
            session.commit()
            removal_message += f"<@!{mod.id}> removed strike from <@!{user.id}> with ID {index}.\n"
            removal_message += f"Removed item: {record.reason}"
            await self.bot.say(removal_message)
        except Exception as e:
            await self.bot.say(content=None, embed=create_error(f"deleting from DB: {e}"))
            return False

        await self._deletion_queue(delete=True)



    @commands.command(invoke_without_command=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def table(self):
        """Generate complete list of strikes"""
        message = '`,-------------------------------------------------------------.`\n'
        message += '`| #   | Amount  | User                                        |`\n'
        id_dict = {}
        count = 1
        for row in session.query(Strike_Table.user_id).distinct():
            row = row[0]
            id_dict[str(count)] = row
            strikes = session.query(Strike_Table).filter_by(user_id=row).count()
            strikes = f"`| {count}{((4-len(str(count)))*' ')}| {strikes}{((8-len(str(strikes)))*' ')}|`  <@!{row}>\n"
            if len(message) + len(strikes) < 1000:
                message += strikes
            else:
                await self.bot.say(message)
                message = strikes
            count += 1

        message += "`'-------------------------------------------------------------'`"
        await self.bot.say(message)

        # If a mod enters a number give more info about the strikes of that user
        await self._get_more_info(id_dict)
        await self._deletion_queue(None, delete=True)



    @commands.command(pass_context=True, invoke_without_command=True)
    async def strikes(self, ctx):
        """Check strikes of user or self"""
        user = await self._parse_user(ctx, author=True)
        if not user:
            return False

        message = self._get_strike_message(user.id)

        if ctx.message.channel.id == config["channels"]["mod-commands"]:
            await self.bot.say(message)
        else:
            if ctx.message.author.id == user.id:
                await self.bot.send_message(user, content=message)
            else:
                await self.bot.say(content=None, embed=create_error("- you may only view your own strikes"))



def setup(bot):
    bot.add_cog(Strike(bot))
    