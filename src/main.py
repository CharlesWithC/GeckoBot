#!/usr/bin/python3

# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Gecko Bot 

from bot import bot
from settings import *
import json

import general.main
import globaltrucking.main

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    
config_txt = open("./bot.conf","r").read()
config = json.loads(config_txt)
bot.run(config["token"])