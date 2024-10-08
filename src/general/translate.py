# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Translate
# Translate command free for all guilds
# Auto translate for only premium guilds

import os, asyncio
import discord
from discord.ext import commands
import base64
from time import time
from datetime import datetime
import re

from bot import bot, tbot
from settings import *
from functions import *
from db import newconn
from rapidfuzz import process

async def LangAutocomplete(ctx: discord.AutocompleteContext):
    if ctx.value.replace(" ","") == "":
        return list(name2code.keys())[:25]
    ret = []
    if len(ctx.value) == 2 and ctx.value.lower() in code2name.keys():
        ret.append(code2name[ctx.value.lower()])
    d = process.extract(ctx.value.lower(), name2code.keys(), limit = 25 - len(ret))
    for dd in d:
        ret.append(dd[0])
    return ret

@bot.slash_command(name="translate", description="Translate text")
async def translate(ctx, text: discord.Option(str, "Text to translate"), 
        tolang: discord.Option(str, "Translate into what language, default English", default="English", required = False, autocomplete = LangAutocomplete),
        ephemeral: discord.Option(str, "Whether to make the result visible only to you", required = False, choices = ["Yes", "No"])):
    if ephemeral == "Yes":
        ephemeral = True
    else:
        ephemeral = False
    if not ephemeral:
        await ctx.defer()
    tolang = tolang.lower()
    if len(tolang) == 2 and tolang in code2name.keys():
        tolang = code2name[tolang]
    tolang = process.extract(tolang, name2code.keys(), limit = 1)[0][0]

    text = text.replace("@!","@")
    channels = re.findall(r"<#(\d+)>", text)
    for channel in channels:
        try:
            channel = bot.get_channel(int(channel))
            text = text.replace(f"<#{channel.id}>", f"#{channel.name}")
        except:
            import traceback
            traceback.print_exc()
            pass
    mentions = re.findall(r"<@(\d+)>", text)
    for mention in mentions:
        try:
            mention = bot.get_user(int(mention))
            text = text.replace(mention.mention, f"@{mention.name}")
        except:
            pass
    roles = re.findall(r"<@&(\d+)>", text)
    for role in roles:
        try:
            role = ctx.guild.get_role(int(role))
            text = text.replace(f"<@&{role.id}>", f"@{role.name}")
        except:
            pass
    text = re.sub("<:(\w+):(\d+)>","\\1",text) # emoji fix
    text = re.sub("<:(\w+):>","\\1",text)

    res = Translate(text, name2code[tolang])
    if res is None:
        res = (text, tolang, tolang)
    embed = discord.Embed(description = res[0], color = GECKOCLR)
    avatar = discord.Embed.Empty
    if ctx.author.avatar != None and ctx.author.avatar.url != None:
        avatar = ctx.author.avatar.url
    embed.timestamp = datetime.now()
    embed.set_author(name = f"{ctx.author.name}#{ctx.author.discriminator}", icon_url = avatar)
    embed.set_footer(text = f"{res[1]} -> {res[2]} • {TRANSLATE} ", icon_url = GECKOICON)

    await ctx.respond(embed = embed, ephemeral = ephemeral)

@tbot.command(aliases=['translate', 'tr'], description="Reply to a text to translate it, default to English")
async def ttranslate(ctx):
    if ctx.message.reference is None or ctx.message.reference.message_id is None:
        await ctx.send("Please reply to a message to translate it")
        return
    
    t = ctx.message.content.split(" ")
    tolang = "English (en)"
    if len(t) > 1:
        tolang = t[1].lower()
        if len(tolang) == 2 and tolang in code2name.keys():
            tolang = code2name[tolang]
        tolang = process.extract(tolang, name2code.keys(), limit = 1)[0][0]
        
    message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    if message is None:
        await ctx.send("Message not found")
        return
    
    text = message.content
    text = text.replace("@!","@")
    channels = re.findall(r"<#(\d+)>", text)
    for channel in channels:
        try:
            channel = bot.get_channel(int(channel))
            text = text.replace(f"<#{channel.id}>", f"#{channel.name}")
        except:
            import traceback
            traceback.print_exc()
            pass
    mentions = re.findall(r"<@(\d+)>", text)
    for mention in mentions:
        try:
            mention = bot.get_user(int(mention))
            text = text.replace(mention.mention, f"@{mention.name}")
        except:
            pass
    roles = re.findall(r"<@&(\d+)>", text)
    for role in roles:
        try:
            role = ctx.guild.get_role(int(role))
            text = text.replace(f"<@&{role.id}>", f"@{role.name}")
        except:
            pass
    text = re.sub("<:(\w+):(\d+)>","\\1",text) # emoji fix
    text = re.sub("<:(\w+):>","\\1",text)
    
    res = Translate(text, name2code[tolang])
    if res is None:
        res = (text, tolang, tolang)
    embed = discord.Embed(description = res[0], color = GECKOCLR)
    avatar = discord.Embed.Empty
    if message.author.avatar != None and message.author.avatar.url != None:
        avatar = message.author.avatar.url
    embed.timestamp = datetime.now()
    embed.set_author(name = f"{message.author.name}#{message.author.discriminator}", icon_url = avatar)
    embed.set_footer(text = f"{res[1]} -> {res[2]} • {TRANSLATE} ", icon_url = GECKOICON)
    
    await message.reply(embed = embed, mention_author = False)

@bot.slash_command(name="autotranslate", description="Auto translate messages in specific channels.")
async def autotranslate(ctx, channel: discord.Option(discord.TextChannel, "Channel to translate text, leave empty to translate all channels", required = False), 
    fromlang: discord.Option(str, "Use full language name (e.g. Spanish), separate with ',', default all non-english language", required = False),
    tolang: discord.Option(str, "Translate into what language, default English", default="English", required = False, autocomplete = LangAutocomplete),
    disable: discord.Option(str, "Disable auto translate", required = False, choices = ["Yes", "No"])):

    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    premium = GetPremium(ctx.guild)
    if premium == 0:
        await ctx.respond("Auto translate is premium only.", ephemeral = True)
        return

    if channel is None:
        channel = 0
    else:
        channel = channel.id

    conn = newconn()
    cur = conn.cursor()
    if disable:
        cur.execute(f"SELECT * FROM translate WHERE guildid = {ctx.guild.id} AND channelid = {channel}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Auto translate not enabled.")
            return
        cur.execute(f"DELETE FROM translate WHERE guildid = {ctx.guild.id} AND channelid = {channel}")
        conn.commit()
        await ctx.respond("Auto translate disabled.")
        return

    if fromlang is None:
        fromlang = "*"
    else:
        fromlang = fromlang.split(",")
        for i in range(len(fromlang)):
            fromlang[i] = name2code[process.extract(fromlang[i].lower(), name2code.keys(), limit = 1)[0][0]]
        fromlang = ",".join(fromlang)

    if tolang is None:
        tolang = "en"
    else:
        tolang = name2code[process.extract(tolang.lower(), name2code.keys(), limit = 1)[0][0]]

    if fromlang == tolang:
        await ctx.respond("You can't translate into the same language", ephemeral = True)
        return

    cur.execute(f"DELETE FROM translate WHERE guildid = {ctx.guild.id} AND channelid = {channel}")
    cur.execute(f"INSERT INTO translate VALUES ({ctx.guild.id}, {channel}, '{fromlang}', '{tolang}')")
    conn.commit()

    if channel != 0:
        await ctx.respond(f"Auto translate enabled for <#{channel}> ({fromlang} -> {tolang})")
    else:
        await ctx.respond(f"Auto translate enabled for all channels ({fromlang} -> {tolang})")