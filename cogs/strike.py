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
import aiohttp

"""
Keeps track of strikes
"""

class BetaStrike:
    """Keep track of user strikes"""
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.BASE_URL = "https://qtto.pythonanywhere.com"
        self.MAX_STRIKE_POINTS = 12
        self.API_KEY = config["tokens"]["strike"]
        

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


    async def _confirm_action(self, confirmation, mod):
        """Have mod confirm their action"""
        def check(reaction, user):
            """Check if the reaction is by the bot and then if it's an OK or a not OK"""
            if user.id == msg.author.id:
                pass
            else:
                return user.id == mod.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '🛑')

        msg = await self.bot.say(confirmation)

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


    async def _get_tier(self, mod):
        """Gets the strike tier"""

        def check(message):
            """Check if the strike tier exists"""
            try:
                int(message.content) < 6 and int(message.content) > 0
                return True
            except:
                return False

        message = "Provide a tier (1-5) for this strike (guidelines: https://vgy.me/3KgA3V.png)"
        message += "\n_1: green_\n_2: yellow_\n_3: orange_\n_4: red_\n_5: carmine_"
        msg = await self.bot.say(message)
        await self._deletion_queue(msg)

        user_msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)
        if user_msg and not user_msg.attachments:
            await self._deletion_queue(user_msg)

        resp = user_msg.clean_content if user_msg else False

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

        await self.bot.say(content=None, embed=create_error("- no user found in your message"))
        return False


    async def _get_user_strikes(self, id):
        headers = {"authorization": self.API_KEY}
        text = "" 
        # Get the strikes and the strike IDs for the specified user
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.BASE_URL}/user/{id}', headers=headers) as resp:
                try:
                    text = await resp.json()
                except:
                    await self.bot.say(content=None, embed=create_error("- something went wrong getting strikes"))
                    return False
        
        try:
            text['user']
        except:
            await self.bot.say(content=None, embed=create_error("- this user doesn't have any strikes, it seems"))
            return False
        
        return text


    @commands.command(pass_context=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def strike(self, ctx):
        """Add a strike to the database"""
        async def cancel_action():
            await self.bot.say("Cancelled.")
            await self._deletion_queue(None, delete=True)
            return False

        user = await self._parse_user(ctx)
        if not user:
            return False

        mod = ctx.message.author
        await self._deletion_queue(ctx.message)

        if not await self._confirm_action(f"Strike: <@!{user.id}>. Is this correct?", mod):
            return await cancel_action()

        reason = await self._get_reason(mod) #Get a reason
        if not reason:
            return await cancel_action()

        notes = await self._get_notes(mod) #Get any further notes

        tier_id = await self._get_tier(mod) #Get any further notes
        if not tier_id:
            return await cancel_action()

        if not await self._confirm_action(f"Giving <@!{user.id}> a tier {tier_id} strike for {reason}. Is this correct?", mod):
            return await cancel_action()

        notes = '' if not notes else notes

        strike = {
            "user_id": user.id,
            "created_by": mod.id,
            "reason": reason,
            "attachment": notes,
            "tier_id": tier_id
        }
        
        headers = {"authorization": self.API_KEY}
        text = ""

        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.BASE_URL}/strike', data=strike, headers=headers) as resp:
                text = await resp.json()

        mod_message = f"<@!{mod.id}> has given user <@!{user.id}> a strike.\n\n"
        mod_message += f"**Reason:** {reason}\n"
        if notes:
            mod_message += f"**Notes:** {notes}\n"
        
        
        mod_message += f"\nUser has **{text['user_points']} strike points**. "
        if text['user_points'] < self.MAX_STRIKE_POINTS:
            mod_message += f"Mute this user for {text['mute']} hours."
        else:
            mod_message += "**This user should be banned.**"
        mod_message += f"\nView strikes at {self.BASE_URL}/#user/{user.id}"
        await self.bot.say(mod_message)
        await self._deletion_queue(None, delete=True)

        user_message = f"Hi {user.name},\n\nYou have received a strike in Eggserver.\n\n"
        user_message += f"**Reason:** {reason}.\n"
        user_message += f"You now have **{text['user_points']} strike points**, "
        user_message += f"view your strikes at {self.BASE_URL}/#user/{user.id}.\n"
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

        text = await self._get_user_strikes(user.id)
        if not text:
            return False

        ids = {}
        counter = 1
        message = ""
        for item in text["strikes"]:
            strike = f"Strike {counter} ({item['tier']} tier)\n  - {item['reason']}"
            if item['removed']:
                strike = f"```haskell\n#REMOVED\n{strike}```\n"
            elif item['expired']:
                strike = f"```haskell\n#EXPIRED\n{strike}```\n"
            else:
                strike = f"```haskell\n{strike}```\n"
            
            if len(message) + len(strike) < 2000:
                message += strike
            else:
                await self.bot.say(message)
                message = strike
            
            if not item['expired'] and not item['removed']:
                ids[counter] = item['id']
            
            counter += 1

        await self.bot.say(message)

        prompt_msg = await self.bot.say(content="**Strike to remove:**")
        await self._deletion_queue(prompt_msg)

        user_msg = await self.bot.wait_for_message(timeout=120.0, author=mod, check=check)
        if user_msg:
            await self._deletion_queue(user_msg)

        if not user_msg.content:
            return False

        removal_message = f'<@!{mod.id}> removed strike {user_msg.content} from <@!{user.id}>.'
        try:
            index = ids[int(user_msg.content)]
            data = {
                "removed_by": mod.id
            }

            headers = {"authorization": self.API_KEY}
            async with aiohttp.ClientSession() as session:
                async with session.delete(f'{self.BASE_URL}/strike/{index}', data=data, headers=headers) as resp:
                    text = await resp.json()
            
            await self.bot.say(removal_message)
        except Exception as e:
            await self.bot.say(content=None, embed=create_error(f"deleting from DB: {e}"))
            return False

        await self._deletion_queue(delete=True)


    @commands.command(pass_context=True)
    @channels_allowed(["mod-commands"])
    @is_mod()
    async def strikes(self, ctx):
        """Check user"""

        user = await self._parse_user(ctx)
        if not user:
            return False

        text = await self._get_user_strikes(user.id)
        if not text:
            return False

        counter = 1
        message = ""
        message += f"Information for user <@!{text['user']['id']}>. Strike points: `{text['user']['strike_points']}/{self.MAX_STRIKE_POINTS}`."
        for item in text["strikes"]:
            strike = f"Strike {counter} ({item['tier']} tier)\n  - {item['reason']}"
            if item['removed']:
                strike = f"```haskell\n#REMOVED\n{strike}```\n"
            elif item['expired']:
                strike = f"```haskell\n#EXPIRED\n{strike}```\n"
            else:
                strike = f"```haskell\n{strike}```\n"
            
            if len(message) + len(strike) < 2000:
                message += strike
            else:
                await self.bot.say(message)
                message = strike
            
            counter += 1

        await self.bot.say(message)


def setup(bot):
    bot.add_cog(BetaStrike(bot))
    