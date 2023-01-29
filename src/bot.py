# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Gecko Bot 

import discord,sys
from discord.ext import commands,tasks

synccmd = False
if len(sys.argv) > 1 and "synccmd" in sys.argv:
    synccmd = True

shard = 2
for arg in sys.argv:
    try:
        shard = int(arg)
    except:
        pass

print(f"Starting main bot with {shard} shards, traditional bot with {max(int(shard / 2), 1)} shards.")
    
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.AutoShardedBot(command_prefix='/', intents=intents, shard_count=shard, auto_sync_commands = synccmd)
tbot = commands.AutoShardedBot(command_prefix=('g?','G?','g!','G!'), intents=intents, shard_count=max(int(shard / 2), 1), auto_sync_commands = False)