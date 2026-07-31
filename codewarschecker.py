#!/usr/bin/env python3
"""Module: Codewars kata checker."""

import requests
import json
from pprint import pprint


def check_stats(dailykata: str):
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


def print_clan(clan: dict[str, dict]) -> None:
    """Print clan formated."""
    for member in clan.values():
        print(member["discord_username"] + ":")
        print("\t" + "codewars_username: " + str(member["codewars_username"]))
        print("\t" + "completed:         " + str(member["completed"]))
        if member["completed"]:
            print("\t" + "languages:         " + str(member["languages"]))
        print()


if __name__ == "__main__":
    from sys import argv

    # dailykata = "55685cd7ad70877c23000102"
    dailykata: str = argv[1]
    print_clan(check_stats(dailykata))
