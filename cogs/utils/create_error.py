import discord

def create_error(error: str):
    return discord.Embed(title="Sorry!", description=f"Error {error}.", color=0xcc554d)
