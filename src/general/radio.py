# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Radio of Gecko Bot

import os, asyncio
import discord
from base64 import b64encode, b64decode

from bot import bot
from settings import *
from functions import *
from db import newconn

async def Radio():
    conn = newconn()
    cur = conn.cursor()
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    await bot.change_presence(activity=discord.Game(name = "with Charles"))
    while not bot.is_closed():
        # Play radio
        for sid in RADIO_CHANNEL:
            try:
                guild = bot.get_guild(sid[0])
                voice_channel = guild.voice_client
                channel = bot.get_channel(sid[1])
                if voice_channel is None or not voice_channel.is_connected():
                    try:
                        await log("Radio", f"Connecting to {channel}")
                        await channel.connect(timeout = 5)
                        voice_channel = guild.voice_client
                    except Exception as e:
                        await log("Radio", f"Failed to connect to {channel}  {str(e)}")
                        if not voice_channel is None:
                            await voice_channel.disconnect()
                            await log("Radio", f"Disconnected from {channel}")
                        continue

                    try:
                        player = discord.FFmpegPCMAudio(source = TFM)
                        await log("Radio", f"Playing TruckersFM in {channel}")
                        voice_channel.play(player)
                    except Exception as e:
                        await log("Radio", f"Failed to play TruckersFM in {channel} {str(e)}")
                        await voice_channel.disconnect()
                        await log("Radio", f"Disconnected from {channel}")
                        continue

            except Exception as e:
                await log("Radio", f"Unknown exception: {str(e)}")
                pass

        await asyncio.sleep(3)

bot.loop.create_task(Radio())