""""""

import discord
from discord import app_commands
from discord.ext import commands
from duckbot.helpers import load_config


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@app_commands.command(name="load", description="Load a specific cog")
async def load_cog(interaction: discord.Interaction, extension: str) -> None:
    """"""
    if f"duckbot.cogs.{extension}" in bot.extensions:
        await interaction.response.send_message(
            f"Cog '{extension}' already loaded."
        )
        return

    await bot.load_extension(f"duckbot.cogs.{extension}")
    await interaction.response.send_message(f"Cog '{extension}' loaded.")
    print(f"Cog '{extension}' has been loaded.")


@app_commands.command(name="unload", description="Unload a specific cog")
async def unload_cog(interaction, extension: str) -> None:
    """"""
    if f"duckbot.cogs.{extension}" not in bot.extensions:
        await interaction.response.send_message(
            f"Cog '{extension}' not loaded."
        )
        return

    await bot.unload_extension(f"duckbot.cogs.{extension}")
    await interaction.response.send_message(f"Cog '{extension}' unloaded.")
    print(f"Cog '{extension}' has been unloaded.")


@app_commands.command(name="reload", description="Reload a specific cog")
async def reload_cog(interaction, extension: str) -> None:
    """"""
    if f"duckbot.cogs.{extension}" in bot.extensions:
        await bot.unload_extension(f"duckbot.cogs.{extension}")

    if f"duckbot.cogs.{extension}" not in bot.extensions:
        await bot.load_extension(f"duckbot.cogs.{extension}")

    await interaction.response.send_message(f"Cog '{extension}' reloaded.")
    print(f"Cog '{extension}' has been reloaded.")


@bot.event
async def on_ready() -> None:
    """"""
    try:
        bot.tree.add_command(load_cog)
        bot.tree.add_command(unload_cog)
        bot.tree.add_command(reload_cog)
        await bot.load_extension("duckbot.cogs.core")
        await bot.load_extension("duckbot.cogs.codewars")
        await bot.tree.sync()
    except discord.app_commands.CommandAlreadyRegistered as err:
        print("error in on_ready, command already registered:")
        print(err.__cause__)
    print(f"Bot is ready as {bot.user}")


def main() -> None:
    """"""
    config: dict = load_config("config/config.json")
    bot.run(config["BOTTOKEN"])
