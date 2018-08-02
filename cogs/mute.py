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
from cogs.utils.checks import is_manager


"""
Keeps track of mutes
"""

class Mute:
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


    async def _parse_user(self, ctx):
        """Parse user from message"""
        user = ctx.message.mentions
        mentions = len(user)

        if mentions > 1:
            await self.bot.say(content=None, embed=create_error("- too many users specified"))
            return False

        elif mentions == 1:
            return user[0]

        elif mentions == 0:
            try:
                members = ctx.message.server.members
                query = ' '.join(ctx.message.content.lower().split(' ')[1:])
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

        await self.bot.say(content=None, embed=create_error("- no user found in your message"))
        return False


    async def _getrole(self, ctx, role, all=False):
        dict = {"#events mute": discord.utils.get(ctx.message.author.server.roles, name="#events mute"),
                      "#rotating mute": discord.utils.get(ctx.message.author.server.roles, name="#rotating mute"),
                      "Big Discord Winner": discord.utils.get(ctx.message.author.server.roles, name="👑 Big Discord Winner"),
                      "Survivor": discord.utils.get(ctx.message.author.server.roles, name="👑 Survivor"),
                      "America's Favorite": discord.utils.get(ctx.message.author.server.roles, name="👑 America's Favorite")}
        
        if all:
            return dict
        
        return dict[role]

    
    async def _confirm_action(self, confirmation, manager):
        """Have manager confirm their action"""
        def check(reaction, user):
            """Check if the reaction is by the bot and then if it's an OK or a not OK"""
            if user.id == msg.author.id:
                pass
            else:
                return user.id == manager.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '🛑')

        msg = await self.bot.say(confirmation)

        await self.bot.add_reaction(msg, '✅')
        await self.bot.add_reaction(msg, '🛑')
        await self._deletion_queue(msg)

        react = await self.bot.wait_for_reaction(timeout=60.0, message=msg, check=check)
        if react:
            return str(react.reaction.emoji) == '✅'
        return False

    
    async def _pick_channel(self, manager, action, user):
        """Have manager pick the channel to mute in"""
        def check(reaction, user):
            if user.id == msg.author.id:
                pass
            else:
                return user.id == manager.id

        msg = await self.bot.say(f"Pick a channel to {action} <@!{user.id}> in (mathas: events, NL: rotating, X: cancel)")


        mathas = discord.utils.get(self.bot.get_all_emojis(), name='MathasStrong')
        NL = discord.utils.get(self.bot.get_all_emojis(), name='lionDoubt')

        await self.bot.add_reaction(msg, mathas)
        await self.bot.add_reaction(msg, NL)
        await self.bot.add_reaction(msg, '❌')
        await self._deletion_queue(msg)

        react = await self.bot.wait_for_reaction(timeout=60.0, message=msg, check=check)
        if react:
            try:
                if str(react.reaction.emoji.name) == "MathasStrong":
                    return "#events mute"
                elif str(react.reaction.emoji.name) == "lionDoubt":
                    return "#rotating mute"
                return False
            except:
                return False
        return False

    
    async def _toggle_role(self, ctx, role, user, strict=False):
        try:
            role = await self._getrole(ctx, role)
        except:
            return False

        if role in user.roles and strict != "mute":
            await self.bot.remove_roles(user,role)
            await self.bot.say(f"<@!{ctx.message.author.id}> removed `{role}` from <@!{user.id}>.")
            await self._deletion_queue(delete=True)
            return True

        elif role not in user.roles and strict != "unmute":
            await self.bot.add_roles(user,role)
            await self.bot.say(f"<@!{ctx.message.author.id}> gave `{role}` to <@!{user.id}>.")
            await self._deletion_queue(delete=True)
            return True
        
        return False


    async def _toggle_mute(self, ctx, mute):
        async def cancel_action():
            await self.bot.say("Cancelled.")
            await self._deletion_queue(None, delete=True)
            return False
        
        user = await self._parse_user(ctx)
        if not user:
            return False

        action = "mute" if mute else "unmute"
        manager = ctx.message.author
        role = await self._pick_channel(manager, action, user)

        if not role:
            return await cancel_action()

        if not await self._toggle_role(ctx, role, user, strict=action):
            await self.bot.say(content=None, embed=create_error(f"toggling role on <@!{user.id}>. Maybe they already have it?"))


    @commands.command(pass_context=True)
    @channels_allowed(["manager-chat"])
    @is_manager()
    async def mute(self, ctx):
        """mute a user"""        
        await self._toggle_mute(ctx, True)
        

    @commands.command(pass_context=True)
    @channels_allowed(["manager-chat"])
    @is_manager()
    async def unmute(self, ctx):
        """unmute a user"""
        await self._toggle_mute(ctx, False)


    @commands.command(pass_context=True)
    @channels_allowed(["manager-chat"])
    @is_manager()
    async def togglerole(self, ctx):
        """toggle a role"""
        def check(message):
            try:
                return int(message.content) < 6 and int(message.content) > 0
            except:
                return False

        async def cancel_action():
            await self.bot.say("Cancelled.")
            await self._deletion_queue(None, delete=True)
            return False

        msg = ""
        counter = 1
        roles = await self._getrole(ctx, None, True)
        rolenames = []
        for role in roles:
            msg += f"` {counter} ` _{role}_\n"
            rolenames.append(role)
            counter += 1
        
        user = await self._parse_user(ctx)
        if not user:
            return False

        manager = ctx.message.author
        
        msg = await self.bot.say(msg)
        await self._deletion_queue(msg)

        user_msg = await self.bot.wait_for_message(timeout=120.0, author=manager, check=check)
        if not user_msg:
            await self.bot.say(content=None, embed=create_error("that's not a valid response"))
            return False
        await self._deletion_queue(user_msg)

        role = rolenames[int(user_msg.content)-1]

        if not await self._confirm_action(f"Toggle `{role}` on <@!{user.id}>. Is this correct?", manager):
            return await cancel_action()
        
        if not await self._toggle_role(ctx, role, user):
            await self.bot.say(content=None, embed=create_error("toggling role"))
            return False


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["manager-chat"])
    @is_manager()
    async def rolelist(self, ctx):
        """Generate complete list of peeps"""
        members = ctx.message.server.members

        members_with_role = []
        roles = await self._getrole(ctx, None, True)
        for member in members:
            for role in roles:
                if roles[role] in member.roles:
                    members_with_role.append((member.id, role))
        
        message = ""
        for member in members_with_role:
            message += f"<@!{member[0]}> has `{member[1]}`\n"
        
        if message == "":
            await self.bot.say(content=None, embed=create_error("- no members with relevant roles"))
        
        await self.bot.say(message)


def setup(bot):
    bot.add_cog(Mute(bot))
    