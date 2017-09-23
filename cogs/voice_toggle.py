import discord
from discord.ext import commands
from config import config


"""
Add/remove a specified role when a user joins/leaves any voice channel
"""


class VoiceToggle:
    """Toggle voice role"""

    def __init__(self, bot):
        self.bot = bot


    async def on_voice_state_update(self, before: discord.Member, after: discord.Member):
        """Fires when somebody's voice state changes"""

        voice_role = discord.utils.get(after.server.roles, name=config["roles"]["voice"])

        # check if user is actually in voice chat and try to add the role
        if after.voice.voice_channel != None:
            try:
                await self.bot.add_roles(after, voice_role)
            except Exception as e:
                print("Error adding role to user")
                print(e)

        # if the user is not in voice chat, try to remove the role instead
        else:
            try:
                await self.bot.remove_roles(after, voice_role)
            except Exception as e:
                print("Error removing role from user")
                print(e)


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(VoiceToggle(bot))
