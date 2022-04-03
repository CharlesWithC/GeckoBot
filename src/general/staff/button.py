# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff Functions of Gecko Bot

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText, Button, View
from discord.enums import ButtonStyle
from base64 import b64encode, b64decode
from time import time
from random import randint
import io

from bot import bot
from settings import *
from functions import *
from db import newconn

class ManageButton(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("button", "Manage button")

    @manage.command(name="clear", description="Staff - Clear all buttons in a message")
    async def clear(self, ctx, msglink: discord.Option(str, "Link to the message", required = True)):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if not msglink.endswith("/"):
            msglink = msglink + "/"
        msglink = msglink.split("/")
        msgid = int(msglink[-2])
        channelid = int(msglink[-3])
        guildid = int(msglink[-4])
        message = None
        try:
            channel = bot.get_channel(channelid)
            message = await channel.fetch_message(msgid)
            if message is None:
                await ctx.respond("I cannot fetch the message!", ephemeral = True)
                return
        except:
            await ctx.respond("I cannot fetch the message!", ephemeral = True)
            return
        if message.author.id != BOTID:
            await ctx.respond("The message isn't sent by Gecko", ephemeral = True)
            return

        await message.edit(content = message.content, embeds = message.embeds, view = None)
        await ctx.respond(f"Buttons in [message]({'/'.join(msglink)[-1]}) cleared.")

bot.add_cog(ManageButton(bot))