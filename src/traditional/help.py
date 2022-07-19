# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Help

import os, asyncio
import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText
from time import time
from random import randint
import io

from bot import tbot
from settings import *
from functions import *
from db import newconn
from rapidfuzz import process

from general.help import commands, cmdlist

@tbot.command(name="about", description="About Gecko")
async def tabout(ctx):
    await ctx.send(commands["about"])

tbot.remove_command('help')
@tbot.command(name="help", description="Get help.")
async def thelp(ctx):
    if len(ctx.message.content.split(" ")) > 1:
        cmd = " ".join(ctx.message.content.split(" ")[1:])
        d = process.extract(cmd, commands.keys(), limit = 1, score_cutoff = 40)
        await ctx.send(embed = discord.Embed(title = d[0][0], description=commands[d[0][0]], color = GECKOCLR))
    else:
        await ctx.send(embed = cmdlist)