# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Voice Channel

import os, asyncio
import discord
from discord.ext import commands
import base64
from time import time
import requests
import io
import validators
import math

from bot import bot
from settings import *
from functions import *
from db import newconn

import pyttsx3
import importlib

def onloop(guildid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = 'loop' AND userid = 0")
    t = cur.fetchall()
    if len(t) > 0:
        return True
    return False

@bot.slash_command(name="join", description = "Staff - Join the voice channel.")
async def join(ctx, channel: discord.Option(discord.VoiceChannel, "Specify a voice channel, if not specified, then join the channel you are in.", required = False)):
    await ctx.defer()
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    if channel is None and (ctx.author.voice is None or ctx.author.voice.channel is None):
        await ctx.respond("You are not in a voice channel!", ephemeral = True)
        return
    
    voice_client = ctx.guild.voice_client
    if not voice_client is None and voice_client.is_connected():
        await voice_client.disconnect()
    try:
        if channel is None:
            channel = ctx.author.voice.channel
        await channel.connect(timeout = 5)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True)
    except:
        await ctx.respond(f"I cannot join the voice channel. Maybe I don't have access or I'm rate limited. Please try again later.", ephemeral = True)
        return

    conn = newconn()
    cur = conn.cursor()
    guildid = ctx.guild.id
    voice_client = ctx.guild.voice_client
    cur.execute(f"DELETE FROM vcbind WHERE guildid = {guildid}")
    cur.execute(f"INSERT INTO vcbind VALUES ({guildid}, {voice_client.channel.id})")
    cur.execute(f"SELECT userid FROM playlist WHERE guildid = {guildid} AND userid < 0")
    t = cur.fetchall()    
    if not onloop(guildid) or len(t) > 0 and t[0][0] == -1:
        cur.execute(f"DELETE FROM playlist WHERE userid < 0 AND guildid = {guildid}")
    else:
        cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
        q = cur.fetchall()
        if len(q) > 0:
            cur.execute(f"INSERT INTO playlist VALUES ({guildid}, {-q[0][0]}, '{q[0][1]}')")
        cur.execute(f"DELETE FROM playlist WHERE userid < 0 AND guildid = {guildid}")
    conn.commit()
    
    await ctx.respond(f"I've joined the voice channel.")

@bot.slash_command(name="leave", description = "Staff - Leave the voice channel.")
async def leave(ctx):
    await ctx.defer()
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    voice_client = ctx.guild.voice_client
    if not voice_client is None and voice_client.is_connected():
        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id
        cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND userid = -2")
        t = cur.fetchall()
        if len(t) > 0:
            cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND userid = -2")
            conn.commit()
            try:
                voice_client.stop_recording()
            except:
                pass
            cur.execute(f"SELECT laststart FROM vcrecord WHERE guildid = {guildid}")
            c = cur.fetchall()
            laststart = c[0][0]
            cur.execute(f"UPDATE vcrecord SET minutes = minutes + {int((int(time.time()) - laststart)/60)}, laststart = 0 WHERE guildid = {guildid}")
            conn.commit()
        await voice_client.disconnect()

        cur.execute(f"DELETE FROM vcbind WHERE guildid = {guildid}")
        conn.commit()
        await ctx.respond(f"I've left the voice channel.")
    else:
        await ctx.respond(f"I'm not connected to a voice channel.", ephemeral = True)

async def svoice(ctx: discord.AutocompleteContext):
    if ctx.value.replace(" ", "") == "":
        return VOICES[:10]
    return SearchVoice(ctx.value)

@bot.slash_command(name="tts", description="Turn text to speech and speak it in the voice channel Gecko is connected to.")
async def TTS(ctx, text: discord.Option(str, "Text to speak.", required = True),
        voice: discord.Option(str, "Select a voice, or different language", required = False, autocomplete = svoice, default = "english"),
        gender: discord.Option(str, "Voice gender", required = False, choices = ["male", "female"], default="male"),
        speed: discord.Option(float, "Voice speed", required = False, default = 1)):
        
    if ctx.guild is None:
        await ctx.respond(f"You can only use this command in guilds, not in DMs.")
        return

    guild = ctx.guild
    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Use `/join` command to join me in.", ephemeral = True)
        return    
    
    premium = GetPremium(ctx.guild)
    if premium == 0:
        await ctx.respond(f"TTS is premium only.", ephemeral = True)
        return

    if len(text) > 500:
        await ctx.respond(f"Text is too long. Max 200 characters.", ephemeral = True)
        return

    if voice_client.is_playing():
        voice_client.stop()

    await ctx.respond(f"TTS: {text}", ephemeral = True)

    voice = SearchVoice(voice)

    importlib.reload(pyttsx3)
    fp = f"/tmp/{int(time()*100000)}{ctx.guild.id}.mp3"
    engine = pyttsx3.init()
    engine.setProperty('voice', voice)
    if gender == "female":
        engine.setProperty('voice', 'english+f4')
    engine.setProperty("rate", int(max(100*speed,1)))
    engine.save_to_file(f"{ctx.author.name} said: {text}", fp)
    engine.runAndWait()
    await asyncio.sleep(0.5)

    await ctx.guild.change_voice_state(channel = voice_client.channel, self_mute = False)
    voice_client.play(discord.FFmpegPCMAudio(source = fp))
    while voice_client.is_playing():
        await asyncio.sleep(0.1)
    await ctx.guild.change_voice_state(channel = voice_client.channel, self_mute = True)
    os.remove(fp)