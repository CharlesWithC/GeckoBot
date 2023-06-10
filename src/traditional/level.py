# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Levling 

import os, asyncio
import discord
from discord.ext import commands
import base64
from time import time
import requests
import io
import validators
import math

from bot import tbot
from settings import *
from functions import *
from db import newconn

from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps, ImageColor, ImageFilter

@tbot.command(name="rank", description="Get your rank card")
async def rank(ctx, member: discord.Member = None):
    if ctx.guild is None:
        await ctx.send("You can only run this command in guilds!")
        return
    await ctx.channel.trigger_typing()

    conn = newconn()
    cur = conn.cursor()

    user = ctx.author
    if member != None:
        user = member
    else:
        guild = ctx.guild
        members = guild.members
        for member in members:
            if member.id == ctx.author.id:
                user = member
                break

    xp = 0
    level = 0
    cur.execute(f"SELECT xp, level FROM level WHERE guildid = {ctx.guild.id} AND userid = {user.id}")
    t = cur.fetchall()
    if len(t) > 0:
        xp = t[0][0]
        level = t[0][1]
    nxtlvl = int(CalcXP(level + 1))
    if level == 100:
        nxtlvl = "∞"
    cur.execute(f"SELECT COUNT(*) FROM level WHERE guildid = {ctx.guild.id} AND xp > {xp}")
    rank = 1
    t = cur.fetchall()
    if len(t) > 0:
        rank = t[0][0] + 1
        
    cur.execute(f"SELECT bgcolor, fgcolor FROM rankcard WHERE guildid = {ctx.guild.id} AND userid = {user.id}")
    bgclr = (144, 255, 144) # light green
    bg = ""
    fgclr = (255, 255, 255)
    greyclr = (128, 128, 128) # grey
    t = cur.fetchall()
    if len(t) > 0:
        if len(t[0][0].split(" ")) == 3:
            bgclr = t[0][0].split(" ")
            bgclr = (int(bgclr[0]), int(bgclr[1]), int(bgclr[2]))
        if len(t[0][1].split(" ")) == 3:
            fgclr = t[0][1].split(" ")
            fgclr = (int(fgclr[0]), int(fgclr[1]), int(fgclr[2]))
        bg = b64d(t[0][0])
    else:
        cur.execute(f"SELECT bgcolor, fgcolor FROM rankcard WHERE guildid = 0 AND userid = {user.id}")
        t = cur.fetchall()
        if len(t) > 0:
            if len(t[0][0].split(" ")) == 3:
                bgclr = t[0][0].split(" ")
                bgclr = (int(bgclr[0]), int(bgclr[1]), int(bgclr[2]))
            if len(t[0][1].split(" ")) == 3:
                fgclr = t[0][1].split(" ")
                fgclr = (int(fgclr[0]), int(fgclr[1]), int(fgclr[2]))
            bg = b64d(t[0][0])
    
    # background
    premium = GetPremium(ctx.guild)
    if validators.url(bg) == True and (premium > 0 or ctx.author.id == BOTOWNER):
        try:
            bg = requests.get(bg)
            bg = Image.open(io.BytesIO(bg.content))
            (w,h) = bg.size
            if w/h > 934/282: # width crop
                bg = bg.resize((int(w/h*282), 282))
                (w,h) = bg.size
                bg = bg.crop((w/2-934/2, 0, w/2+934/2, 282))
            elif w/h < 934/282: # height crop
                bg = bg.resize((934, int(934/w*h)))
                (w,h) = bg.size
                bg = bg.crop((0, h/2-282/2, 934, h/2+282/2))
            bg = bg.resize((934, 282))
            bg = bg.convert("RGBA")
        except:
            bg = Image.new("RGBA", (934, 282), bgclr + (255,))
    else:
        bg = Image.new("RGBA", (934, 282), bgclr + (255,))
    txtclr = (255, 255, 255)

    # Gaussian Blur Background
    datas = bg.getdata()
    op = []
    odata = []
    bkdata = []
    for i in range(0,282):
        for j in range(0,934):
            odata.append(datas[i*934+j])
            bkdata.append(datas[i*934+j])
            if i>=42 and i<282-42 and j>=24 and j<934-24:
                op.append(datas[i*934+j])
    p = Image.new("RGBA", (934-24*2,282-42*2),(0,0,0,0))
    p.putdata(op)
    p=p.filter(ImageFilter.GaussianBlur(radius = 10))
    np = p.getdata()
    for i in range(0,282):
        for j in range(0,934):
            if i>=42 and i<282-42 and j>=24 and j<934-24:
                odata[i*934+j]=np[(i-42)*(934-24*2)+(j-24)]

    # Process blurred background card cornor
    def dist(a, b, c, d):
        return (c-a)*(c-a) + (d-b)*(d-b)
    radius = 15
    lpoints = [[42, 24], [42, 934-24-radius], [282-42-radius, 24], [282-42-radius,934-24-radius]]
    opoints = [[42+radius, 24+radius], [42+radius, 934-24-radius], [282-42-radius, 24+radius], [282-42-radius, 934-24-radius]]
    for k in range(4):
        li = lpoints[k][0]
        lj = lpoints[k][1]
        for i in range(li, li+radius):
            for j in range(lj, lj+radius):
                if dist(i, j, opoints[k][0], opoints[k][1]) > radius * radius:
                    odata[i*934+j] = bkdata[i*934+j]
    bg.putdata(odata)

    # basic card 
    card = Image.new("RGBA", (934, 282), (0,0,0,0))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((24, 42, card.size[0] - 24, card.size[1] - 42), fill=(0, 0, 0, 64), radius = radius)

    # avatar (transparent => grey) + draw
    avatar = user.avatar.url
    avatar = requests.get(avatar)
    avatar = Image.open(io.BytesIO(avatar.content))
    avatar = avatar.convert("RGBA")
    datas = avatar.getdata()
    newData = []
    for item in datas:
        newData.append((item[0], item[1], item[2], item[3] + 64))
    avatar.putdata(newData)
    avatar = avatar.resize((150, 150))
    card.paste(avatar, (int(card.size[1]/2-75) - 42 + 24, int(card.size[1]/2-75)))

    # draw level xp etc
    top = 42
    left = 150 + (int(card.size[1]/2-75) - 42 + 24) * 2
    right = card.size[0] - 24
    bottom = card.size[1] - 42
    margin = 20
    offset = 10
    # username#discriminator
    fontB4 = ImageFont.truetype("../res/ComicSansMSBold.ttf", 40)
    draw.text((left + margin, top + margin), f"{user.name}", fill=txtclr, font=fontB4)
    if user.discriminator != "0":
        draw.text((left + margin + fontB4.getsize(f"{user.name}")[0], top + margin), f"#", fill=greyclr, font=fontB4)
        draw.text((left + margin + fontB4.getsize(f"{user.name}#")[0], top + margin), f"{user.discriminator}", fill=txtclr, font=fontB4)
    # rank
    fontB5 = ImageFont.truetype("../res/ComicSansMSBold.ttf", 50)
    draw.text((right - margin - fontB5.getsize(f"#{rank}")[0], top + margin / 2), f"#{rank}", font=fontB5, fill=fgclr)
    font3 = ImageFont.truetype("../res/ComicSansMS3.ttf", 30)
    draw.text((right - margin - fontB5.getsize(f"#{rank}")[0] - font3.getsize("Rank")[0] - offset, top + margin + offset), f"Rank", font=font3, fill=txtclr)
    # user activity
    font3 = ImageFont.truetype("../res/ComicSansMS3.ttf", 30)
    actv = " Not doing anything at the moment -.-"
    if user.activity != None and user.activity.name != None:
        actv = " "+user.activity.name
        while font3.getsize(actv)[0] + left + margin > right - margin:
            actv = actv[:-5] + "..."
    draw.text((left + margin, top + margin + fontB4.getsize(user.name)[1] + offset), f"{actv}", font=font3, fill=txtclr)
    # level / xp
    font3B = ImageFont.truetype("../res/ComicSansMSBold.ttf", 30)
    draw.text((right - margin - font3B.getsize(f"Lv.{level} ({xp}/{nxtlvl})")[0], bottom - font3B.getsize("Lv.")[1] - margin), f"Lv.{level} ({xp}/{nxtlvl})", font=font3B, fill=fgclr)
    # gecko trademark

    txt = Image.new('RGBA', card.size, (255,255,255,0))  
    draw = ImageDraw.Draw(txt)
    font2 = ImageFont.truetype("../res/ComicSansMS3.ttf", 20)
    draw.text((card.size[0] - font2.getsize("Gecko Rank Card")[0] - margin/2, card.size[1] - font2.getsize("Gecko Rank Card")[1] - margin/2), "Gecko Rank Card", font=font2, fill=(0,0,0,60))
    
    card = Image.alpha_composite(card, txt)
    img = Image.alpha_composite(bg, card)
    
    with io.BytesIO() as image_binary:
        img.save(image_binary, 'PNG')
        image_binary.seek(0)
        await ctx.send(file=discord.File(fp=image_binary, filename='rankcard.png'))
        
@tbot.command(name="leaderboard", description="Get the leaderboard.")
async def leaderboard(ctx, page: int = 1):
    if ctx.guild is None:
        await ctx.send("You can only run this command in guilds!")
        return
    await ctx.channel.trigger_typing()
    conn = newconn()
    cur = conn.cursor()
    guild = ctx.guild
    guildid = guild.id
    cur.execute(f"SELECT * FROM level WHERE guildid = {guildid} ORDER BY level DESC, xp DESC, userid ASC")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send("No members found.")
        return
    pages = math.ceil(len(t)/10)
    if page > pages:
        await ctx.send(f"Page {page} not found.")
        return
    if page < 1:
        await ctx.send(f"Page {page} not found.")
        return
    start = (page-1)*10
    end = start + 10
    if end > len(t):
        end = len(t)
    t = t[start:end]
    msg = ""
    for i in range(len(t)):
        user = guild.get_member(t[i][1])
        if user is None:
            user = "Unknown"
        else:
            user = f"{user.name}"
        nxtlvl = int(CalcXP(t[i][2] + 1))
        if t[i][2] == 100:
            nxtlvl = "∞"
        msg += f"#**{(page-1) * 10 + i + 1}**. **{user}**\nLv.{t[i][2]} ({t[i][3]}/{nxtlvl})\n\n"
    embed = discord.Embed(title = f"Leaderboard - Page {page}/{pages}", description = msg, color = GECKOCLR)
    await ctx.send(embed = embed)