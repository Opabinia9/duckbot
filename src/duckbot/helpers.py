""""""

import json
import datetime
import requests
from zoneinfo import ZoneInfo
from pathlib import Path
from pprint import pprint


def load_config(config_file: str) -> dict:
    """"""
    with open(config_file, "r") as conf:
        return json.load(conf)


def save_config(
    config_file: str, key: str, value: str | bool | list | dict
) -> dict:
    """"""
    config = load_config(config_file)
    config[key] = value
    with open(config_file, "w") as conf:
        json.dump(config, conf, indent=2)
    return config


def load_clan(config: dict) -> dict:
    """Load existing mapping or create empty one.

    Returns:
        dictionry of users discord and codewars usernames.

    """
    if Path(config["clan_list"]).exists():
        with open(config["clan_list"], "r") as file:
            return json.load(file)
    return {}


def save_clan(config: dict, data: dict) -> None:
    """Save mapping to file."""
    with open(config["clan_list"], "w") as f:
        json.dump(data, f, indent=2)


def fetch_kata(config: dict, kata_id: str) -> dict[str, str]:
    """Fetch name of kata and return dict of name and id."""
    kata = requests.get(
        config["kata_api"].format(kata_id),
        timeout=500,
    ).json()
    return {
        "kata_name": kata["name"],
        "kata_id": kata_id,
        "kata_rank": kata["rank"]["name"],
        "kata_category": kata["category"],
    }


def load_katalog(config: dict) -> dict:
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
    kata_log = load_katalog(config)
    kata = fetch_kata(config, kata_id)
    kata_log[str(date)] = {
        "kata_id": kata["kata_id"],
        "kata_name": kata["kata_name"],
        "kata_rank": kata["kata_rank"],
        "kata_category": kata["kata_category"],
    }

    with open(config["kata_log"], "w") as log_file:
        json.dump(kata_log, log_file, indent=2)

    return kata_log


def check_stats(config: dict, dailykata: str) -> dict[str, dict]:
    """"""
    clan: dict[str, dict] = load_clan(config)

    for member in clan.values():
        response = requests.get(
            config["completed_api"].format(member["codewars_username"]),
            timeout=500,
        )
        member["response"] = response.json()

    for member in clan.values():
        try:
            if "data" in member["response"].keys():
                for kata in member["response"]["data"]:
                    if kata["id"] == dailykata:
                        member["completed"] = True
                        member["languages"] = kata["completedLanguages"]
                        break
                else:
                    member["completed"] = False
            else:
                print(
                    f"error for {member['discord_username']}: "
                    + f"{member['response']['reason']}"
                )
                member["completed"] = False
            del member["response"]
        except BaseException:
            print("============================")
            print("check_status failed")
            pprint(member.items())
            print("============================")
            print()
            exit(-1)
    return clan


def strtoemote(emotes: dict, strings: list[str]) -> list[str]:
    """"""
    newstrings = []
    for string in strings:
        string = str(string)
        if string in emotes.keys():
            newstrings.append(emotes[string])
        else:
            newstrings.append(str("`" + string + "`"))
    return newstrings


def get_date(zone: str) -> datetime.date:
    """"""
    timezone = ZoneInfo(zone)
    return datetime.datetime.now(timezone).date()
