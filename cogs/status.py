import datetime
import json
import discord
from discord.ext import commands
from config import config
from cogs.utils.fetch import fetch
from cogs.utils.create_error import create_error
from cogs.utils.checks import channels_allowed


"""
Tells you the status of given twitch streamers
"""


class Status:
    """Stream status listings"""
    def __init__(self, bot):
        self.bot = bot
        self.twitch_token = config["tokens"]["twitch"]
        self.streamers = config["streamers"]
        self.channels = [config["channels"]["nlss-chat"], config["channels"]["testing"]]


    def _check_main(self, twitch_status, main):
        """
        Checks if the channel defined as 'main' is streaming;
        checks the ones in 'others' as well.
        """
        if twitch_status["_total"] == 0:
            return False # No given streamers online

        for stream in twitch_status["streams"]:
            if stream["channel"]["display_name"] == main:
                return stream # main streamer online
        return False # only other streamers online


    def _build_uptime(self, created):
        """Returns formatted uptime string"""
        started = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
        now = datetime.datetime.utcnow()
        diff = now - started
        hours = diff.seconds // 3600
        mins = (diff.seconds // 60) - (60 * hours)
        return f"{hours} hr, {mins} min" if hours > 0 else f"{mins} min"


    def _build_embed(self, twitch_status, main):
        """Returns fancy embed for main streamer"""
        timestr = self._build_uptime(main["created_at"])

        emb = discord.Embed(url=main["channel"]["url"], color=0x933bce)  #Create the embed object
        emb.set_author(name=main["channel"]["display_name"], icon_url=main["channel"]["logo"])
        emb.set_thumbnail(url=main["preview"]["medium"])   
        emb.add_field(name="Live!", value=main["channel"]["status"], inline=False)
        emb.add_field(name="Currently playing", value=main["channel"]["game"], inline=False)
        emb.add_field(name="Viewers", value=main["viewers"])
        emb.add_field(name="Uptime", value=timestr)

        if twitch_status["_total"] > 1:
            emb.set_footer(text=f"There are other streamers online too! Check `!status others`.")
        else:
            emb.set_footer(text=f"No other streamers are online at this moment.")
        return emb


    async def _build_list(self, twitch_status, main):
        """Builds a list of everyone currently streaming"""
        try:
            emb = discord.Embed(color=0x933bce) 
            
            if not main: 
                if twitch_status["_total"] > 0:
                    emb.description = f"**[Northernlion](https://twitch.tv/Northernlion)**\n"
                    emb.description += f"Northernlion is not streaming at the moment."
                    
                    when_url = "http://whenisnlss.com/when"
                    try:
                        response = await fetch(when_url)
                        emb.description += f"\n{response}"
                    except:
                        print('Error getting when')
                
                else:
                    emb.color=0x333333
                    emb.description = "**Offline**\nNo NLSS members are streaming at the moment."

                    when_url = "http://whenisnlss.com/when"
                    try:
                        response = await fetch(when_url)
                        emb.description += f"\n{response}"
                    except:
                        print('Error getting when')
                    
                    return emb

            if twitch_status["_total"] > 0:
                build_string = ""

                for stream in twitch_status["streams"]:
                    timestr = self._build_uptime(stream["created_at"])

                    build_string += f'**[{stream["channel"]["display_name"]}]({stream["channel"]["url"]})**\n'
                    build_string += f'**{stream["channel"]["status"]}**\n'
                    build_string += f'Playing {stream["channel"]["game"]}\n'
                    build_string += f'`{timestr} uptime | {stream["viewers"]} viewers`\n\n'
    
                emb.add_field(name="Streamers to watch", value=build_string)
            
            return emb
        
        except Exception as e:
            print(e)
            return create_error("building stream list")


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["nlss-chat", "circlejerk"])
    async def status(self, ctx, *args):
        """Lists streams in specified or recommended way"""

        arg = ""
        try:
            arg = args[0]
        except:
            arg = "None given"

        channels = ','.join(self.streamers["other"])
        twitch_url = "https://api.twitch.tv/kraken/streams/"
        params = dict(channel=channels, 
                      client_id=self.twitch_token)

        await self.bot.send_typing(ctx.message.channel)
        try:
            response = await fetch(twitch_url, params=params)
            twitch_status = json.loads(response)

            main = self._check_main(twitch_status, self.streamers["main"]) # can be bool or object

            # Show status of main streamer if online
            if main and arg != "others":
                emb = self._build_embed(twitch_status, main)
                await self.bot.say(content=None, embed=emb)

            # Else or if specified, show other streamers instead
            elif not main or arg == "others":
                emb = await self._build_list(twitch_status, main)
                await self.bot.say(content=None, embed=emb)

        except Exception as e:
            print(f"{type(e).__name__}, {str(e)}")
            print(e)
            await self.bot.say(content=None, embed=create_error("getting stream information"))


# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(Status(bot))
