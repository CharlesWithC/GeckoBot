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

    @vcrecord.command(name="join", description="Staff - Join the voice channel you are in.")
    async def join(self, ctx):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if CheckVCLock(ctx.guild.id):
            await ctx.respond("Gecko VC is locked. Use `/vcrecord unlock` to unlock it.", ephemeral = True)
            return

        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.respond("You are not in a voice channel!", ephemeral = True)
            return
            
        voice_client = ctx.guild.voice_client
        if voice_client != None:
            if voice_client.channel.id == ctx.author.voice.channel.id:
                await ctx.respond("I'm already connected to the channel you are in.", ephemeral = True)
                return
            else:
                await ctx.respond("I am already connected to a voice channel, probably playing music.\nUse `/music leave` to stop it.", ephemeral = True)
                return

        try:
            channel = ctx.author.voice.channel
            await channel.connect(timeout = 5)
        except:
            await ctx.respond(f"I cannot join the voice channel you are in. Maybe I don't have access or I'm rate limited. Please try again later.", ephemeral = True)
            return
        
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND userid = -2")
        cur.execute(f"INSERT INTO playlist VALUES ({guildid}, -2, '{b64e('Gecko VCR')}')")
        conn.commit()

        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True, self_deaf = True)
        BTW = "**NOTE** Gecko locks its VC function when voice recorder is activated. This prevents it from playing music requested by other users."
        await ctx.respond(f"I have joined the voice channel.\nUse `/vcrecord start` and `/vcrecord stop` to start and stop recording.\n\nThe audio files will be sent to you by **DM** when the recording is over.\n\n{BTW}")

    @vcrecord.command(name="leave", description="Staff - Leave the voice channel.")
    async def leave(self, ctx):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
            
        if not CheckVCLock(ctx.guild.id):
            await ctx.respond("Gecko VC is not locked meaning voice recorder is inactive.", ephemeral = True)
            return

        voice_client = ctx.guild.voice_client
        if voice_client == None:
            await ctx.respond("I'm not connected to a voice channel!", ephemeral = True)
            return
        if voice_client.is_playing():
            await ctx.respond("I'm playing music but not recording. Use `/music leave` instead.", ephemeral = True)
            return
        
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND userid = -2")
        conn.commit()
        try:
            try:
                voice_client.stop_recording()
            except:
                pass
            await voice_client.disconnect()
            await ctx.respond("I have left the voice channel.")
        except:
            await ctx.respond("I cannot leave the voice channel by myself due to unknown error. The VC lock is released.")            
    
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
            
        if not CheckVCLock(ctx.guild.id):
            await ctx.respond("Gecko VC is not locked meaning voice recorder is inactive.", ephemeral = True)
            return
            
        voice_client = ctx.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            await ctx.respond("I am not in a voice channel!", ephemeral = True)
            return

        channel = None
        try:
            channel = await ctx.author.create_dm()
            await channel.send("Recorded audio will be sent here after it's done.\nUse `/vcrecord stop` to stop recording.\nDO NOT use `/vcrecord unlock` as it may allow others to break the conversation.")
        except:
            await ctx.respond("I cannot DM you which means I cannot send you the recorded audio. The operation has been cancelled.", ephemeral = True)
            return

        try:
            await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True, self_deaf = False)
            voice_client.start_recording(discord.sinks.MP3Sink(), self.callback, channel)
            await ctx.respond("I have started recording the voice channel.")
        except:
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
            
        if not CheckVCLock(ctx.guild.id):
            await ctx.respond("Gecko VC is not locked meaning voice recorder is inactive.", ephemeral = True)
            return
            
        voice_client = ctx.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            await ctx.respond("I am not in a voice channel!", ephemeral = True)
            return

        try:
            voice_client.stop_recording()
            await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True, self_deaf = True)
            await ctx.respond("I have stopped recording the voice channel.")
        except:
            await ctx.respond("Failed to stop recording, probably not recording.", ephemeral = True)

bot.add_cog(VCRecord(bot))