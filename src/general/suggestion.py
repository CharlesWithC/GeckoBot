# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Button Management

import os, json, asyncio
import discord
from discord.ext import commands
from discord.ui import Modal, InputText
from time import time
from random import randint
import io
import validators

from bot import bot
from settings import *
from functions import *
from db import newconn
from general.staff.form import FormModal

@bot.slash_command(name="suggest", description="Make a suggestion")
async def suggestion(ctx, editlink: discord.Option(str, "Specify a suggestion message link to edit it", required = False)):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {ctx.guild.id} AND category = 'suggestion'")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send("Staff haven't set up a suggestion channel.", ephemeral = True)
        return
    channel = bot.get_channel(t[0][0])
    if channel is None:
        await ctx.send("Staff have set up a suggestion channel but it's no longer valid.", ephemeral = True)
        return

    if editlink is not None:
        messageid = editlink.split("/")[-1]
        cur.execute(f"SELECT subject, content, userid FROM suggestion WHERE messageid = {messageid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send("Original suggestion message not found.", ephemeral = True)
            return
        subject = b64d(t[0][0])
        content = b64d(t[0][1])
        if t[0][2] != ctx.author.id:
            await ctx.respond("You can only edit your own suggestions.", ephemeral = True)
            return
        modal = FormModal(-int(messageid), ["[Short] Subject", "[Long] Content"], [subject, content], "Edit Suggestion")
        await ctx.send_modal(modal)
        return
    
    modal = FormModal(-1, ["[Short] Subject", "[Long] Content"], None, "Make Suggestion")
    await ctx.send_modal(modal)

@bot.slash_command(name="dlsuggestion", description="Download all suggestions")
async def dlsuggestion(ctx):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    conn = newconn()
    cur = conn.cursor()

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    cur.execute(f"SELECT messageid, userid, subject, content, upvote, downvote FROM suggestion WHERE guildid = {ctx.guild.id}")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send("No suggestions found.", ephemeral = True)
        return
    res = ""
    for tt in t:
        res += f"**Subject**: **{b64d(tt[2])}**  \n"
        res += f"**Content**: {b64d(tt[3])}  \n"
        user = bot.get_user(tt[1])
        if user is None:
            user = f"**Unknown User** (`{tt[1]}`)"
        else:
            user = f"**{user.name}** (`{user.id}`)"
        res += f"By {user} | Upvote: {tt[4]} | Downvote: {tt[5]} | Message ID: `{tt[0]}`  \n"
        res += "\n"
    
    f = io.BytesIO()
    f.write(res.encode())
    f.seek(0)
    await ctx.respond(file=discord.File(fp=f, filename='Suggestions.MD'))