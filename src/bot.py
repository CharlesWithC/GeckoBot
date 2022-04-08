# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Gecko Bot 

import discord
from discord.ext import commands,tasks

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='/', intents=intents, auto_sync_commands = False)
tbot = commands.Bot(command_prefix=('g?','G?','g!','G!'), intents=intents, auto_sync_commands = False)