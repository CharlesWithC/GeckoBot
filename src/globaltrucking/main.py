# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Global Trucking VTC exclusive

import os, asyncio, io
import discord
from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps, ImageColor
from random import randint

from bot import bot
from settings import *
from functions import *
from db import newconn

GTGUILD = 823779955305480212
GTLOGO = "./globaltrucking/logo.png"
BANNER_BG = "#520000"
BANNER_Y = 700 # pixel
BANNER_FONT = "./globaltrucking/WOODCUT.TTF"

@bot.slash_command(name="banner", description="Global Trucking - Generate a driver banner.", guild_ids = [GTGUILD])
async def GenerateBanner(ctx, name: discord.Option(str, "Driver's name", required = True)):
    await ctx.defer()    
    conn = newconn()
    cur = conn.cursor()

    if ctx.guild is None or ctx.guild.id != GTGUILD:
        await ctx.respond("/banner command is Global Trucking VTC exclusive.", ephemeral = True)
        return

    img = Image.open(GTLOGO)
    font = ImageFont.truetype(BANNER_FONT, 50)
    draw = ImageDraw.Draw(img)
    w, h = draw.textsize(name, font=font)
    h *= 0.21
    draw.rectangle(((img.size[0]-w)/2-10, BANNER_Y+h/2-5, (img.size[0]+w)/2+10, BANNER_Y+3*h/0.21/2), fill=ImageColor.getrgb("#530000"))
    draw.text(((img.size[0]-w)/2, BANNER_Y+h/2), text=name, fill='white', font=font)
    with io.BytesIO() as image_binary:
        img.save(image_binary, 'PNG')
        image_binary.seek(0)
        await ctx.respond(file=discord.File(fp=image_binary, filename='banner.png'))
        await log("Staff", f"{ctx.author} created a banner for {name}", ctx.guild.id)