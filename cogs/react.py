import discord
from discord.ext import commands
from config import config


class React:
    """Reacts to keywords"""

    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        args = message.content.lower().split(' ')
        getrole = {'anime': 'BeAdvised', 'mod': 'HyperAdvised', 'egg': 'eggGasm', 
                     'dan': 'DanAdvised', 'scringis': 'lionWut'}

        if args[0] == '+getrole' and args[1] in getrole:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name=getrole[args[1]])
            await self.bot.add_reaction(message, emoji)

        if 'delet' in args:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='nukeplz')
            await self.bot.add_reaction(message, emoji)

        if '<@&346251636517109770>' in args or '<@&346251636517109770>s' in args:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='BeAdvised')
            await self.bot.add_reaction(message, emoji)

        if 'fuck' in args and 'mathas' in args:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='BeAdvised')
            await self.bot.add_reaction(message, emoji)

        if 'overwatch' in args or 'overwatch,' in args:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='ULU')
            await self.bot.add_reaction(message, emoji)

        ricks = ['rick', 'jidril', 'rickon', 'richard', 'dick', 'sheldon', 'young', 'mod', 'bick', 'yeet', 'wek', 'song']
        if 'pickle' in args and args[args.index('pickle')+1] in ricks:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='lionSalt')
            await self.bot.add_reaction(message, emoji)

        if 'delete' in args and args[args.index('delete')+1] == 'this' and args[args.index('delete')+2] == 'server':
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='nukeplz')
            await self.bot.add_reaction(message, emoji)

        if 'dead' in args and args[args.index('dead')+1] == 'hours':
            emoji = '💀'
            await self.bot.add_reaction(message, emoji)

        dontatme = ["dont at me", "don't at me", "dont @ me", "don't @ me"]
        if ' '.join(args[0:3]) in dontatme:
            channel = self.bot.get_channel('346601597335240704')  #bot-commands
            await self.bot.send_message(channel, f'<@!{message.author.id}>')

        realeuhours = ["real eu hours", "real eu hour", "false eu hours", "real na hours", "real oce hours"]
        if ' '.join(args[0:3]) in realeuhours:
            emoji = '🇪🇺'
            await self.bot.add_reaction(message, emoji)

# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(React(bot))
    