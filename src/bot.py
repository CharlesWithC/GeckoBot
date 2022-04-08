# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Gecko Bot 

import discord,sys
from discord.ext import commands,tasks

synccmd = False
if len(sys.argv) > 1 and sys.argv[1] == "synccmd":
    synccmd = True
    
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='/', intents=intents, auto_sync_commands = synccmd)
tbot = commands.Bot(command_prefix=('g?','G?','g!','G!'), intents=intents, auto_sync_commands = False)