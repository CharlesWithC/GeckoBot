# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Music of Gecko Bot

import os, asyncio
import discord
from base64 import b64encode, b64decode

from requests import get
from youtube_dl import YoutubeDL

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
def search(arg):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            get(arg) 
        except:
            video = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        else:
            video = ydl.extract_info(arg, download=False)
    return video

from bot import bot
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

@bot.slash_command(name="join", description = "Staff - Music - Join the voice channel you are in.")
async def JoinVC(ctx):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    voice_client = ctx.guild.voice_client
    if not voice_client is None and voice_client.is_connected():
        await voice_client.disconnect()
    try:
        channel = ctx.author.voice.channel
        await channel.connect(timeout = 5)
    except:
        await ctx.respond(f"I cannot join the voice channel you are in. Maybe I don't have access or I'm rate limited. Please try again later.", ephemeral = True)
        return

    conn = newconn()
    cur = conn.cursor()
    guildid = ctx.guild.id
    voice_client = ctx.guild.voice_client
    cur.execute(f"DELETE FROM vcbind WHERE guildid = {guildid}")
    cur.execute(f"INSERT INTO vcbind VALUES ({guildid}, {voice_client.channel.id})")
    conn.commit()

    user = ctx.guild.get_member(BOTID)
    await user.edit(mute = True, deafen = True)
    
    await ctx.respond(f"I've joined the voice channel.")

@bot.slash_command(name="leave", description = "Staff - Music - Join the voice channel you are in.")
async def LeaveVC(ctx):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    voice_client = ctx.guild.voice_client
    if not voice_client is None and voice_client.is_connected():
        await voice_client.disconnect()
        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id
        cur.execute(f"DELETE FROM vcbind WHERE guildid = {guildid}")
        conn.commit()
        await ctx.respond(f"I've left from the voice channel.")
    else:
        await ctx.respond(f"I'm not connected to a voice channel.", ephemeral = True)

@bot.slash_command(name="pause", description="Staff - Music - Pause music.")
async def PauseMusic(ctx):  
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    voice_client = ctx.guild.voice_client
    if voice_client is None or not voice_client.is_playing():
        await ctx.respond(f"Music hasn't even started!", ephemeral = True)
        return

    voice_client.pause()
    await ctx.respond(f"Music paused! You can use /resume to restart from where it paused.")

@bot.slash_command(name="resume", description="Staff - Music - Resume music.")
async def ResumeMusic(ctx): 
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        await ctx.respond(f"Music is already playing.", ephemeral = True)
        return

    voice_client.resume()
    await ctx.respond(f"Music resumed!")

@bot.slash_command(name="clear", description="Staff - Music - Clear playlist.")
async def ResumeMusic(ctx): 
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM playlist WHERE userid > 0")
    conn.commit()
    
    await ctx.respond(f"Playlist cleared!")

@bot.slash_command(name="loop", description="Staff - Music - Toggle loop playback of the playlist.")
async def LoopMusic(ctx): 
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    conn = newconn()
    cur = conn.cursor()
    guildid = ctx.guild.id
    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = 'loop' AND userid = 0")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO playlist VALUES ({guildid}, 0, 'loop')")
        conn.commit()
        await ctx.respond(f"Loop playback enabled for playlist!")
    else:
        cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND title = 'loop' AND userid = 0")
        conn.commit()
        await ctx.respond(f"Loop playback disabled for playlist!")

@bot.slash_command(name="play", description="Staff - Music - Play a song.")
async def PlayMusic(ctx, song: discord.Option(str, "Keywords to search on Youtube", required = True)):    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Use /join command to join me in.", ephemeral = True)
        return

    await ctx.defer()

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.respond(f"I cannot find that song. This might be a temporary issue.")
        return
    
    if voice_client.is_playing() and not voice_client.is_paused():
        voice_client.stop()
    try:
        user = ctx.guild.get_member(BOTID)
        await user.edit(mute = False, deafen = True)
        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
        voice_client.play(player)
    except:
        await ctx.respond(f"It looks like I'm blocked by youtube. Please try again later.")
        return
    
    if not onloop(guildid):
        cur.execute(f"DELETE FROM playlist WHERE userid < 0 AND guildid = {guildid}")
    else:
        cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
        q = cur.fetchall()
        if len(q) > 0:
            cur.execute(f"INSERT INTO playlist VALUES ({guildid}, {-q[0][0]}, '{q[0][1]}')")
        cur.execute(f"DELETE FROM playlist WHERE userid < 0 AND guildid = {guildid}")
    
    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = '{b64encode(title.encode()).decode()}'")
    t = cur.fetchall()
    if len(t) > 0:
        cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND title = '{b64encode(title.encode()).decode()}'")
    cur.execute(f"INSERT INTO playlist VALUES ({guildid}, -{ctx.author.id}, '{b64encode(title.encode()).decode()}')")
    conn.commit()

    embed = discord.Embed(title=f"Now playing", description=title)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = ctx.author.avatar.url)
    await ctx.respond(embed = embed)

@bot.slash_command(name="next", description="Music - Play next song in queue.")
async def NextSong(ctx):    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return
    
    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Tell staff to use /join command to join me in.", ephemeral = True)
        return

    conn = newconn()
    cur = conn.cursor()
    guildid = ctx.guild.id
    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid > 0 LIMIT 1")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.respond(f"There is no next-up songs in the playlist! Use /queue to add a song.", ephemeral = True)
        return
    userid = t[0][0]
    title = t[0][1]

    await ctx.defer()

    url = ""
    try:
        ydl = search(b64decode(title.encode()).decode())
        url = ydl['formats'][0]['url']
    except:
        await ctx.respond(f"Something went wrong. Try again later.")
        return

    try:
        user = ctx.guild.get_member(BOTID)
        await user.edit(mute = False, deafen = True)
        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
        if voice_client.is_playing():
            voice_client.stop()
        voice_client.play(player)
    except:
        await ctx.respond(f"It looks like I'm blocked by youtube. Please try again later.")
        return

    username = "Unknown user"
    avatar = ""
    try:
        user = guild.get_member(userid)
        username = user.name
        avatar = user.avatar.url
    except:
        pass
    
    if not onloop(guildid):
        cur.execute(f"DELETE FROM playlist WHERE userid < 0 AND guildid = {guildid}")
    else:
        cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
        q = cur.fetchall()
        if len(q) > 0:
            cur.execute(f"INSERT INTO playlist VALUES ({guildid}, {-q[0][0]}, '{q[0][1]}')")
        cur.execute(f"DELETE FROM playlist WHERE userid < 0 AND guildid = {guildid}")

    cur.execute(f"UPDATE playlist SET userid = -userid WHERE guildid = {guildid} AND userid = {userid} AND title = '{title}'") # title already encoded
    conn.commit()

    embed = discord.Embed(title=f"Now playing", description=b64decode(title.encode()).decode())
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    embed.set_footer(text=f"Requested by {username}", icon_url = avatar)
    await ctx.respond(embed = embed)

@bot.slash_command(name="queue", description="Music - Queue your song to the play list.")
async def PlayMusic(ctx, song: discord.Option(str, "Keywords to search on Youtube", required = True)):    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"{ctx.author.name}, staff haven't set up a channel to request music! Tell them to use `/setchannel music {{#channel}}` to set it up!", ephemeral = True)
            return
        if t[0][0] != ctx.channel.id:
            await ctx.respond(f"This is not the channel for requesting music!", ephemeral = True)
            return

    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Tell staff to use /join command to join me in.", ephemeral = True)
        return

    await ctx.defer()

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.respond(f"I cannot find that song. This might be a temporary issue.")
        return

    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = '{b64encode(title.encode()).decode()}'")
    t = cur.fetchall()
    if len(t) > 0:
        await ctx.respond(f"The song is already in the playlist.", ephemeral = True)
        return
    cur.execute(f"INSERT INTO playlist VALUES ({guildid}, {ctx.author.id}, '{b64encode(title.encode()).decode()}')")
    conn.commit()

    embed = discord.Embed(title=f"Added to queue", description=title)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = ctx.author.avatar.url)
    await ctx.respond(embed = embed)

@bot.slash_command(name="dequeue", description="Music - Remove a song from play list.")
async def UnqueueMusic(ctx, songid: discord.Option(int, "Song id (the number in front of its name)", required = True)): 
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id

    cur.execute(f"SELECT title, userid FROM playlist WHERE guildid = {guildid} AND userid > 0")
    d = cur.fetchall()
    i = 0
    msg = ""
    for dd in d:
        i += 1
        if songid == i:
            if dd[1] != ctx.author.id and not isStaff(ctx.guild, ctx.author):
                await ctx.respond(f"Only who queued the song or the staff could dequeue the song!", ephemeral = True)
                return
            cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND title = '{dd[0]}' AND userid = {dd[1]}")
            conn.commit()
            await ctx.respond(f"**{songid}.** **{b64decode(dd[0].encode()).decode()}** removed from queue.")

@bot.slash_command(name="playlist", description="Music - See the queued play list.")
async def PlayList(ctx): 
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id

    current = "No song is being played at the moment."
    cur.execute(f"SELECT title FROM playlist WHERE guildid = {guildid} AND userid < 0")
    t = cur.fetchall()
    if len(t) > 0:
        current = b64decode(t[0][0].encode()).decode()
    msg = f"**Current song**:\n {current}\n\n"

    msg += f"**Next Up**\n"

    cur.execute(f"SELECT title FROM playlist WHERE guildid = {guildid} AND userid > 0")
    d = cur.fetchall()
    i = 0
    for dd in d:
        i += 1
        msg += f"**{i}.** {b64decode(dd[0].encode()).decode()}\n"
    if i == 0:
        msg += f"No song in queue.\n"
    else:
        msg += "\n\n*You can remove a song from playlist by using /dequeue [queue position].*"
    
    embed = discord.Embed(title=f"Playlist", description=msg)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    if onloop(guildid):
        embed.set_footer(text=f"Loop playback enbled.")
    await ctx.respond(embed = embed)

@bot.slash_command(name="current", description="Music - Get current playing song.")
async def CurrentSong(ctx):
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return
    guildid = ctx.guild.id

    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.respond(f"No song is being played at the moment! Use /queue to start.")
        return
    userid = -t[0][0]
    title = b64decode(t[0][1].encode()).decode()

    username = "Unknown user"
    avatar = ""

    try:
        user = ctx.guild.get_member(userid)
        username = user.name
        avatar = user.avatar.url
    except:
        pass

    embed = discord.Embed(title=f"Now playing", description=title)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    embed.set_footer(text=f"Requested by {username}", icon_url = avatar)
    await ctx.respond(embed = embed)

async def MusicLoop():
    conn = newconn()
    cur = conn.cursor()
    await bot.wait_until_ready()
    await bot.change_presence(activity=discord.Game(name = "with Charles"))
    await asyncio.sleep(5)

    emptynotice = []

    while not bot.is_closed():
        cur.execute(f"SELECT guildid, channelid FROM vcbind")
        t = cur.fetchall()
        for tt in t:
            guildid = tt[0]
            channelid = tt[1]

            guild = bot.get_guild(guildid)
            voice_client = guild.voice_client

            if voice_client is None or voice_client.channel is None:
                # bot is disconnected - then play current / previous song
                cur.execute(f"SELECT channelid FROM vcbind WHERE guildid = {guildid}")
                p = cur.fetchall()
                if len(p) > 0:
                    channelid = p[0][0]
                    channel = bot.get_channel(channelid)
                    try:
                        await channel.connect(timeout = 5)
                        user = guild.get_member(BOTID)
                        await user.edit(mute = True, deafen = True)
                    except:
                        # failed to connect, try again next loop
                        continue
        
                cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
                p = cur.fetchall()
                if len(p) > 0:
                    guild = bot.get_guild(guildid)
                    voice_client = guild.voice_client

                    url = ""
                    try:
                        ydl = search(b64decode(p[0][1].encode()).decode())
                        url = ydl['formats'][0]['url']
                    except:
                        # failed to connect, try again next loop
                        continue
                    
                    try:
                        user = guild.get_member(BOTID)
                        await user.edit(mute = False, deafen = True)
                        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
                        voice_client.play(player)
                    except:
                        # failed to play, try again next loop
                        continue
                    
                continue
            
            textchn = None
            cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
            t = cur.fetchall()
            if len(t) > 0:
                textchnid = t[0][0]
                try:
                    textchn = bot.get_channel(textchnid)
                except:
                    pass
            
            # play only if the previous music has ended
            if not voice_client.is_playing() and not voice_client.is_paused():
                if not onloop(guildid):
                    cur.execute(f"DELETE FROM playlist WHERE userid < 0 AND guildid = {guildid}")
                else:
                    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
                    q = cur.fetchall()
                    if len(q) > 0:
                        cur.execute(f"INSERT INTO playlist VALUES ({guildid}, {-q[0][0]}, '{q[0][1]}')")
                    cur.execute(f"DELETE FROM playlist WHERE userid < 0 AND guildid = {guildid}")
                conn.commit()

                cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid > 0")
                d = cur.fetchall()
                if len(d) == 0:
                    user = guild.get_member(BOTID)
                    await user.edit(mute = True, deafen = True)
                    if not guildid in emptynotice:
                        emptynotice.append(guildid)
                        embed = discord.Embed(title=f"Playlist is empty", description="Use /queue to fill it!")
                        embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
                        embed.set_thumbnail(url=BOT_ICON)
                        if textchn != None:
                            await textchn.send(embed = embed)
                    continue
                if guildid in emptynotice:
                    emptynotice.remove(guildid)
                dd = d[0]
                userid = dd[0]
                title = dd[1]

                url = ""
                
                try:
                    ydl = search(b64decode(title.encode()).decode())
                    url = ydl['formats'][0]['url']
                    title = ydl['title']
                except:
                    if textchn != None:
                        await textchn.send(f"I cannot find the song **{title}**. This might be a temporary issue.")
                    continue

                username = "Unknown user"
                avatar = ""
                try:
                    user = guild.get_member(userid)
                    username = user.name
                    avatar = user.avatar.url
                except:
                    pass

                try:
                    user = guild.get_member(BOTID)
                    await user.edit(mute = False, deafen = True)
                    player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
                    if voice_client.is_playing():
                        continue
                    voice_client.play(player)
                except:
                    if textchn != None:
                        await textchn.send(f"Something went wrong.")
                    continue

                cur.execute(f"UPDATE playlist SET userid = -userid WHERE guildid = {guildid} AND userid = {userid} AND title = '{b64encode(title.encode()).decode()}'")
                conn.commit()
                if textchn != None:
                    title = ydl['title']

                    current = "No song is being played at the moment."
                    cur.execute(f"SELECT title FROM playlist WHERE guildid = {guildid} AND userid < 0")
                    q = cur.fetchall()
                    if len(q) > 0:
                        current = b64decode(q[0][0].encode()).decode()
                    msg = f"**Current song**:\n {current}\n\n"

                    msg += f"**Next Up**\n"

                    cur.execute(f"SELECT title FROM playlist WHERE guildid = {guildid} AND userid > 0")
                    q = cur.fetchall()
                    i = 0
                    for qq in q:
                        i += 1
                        msg += f"**{i}.** {b64decode(qq[0].encode()).decode()}\n"
                    if i == 0:
                        msg += f"No song in queue.\n"
                    else:
                        msg += "\n\n*You can remove a song from playlist by using /dequeue [queue position].*"
                    
                    embed = discord.Embed(title=f"Playlist", description=msg)
                    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
                    embed.set_thumbnail(url=BOT_ICON)
                    if onloop(guildid):
                        embed.set_footer(text=f"Loop playback enbled.")
                    await textchn.send(embed = embed)
    
        await asyncio.sleep(3)

bot.loop.create_task(MusicLoop())