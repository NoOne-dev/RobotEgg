import discord
import json
from discord.ext import commands
from config import config
from cogs.utils.fetch import fetch
from cogs.utils.create_error import create_error
from cogs.utils.checks import channels_allowed


class Bible:
    """Gets a verse from the bible"""

    def __init__(self, bot):
        self.bot = bot
        self.replacements = {
            "Jesus": "Tomo Buddy", "David": "Nek", "Moses": "Dan 'the Gheese'", "Jacob": "Robert 'Alpacapatrol'", "Saul": "MALF",
            "Aaron": "Austin", "Abraham": "Daddy NL", "Abram": "Daddy NL", "Solomon": "GOLDMAN", "Joseph": "Dan", "Paul": "Sinvicta",
            "Joshua": "J O S H", "Peter": "K8", "Jeremiah": "Eluc", "God": "Big Daddy", "Adam": "The First Egg", "Lord": "Egg",
            "Judas": "the Funeral Director", "give": "acquiesce", "Give": "Acquiesce"
            }


    async def _get_verse(self, param: str):
        try:
            url = "http://labs.bible.org/api/"
            params = dict(passage=param,
                          formatting="plain",
                          type="json")
            
            msg = await fetch(url, params=params)
            msg = json.loads(msg)[0]

            return msg
        except Exception as e:
            print(e)
            return False


    def _build_embed(self, msg: dict, author, type: str):
        colors  = {"random": 0xff84a7, "daily": 0xffffff, "verse": 0xc3f945}

        try:
            for key in self.replacements:
                msg['text'] = msg['text'].replace(key, self.replacements[key])

            emb = discord.Embed(title=f"{msg['bookname']} {msg['chapter']}:{msg['verse']}", description=f"{msg['text']}", color=colors[type])          #Create the embed object
            emb.set_footer(text=f"And bless you, {author.nick if author.nick else author.name}")

            return emb
        except Exception as e:
            print(e)
            return create_error("building embed")


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["circlejerk"])
    async def random(self, ctx):
        await self.bot.send_typing(ctx.message.channel)
        try:
            msg = await self._get_verse("random")
            emb = self._build_embed(msg, ctx.message.author, "random")

            await self.bot.say(content=None, embed=emb)

        except Exception as e:
            print(e)
            await self.bot.say(content=None, embed=create_error("getting a random verse"))


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["circlejerk"])
    async def daily(self, ctx):
        await self.bot.send_typing(ctx.message.channel)
        try:
            msg = await self._get_verse("votd")
            emb = self._build_embed(msg, ctx.message.author, "daily")

            await self.bot.say(content=None, embed=emb)

        except Exception as e:
            print(e)
            await self.bot.say(content=None, embed=create_error("getting daily verse"))


    @commands.command(pass_context=True, invoke_without_command=True)
    @channels_allowed(["circlejerk"])
    async def verse(self, ctx, *args):
        await self.bot.send_typing(ctx.message.channel)
        try:
            requested_verse = f"{args[0]} {args[1]}"
            msg = await self._get_verse(requested_verse)
            emb = self._build_embed(msg, ctx.message.author, "verse")

            await self.bot.say(content=None, embed=emb)

        except Exception as e:
            print(e)
            await self.bot.say(content=None, embed=create_error("getting your verse"))


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case SimpleCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(Bible(bot))
