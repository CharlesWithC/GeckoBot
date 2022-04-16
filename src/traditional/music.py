# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Music

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from time import time
import requests
from fuzzywuzzy import process

from general.radiolist import radiolist, radioname, radiolink, SearchRadio, SearchRadioMul

from requests import get
from youtube_dl import YoutubeDL

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True', 'quite': True, 'ignoreerrors': True}
def search(arg):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            get(arg) 
        except:
            video = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        else:
            video = ydl.extract_info(arg, download=False)
    return video

from bot import bot, tbot
from settings import *
from functions import *
from db import newconn

def onloop(guildid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = 'loop' AND userid = 0")
    t = cur.fetchall()
    if len(t) > 0:
        return True
    return False

@tbot.command(name="join", description = "Staff - Music - Join the voice channel you are in.")
async def join(ctx):
    await ctx.channel.trigger_typing()
    
    if ctx.guild is None:
        await ctx.send("You can only run this command in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return

    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("You are not in a voice channel!")
        return
    guildid = ctx.guild.id
    conn = newconn()
    cur = conn.cursor()
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
    
    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if not voice_client is None and voice_client.is_connected():
        await voice_client.disconnect()
    try:
        channel = ctx.author.voice.channel
        await channel.connect(timeout = 5)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True)
    except:
        await ctx.send(f"I cannot join the voice channel you are in. Maybe I don't have access or I'm rate limited. Please try again later.")
        return

    guildid = ctx.guild.id
    cur.execute(f"DELETE FROM vcbind WHERE guildid = {guildid}")
    cur.execute(f"INSERT INTO vcbind VALUES ({guildid}, {voice_client.channel.id})")
    conn.commit()
    
    await ctx.send(f"I've joined the voice channel.")

@tbot.command(name="leave", description = "Staff - Music - Join the voice channel you are in.")
async def leave(ctx):
    await ctx.channel.trigger_typing()
    
    if ctx.guild is None:
        await ctx.send("You can only run this command in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return
    
    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
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
        await ctx.send(f"I've left the voice channel.")
    else:
        await ctx.send(f"I'm not connected to a voice channel.")

@tbot.command(name="pause", description="Staff - Music - Pause music.")
async def pause(ctx):
    await ctx.channel.trigger_typing()  
    
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return

    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client is None or not voice_client.is_playing():
        await ctx.send(f"Music hasn't even started!")
        return

    voice_client.pause()
    user = ctx.guild.get_member(BOTID)
    await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True)
    await ctx.send(f"Music paused! You can use /music resume to restart from where it paused.")

@tbot.command(name="resume", description="Staff - Music - Resume music.")
async def resume(ctx):
    await ctx.channel.trigger_typing() 
    
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return

    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client.is_playing():
        await ctx.send(f"Music is already playing.")
        return

    voice_client.resume()
    user = ctx.guild.get_member(BOTID)
    await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
    await ctx.send(f"Music resumed!")

@tbot.command(name="toggle", description="Staff - Music - Toggle 'Now Playing' auto post, whether Gecko should send it or not.")
async def toggle(ctx):
    await ctx.channel.trigger_typing() 
    
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return

    conn = newconn()
    cur = conn.cursor()

    cur.execute(f"SELECT sval FROM settings WHERE guildid = {ctx.guild.id} AND skey = 'music_update_post'")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO settings VALUES ({ctx.guild.id}, 'music_update_post', 0)")
        conn.commit()
        await ctx.send(f"'Now Playing' will no longer be posted automatically.\nUse /current to get the current song.")
        return
    if t[0][0] == "1":
        cur.execute(f"UPDATE settings SET sval = '0' WHERE guildid = {ctx.guild.id} AND skey = 'music_update_post'")
        conn.commit()
        await ctx.send(f"'Now Playing' will no longer be posted automatically.\nUse /current to get the current song.")
    else:
        cur.execute(f"UPDATE settings SET sval = '1' WHERE guildid = {ctx.guild.id} AND skey = 'music_update_post'")
        conn.commit()
        await ctx.send(f"'Now Playing' will be posted automatically from now on.")

@tbot.command(name="clear", description="Staff - Music - Clear playlist.")
async def clear(ctx):
    await ctx.channel.trigger_typing() 
    
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return

    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM playlist WHERE userid > 0")
    conn.commit()
    
    await ctx.send(f"Playlist cleared!")

@tbot.command(name="loop", description="Staff - Music - Toggle loop playback of the playlist.")
async def loop(ctx):
    await ctx.channel.trigger_typing() 
    
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return
    
    conn = newconn()
    cur = conn.cursor()
    guildid = ctx.guild.id
    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = 'loop' AND userid = 0")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO playlist VALUES ({guildid}, 0, 'loop')")
        conn.commit()
        await ctx.send(f"Loop playback enabled for playlist!")
    else:
        cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND title = 'loop' AND userid = 0")
        conn.commit()
        await ctx.send(f"Loop playback disabled for playlist!")

@tbot.command(name="play", description="Staff - Music - Play a song.")
async def PlayMusic(ctx):
    await ctx.channel.trigger_typing()
    guildid = 0
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return

    if CheckVCLock(ctx.guild.id):
        await ctx.send("Gecko VC is locked. Use `/vcrecord unlock` to unlock it.")
        return

    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.send(f"I'm not in a voice channel. Use `/join` command to join me in.")
        return

    if len(ctx.message.content.split(" ")) == 1:
        cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
        p = cur.fetchall()
        if len(p) > 0:
            guild = bot.get_guild(guildid)
            voice_client = guild.voice_client

            url = ""
            if p[0][0] != -1:
                try:
                    ydl = search(b64d(p[0][1]))
                    url = ydl['formats'][0]['url']
                except:
                    await voice_client.disconnect()
                    # failed to connect, try again using loop
                    return
            else:
                title = p[0][1].split("-")[1]
                url = p[0][1].split("-")[2]
            
            try:
                player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
                voice_client.play(player)
                await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
            except:
                await voice_client.disconnect()
                # failed to play, try again using loop
                return
    
    voice_client = ctx.guild.voice_client
    if not voice_client.is_playing() and not voice_client.is_paused():
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True)
    song = " ".join(ctx.message.content.split(" ")[1:])

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.send(f"I cannot find that song. This might be a temporary issue.")
        return
    
    if voice_client.is_playing() and not voice_client.is_paused():
        voice_client.stop()
    try:
        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
        voice_client.play(player)
        user = ctx.guild.get_member(BOTID)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
    except:
        await ctx.send(f"It looks like I'm blocked by music provider service. Please try again later.")
        return
    
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
    
    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = '{b64e(title)}'")
    t = cur.fetchall()
    if len(t) > 0:
        cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND title = '{b64e(title)}'")
    cur.execute(f"INSERT INTO playlist VALUES ({guildid}, -{ctx.author.id}, '{b64e(title)}')")
    conn.commit()

    embed = discord.Embed(title=f"Now playing", description=title, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    icon_url = None
    if not ctx.author.avatar is None:
        icon_url = ctx.author.avatar.url
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = icon_url)
    await ctx.send(embed = embed)

@tbot.command(name="next", description="Music - Play next song in queue.")
async def NextSong(ctx):
    await ctx.channel.trigger_typing()    
        
    guildid = 0
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    if CheckVCLock(ctx.guild.id):
        await ctx.send("Gecko VC is locked. Use `/vcrecord unlock` to unlock it.")
        return
    
    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send(f"{ctx.author.name}, staff haven't set up a channel to request music! Tell them to use `/setchannel music {{#channel}}` to set it up!")
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.send(f"This is not the channel for using music commands.")
            return
        cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND userid = -1")
        t = cur.fetchall()
        if len(t) != 0:
            await ctx.send(f"A radio stream is being played and you cannot override it. Only staff are allowed to run this command during radio streams.")
            return
    
    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.send(f"I'm not in a voice channel. Tell staff to use `/join` command to join me in.")
        return

    guildid = ctx.guild.id
    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid > 0 LIMIT 1")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send(f"There is no next-up songs in the playlist! Use /queue to add a song.")
        return
    userid = t[0][0]
    title = t[0][1]

    url = ""
    try:
        ydl = search(b64d(title))
        url = ydl['formats'][0]['url']
    except:
        await ctx.send(f"Something went wrong. Try again later.")
        return

    if voice_client.is_playing() and not voice_client.is_paused():
        voice_client.stop()
    try:
        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
        voice_client.play(player)
        user = ctx.guild.get_member(BOTID)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
    except:
        await ctx.send(f"It looks like I'm blocked by music provider service. Please try again later.")
        return

    username = "Unknown user"
    avatar = None
    try:
        user = guild.get_member(userid)
        username = user.name
        avatar = user.avatar.url
    except:
        pass

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

    cur.execute(f"UPDATE playlist SET userid = -userid WHERE guildid = {guildid} AND userid = {userid} AND title = '{title}'") # title already encoded
    conn.commit()

    embed = discord.Embed(title=f"Now playing", description=b64d(title), color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    embed.set_footer(text=f"Requested by {username}", icon_url = avatar)
    await ctx.send(embed = embed)

@tbot.command(name="queue", description="Music - Queue your song to the play list.")
async def PlayMusic(ctx):
    await ctx.channel.trigger_typing()    
    song = " ".join(ctx.message.content.split(" ")[1:])
    guildid = 0
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send(f"{ctx.author.name}, staff haven't set up a channel to request music! Tell them to use `/setchannel music {{#channel}}` to set it up!")
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.send(f"This is not the channel for using music commands.")
            return

    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.send(f"I'm not in a voice channel. Tell staff to use `/join` command to join me in.")
        return

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.send(f"I cannot find that song. This might be a temporary issue.")
        return

    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = '{b64e(title)}'")
    t = cur.fetchall()
    if len(t) > 0:
        await ctx.send(f"The song is already in the playlist.")
        return
    cur.execute(f"INSERT INTO playlist VALUES ({guildid}, {ctx.author.id}, '{b64e(title)}')")
    conn.commit()

    embed = discord.Embed(title=f"Added to queue", description=title, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    icon_url = None
    if not ctx.author.avatar is None:
        icon_url = ctx.author.avatar.url
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = icon_url)
    await ctx.send(embed = embed)

@tbot.command(name="dequeue", description="Music - Remove a song from play list.")
async def UnqueueMusic(ctx):
    await ctx.channel.trigger_typing() 
    song = " ".join(ctx.message.content.split(" ")[1:])   
    guildid = 0
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send(f"{ctx.author.name}, staff haven't set up a channel to request music! Tell them to use `/setchannel music {{#channel}}` to set it up!")
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.send(f"This is not the channel for using music commands.")
            return

    guildid = ctx.guild.id

    cur.execute(f"SELECT title, userid FROM playlist WHERE guildid = {guildid} AND userid > 0 AND title = '{b64e(song)}'")
    d = cur.fetchall()
    if len(d) == 0:
        await ctx.send(f"Song not in queue, you are suggested to use slash commands with autocomplete results.")
        return
    cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND userid > 0 AND title = '{b64e(song)}'")
    conn.commit()
    await ctx.send(f"**{song}** removed from queue.")

@tbot.command(name="fav", description="Music - Add the current song to your favourite list. Or add a custom one by providing its name.")
async def FavouriteMusic(ctx):
    await ctx.channel.trigger_typing()
    song = None
    if len(ctx.message.content.split(" ")) > 1:
        song = " ".join(ctx.message.content.split(" ")[1:])
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return
    guildid = ctx.guild.id

    conn = newconn()
    cur = conn.cursor()

    if song is None:
        cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send(f"No song is being played at the moment!")
            return
        tuserid = t[0][0]
        title = b64d(t[0][1])
        if tuserid == -1:
            title = t[0][1]
            link = title.split("-")[2]
            
            radiosong = GetCurrentSong(link)
            if radiosong != -1:
                song = radiosong
            else:
                song  = title.split("-")[1]
        else:
            song = title
    
    else:
        try:
            ydl = search(song)
            url = ydl['formats'][0]['url']
            title = ydl['title']
        except:
            await ctx.send(f"I cannot find that song. This might be a temporary issue.")
            return
        
        song = title
    
    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO favourite VALUES ({ctx.author.id}, '{b64e(song)}')")
    else:
        org = t[0][0].split(",")
        if b64e(song) in org:
            await ctx.send(f"The song is already in your favourite list.")
            return
        cur.execute(f"UPDATE favourite SET songs = '{t[0][0] + ',' + b64e(song)}' WHERE userid = {ctx.author.id}")
    conn.commit()

    await ctx.send(f"**{song}** has been added to your favourite list.")

@tbot.command(name="unfav", description="Music - Remove a song from your favourite list.")
async def UnFavouriteMusic(ctx):
    await ctx.channel.trigger_typing()
    song = " ".join(ctx.message.content.split(" ")[1:])
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return
    guildid = ctx.guild.id

    conn = newconn()
    cur = conn.cursor()

    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    org = t[0][0].split(",")
    if b64e(song) not in org:
        await ctx.send(f"The song is not in your favourite list.")
        return
    org.remove(b64e(song))
    cur.execute(f"UPDATE favourite SET songs = '{','.join(org)}' WHERE userid = {ctx.author.id}")
    conn.commit()

    await ctx.send(f"**{song}** is removed from your favourite list.")

@tbot.command(name="favlist", description="Music - Get your favourite list.")
async def FavouriteList(ctx):
    await ctx.channel.trigger_typing()
        
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    org = t[0][0].split(",")
    if len(org) == 0:
        await ctx.send(f"You don't have any favourite song.")
        return
    d = []
    for dd in org:
        d.append(b64d(dd))
    msg = f"**Your favourite song list:**\n" + '\n'.join(d)
    if len(msg) < 2000:
        embed = discord.Embed(title=f"{ctx.author.name}'s favourite list", description='\n'.join(d), color = GECKOCLR)
        embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
        embed.set_thumbnail(url=BOT_ICON)
        icon_url = None
        if not ctx.author.avatar is None:
            icon_url = ctx.author.avatar.url
        embed.set_footer(text=f"{ctx.author.name}", icon_url = icon_url)
        await ctx.send(embed = embed)
    else:
        f = io.BytesIO()
        f.write(msg.encode())
        f.seek(0)
        await ctx.send(file=discord.File(fp=f, filename='favourites.MD'))

@tbot.command(name="qfav", description="Music - Queue a song from your favourite list.")
async def Queuefavourite(ctx):
    await ctx.channel.trigger_typing()
    song = " ".join(ctx.message.content.split(" ")[1:])
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return
    guildid = ctx.guild.id
      
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    org = t[0][0].split(",")
    if b64e(song) not in org:
        await ctx.send(f"The song is not in your favourite list.")
        return

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send(f"{ctx.author.name}, staff haven't set up a channel to request music! Tell them to use `/setchannel music {{#channel}}` to set it up!")
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.send(f"This is not the channel for using music commands.")
            return

    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.send(f"I'm not in a voice channel. Tell staff to use `/join` command to join me in.")
        return

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.send(f"I cannot find that song. This might be a temporary issue.")
        return

    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = '{b64e(title)}'")
    t = cur.fetchall()
    if len(t) > 0:
        await ctx.send(f"The song is already in the playlist.")
        return
    cur.execute(f"INSERT INTO playlist VALUES ({guildid}, {ctx.author.id}, '{b64e(title)}')")
    conn.commit()

    embed = discord.Embed(title=f"Added to queue", description=title, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    icon_url = None
    if not ctx.author.avatar is None:
        icon_url = ctx.author.avatar.url
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = icon_url)
    await ctx.send(embed = embed)

@tbot.command(name="playlist", description="Music - See the queued play list.")
async def PlayList(ctx):
    await ctx.channel.trigger_typing() 
        
    guildid = 0
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send(f"{ctx.author.name}, staff haven't set up a channel to request music! Tell them to use `/setchannel music {{#channel}}` to set it up!")
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.send(f"This is not the channel for using music commands.")
            return

    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.send(f"Gecko is not playing music at the moment.")
        return

    guildid = ctx.guild.id

    current = "No song is being played at the moment."
    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
    t = cur.fetchall()
    if len(t) > 0:
        userid = t[0][0]
        title = t[0][1]
        current = b64d(t[0][1])

        if userid == -1:
            link = title.split("-")[2]
            
            radiosong = GetCurrentSong(link)
            if radiosong != -1:
                current = f"{radiosong} (**{title.split('-')[1]}**)"           
            else:
                current = title.split('-')[1]

    msg = f"**Current song**:\n {current}\n\n"

    msg += f"**Next Up**\n"

    cur.execute(f"SELECT title FROM playlist WHERE guildid = {guildid} AND userid > 0")
    d = cur.fetchall()
    i = 0
    for dd in d:
        i += 1
        msg += f"**{i}.** {b64d(dd[0])}\n"
    if i == 0:
        msg += f"No song in queue.\n"
    else:
        msg += "\n\n*Use /dequeue to remove a song from the list.*"
    
    embed = discord.Embed(title=f"Playlist", description=msg, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    if onloop(guildid):
        embed.set_footer(text=f"Loop playback enbled.")
    await ctx.send(embed = embed)

@tbot.command(name="current", description="Music - Get current playing song.")
async def CurrentSong(ctx):
    await ctx.channel.trigger_typing()
        
    if ctx.guild is None:
        await ctx.send(f"Music commands can only be used in guilds!")
        return
    guildid = ctx.guild.id

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send(f"{ctx.author.name}, staff haven't set up a channel to request music! Tell them to use `/setchannel music {{#channel}}` to set it up!")
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.send(f"This is not the channel for using music commands.")
            return

    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.send(f"Gecko is not playing music at the moment.")
        return

    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send(f"No song is being played at the moment! Use /queue to start.")
        return
    userid = -t[0][0]
    title = b64d(t[0][1])

    username = "Unknown user"
    avatar = None

    try:
        user = ctx.guild.get_member(userid)
        username = user.name
        avatar = user.avatar.url
    except:
        pass
    
    if userid == 1:
        title = t[0][1]
        link = title.split("-")[2]
        
        radiosong = GetCurrentSong(link)
        if radiosong != -1:
            embed = discord.Embed(title=f"Now playing", description=radiosong, color = GECKOCLR)
            embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
            embed.set_thumbnail(url=BOT_ICON)
            embed.set_footer(text="Radio: "+title.split("-")[1])
            await ctx.send(embed = embed)
        
        else:
            embed = discord.Embed(title=f"Now playing", description=title.split("-")[1], color = GECKOCLR)
            embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
            embed.set_thumbnail(url=BOT_ICON)
            embed.set_footer(text=f"Radio: "+title.split("-")[1], icon_url = avatar)
            await ctx.send(embed = embed)
    else:
        embed = discord.Embed(title=f"Now playing", description=title, color = GECKOCLR)
        embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
        embed.set_thumbnail(url=BOT_ICON)
        embed.set_footer(text=f"Requested by {username}", icon_url = avatar)
        await ctx.send(embed = embed)

@tbot.command(name="radio", description="Staff - Music - Play radio.")
async def Radio(ctx):
    await ctx.channel.trigger_typing()
    station = " ".join(ctx.message.content.split(" ")[1:])
    if ctx.guild is None:
        await ctx.send("You can only run this command in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return

    if CheckVCLock(ctx.guild.id):
        await ctx.send("Gecko VC is locked. Use `/vcrecord unlock` to unlock it.")
        return

    guildid = ctx.guild.id
    guild = ctx.guild
    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.send(f"I'm not in a voice channel. Use `/join` command to join me in.")
        return

    station = SearchRadio(station)
    idx = radioname.index(station)
    link = radiolist[idx].split("|")[0]

    conn = newconn()
    cur = conn.cursor()

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
    cur.execute(f"INSERT INTO playlist VALUES ({guildid}, -1, 'radio-{station}-{link}')")
    conn.commit()

    guild = bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client
    voice_client.stop()
    player = discord.FFmpegPCMAudio(source = link, before_options = FFMPEG_OPTIONS)
    voice_client.play(player)
    await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)

    await ctx.send(f"Current song has been overwritten to radio station **{station}**.\nThe playlist has been **saved**, use `/next` to go back playing songs.\nRadio streams have **no end**, so Gecko will not stop playing automatically.")

@tbot.command(name="radiolist", description="Music - Available radio station list.")
async def RadioList(ctx):
    await ctx.channel.trigger_typing()
    msg = ""
    for name in radioname:
        msg += name + "\n"
        if len(msg) > 2000:
            embed = discord.Embed(title=f"Radio station list", description=msg, color = GECKOCLR)
            embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
            embed.set_thumbnail(url=BOT_ICON)
            await ctx.send(embed = embed)
            msg = ""
    embed = discord.Embed(title=f"Radio station list", description=msg, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    await ctx.send(embed = embed)