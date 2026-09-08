"""duck-bot for Holberton codewars server."""

import datetime
from zoneinfo import ZoneInfo
import requests
import discord
from discord import app_commands
from discord.ext import commands, tasks
from pprint import pprint
from duckbot.helpers import (
    get_date,
    load_config,
    load_clan,
    save_clan,
    load_katalog,
    save_katalog,
    check_stats,
    strtoemote,
)


class Codewars(commands.Cog):
    """"""

    config_file: str = "config/config.json"
    zone = ZoneInfo(load_config(config_file)["timezone"])
    results_time = datetime.time(hour=7, minute=0, tzinfo=zone)
    next_level_time = datetime.time(hour=7, minute=5, tzinfo=zone)

    def __init__(self, bot: commands.bot.Bot) -> None:
        """"""
        self.bot = bot
        self.config: dict = load_config(self.config_file)
        self.daily_results.start()
        self.next_level_poll.start()

    @commands.command()
    async def set_kata(
        self, ctx: commands.context.Context, kata_url: str
    ) -> None:
        """"""
        print("Command: set_kata")
        date = get_date(self.config["timezone"])
        kata_id = kata_url.split("/")[-1]
        kata_log = save_katalog(self.config, str(date), kata_id)
        kata = kata_log[str(date)]

        if ctx.guild is None:
            await ctx.send("This command can only be run in a server")
            return
        challenge_channel = await ctx.guild.fetch_channel(
            self.config["challenge_channel"]
        )

        try:
            message = await challenge_channel.send(  # type: ignore
                f"@here the kata for {date} will be: "
                + "https://www.codewars.com/kata/"
                + kata["kata_id"]
                + "\n"
                + f"Rank: {kata['kata_rank']}"
            )
            await message.add_reaction(
                "".join(strtoemote(self.config["emotes"], [kata["kata_rank"]]))
            )
            await message.create_thread(name=f"{date} {kata['kata_name']}")
        except BaseException as e:
            print(f"Could not post to {challenge_channel}")
            raise e

    @commands.command()
    async def get_unregistered(self, ctx: commands.context.Context) -> None:
        """"""
        print("Command: get_unregistered")
        clan = load_clan(self.config)
        unregistered = []
        if ctx.guild is None:
            await ctx.send("This command can only be run in a server")
            return
        for member in ctx.guild.members:
            if member.name in self.config["bots"]:
                continue
            if str(member.id) not in clan.keys():
                unregistered.append(member.name)
                embed = discord.Embed(
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

    @commands.command()
    async def member_status(self, ctx: commands.context.Context) -> None:
        """Status of member codewars linking."""
        print("Command: member_status")
        clan = load_clan(self.config)
        list_text = "**Members Registration Status:**\n"

        if ctx.guild is None:
            await ctx.send("This command can only be run in a server")
            return

        for member in ctx.guild.members:
            if member.name in self.config["bots"]:
                continue
            if str(member.id) in clan.keys():
                codewars_username = clan[str(member.id)]["codewars_username"]
                list_text += f"{member.name} → {codewars_username}\n"
            else:
                list_text += f"{member.display_name} → :x:\n"
        await ctx.send(list_text)

    @commands.command()
    async def register(
        self, ctx: commands.context.Context, codewars_username: str
    ) -> None:
        """User registers their codewars username."""
        print("Command: register")
        clan = load_clan(self.config)
        clan[str(ctx.author.id)] = {
            "discord_id": str(ctx.author.id),
            "discord_username": ctx.author.name,
            "codewars_username": codewars_username,
        }
        save_clan(self.config, clan)

        await ctx.send(
            f"✓ Registered! `{codewars_username}`"
            + "is now linked to your account."
        )
        print(f"{ctx.author.name} registered as {codewars_username}")

    @commands.command()
    async def reregister(self, ctx: commands.context.Context) -> None:
        """"""
        print("Command: reregister")
        clan = load_clan(self.config)
        for discord_id, member in clan.items():
            user = self.bot.get_user(int(discord_id))
            if user is None:
                raise TypeError("User is None")
            member["discord_id"] = str(user.id)
            member["discord_username"] = user.name
        save_clan(self.config, clan)

    @commands.command()
    async def stats_daily(self, ctx: commands.context.Context) -> None:
        """Daily stats for task completion."""
        print("Command: stats_daily")
        date = str(get_date(self.config["timezone"]))
        kata_log = load_katalog(self.config)

        if date in kata_log.keys():
            clan = check_stats(self.config, kata_log[date]["kata_id"])
        else:
            await ctx.send(f"Error: kata for {date} unset")
            return
        clanstats = f"Results for {date}: **{kata_log[date]['kata_name']}**\n"
        for disc_id, member in clan.items():
            stats: str = (
                f"<@{disc_id}>:\n"
                + "\t**codewars_username**:    "
                + str(member["codewars_username"])
                + "\n\t**completed**:                        "
                + str(":white_check_mark:" if member["completed"] else ":x:")
                + "\n"
            )
            if member["completed"]:
                stats += str(
                    "\t**languages**:                         "
                    + "".join(
                        strtoemote(self.config["emotes"], member["languages"])
                    )
                    + "\n"
                )
            clanstats += "\n" + stats
        await ctx.send(clanstats)

    @commands.command()
    async def stats_yesterday(self, ctx: commands.context.Context) -> None:
        """Daily stats for task completion."""
        print("Command: stats_yesterday")
        date = str(
            get_date(self.config["timezone"]) - datetime.timedelta(days=1)
        )
        kata_log = load_katalog(self.config)
        clan = check_stats(self.config, kata_log[date]["kata_id"])
        clanstats = (
            "@here\nResults for yesterday!!!: "
            + f"**{kata_log[date]['kata_name']}**\n"
        )
        for disc_id, member in clan.items():
            stats: str = (
                f"<@{disc_id}>:\n"
                + "\t**codewars_username**:    "
                + str(member["codewars_username"])
                + "\n\t**completed**:                        "
                + str(":white_check_mark:" if member["completed"] else ":x:")
                + "\n"
            )
            if member["completed"]:
                stats += str(
                    "\t**languages**:                         ".join(
                        strtoemote(self.config["emotes"], member["languages"])
                    )
                    + "\n"
                )
            clanstats += "\n" + stats

        if ctx.guild is None:
            await ctx.send("This command can only be run in a server")
            return
        challenge_channel = await ctx.guild.fetch_channel(
            self.config["stats_channel"]
        )
        try:
            await challenge_channel.send(clanstats)  # type: ignore
        except BaseException as e:
            print(f"Could not post to {self.config['stats_channel']}")
            raise e

    @tasks.loop(time=results_time)
    async def daily_results(self) -> None:
        """Daily stats for task completion."""
        print("Command: daily_results")
        date = str(
            get_date(self.config["timezone"]) - datetime.timedelta(days=1)
        )
        kata_log = load_katalog(self.config)
        clan = check_stats(self.config, kata_log[date]["kata_id"])
        clanstats = (
            "@here\nResults for yesterday!!!: "
            + f"**{kata_log[date]['kata_name']}**\n"
        )
        for disc_id, member in clan.items():
            stats: str = (
                f"<@{disc_id}>:\n"
                + "\t**codewars_username**:    "
                + str(member["codewars_username"])
                + "\n\t**completed**:                        "
                + str(":white_check_mark:" if member["completed"] else ":x:")
                + "\n"
            )
            if member["completed"]:
                stats += str(
                    "\t**languages**:                         "
                    + ", ".join(
                        strtoemote(self.config["emotes"], member["languages"])
                    )
                    + "\n"
                )
            clanstats += "\n" + stats

        guild = self.bot.guilds[0]

        challenge_channel = await guild.fetch_channel(
            self.config["stats_channel"]
        )
        try:
            await challenge_channel.send(clanstats)  # type: ignore
        except BaseException as e:
            print(f"Could not post to {self.config['stats_channel']}")
            raise e

    @daily_results.before_loop
    async def before_daily_results(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()
        print("daily_results running")

    @commands.command()
    async def daily_results_is_running(
        self, ctx: commands.context.Context
    ) -> None:
        """"""
        print("daily_results_is_running was here")
        print(self.daily_results.is_running())
        print(f"Current time (Melbourne): {datetime.datetime.now(self.zone)}")
        print(f"Task next run: {self.daily_results.next_iteration}")
        print(f"Task time: {self.daily_results.time}")

    @commands.command()
    async def stats_on(self, ctx: commands.context.Context, date: str) -> None:
        """Daily stats for task completion."""
        print("Command: stats_on")
        kata_log = load_katalog(self.config)
        if date in kata_log.keys():
            clan = check_stats(self.config, kata_log[date]["kata_id"])
        else:
            await ctx.send(f"Error: kata for {date} unset")
            return
        clanstats = f"Results for {date}: **{kata_log[date]['kata_name']}**\n"
        for disc_id, member in clan.items():
            stats: str = (
                f"<@{disc_id}>:\n"
                + "\t**codewars_username**:    "
                + str(member["codewars_username"])
                + "\n\t**completed**:                        "
                + str(":white_check_mark:" if member["completed"] else ":x:")
                + "\n"
            )
            if member["completed"]:
                stats += str(
                    "\t**languages**:                         "
                    + ", ".join(
                        strtoemote(self.config["emotes"], member["languages"])
                    )
                    + "\n"
                )
            clanstats += "\n" + stats
        await ctx.send(clanstats)

    @app_commands.command(name="leaderboard", description="U")
    async def leaderboard(
        self, interaction: discord.interactions.Interaction
    ) -> None:
        """"""
        print("Command: leaderboard")
        clan = load_clan(self.config)

        await interaction.response.defer()
        for member in clan.values():
            response = requests.get(
                self.config["user_api"].format(member["codewars_username"]),
                timeout=500,
            )
            member["response"] = response.json()

        for member in clan.values():
            try:
                member["honour"] = member["response"]["honor"]
                member["rank"] = member["response"]["ranks"]["overall"]["name"]
                member["total_score"] = int(
                    member["response"]["ranks"]["overall"]["score"]
                )
                del member["response"]
            except BaseException as err:
                print("==========member.items=====================")
                pprint(member)
                print("===========================================")
                print()
                raise err
        # try:
        #     with open("config/leaderboard.json", "w") as file:
        #         json.dump(clan, file, indent=2)
        # except BaseException as err:
        #     raise err
        clan_orderd: list = list(clan.values())
        try:
            clan_orderd.sort(key=lambda x: x["total_score"], reverse=True)
        except KeyError as err:
            print("=========================")
            print("failed to sort clanlist in leaderboad")
            pprint(clan_orderd)
            print("=========================")
            raise err
        scoreboard: str = str(
            "# Clan leaderboard:\n"
            + f"{'# #.':<10}"
            + f"{'Rank':>11}"
            + f"{'Score':>14}"
            + f"{'Honor':>14}"
            + f"{'User':>18}"
            + "\n"
            + ("-" * 89)
            + "\n"
        )
        for pos, member in enumerate(clan_orderd):
            rank = "".join(strtoemote(self.config["emotes"], [member["rank"]]))
            scoreboard += str(
                f"# {pos:<16}"
                + f"{f'{rank}'}"
                + f"{f'{str(member["total_score"]).zfill(3):>16}'}"
                + f"{f'{str(member["honour"]).zfill(3):>16}':<35}"
                + f"{f' <@{member["discord_id"]}>'}"
                + "\n"
            )
            if pos == 9:
                break
        await interaction.followup.send(scoreboard)

    @tasks.loop(time=next_level_time)
    async def next_level_poll(self) -> None:
        """"""
        date = get_date(self.config["timezone"])
        tommorow = date + datetime.timedelta(days=1)
        p = discord.Poll(
            question=f"Challenge level for {tommorow}",
            duration=datetime.timedelta(hours=23.0, minutes=55),
        )
        for kyu, emote in self.config["emotes"].items():
            if "kyu" in kyu:
                p.add_answer(text=kyu, emoji=emote)

        guild = self.bot.guilds[0]
        if guild is None:
            return
        challenge_channel = await guild.fetch_channel(
            self.config["next_level_channel"]
        )
        try:
            await challenge_channel.send("<@here>")  # type: ignore
            await challenge_channel.send(poll=p)  # type: ignore
        except BaseException as e:
            print(f"Could not post to {self.config['next_level_channel']}")
            raise e

    @next_level_poll.before_loop
    async def next_level_poll_before(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.bot.Bot) -> None:
    """"""
    await bot.add_cog(Codewars(bot))
