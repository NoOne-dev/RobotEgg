import discord
from config import config
from discord.ext import commands

def channels_allowed(channels):
    def predicate(ctx):
        allowed = [config["channels"]["bot-commands"], config["channels"]["testing"]]
        try:
            for channel in channels:
                allowed.append(config["channels"][channel])
        except Exception as e:
            print(e)
            return False
        return ctx.message.channel.id in allowed
    return commands.check(predicate)


def is_owner():
    def predicate(ctx):
        return ctx.message.author.id == config["owner_ids"]
    return commands.check(predicate)


def is_mod():
    def predicate(ctx):
        mod_role = discord.utils.get(ctx.message.author.server.roles, name=config["roles"]["mod"])
        return mod_role in ctx.message.author.roles
    return commands.check(predicate)
