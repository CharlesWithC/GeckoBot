# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Global Trucking VTC Functions of Gecko Bot

import os, asyncio, io
import discord
from base64 import b64encode, b64decode
from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps

from bot import bot
from settings import *
from functions import *
from db import newconn

@bot.command(name="banner")
async def GenerateBanner(ctx, name):
    conn = newconn()
    cur = conn.cursor()
    if ctx.message.author.id == BOTID:
        return
    if ctx.guild.id != GT_GUILD:
        return
    async with ctx.typing():
        img = Image.open(GTLOGO)
        font = ImageFont.truetype(BANNER_FONT, 50)
        draw = ImageDraw.Draw(img)
        w, h = draw.textsize(name, font=font)
        h *= 0.21
        draw.text(((img.size[0]-w)/2, BANNER_Y+h/2), text=name, fill='white', font=font)
        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename='banner.png'))
            await log("Staff", f"{ctx.message.author.name} created a banner for {name}")