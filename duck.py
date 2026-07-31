"""duck-bot for Holberton codewars server."""

import datetime
import pytz
import json
from pathlib import Path
import discord
from discord.ext import commands
import requests

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# HELPERS SECTION
def load_config(config_file: str) -> dict:
    """"""
    with open(config_file, "r") as conf:
        return json.load(conf)


global config
config: dict = load_config("config.json")


def load_mapping() -> dict:
    """Load existing mapping or create empty one.

    Returns:
        dictionry of users discord and codewars usernames.

    """
    if Path(config["clan_list"]).exists():
        with open(config["clan_list"], "r") as file:
            return json.load(file)
    return {}


def save_mapping(data: dict) -> None:
    """Save mapping to file."""
    with open(config["clan_list"], "w") as f:
        json.dump(data, f, indent=2)


def save_config(
    config_file: str, key: str, value: str | bool | list | dict
) -> dict:
    """"""
    config = load_config(config_file)
    config[key] = value
    with open(config_file, "w") as conf:
        json.dump(config, conf)
    return config


def fetch_kata(kata_id: str) -> dict[str, str]:
    """Fetch name of kata and return dict of name and id."""
    kata = requests.get(
        f"https://www.codewars.com/api/v1/code-challenges/{kata_id}",
        timeout=500,
    ).json()
    return {"kata_name": kata["name"], "kata_id": kata_id}


def load_katalog() -> dict:
    """"""
    with open(config["kata_log"], "r") as log_file:
        kata_log = json.load(log_file)
    if kata_log is None:
        raise TypeError("kata_log is None")
    return kata_log


def save_katalog(
    config: dict, date: str, kata_id: str
) -> dict[str, dict[str, str]]:
    """"""
    kata_log = load_katalog()
    kata = fetch_kata(kata_id)
    kata_log[str(date)] = {"kata_id": kata["id"], "kata_name": kata["name"]}

    with open(config["kata_log"], "w") as log_file:
        json.dump(kata_log, log_file)

    return kata_log


def check_stats(dailykata: str) -> dict[str, dict]:
    """"""
    api: str = (
        "https://www.codewars.com/api/v1/users/{}/code-challenges/completed"
    )
    clanfile: str = "clan_list.json"
    with open(clanfile) as file:
        clan: dict[str, dict] = json.load(file)

    for member in clan.values():
        response = requests.get(
            api.format(member["codewars_username"]), timeout=50
        )
        member["response"] = response.json()

    for member in clan.values():
        try:
            for kata in member["response"]["data"]:
                if kata["id"] == dailykata:
                    member["completed"] = True
                    member["languages"] = kata["completedLanguages"]
                    del member["response"]
                    break
            else:
                member["completed"] = False
                del member["response"]
        except:
            print(member.items())
            print()
            exit(-1)
    return clan


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


def get_date() -> datetime.date:
    """"""
    timezone = pytz.timezone("Australia/Melbourne")
    return datetime.datetime.now(timezone).date()


@bot.command()
async def set_kata(ctx: commands.context.Context, kata_url: str) -> None:
    """"""
    date = get_date()
    kata_id = kata_url.split("/")[-1]
    kata_log = save_katalog(config, str(date), kata_id)

    if ctx.guild is None:
        raise TypeError("Guild Not Found")
    challenge_channel = await ctx.guild.fetch_channel(
        config["challenge_channel"]
    )
    try:
        await challenge_channel.send(  # type: ignore
            f"@here the kata for {date} will be: "
            + f"{'https://www.codewars.com/kata/' + kata_log[str(date)]['id']}"
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
            if member.name in config["bots"]:
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
            if member.name in config["bots"]:
                continue
            if str(member.id) in mapping.keys():
                codewars_username = mapping[str(member.id)][
                    "codewars_username"
                ]
                list_text += f"{member.name} → {codewars_username}\n"
            else:
                list_text += f"{member.display_name} → :x:\n"
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
    date = str(get_date())
    kata_log = load_katalog()
    clan = check_stats(kata_log[date]["id"])
    clanstats = f"Results for {date}: **{kata_log[date]['name']}**\n"
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


@bot.command()
async def stats_yesterday(ctx: commands.context.Context) -> None:
    """Daily stats for task completion."""
    from codewarschecker import check_stats

    date = str(get_date() - datetime.timedelta(days=1))
    kata_log = load_katalog()
    clan = check_stats(kata_log[date]["id"])
    clanstats = (
        f"@here\nResults for yesterday!!!: **{kata_log[date]['name']}**\n"
    )
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
    if ctx.guild is None:
        raise TypeError("Guild Not Found")
    challenge_channel = await ctx.guild.fetch_channel(config["stats_channel"])
    try:
        await challenge_channel.send(clanstats)  # type: ignore
    except BaseException as e:
        print(f"Could not post to {config['stats_channel']}")
        raise e


@bot.command()
async def stats_on(ctx: commands.context.Context, date: str) -> None:
    """Daily stats for task completion."""
    from codewarschecker import check_stats

    kata_log = load_katalog()
    clan = check_stats(kata_log[date]["id"])
    clanstats = f"Results for {date}: **{kata_log[date]['name']}**\n"
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


@bot.event
async def on_ready() -> None:
    """"""
    print(f"Bot is ready as {bot.user}")


bot.run(config["BOTTOKEN"])
