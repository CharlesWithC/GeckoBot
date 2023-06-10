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

from bot import bot
from settings import *
from functions import *
from db import newconn

from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps, ImageColor, ImageFilter

@bot.slash_command(name="rank", description="Get your / other member's rank card")
async def rank(ctx, member: discord.Option(discord.User, "@member", required = False)):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    await ctx.defer()

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
        await ctx.respond(file=discord.File(fp=image_binary, filename='rankcard.png'))

@bot.slash_command(name="card", description="Customize your rank card.")
async def card(ctx, background: discord.Option(str, "Backgroun image, supports RGB (solid color), or URL (web image)", required = False),
        foreground: discord.Option(str, "Rank and level text color, accepts RGB (solid color)", required = False),
        globallayout: discord.Option(str, "Whether this layout will apply to all guilds, overridden by guild specific layout", required = False, choices = ["Yes", "No"]),
        remove: discord.Option(str, "Remove guild specific layout, or general layout if global is yes", required = False, choices = ["Yes", "No"])):
    # NOTE For URL background, check premium when Gecko reaches 100 guilds
    await ctx.defer()
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return

    conn = newconn()
    cur = conn.cursor()
    guildid = ctx.guild.id
    if globallayout == "Yes":
        guildid = 0
    
    if remove == "Yes":
        cur.execute(f"SELECT * FROM rankcard WHERE guildid = {guildid} AND userid = {ctx.author.id}")
        t = cur.fetchall()
        if len(t) == 0:
            if guildid == 0:
                await ctx.respond("No general layout created.", ephemeral = True)
            else:
                await ctx.respond(f"No guild specific layout created.", ephemeral = True)
        else:
            cur.execute(f"DELETE FROM rankcard WHERE guildid = {guildid} AND userid = {ctx.author.id}")
            conn.commit()
            if guildid == 0:
                await ctx.respond("General layout removed.", ephemeral = True)
            else:
                await ctx.respond(f"Guild specific layout removed.", ephemeral = True)
        return
        
    if background is None and foreground is None:
        await ctx.respond("You must specify either background or foreground.")
        return
    
    cur.execute(f"SELECT * FROM rankcard WHERE guildid = {guildid} AND userid = {ctx.author.id}")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO rankcard VALUES ({guildid}, {ctx.author.id}, '', '')")
    
    notice = ""

    if background != None:
        if not validators.url(background):
            bg = background.split(" ")
            if len(bg) != 3:
                await ctx.respond("Invalid background RGB. RGB Format: `r g b`, separate with spaces, e.g. `255 255 255`", ephemeral = True)
                return
            try:
                bg = (int(bg[0]), int(bg[1]), int(bg[2]))
            except:
                await ctx.respond("Invalid background RGB. RGB Format: `r g b`, separate with spaces, e.g. `255 255 255`", ephemeral = True)
                return
        else:
            r = requests.get(background)
            if r.status_code != 200:
                await ctx.respond("Gecko cannot access the URL, make sure it's valid, and the website owner allows hosting IPs to access.", ephemeral = True)
                return
            if not r.headers['content-type'] in ['image/png', 'image/jpeg']:
                await ctx.respond("The URL does not point to a png / jpeg image.", ephemeral = True)
                return
            background = b64e(background)
            
            premium = GetPremium(ctx.guild)
            if premium == 0:
                await ctx.respond("Premium is required to use image backgrounds.", ephemeral = True)
                return

            notice = "\nYou have set a web image as background, make sure the URL is always valid or Gecko will not be able to display it."
        cur.execute(f"UPDATE rankcard SET bgcolor = '{background}' WHERE guildid = {guildid} AND userid = {ctx.author.id}")
    
    if foreground != None:
        fg = foreground.split(" ")
        if len(fg) != 3:
            await ctx.respond("Invalid foreground RGB. RGB Format: `r g b`, separate with spaces, e.g. `255 255 255`", ephemeral = True)
            return
        try:
            fg = (int(fg[0]), int(fg[1]), int(fg[2]))
        except:
            await ctx.respond("Invalid foreground RGB. RGB Format: `r g b`, separate with spaces, e.g. `255 255 255`", ephemeral = True)
            return
        cur.execute(f"UPDATE rankcard SET fgcolor = '{foreground}' WHERE guildid = {guildid} AND userid = {ctx.author.id}")
    
    conn.commit()
    await ctx.respond("Rank card updated." + notice)

# give xp
@bot.slash_command(name="givexp", description="Give XP to a member, or remove XP if negative.")
async def givexp(ctx, user: discord.Option(discord.User, "Member to give / remove XP", required = True), 
        xp: discord.Option(int, "Amount of XP to give / remove", required = True)):
        
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    if xp == 0:
        await ctx.respond("You can't give 0 XP.", ephemeral = True)
        return

    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    guild = ctx.guild
    guildid = guild.id
    userid = user.id
    members = guild.members
    found = False
    for member in members:
        if member.id == user.id:
            found = True
            break
    if not found:
        await ctx.respond("Member not found.", ephemeral = True)
        return
    if member.bot:
        await ctx.respond("Bots cannot receive XP.", ephemeral = True)
        return

    cur.execute(f"SELECT xp FROM level WHERE guildid = {guildid} AND userid = {userid}")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO level VALUES ({guildid}, {userid}, {CalcLevel(xp)}, {xp}, 0)")
    else:
        cur.execute(f"UPDATE level SET xp = xp + {xp}, level = {CalcLevel(t[0][0]+xp)} WHERE guildid = {guildid} AND userid = {userid}")
    conn.commit()

    if xp > 0:
        await ctx.respond(f"{user.mention} has been given {xp} XP.")
    else:
        await ctx.respond(f"{user.mention} has had {-xp} XP removed.")

@bot.slash_command(name="levelrole", description="Assign members role when they reach a certain level.")
async def levelrole(ctx, level: discord.Option(int, "Level to assign role to", required = True), 
        role: discord.Option(discord.Role, "Role to assign", required = True),
        remove: discord.Option(str, "Remove this level role.", required = False, choices = ["Yes", "No"])):
    
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    if level <= 0:
        await ctx.respond(f"You can't assign a role to level {level}.", ephemeral = True)
        return

    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()

    guild = ctx.guild
    guildid = guild.id
    cur.execute(f"SELECT * FROM levelrole WHERE guildid = {guildid} AND level = {level}")
    t = cur.fetchall()
    if remove != "Yes":
        if len(t) == 0:
            cur.execute(f"INSERT INTO levelrole VALUES ({guildid}, {level}, {role.id})")
        else:
            cur.execute(f"UPDATE levelrole SET roleid = {role.id} WHERE guildid = {guildid} AND level = {level}")
        conn.commit()
        await ctx.respond(f"When member reach level {level}, they will be assigned {role.name} role.")
    else:
        if len(t) == 0:
            await ctx.respond(f"There is no role assigned to level {level}.", ephemeral = True)
            return
        cur.execute(f"DELETE FROM levelrole WHERE guildid = {guildid} AND level = {level}")
        conn.commit()
        await ctx.respond(f"Level {level} role removed. Members will not be assigned the role. Existing roles are not affected.")

@bot.slash_command(name="leaderboard", description="Get the leaderboard.")
async def leaderboard(ctx, page: discord.Option(int, "Page number", required = False, default = 1)):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    guild = ctx.guild
    guildid = guild.id
    cur.execute(f"SELECT * FROM level WHERE guildid = {guildid} ORDER BY level DESC, xp DESC, userid ASC")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.respond("No members found.", ephemeral = True)
        return
    pages = math.ceil(len(t)/10)
    if page > pages:
        await ctx.respond(f"Page {page} not found.", ephemeral = True)
        return
    if page < 1:
        await ctx.respond(f"Page {page} not found.", ephemeral = True)
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
    await ctx.respond(embed = embed)

@bot.slash_command(name="xprate", description="Set XP rate, default 1")
async def xprate(ctx, rate: discord.Option(float, "XP rate", required = True)):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    if rate <= 0:
        await ctx.respond("XP rate must be greater than 0.", ephemeral = True)
        return

    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    guild = ctx.guild
    guildid = guild.id
    cur.execute(f"SELECT * FROM settings WHERE guildid = {guildid} AND skey='xprate'")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO settings VALUES ({guildid}, 'xprate', '{rate}')")
    else:
        cur.execute(f"UPDATE settings SET sval = '{rate}' WHERE guildid = {guildid} AND skey='xprate'")
    conn.commit()
    await ctx.respond(f"XP rate set to {rate}.")

@bot.slash_command(name="thumbxp", description="Enable / Disable the function to add XP when messages are reacted with thumb-up(s).")
async def thumbxp(ctx):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    guild = ctx.guild
    guildid = guild.id
    cur.execute(f"SELECT * FROM settings WHERE guildid = {guildid} AND skey='thumbxp'")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO settings VALUES ({guildid}, 'thumbxp', '1')")
        conn.commit()
        await ctx.respond("Thumb-up XP enabled.")
    else:
        cur.execute(f"DELETE FROM settings WHERE guildid = {guildid} AND skey='thumbxp'")
        conn.commit()
        await ctx.respond("Thumb-up XP disabled.")

@bot.slash_command(name="resetxp", description="Reset everyone's XP")
async def reset(ctx):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    guild = ctx.guild
    guildid = guild.id
    cur.execute(f"DELETE FROM level WHERE guildid = {guildid}")
    conn.commit()
    await ctx.respond("All XP reset.")