"""duck-bot for Holberton codewars server."""

import discord
from discord.ext import commands
import json
from pathlib import Path

from discord.utils import utcnow

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def load_config(config_file: str) -> dict:
    """"""
    with open(config_file, "r") as conf:
        return json.load(conf)


def config_update(
    config_file: str, key: str, value: str | bool | list | dict
) -> dict:
    """"""
    config = load_config(config_file)
    config[key] = value
    with open(config_file, "w") as conf:
        json.dump(config, conf)
    return config


global congig
config = load_config("config.json")
dailykata = config["dailykata"]
bots = config["bots"]
clan_list = config["clan_list"]
BOTTOKEN = config["BOTTOKEN"]
daily_challenge = config["daily_challenge"]


def langtoemote(langs: list) -> str:
    """"""
    emotes = config["emotes"]
    newlangs = []
    for lang in langs:
        if lang in emotes.keys():
            newlangs.append(emotes[lang])
        else:
            newlangs.append(str("`" + lang + "`"))
    return ", ".join(newlangs)
    # <:oh_i_c:1532006641296212111>


@bot.command()
async def set_kata(ctx: commands.context.Context, kata_url: str) -> None:
    """"""
    global config

    kata_id = kata_url.split("/")[-1]
    config = config_update(config["config_file"], "dailykata", kata_id)
    date = utcnow().date()

    if ctx.guild is None:
        raise TypeError("Guild Not Found")
    challenge_channel = await ctx.guild.fetch_channel(daily_challenge)
    try:
        await challenge_channel.send(
            f"@here the kata for {date} will be: "
            + f"{'https://www.codewars.com/kata/' + config['dailykata']}"
        )
    except BaseException as e:
        print(f"Could not post to {challenge_channel}")
        raise e


@bot.event
async def on_member_join(member) -> None:
    """When someone joins, ask them to register."""
    print("The type of member is: " + str(type(member)))
    embed = discord.Embed(
        title="Welcome!",
        description=(
            f"Hi {member.mention}!"
            + " Please register your codewars username."
        ),
        color=discord.Color.blue(),
    )

    try:
        await member.send(embed=embed)
        await member.send("Use: `!register <your_codewars_username>`")
    except BaseException as err:
        print(f"Could not DM {member.name}")
        raise err


@bot.command()
async def get_unregistered(ctx: commands.context.Context) -> None:
    """"""
    mapping = load_mapping()
    unregistered = []
    for guild in bot.guilds:
        for member in guild.members:
            if member.name in bots:
                continue
            if str(member.id) not in mapping.keys():
                unregistered.append(member.name)
                embed = discord.Embed(
                    title="New bot!",
                    description=(
                        f"Hi {member.mention}!"
                        + "Please register your codewars username."
                    ),
                    color=discord.Color.blue(),
                )

                try:
                    await member.send(embed=embed)
                    await member.send(
                        "Use: `!register <your_codewars_username>`\n"
                        + "(PS. don't include the <> around your username)"
                    )
                except BaseException as err:
                    print(f"Could not DM {member.name}")
                    raise err

    list_text = "**Unregistered Members:**\n"
    for discord_name in unregistered:
        list_text += f"{discord_name}\n"

    await ctx.send(list_text)


@bot.command()
async def member_status(ctx: commands.context.Context) -> None:
    """Status of member codewars linking."""
    mapping = load_mapping()
    list_text = "**Members Registration Status:**\n"
    for guild in bot.guilds:
        for member in guild.members:
            if member.name in bots:
                continue
            if str(member.id) in mapping.keys():
                codewars_username = mapping[str(member.id)][
                    "codewars_username"
                ]
                list_text += f"{member.name} → {codewars_username}\n"
            else:
                list_text += f"{member.name} → :x:\n"
    await ctx.send(list_text)


@bot.command()
async def register(
    ctx: commands.context.Context, codewars_username: str
) -> None:
    """User registers their codewars username."""
    mapping = load_mapping()
    mapping[str(ctx.author.id)] = {
        "discord_username": ctx.author.name,
        "codewars_username": codewars_username,
    }
    save_mapping(mapping)

    await ctx.send(
        f"✓ Registered! `{codewars_username}` is now linked to your account."
    )
    print(f"{ctx.author.name} registered as {codewars_username}")


@bot.command()
async def stats_daily(ctx: commands.context.Context) -> None:
    """Daily stats for task completion."""
    from codewarschecker import check_stats

    clan = check_stats(dailykata)
    clanstats = ""
    for disc_id, member in clan.items():
        stats: str = ""
        stats += f"<@{disc_id}>:\n"
        stats += (
            "\t"
            + "**codewars_username**:    "
            + str(member["codewars_username"])
            + "\n"
        )
        stats += (
            "\t"
            + "**completed**:                        "
            + str(":white_check_mark:" if member["completed"] else ":x:")
            + "\n"
        )
        if member["completed"]:
            stats += "\t" + "**languages**:                         "
            stats += langtoemote(member["languages"])
            stats += "\n"
        clanstats += "\n" + stats
    await ctx.send(clanstats)


def load_mapping() -> dict:
    """Load existing mapping or create empty one.

    Returns:
        dictionry of users discord and codewars usernames.

    """
    if Path(clan_list).exists():
        with open(clan_list, "r") as file:
            return json.load(file)
    return {}


def save_mapping(data: dict) -> None:
    """Save mapping to file."""
    with open(clan_list, "w") as f:
        json.dump(data, f, indent=2)


@bot.event
async def on_ready():
    """"""
    print(f"Bot is ready as {bot.user}")


bot.run(BOTTOKEN)
