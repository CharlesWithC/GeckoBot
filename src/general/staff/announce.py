# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff Functions of Gecko Bot

import os, asyncio
import discord
from base64 import b64encode, b64decode

from bot import bot
from settings import *
from functions import *
from db import newconn
        
@bot.command(name="announce")
async def Announce(ctx):
    conn = newconn()
    cur = conn.cursor()
    isAdmin = False
    if ctx.message.author.id in ADMIN_USER_ID:
        isAdmin = True
    for role in ctx.message.author.roles:
        if role.id in ADMIN_ROLE_ID:
            isAdmin = True
    guildid = ctx.guild.id
    
    if not isAdmin:
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !announce command")
        return

    async with ctx.typing():
        msg = ctx.message.content + " "
        if msg.find("<#") == -1 or msg.find("description:") == -1 or msg.find("title:") == -1:
            sample = "!announce {#channel} title: {title} description: {description} <imgurl: {imgurl}>"
            await ctx.reply(f"{ctx.message.author.name}, this is an invalid command!\nThis command works like:\n`{sample}`\nYou only need to change content in {{}}.\nYou can add line breaks or use \\n for line breaking.")
            return

        channelid = int(msg[msg.find("<#") + 2 : msg.find(">")])
        title = msg[msg.find("title:") + len("title:") : msg.find("description:")]
        description = msg[msg.find("description:") + len("description:") : msg.find("imgurl:")]
        imgurl = ""
        if msg.find("imgurl:") != -1:
            imgurl = msg[msg.find("imgurl:") + len("imgurl:"): ]
        embed = discord.Embed(title=title, description=description)
        embed.set_thumbnail(url=imgurl)

        try:
            channel = bot.get_channel(channelid)
            await channel.send(embed = embed)
            await log("Staff", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} made an announcement at {channel} ({channelid})")

        except Exception as e:
            await ctx.message.reply(f"{ctx.message.author.name}, it seems I cannot send message at <#{channelid}>. Make sure the channel exist and I have access to it!")
            await log("Staff", f"[guild {ctx.guild} ({ctx.guild.id})] !announce command executed by {ctx.message.author.name} failed due to {str(e)}")