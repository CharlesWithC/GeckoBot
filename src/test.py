#!/usr/bin/python3

# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Lizard Bot (Beta Gecko)

from bot import bot, tbot
from settings import *
import json, asyncio

import general.main
import traditional.main
import globaltrucking.main
import truckersmp.main
from truckersmp.tmp import UpdateTMPMap, UpdateTMPTraffic

import threading

@bot.event
async def on_ready():
    print(f"[Main Bot] Logged in as {bot.user} (ID: {bot.user.id})")

# traditional bot (slash commands)
@tbot.event
async def on_ready():
    print(f"[Traditional Bot] Logged in as {tbot.user} (ID: {tbot.user.id})")

config_txt = open("./test.conf","r").read()
config = json.loads(config_txt)

threading.Thread(target=UpdateTMPMap).start()
# threading.Thread(target=UpdateTMPTraffic).start()
loop = asyncio.get_event_loop()
loop.create_task(bot.start(config["token"]))
loop.create_task(tbot.start(config["token"]))
loop.run_forever()