# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Voice Channel Recorder Management

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from datetime import datetime

from bot import bot
from settings import *
from functions import *
from db import newconn
import time

# do block music function

class VCRecord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    vcrecord = SlashCommandGroup("vcrecord", "Voice channel recorder")
    
    async def callback(self, sink, channel, *args):
        dt = datetime.now()
        dt = dt.strftime("%Y%m%d%H%M%S")
        await channel.send("Record finished. The files are being uploaded and should be available very soon.")
        for userid, audiodata in sink.audio_data.items():
            user = "UnknownUser"
            try:
                user = bot.get_user(userid)
            except:
                pass
            audio = audiodata.file
            audio.seek(0)
            await channel.send(file=discord.File(fp=audio, filename=f'GeckoVCR-{user}-{userid}-{dt}.MP3'))
        await channel.send(f"All the files have been uploaded. They are named in the format of `GeckoVCR - Username & Tag - User ID - DateTime`")

    @vcrecord.command(name="unlock", description="Staff - Unlock Gecko VC in case it's locked accidentally. DO NOT do this when recording is on.")
    async def unlock(self, ctx):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND userid = -2")
        conn.commit()

        await ctx.respond("Gecko VC is unlocked.")

    @vcrecord.command(name="start", description="Staff - Start recording the voice channel.")
    async def start(self, ctx):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT minutes FROM vcrecord WHERE guildid = {guildid}")
        c = cur.fetchall()
        if len(c) > 0:
            premium = GetPremium(ctx.guild)
            cnt = c[0][0]
            if cnt >= 100*60 and premium >= 2:
                await ctx.respond("Max hours / month: 100.\n\nIf you are looking for more hours / month, contact Gecko Moderator in support server", ephemeral = True)
                return
            elif cnt >= 30*60 and premium == 1:
                await ctx.respond("Premium Tier 1: 30 hours / month.\nPremium Tier 2: 100 hours / month.\n\nCheck out more by using `/premium`", ephemeral = True)
                return
            elif cnt >= 10*60 and premium == 0:
                await ctx.respond("Free guilds: 10 hours / month.\nPremium Tier 1: 30 hours / month.\nPremium Tier 2: 100 hours / month.\n\nCheck out more by using `/premium`", ephemeral = True)
                return
        else:
            cur.execute(f"INSERT INTO vcrecord VALUES ({guildid}, 0, 0)")
            conn.commit()
            
        voice_client = ctx.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            await ctx.respond("I am not in a voice channel!", ephemeral = True)
            return

        if voice_client.is_playing():
            voice_client.stop()
        cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND userid = -2")
        cur.execute(f"INSERT INTO playlist VALUES ({guildid}, -2, '{b64e('Gecko VCR')}')")
        conn.commit()

        channel = None
        try:
            channel = await ctx.author.create_dm()
            await channel.send("Recorded audio will be sent here after it's done.\nUse `/vcrecord stop` to stop recording.\nDO NOT use `/vcrecord unlock` as it kills the recorder and you might lose the recordings.")
        except:
            await ctx.respond("I cannot DM you which means I cannot send you the recorded audio. The operation has been cancelled.", ephemeral = True)
            return

        try:
            await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True, self_deaf = False)
            voice_client.start_recording(discord.sinks.MP3Sink(), self.callback, channel)
            await ctx.respond("I have started recording the voice channel.")
            cur.execute(f"SELECT laststart FROM vcrecord WHERE guildid = {guildid}")
            c = cur.fetchall()
            laststart = c[0][0]
            dur = 0
            if laststart != 0 :
                dur = int(time.time()) - laststart
            cur.execute(f"UPDATE vcrecord SET minutes = minutes + {int(dur/60)}, laststart = {int(time.time())} WHERE guildid = {guildid}")
            conn.commit()
        except:
            import traceback
            traceback.print_exc()
            await ctx.respond("Failed to start recording, probably it already started.", ephemeral = True)
        
    @vcrecord.command(name="stop", description="Staff - Stop recording the voice channel.")
    async def stop(self, ctx):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
            
        voice_client = ctx.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            await ctx.respond("I am not in a voice channel!", ephemeral = True)
            return

        try:
            voice_client.stop_recording()
            await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True, self_deaf = True)
            await ctx.respond("I have stopped recording the voice channel.")
            conn = newconn()
            cur = conn.cursor()
            cur.execute(f"SELECT laststart FROM vcrecord WHERE guildid = {guildid}")
            c = cur.fetchall()
            laststart = c[0][0]
            cur.execute(f"UPDATE vcrecord SET minutes = minutes + {int((int(time.time()) - laststart)/60)}, laststart = 0 WHERE guildid = {guildid}")
            cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND userid = -2")
            conn.commit()
        except:
            await ctx.respond("Failed to stop recording, probably not recording.", ephemeral = True)

bot.add_cog(VCRecord(bot))