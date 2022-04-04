# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Music of Gecko Bot

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from base64 import b64encode, b64decode
from time import time
import requests

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

async def suggest(ctx: discord.AutocompleteContext):
    if ctx.value.replace(" ", "") == "":
        return []
    endpoint = "https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q="
    res = requests.get(endpoint + ctx.value)
    res = res.json()
    return res[1]

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

class ManageMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("music", "Manage music")

    @manage.command(name="join", description = "Staff - Music - Join the voice channel you are in.")
    async def join(self, ctx):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.respond("You are not in a voice channel!", ephemeral = True)
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
        
        await ctx.respond(f"I've joined the voice channel.")

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

    @manage.command(name="leave", description = "Staff - Music - Join the voice channel you are in.")
    async def leave(self, ctx):
        await ctx.defer()
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
            await ctx.respond(f"I've left the voice channel.")
        else:
            await ctx.respond(f"I'm not connected to a voice channel.", ephemeral = True)

    @manage.command(name="pause", description="Staff - Music - Pause music.")
    async def pause(self, ctx):  
        await ctx.defer()
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
        user = ctx.guild.get_member(BOTID)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True)
        await ctx.respond(f"Music paused! You can use /music resume to restart from where it paused.")

    @manage.command(name="resume", description="Staff - Music - Resume music.")
    async def resume(self, ctx): 
        await ctx.defer()
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
        user = ctx.guild.get_member(BOTID)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
        await ctx.respond(f"Music resumed!")

    @manage.command(name="toggle", description="Staff - Music - Toggle 'Now Playing' auto post, whether Gecko should send it or not.")
    async def toggle(self, ctx): 
        await ctx.defer()
        if ctx.guild is None:
            await ctx.respond(f"Music can only be played in voice channels in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT sval FROM settings WHERE guildid = {ctx.guild.id} AND skey = 'music_update_post'")
        t = cur.fetchall()
        if len(t) == 0:
            cur.execute(f"INSERT INTO settings VALUES ({ctx.guild.id}, 'music_update_post', 0)")
            conn.commit()
            await ctx.respond(f"'Now Playing' will no longer be posted automatically.\nUse /current to get the current song.")
            return
        if t[0][0] == "1":
            cur.execute(f"UPDATE settings SET sval = '0' WHERE guildid = {ctx.guild.id} AND skey = 'music_update_post'")
            conn.commit()
            await ctx.respond(f"'Now Playing' will no longer be posted automatically.\nUse /current to get the current song.")
        else:
            cur.execute(f"UPDATE settings SET sval = '1' WHERE guildid = {ctx.guild.id} AND skey = 'music_update_post'")
            conn.commit()
            await ctx.respond(f"'Now Playing' will be posted automatically from now on.")

    @manage.command(name="clear", description="Staff - Music - Clear playlist.")
    async def clear(self, ctx): 
        await ctx.defer()
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

    @manage.command(name="loop", description="Staff - Music - Toggle loop playback of the playlist.")
    async def loop(self, ctx): 
        await ctx.defer()
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
async def PlayMusic(ctx, song: discord.Option(str, "Keywords to search on Youtube", required = True, autocomplete = suggest)):
    await ctx.defer()    
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

    if CheckVCLock(ctx.guild.id):
        await ctx.respond("Gecko VC is locked. Use `/vcrecord unlock` to unlock it.", ephemeral = True)
        return

    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Use /join command to join me in.", ephemeral = True)
        return

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
        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
        voice_client.play(player)
        user = ctx.guild.get_member(BOTID)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
    except:
        await ctx.respond(f"It looks like I'm blocked by youtube. Please try again later.")
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
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = ctx.author.avatar.url)
    await ctx.respond(embed = embed)

@bot.slash_command(name="next", description="Music - Play next song in queue.")
async def NextSong(ctx):    
    await ctx.defer()    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return

    if CheckVCLock(ctx.guild.id):
        await ctx.respond("Gecko VC is locked. Use `/vcrecord unlock` to unlock it.", ephemeral = True)
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
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for using music commands.", ephemeral = True)
            return
    
    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Tell staff to use /join command to join me in.", ephemeral = True)
        return

    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND userid = -1")
    t = cur.fetchall()
    if len(t) != 0:
        await ctx.respond(f"A radio stream is being played and you cannot override it. Only staff are allowed to run this command during radio streams.", ephemeral = True)
        return

    guildid = ctx.guild.id
    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid > 0 LIMIT 1")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.respond(f"There is no next-up songs in the playlist! Use /queue to add a song.", ephemeral = True)
        return
    userid = t[0][0]
    title = t[0][1]

    url = ""
    try:
        ydl = search(b64d(title))
        url = ydl['formats'][0]['url']
    except:
        await ctx.respond(f"Something went wrong. Try again later.")
        return

    if voice_client.is_playing() and not voice_client.is_paused():
        voice_client.stop()
    try:
        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
        voice_client.play(player)
        user = ctx.guild.get_member(BOTID)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
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
    await ctx.respond(embed = embed)

@bot.slash_command(name="queue", description="Music - Queue your song to the play list.")
async def PlayMusic(ctx, song: discord.Option(str, "Keywords to search on Youtube", required = True, autocomplete = suggest)):    
    await ctx.defer()    
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
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for using music commands.", ephemeral = True)
            return

    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Tell staff to use /join command to join me in.", ephemeral = True)
        return

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.respond(f"I cannot find that song. This might be a temporary issue.")
        return

    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND title = '{b64e(title)}'")
    t = cur.fetchall()
    if len(t) > 0:
        await ctx.respond(f"The song is already in the playlist.", ephemeral = True)
        return
    cur.execute(f"INSERT INTO playlist VALUES ({guildid}, {ctx.author.id}, '{b64e(title)}')")
    conn.commit()

    embed = discord.Embed(title=f"Added to queue", description=title, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = ctx.author.avatar.url)
    await ctx.respond(embed = embed)

@bot.slash_command(name="dequeue", description="Music - Remove a song from play list.")
async def UnqueueMusic(ctx, songid: discord.Option(int, "Song id (the number in front of its name)", required = True)): 
    await ctx.defer()    
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
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for using music commands.", ephemeral = True)
            return

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
            await ctx.respond(f"**{songid}.** **{b64d(dd[0])}** removed from queue.")

@bot.slash_command(name="playlist", description="Music - See the queued play list.")
async def PlayList(ctx): 
    await ctx.defer()    
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
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for using music commands.", ephemeral = True)
            return

    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"Gecko is not playing music at the moment.", ephemeral = True)
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
        msg += "\n\n*You can remove a song from playlist by using /dequeue [queue position].*"
    
    embed = discord.Embed(title=f"Playlist", description=msg, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    if onloop(guildid):
        embed.set_footer(text=f"Loop playback enbled.")
    await ctx.respond(embed = embed)

@bot.slash_command(name="current", description="Music - Get current playing song.")
async def CurrentSong(ctx):
    await ctx.defer()    
    if ctx.guild is None:
        await ctx.respond(f"Music can only be played in voice channels in guilds!")
        return
    guildid = ctx.guild.id

    conn = newconn()
    cur = conn.cursor()

    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"{ctx.author.name}, staff haven't set up a channel to request music! Tell them to use `/setchannel music {{#channel}}` to set it up!", ephemeral = True)
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for using music commands.", ephemeral = True)
            return

    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"Gecko is not playing music at the moment.", ephemeral = True)
        return

    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.respond(f"No song is being played at the moment! Use /queue to start.")
        return
    userid = -t[0][0]
    title = b64d(t[0][1])

    username = "Unknown user"
    avatar = ""

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
            await ctx.respond(embed = embed)
        
        else:
            embed = discord.Embed(title=f"Now playing", description=title.split("-")[1], color = GECKOCLR)
            embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
            embed.set_thumbnail(url=BOT_ICON)
            embed.set_footer(text=f"Radio: "+title.split("-")[1], icon_url = avatar)
            await ctx.respond(embed = embed)
    else:
        embed = discord.Embed(title=f"Now playing", description=title, color = GECKOCLR)
        embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
        embed.set_thumbnail(url=BOT_ICON)
        embed.set_footer(text=f"Requested by {username}", icon_url = avatar)
        await ctx.respond(embed = embed)

async def RadioSearcher(ctx: discord.AutocompleteContext):
    if ctx.value.replace(" ", "") == "":
        return radioname[:10]
    res = SearchRadioMul(ctx.value.lower())
    return res

@bot.slash_command(name="radio", description="Staff - Music - Play radio.")
async def Radio(ctx, station: discord.Option(str, "Radio station (274 stations available)", required = True, autocomplete = RadioSearcher)):
    await ctx.defer()    
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    if CheckVCLock(ctx.guild.id):
        await ctx.respond("Gecko VC is locked. Use `/vcrecord unlock` to unlock it.", ephemeral = True)
        return

    guildid = ctx.guild.id
    guild = ctx.guild
    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Use /join command to join me in.", ephemeral = True)
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

    voice_client = guild.voice_client
    voice_client.stop()
    player = discord.FFmpegPCMAudio(source = link, before_options = FFMPEG_OPTIONS)
    voice_client.play(player)
    await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)

    await ctx.respond(f"Current song has been overwritten to radio station **{station}**.\nThe playlist has been **saved**, use `/next` to go back playing songs.\nRadio streams have **no end**, so Gecko will not stop playing automatically.")

@bot.slash_command(name="radiolist", description="Music - Available radio station list.")
async def RadioList(ctx):
    await ctx.defer()    
    msg = ""
    for name in radioname:
        msg += name + "\n"
        if len(msg) > 2000:
            embed = discord.Embed(title=f"Radio station list", description=msg, color = GECKOCLR)
            embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
            embed.set_thumbnail(url=BOT_ICON)
            await ctx.respond(embed = embed, ephemeral = True)
            msg = ""
    embed = discord.Embed(title=f"Radio station list", description=msg, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=BOT_ICON)
    await ctx.respond(embed = embed, ephemeral = True)

def postupdate(guildid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT sval FROM settings WHERE guildid = {guildid} AND skey = 'music_update_post'")
    t = cur.fetchall()
    if len(t) == 0 or t[0][0] == "1":
        return True
    elif t[0][0] == "0":
        return False

async def MusicLoop():
    conn = newconn()
    cur = conn.cursor()
    await bot.wait_until_ready()
    await asyncio.sleep(5)

    emptynotice = []
    cursong = {} # cursong[url] = {song name, last update}
    guildsong = {} # guildsong[guildid] = {song name}
    autopause = []

    while not bot.is_closed():
        cur.execute(f"SELECT guildid, channelid FROM vcbind")
        t = cur.fetchall()
        for tt in t:
            try:
                guildid = tt[0]
                channelid = tt[1]
                if not guildid in guildsong.keys():
                    guildsong[guildid] = ""

                guild = bot.get_guild(guildid)
                voice_client = guild.voice_client
                            
                if CheckVCLock(guildid):
                    continue

                if voice_client is None or voice_client.channel is None:
                    # bot is disconnected - then play current / previous song
                    cur.execute(f"SELECT channelid FROM vcbind WHERE guildid = {guildid}")
                    p = cur.fetchall()
                    if len(p) > 0:
                        channelid = p[0][0]
                        channel = bot.get_channel(channelid)
                        try:
                            await channel.connect(timeout = 5)
                        except:
                            # failed to connect, try again next loop
                            continue
            
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
                                # failed to connect, try again next loop
                                continue
                        else:
                            title = p[0][1].split("-")[1]
                            url = p[0][1].split("-")[2]
                        
                        try:
                            player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
                            voice_client.play(player)
                            await guild.change_voice_state(channel = voice_client.channel, self_mute = False)
                        except:
                            await voice_client.disconnect()
                            # failed to play, try again next loop
                            continue
                    
                    voice_client = guild.voice_client
                    if not voice_client.is_playing() and not voice_client.is_paused():
                        await guild.change_voice_state(channel = voice_client.channel, self_mute = True)
                        
                    continue
                
                # Get music text channel to post updates
                textchn = None
                cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'music'")
                t = cur.fetchall()
                if len(t) > 0:
                    textchnid = t[0][0]
                    try:
                        textchn = bot.get_channel(textchnid)
                    except:
                        pass
                
                # Radio current song update
                cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid = -1")
                o = cur.fetchall()
                if len(o) > 0:
                    title = o[0][1]
                    link = title.split("-")[2]
                    if link in cursong.keys() and guildsong[guildid] != cursong[link][0]:
                        guildsong[guildid] = cursong[link][0]
                        radiosong = cursong[link][0]
                        if postupdate(guildid):
                            embed = discord.Embed(title=f"Now playing", description=radiosong, color = GECKOCLR)
                            embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
                            embed.set_thumbnail(url=BOT_ICON)
                            embed.set_footer(text="Radio: "+title.split("-")[1])
                            if not textchn is None:
                                await textchn.send(embed=embed)
                        
                    if link in cursong.keys() and time() - cursong[link][1] <= 15:
                        continue
                    else:
                        radiosong = GetCurrentSong(link)
                        if radiosong != -1 and (not link in cursong.keys() or cursong[link][0] != radiosong):
                            cursong[link] = (radiosong, int(time()))

                # only bot in channel - then pause music to save bandwidth
                members = voice_client.channel.members
                for member in members:
                    if member.bot == True or member.id == BOTID:
                        members.remove(member)
                        
                if len(members) == 0 and not guildid in autopause:
                    autopause.append(guildid)
                    await guild.change_voice_state(channel = voice_client.channel, self_deaf = True)
                    if len(o) > 0: # if playing radio - then stop ffmpeg to prevent the radio from being paused
                        voice_client.stop()
                    else:
                        voice_client.pause()
                    continue
                if len(members) > 0 and guildid in autopause:
                    autopause.remove(guildid)
                    await guild.change_voice_state(channel = voice_client.channel, self_deaf = False)
                    if len(o) > 0: # if playing radio - then restart ffmpeg
                        radio = o[0][1].split("-")
                        link = radio[2]
                        try:
                            player = discord.FFmpegPCMAudio(source = link, before_options = FFMPEG_OPTIONS)
                            voice_client.play(player)
                        except:
                            autopause.append(guildid)
                            # failed to start, try again next time
                            continue
                    else:
                        voice_client.resume()
                    continue
                
                if guildid in autopause:
                    continue
                
                # play only if the previous music has ended
                if not voice_client.is_playing() and not voice_client.is_paused():
                    # remove current song (move to end if loop)
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

                    # get next song
                    cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid > 0 LIMIT 1")
                    d = cur.fetchall()
                    if len(d) == 0:
                        await guild.change_voice_state(channel = voice_client.channel, self_mute = True)
                        if not guildid in emptynotice:
                            emptynotice.append(guildid)
                            embed = discord.Embed(title=f"Playlist is empty", description="Use /queue to fill it!", color = GECKOCLR)
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
                    etitle = title
                    url = ""

                    if userid != 1:                
                        try:
                            ydl = search(b64d(title))
                            url = ydl['formats'][0]['url']
                            title = ydl['title']
                        except:
                            if textchn != None:
                                await textchn.send(f"I cannot find the song **{title}**. This might be a temporary issue.")
                            continue
                    else: # in case radio is in playlist accidentally - NOTE This shouldn't happen
                        data = title
                        title = data.split("-")[1]
                        url = data.split("-")[2]

                    # get music requester
                    username = "Unknown user"
                    avatar = ""
                    try:
                        user = guild.get_member(userid)
                        username = user.name
                        avatar = user.avatar.url
                    except:
                        pass
                    
                    # play music
                    try:
                        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
                        if voice_client.is_playing(): # if already playing, in case user ran /play or /next
                            continue
                        voice_client.play(player)
                        await guild.change_voice_state(channel = voice_client.channel, self_mute = False)
                    except:
                        if textchn != None:
                            await textchn.send(f"Something went wrong.")
                        continue
                    
                    cur.execute(f"UPDATE playlist SET userid = -userid WHERE guildid = {guildid} AND userid = {userid} AND title = '{etitle}'")
                    conn.commit()

                    # post current song update
                    if textchn != None and postupdate(guildid):
                        embed = discord.Embed(title=f"Now playing", description=title, color = GECKOCLR)
                        embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
                        embed.set_thumbnail(url=BOT_ICON)
                        embed.set_footer(text=f"Requested by {username}", icon_url = avatar)
                        await textchn.send(embed=embed)
                
                else: # in case bot didn't unmute itself automatically NOTE This shouldn't happen
                    await guild.change_voice_state(channel = voice_client.channel, self_mute = False)
                        
            except Exception as e:
                import traceback
                traceback.print_exc()
                try:
                    await log("ERROR",f"Music error: {str(e)}")
                except:
                    pass
            
        await asyncio.sleep(3)

bot.loop.create_task(MusicLoop())
bot.add_cog(ManageMusic(bot))