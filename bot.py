import json
import urllib
from datetime import datetime
import os

import wget
import berserk
import pandas as pd
import matplotlib.pyplot as plt

from discord import File
from discord.ext import commands
from dotenv import load_dotenv
from urllib3.exceptions import ResponseError

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')
lichess_token = os.getenv('LICHESS_TOKEN')
bot = commands.Bot(command_prefix='!')

session = berserk.TokenSession(lichess_token)
client = berserk.Client(session=session)

help_str = """
Gets pgn from lichess

Syntax: !get_pgn <user> <perf_type> <*args>

Examples:
# All rapid games from 1.1.2021 - 2.2.2021 played as white
!get_pgn tbsmrks rapid since=1.1.2021 until=2.2.2021 color=white

# All blitz games played ever
!get_pgn tbsmrks blitz

# All bullet games played as black
!get_pgn tbsmrks bullet color=black
"""


@bot.command(name='get_pgn', help=help_str)
async def get_pgn(ctx, user: str, perf_type: str, *args):
    download_str = f"https://lichess.org/games/export/{user}?perfType={perf_type}"
    out_file_name = f"{user}_{perf_type}"

    for arg in args:
        if arg.startswith("until=") or arg.startswith("since="):
            argument, date = arg.split("=")
            date_unix = int(datetime.strptime(date, '%d.%m.%Y').timestamp() * 1000)
            query = "=".join([argument, str(date_unix)])
        else:
            query = arg
        download_str += f"&{query}"
        file_name_arg = arg.replace('.', '_').replace('=', '_')

        out_file_name += f"_{file_name_arg}"

    out_file_name += ".pgn"

    try:
        wget.download(download_str, out=out_file_name)
        await ctx.send(file=File(out_file_name))
        os.remove(out_file_name)
    except urllib.error.HTTPError:
        await ctx.send("Sorry something went wrong maybe a typo? 404 not found!")


help_str = """
Gets rating history from lichess as excel

Example:
# export DrNykterstein bullet rating
!get_rating_hist DrNykterstein bullet
"""


@bot.command(name='get_rating_hist', help=help_str)
async def get_rating_hist(ctx, user: str, perf_type: str):
    perf_dict = {
        "bullet": 0,
        "blitz": 1,
        "rapid": 2,
        "classical": 3,
        "correspondance": 4,
        "chess960": 5,
        "king_of_the_hill": 6,
        "three_check": 7,
        "antichess": 8,
        "atomic": 9,
        "horde": 10,
        "racing_kings": 11,
        "crazy_house": 12,
        "puzzles": 13,
        "ultrabullet": 14
    }
    # Get the rating History
    rating_hist = json.loads(client.users.get_rating_history(username=user))
    # build a rating list with a time string: Tuple[str, int]
    rating_list = [(f"{rating[0]}-{rating[1] + 1}-{rating[2]}", rating[3]) for rating in
                   rating_hist[perf_dict[perf_type]]['points']]
    x = [rating[0] for rating in rating_list]
    y = [rating[1] for rating in rating_list]

    # create pandas timestamps
    timestamps = pd.to_datetime(x)

    # create a pandas data series resample it with a daily interval and interpolate the data in a linear fashion
    ts = pd.Series(y, index=timestamps)
    ts = ts.resample('D').mean()
    ts = ts.interpolate(method='time')
    # plot the data
    ts.plot(linestyle='dashed', linewidth=1)
    plt.title(f"{user}'s {perf_type} ratings")
    out_file_name = f"{user}_{perf_type}.png"
    plt.savefig(out_file_name)
    await ctx.send(file=File(out_file_name))
    os.remove(out_file_name)
    out_file_name = f"{user}_{perf_type}.xlsx"
    ts.to_excel(out_file_name)
    await ctx.send(file=File(out_file_name))
    os.remove(out_file_name)
    plt.clf()


@bot.command(name='get_game_modes', help="List all game modes")
async def get_game_modes(ctx):
    output = """
    ```
    "bullet"
    "blitz"
    "rapid"
    "classical"
    "correspondance"
    "chess960"
    "king_of_the_hill"
    "three_check"
    "antichess"
    "atomic"
    "horde"
    "racing_kings"
    "crazy_house"
    "puzzles
    "ultrabullet"
    ```
    """
    await ctx.send(output)

help_str = """
Creates a lichess tournament and returns the corresponding link

Example:
# creates a tournament with 10 minutes and 5sec clock_increment with a tournament which lasts 10 minutes
# and starts at the 01.01.2021
!create_tournament MyFirstTournament 10 5 90 "01.01.2021 12:00"
"""
@bot.command(name='create_tournament', help=help_str)
async def create_tournament(ctx, name: str, clock: int, clock_increment: int, duration: int, start_date: str):
    date_unix = int(datetime.strptime(start_date, '%d.%m.%Y %H:%M').timestamp() * 1000)
    try:
        tournament = client.tournaments.create(clock, clock_increment, duration, name=name, start_date=date_unix)
        await ctx.send(f"https://lichess.org/tournament/{tournament['id']}")
    except berserk.exceptions.ResponseError as e:
        await ctx.send(e)

bot.run(discord_token)
