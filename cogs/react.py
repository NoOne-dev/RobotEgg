import discord
from discord.ext import commands
from config import config


class React:
    """Reacts to keywords"""

    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        args = message.content.lower().split(' ')
        reactions = {'anime': 'BeAdvised', 'mod': 'HyperAdvised', 'egg': 'EggGasm', 
                     'dan': 'DanAdvised', 'scringis': 'lionWut'}

        if args[0] == '+getrole' and args[1] in reactions:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name=reactions[args[1]])
            await self.bot.add_reaction(message, emoji)


        if '<@&346251636517109770>' in args or '<@&346251636517109770>s' in args:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='BeAdvised')
            await self.bot.add_reaction(message, emoji)

        if 'fuck' in args and 'mathas' in args:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='BeAdvised')
            await self.bot.add_reaction(message, emoji)

        if 'overwatch' in args:
            emoji = discord.utils.get(self.bot.get_all_emojis(), name='ULU')
            await self.bot.add_reaction(message, emoji)


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(React(bot))
    