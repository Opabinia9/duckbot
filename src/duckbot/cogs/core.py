"""duck-bot for Holberton codewars server."""

import discord
from discord.ext import commands

# TODO: aync get reuests
# TODO: error handling
# TODO: push to git
# TODO: setup server
# TODO: level up noticications


class Core(commands.Cog):
    """"""

    def __init__(self, bot) -> None:
        """"""
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member) -> None:
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


async def setup(bot) -> None:
    """"""
    await bot.add_cog(Core(bot))
