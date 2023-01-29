# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Music

import os, asyncio
import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands
from time import time
import requests
from rapidfuzz import process

from general.radiolist import radiolist, radioname, radiolink, SearchRadio, SearchRadioMul

from requests import get
from youtube_dl import YoutubeDL

WHITELIST = [955721720440975381, 929761730089877626, 648872349516693515]

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True, 'quite': True, 'ignoreerrors': True}
def search(arg):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            get(arg) 
        except:
            video = ydl.extract_info(f"ytsearch1:{arg}", download=False)['entries'][0]
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
    
    manage = SlashCommandGroup("music", "Manage music", guild_ids = WHITELIST)

    @manage.command(name="toggle", description="Staff - Music - Toggle 'Now Playing' auto post, whether Gecko should send it or not.")
    async def toggle(self, ctx): 
        await ctx.defer()
        if ctx.guild is None:
            await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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
            await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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
            await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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

@bot.slash_command(name="pause", description="Staff - Music - Pause music.", guild_ids = WHITELIST)
async def pause(ctx):  
    await ctx.defer()
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    voice_client = ctx.guild.voice_client
    if voice_client is None or not voice_client.is_playing():
        await ctx.respond(f"Music hasn't even started!", ephemeral = True)
        return

    voice_client.pause()
    await ctx.guild.change_voice_state(channel = voice_client.channel, self_mute = True)
    await ctx.respond(f"Music paused! You can use /music resume to restart from where it paused.")

@bot.slash_command(name="resume", description="Staff - Music - Resume music.", guild_ids = WHITELIST)
async def resume(ctx): 
    await ctx.defer()
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        await ctx.respond(f"Music is already playing.", ephemeral = True)
        return

    voice_client.resume()
    await ctx.guild.change_voice_state(channel = voice_client.channel, self_mute = False)
    await ctx.respond(f"Music resumed!")

@bot.slash_command(name="play", description="Staff - Music - Play a song.", guild_ids = WHITELIST)
async def PlayMusic(ctx, song: discord.Option(str, "Keywords for searching, if not specified, play the music on last quit", required = False, autocomplete = suggest)):
    await ctx.defer()    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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
        await ctx.respond(f"I'm not in a voice channel. Use `/join` command to join me in.", ephemeral = True)
        return
    
    if song is None:
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
                if voice_client.is_playing():
                    voice_client.stop()
                voice_client.play(player)
                await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
            except:
                await ctx.respond(f"Unknown error.", ephemeral = True)
                return
    
    voice_client = ctx.guild.voice_client
    if not voice_client.is_playing() and not voice_client.is_paused():
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = True)

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.respond(f"I cannot find that song. This might be a temporary issue.", ephemeral = True)
        return
    
    if voice_client.is_playing() and not voice_client.is_paused():
        voice_client.stop()
    try:
        player = discord.FFmpegPCMAudio(source = url, before_options = FFMPEG_OPTIONS)
        voice_client.play(player)
        user = ctx.guild.get_member(BOTID)
        await ctx.guild.change_voice_state(channel = ctx.voice_client.channel, self_mute = False)
    except:
        await ctx.respond(f"It looks like I'm blocked by music provider service. Please try again later.")
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
    embed.set_thumbnail(url=GECKOICON)
    icon_url = discord.Embed.Empty
    if not ctx.author.avatar is None:
        icon_url = ctx.author.avatar.url
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = icon_url)
    await ctx.respond(embed = embed)

@bot.slash_command(name="next", description="Music - Play next song in queue.", guild_ids = WHITELIST)
async def NextSong(ctx):    
    await ctx.defer()    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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
        cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND userid = -1")
        t = cur.fetchall()
        if len(t) != 0:
            await ctx.respond(f"A radio stream is being played and you cannot override it. Only staff are allowed to run this command during radio streams.", ephemeral = True)
            return
    
    voice_client = ctx.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        await ctx.respond(f"I'm not in a voice channel. Tell staff to use `/join` command to join me in.", ephemeral = True)
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
        await ctx.respond(f"It looks like I'm blocked by music provider service. Please try again later.")
        return

    username = "Unknown user"
    avatar = discord.Embed.Empty
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
    embed.set_thumbnail(url=GECKOICON)
    embed.set_footer(text=f"Requested by {username}", icon_url = avatar)
    await ctx.respond(embed = embed)

@bot.slash_command(name="queue", description="Music - Queue your song to the play list.", guild_ids = WHITELIST)
async def PlayMusic(ctx, song: discord.Option(str, "Keywords for searching", required = True, autocomplete = suggest)):    
    await ctx.defer()    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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
        await ctx.respond(f"I'm not in a voice channel. Tell staff to use `/join` command to join me in.", ephemeral = True)
        return

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.respond(f"I cannot find that song. This might be a temporary issue.", ephemeral = True)
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
    embed.set_thumbnail(url=GECKOICON)
    icon_url = discord.Embed.Empty
    if not ctx.author.avatar is None:
        icon_url = ctx.author.avatar.url
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = icon_url)
    await ctx.respond(embed = embed)

async def GetQueueList(ctx: discord.AutocompleteContext):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT title FROM playlist WHERE guildid = {ctx.interaction.guild.id} AND userid > 0")
    t = cur.fetchall()
    if len(t) == 0:
        return []
    d = []
    for tt in t:
        d.append(b64d(tt[0]))
    if ctx.value.replace(" ","") == "":
        return d[:10]
    d = process.extract(ctx.value.lower(), d, limit = 10, score_cutoff = 80)
    ret = []
    for dd in d:
        ret.append(dd[0])
    return ret[:10]

@bot.slash_command(name="dequeue", description="Music - Remove a song from play list.", guild_ids = WHITELIST)
async def UnqueueMusic(ctx, song: discord.Option(str, "Song, must be one from the autocomplete options", required = True, autocomplete = GetQueueList)): 
    await ctx.defer()    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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

    cur.execute(f"SELECT title, userid FROM playlist WHERE guildid = {guildid} AND userid > 0 AND title = '{b64e(song)}'")
    d = cur.fetchall()
    if len(d) == 0:
        await ctx.respond(f"Song not in queue, make sure you selected one option from the autocomplete results.", ephemeral = True)
        return
    cur.execute(f"DELETE FROM playlist WHERE guildid = {guildid} AND userid > 0 AND title = '{b64e(song)}'")
    conn.commit()
    await ctx.respond(f"**{song}** removed from queue.")

@bot.slash_command(name="fav", description="Music - Add the current song to your favourite list. Or add a custom one by providing its name.", guild_ids = WHITELIST)
async def FavouriteMusic(ctx, song: discord.Option(str, "Keywords for searching", required = False, autocomplete = suggest)):
    await ctx.defer()    
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
        return
    guildid = ctx.guild.id

    conn = newconn()
    cur = conn.cursor()

    if song is None:
        cur.execute(f"SELECT userid, title FROM playlist WHERE guildid = {guildid} AND userid < 0")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"No song is being played at the moment!", ephemeral = True)
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
            await ctx.respond(f"I cannot find that song. This might be a temporary issue.", ephemeral = True)
            return
        
        song = title
    
    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO favourite VALUES ({ctx.author.id}, '{b64e(song)}')")
    else:
        org = t[0][0].split(",")
        if b64e(song) in org:
            await ctx.respond(f"The song is already in your favourite list.", ephemeral = True)
            return
        cur.execute(f"UPDATE favourite SET songs = '{t[0][0] + ',' + b64e(song)}' WHERE userid = {ctx.author.id}")
    conn.commit()

    await ctx.respond(f"**{song}** has been added to your favourite list.", ephemeral = True)

async def GetfavouriteList(ctx: discord.AutocompleteContext):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.interaction.user.id}")
    t = cur.fetchall()
    if len(t) == 0:
        return []
    d = []
    for dd in t[0][0].split(","):
        d.append(b64d(dd))
    if ctx.value.replace(" ","") == "":
        return d[:10]
    d = process.extract(ctx.value.lower(), d, limit = 10, score_cutoff = 80)
    ret = []
    for dd in d:
        ret.append(dd[0])
    return ret[:10]

@bot.slash_command(name="unfav", description="Music - Remove a song from your favourite list.", guild_ids = WHITELIST)
async def UnFavouriteMusic(ctx, song: discord.Option(str, "Song, must be one from the autocomplete options", required = True, autocomplete = GetfavouriteList)):
    await ctx.defer()    
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
        return
    guildid = ctx.guild.id

    conn = newconn()
    cur = conn.cursor()

    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    org = t[0][0].split(",")
    if b64e(song) not in org:
        await ctx.respond(f"The song is not in your favourite list.", ephemeral = True)
        return
    org.remove(b64e(song))
    cur.execute(f"UPDATE favourite SET songs = '{','.join(org)}' WHERE userid = {ctx.author.id}")
    conn.commit()

    await ctx.respond(f"**{song}** is removed from your favourite list.", ephemeral = True)

@bot.slash_command(name="favlist", description="Music - Get your favourite list.", guild_ids = WHITELIST)
async def FavouriteList(ctx):
    await ctx.defer()    
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    org = t[0][0].split(",")
    if len(org) == 0:
        await ctx.respond(f"You don't have any favourite song.", ephemeral = True)
        return
    d = []
    for dd in org:
        d.append(b64d(dd))
    msg = f"**Your favourite song list:**\n" + '\n'.join(d)
    if len(msg) < 2000:
        embed = discord.Embed(title=f"{ctx.author.name}'s favourite list", description='\n'.join(d), color = GECKOCLR)
        embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
        embed.set_thumbnail(url=GECKOICON)
        icon_url = discord.Embed.Empty
        if not ctx.author.avatar is None:
            icon_url = ctx.author.avatar.url
        embed.set_footer(text=f"{ctx.author.name}", icon_url = icon_url)
        await ctx.respond(embed = embed)
    else:
        f = io.BytesIO()
        f.write(msg.encode())
        f.seek(0)
        await ctx.respond(file=discord.File(fp=f, filename='favourites.MD'))

@bot.slash_command(name="qfav", description="Music - Queue a song from your favourite list.", guild_ids = WHITELIST)
async def Queuefavourite(ctx, song: discord.Option(str, "Song, must be one from the autocomplete options", required = True, autocomplete = GetfavouriteList)):
    # queue the song
    await ctx.defer()    
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
        return
    guildid = ctx.guild.id
      
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT songs FROM favourite WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    org = t[0][0].split(",")
    if b64e(song) not in org:
        await ctx.respond(f"The song is not in your favourite list.", ephemeral = True)
        return

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
        await ctx.respond(f"I'm not in a voice channel. Tell staff to use `/join` command to join me in.", ephemeral = True)
        return

    try:
        ydl = search(song)
        url = ydl['formats'][0]['url']
        title = ydl['title']
    except:
        await ctx.respond(f"I cannot find that song. This might be a temporary issue.", ephemeral = True)
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
    embed.set_thumbnail(url=GECKOICON)
    icon_url = discord.Embed.Empty
    if not ctx.author.avatar is None:
        icon_url = ctx.author.avatar.url
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url = icon_url)
    await ctx.respond(embed = embed)

@bot.slash_command(name="playlist", description="Music - See the queued play list.", guild_ids = WHITELIST)
async def PlayList(ctx): 
    await ctx.defer()    
    guildid = 0
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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
        msg += "\n\n*Use /dequeue to remove a song from the list.*"
    
    embed = discord.Embed(title=f"Playlist", description=msg, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=GECKOICON)
    if onloop(guildid):
        embed.set_footer(text=f"Loop playback enbled.")
    await ctx.respond(embed = embed)

@bot.slash_command(name="current", description="Music - Get current playing song.", guild_ids = WHITELIST)
async def CurrentSong(ctx):
    await ctx.defer()    
    if ctx.guild is None:
        await ctx.respond(f"Music commands can only be used in guilds!", ephemeral = True)
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
        await ctx.respond(f"No song is being played at the moment! Use /queue to start.", ephemeral = True)
        return
    userid = -t[0][0]
    title = b64d(t[0][1])

    username = "Unknown user"
    avatar = discord.Embed.Empty

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
            embed.set_thumbnail(url=GECKOICON)
            embed.set_footer(text="Radio: "+title.split("-")[1])
            await ctx.respond(embed = embed)
        
        else:
            embed = discord.Embed(title=f"Now playing", description=title.split("-")[1], color = GECKOCLR)
            embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
            embed.set_thumbnail(url=GECKOICON)
            embed.set_footer(text=f"Radio: "+title.split("-")[1], icon_url = avatar)
            await ctx.respond(embed = embed)
    else:
        embed = discord.Embed(title=f"Now playing", description=title, color = GECKOCLR)
        embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
        embed.set_thumbnail(url=GECKOICON)
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
        await ctx.respond(f"I'm not in a voice channel. Use `/join` command to join me in.", ephemeral = True)
        return
    
    premium = GetPremium(ctx.guild)
    if premium == 0:
        await ctx.respond(f"Radio function is premium only.", ephemeral = True)
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
            embed.set_thumbnail(url=GECKOICON)
            await ctx.respond(embed = embed, ephemeral = True)
            msg = ""
    embed = discord.Embed(title=f"Radio station list", description=msg, color = GECKOCLR)
    embed.set_author(name="Gecko Music", icon_url=MUSIC_ICON)
    embed.set_thumbnail(url=GECKOICON)
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
    await bot.wait_until_ready()
    await asyncio.sleep(5)

    emptynotice = []
    cursong = {} # cursong[url] = {song name, last update}
    guildsong = {} # guildsong[guildid] = {song name}
    autopause = []

    while not bot.is_closed():
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT guildid, channelid FROM vcbind")
        t = cur.fetchall()
        for tt in t:
            try:
                guildid = tt[0]
                channelid = tt[1]
                if not guildid in guildsong.keys():
                    guildsong[guildid] = ""

                guild = bot.get_guild(guildid)
                if guild is None: # bot is kicked
                    cur.execute(f"DELETE FROM vcbind WHERE guildid = {guildid}")
                    conn.commit()
                    continue
                voice_client = guild.voice_client
                            
                if CheckVCLock(guildid):
                    continue

                cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND userid < 0")
                t = cur.fetchall()
                if len(t) == 0:
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
                
                if voice_client.is_paused():
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
                            embed.set_thumbnail(url=GECKOICON)
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
                        
                if len(members) == 0:
                    if not guildid in autopause:
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
                            embed.set_thumbnail(url=GECKOICON)
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
                    avatar = discord.Embed.Empty
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
                        embed.set_thumbnail(url=GECKOICON)
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