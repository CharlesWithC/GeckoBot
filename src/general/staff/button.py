# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Button Management

import os, json, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText, Button, View
from discord.enums import ButtonStyle
from time import time
from datetime import datetime
from random import randint
import io
import validators
import chat_exporter, minify_html 

from bot import bot
from settings import *
from functions import *
from db import newconn
from general.staff.form import FormModal
from general.games.four import ConnectFourJoinButton

class GeckoButton(Button):
    def __init__(self, label, url, style, disabled, custom_id):
        super().__init__(
            label=label,
            url=url,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
        )  

    async def callback(self, interaction: discord.Interaction):  
        user = interaction.user
        guild = interaction.guild
        userid = interaction.user.id
        guildid = interaction.guild_id
        conn = newconn()
        cur = conn.cursor()

        custom_id = self.custom_id
        if custom_id.startswith("GeckoTicket"):
            custom_id = custom_id.split("-")
            op = custom_id[1]
            ticketid = int(custom_id[2])
            if op == "closeconfirm":
                cur.execute(f"SELECT channelid, userid FROM ticketrecord WHERE ticketid = {ticketid} AND closedBy = 0")
                t = cur.fetchall()
                if len(t) == 0:
                    return
                channelid = t[0][0]
                creator = t[0][1]
                try:                    
                    embed = discord.Embed(title = "Ticket", description = f"Ticket closed by <@{userid}>\nYou can use `/ticket viewrecord {ticketid}` to view conversation.", color = GECKOCLR)
                    embed.timestamp = datetime.now()
                    embed.set_footer(text = f"Gecko Ticket • ID: {ticketid} ", icon_url = GECKOICON)
                    await interaction.response.edit_message(embed = embed, view = None)
                    channel = bot.get_channel(channelid)
                    await channel.set_permissions(guild.default_role, send_messages = False)
                    await channel.edit(name = f"closed-ticket-{ticketid}")
                    
                    data = await chat_exporter.export(channel)
                    data = data.replace(f"Channel: closed-ticket-{ticketid}", f"Ticket {ticketid}")
                    data = minify_html.minify(data, minify_js=True, minify_css=True, remove_processing_instructions=True, remove_bangs=True)
                    
                    closedBy = userid
                    closedTs = int(time())
                    cur.execute(f"UPDATE ticketrecord SET data = '{b64e(data)}', closedBy = {closedBy}, closedTs = {closedTs} WHERE ticketid = {ticketid}")
                    cur.execute(f"DELETE FROM buttonview WHERE buttonid = {-ticketid}")
                    conn.commit()

                    await channel.delete()

                    preserve = False
                    cur.execute(f"SELECT gticketid FROM ticketrecord WHERE userid = {creator} AND closedBy = 0")
                    p = cur.fetchall()
                    for pp in p:
                        gticketid = pp[0]
                        cur.execute(f"SELECT categoryid FROM ticket WHERE gticketid = {gticketid}")
                        c = cur.fetchall()
                        if len(c) > 0:
                            cid = c[0][0]
                            if cid == interaction.channel.category.id:
                                preserve = True
                    if not preserve:
                        await interaction.channel.category.set_permissions(user, view_channel = False)

                    try:
                        creator = bot.get_user(creator)
                        dmchannel = await creator.create_dm()
                        
                        embed = discord.Embed(title = "Ticket Record", description = "Conversation record in attached file", color = GECKOCLR)
                        embed.add_field(name = "Created By", value = f"<@{creator.id}> (`{creator.id}`)", inline = True)
                        embed.add_field(name = "Closed By", value = f"<@{closedBy}> (`{closedBy}`)", inline = True)
                        embed.add_field(name = "Closed At", value = f"<t:{closedTs}>", inline = True)
                        embed.timestamp = datetime.now()
                        embed.set_footer(text = f"Gecko Ticket • ID: {ticketid} ", icon_url = GECKOICON)

                        await dmchannel.send(embed = embed, file=discord.File(io.BytesIO(data.encode()), filename=f"Ticket-{ticketid}.html"))
                    except:
                        pass
                except:
                    import traceback
                    traceback.print_exc()
                    
                    embed = discord.Embed(title = "Ticket", description = f"Something went wrong.", color = GECKOCLR)
                    embed.timestamp = datetime.now()
                    embed.set_footer(text = f"Gecko Ticket • ID: {ticketid} ", icon_url = GECKOICON)
                    await interaction.response.edit_message(embed = embed, view = None)

            elif op == "close":
                embed = discord.Embed(title = "Ticket", description = f"Are you sure to close ticket?", color = GECKOCLR)
                embed.timestamp = datetime.now()
                embed.set_footer(text = f"Gecko Ticket • ID: {ticketid} ", icon_url = GECKOICON)
                view = View(timeout = 300)
                uniq = f"{randint(1,100000)}{int(time()*100000)}"
                custom_id = "GeckoTicket-closeconfirm-"+str(ticketid)+"-"+uniq
                button = GeckoButton("Close", None, BTNSTYLE["red"], False, custom_id)
                view.add_item(button)
                custom_id = "GeckoTicket-closecancel-"+str(ticketid)+"-"+uniq
                button = GeckoButton("Cancel", None, BTNSTYLE["grey"], False, custom_id)
                view.add_item(button)
                await interaction.response.send_message(embed = embed, view = view)

            elif op == "closecancel":
                embed = discord.Embed(title = "Ticket", description = f"Are you sure to close ticket?\nCancelled.", color = GECKOCLR)
                embed.timestamp = datetime.now()
                embed.set_footer(text = f"Gecko Ticket • ID: {ticketid} ", icon_url = GECKOICON)
                view = View(timeout = 300)
                uniq = f"{randint(1,100000)}{int(time()*100000)}"
                custom_id = "GeckoTicket-closeconfirm-"+str(ticketid)+"-"+uniq
                button = GeckoButton("Close", None, BTNSTYLE["red"], True, custom_id)
                view.add_item(button)
                custom_id = "GeckoTicket-closecancel-"+str(ticketid)+"-"+uniq
                button = GeckoButton("Cancel", None, BTNSTYLE["grey"], True, custom_id)
                view.add_item(button)
                await interaction.response.edit_message(embed = embed, view = view)

            return

        if not custom_id.startswith("GeckoButton"):
            return

        buttonid = int(custom_id.split("-")[1])

        cur.execute(f"SELECT data FROM button WHERE buttonid = {buttonid}")
        t = cur.fetchall()
        if len(t) == 0:
            raise Exception("Button not found!")

        data = json.loads(b64d(t[0][0]))
        disabled = data["disabled"]
        if disabled:
            await interaction.response.send_message(f"Button disabled.", ephemeral = True)
            return
        
        ephemeral = data["ephemeral"]
        content = data["content"]
        embedid = data["embedid"]
        formid = data["formid"]
        # below are update after release, old buttons might not contain this key
        # hence need to do key check to prevent errors
        gticketid = None
        if "gticketid" in data.keys():
            gticketid = data["gticketid"]
        roles = None
        if "roles" in data.keys():
            roles = data["roles"] 
        
        response = []
        
        if content != None:
            response.append({"content": content, "ephemeral": ephemeral})
        
        if embedid != None:
            cur.execute(f"SELECT data FROM embed WHERE guildid = {guildid} AND embedid = {embedid}")
            t = cur.fetchall()
            if len(t) != 0:
                d = t[0][0].split("|")
                title = b64d(d[0])
                url = b64d(d[1])
                description = b64d(d[2])
                footer = b64d(d[3])
                thumbnail_url = [b64d(d[4]), b64d(d[5])]
                clr = d[6].split(" ")

                footer_icon_url = ""

                if footer.startswith("["):
                    footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
                    footer = footer[footer.find("]") + 1:]
                
                embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
                embed.set_footer(text=footer, icon_url=footer_icon_url)
                embed.set_thumbnail(url=thumbnail_url[0])
                embed.set_image(url=thumbnail_url[1])

                response.append({"embed": embed, "ephemeral": ephemeral})
        
        if formid != None:
            cur.execute(f"SELECT data FROM form WHERE guildid = {guildid} AND formid = {formid}")
            t = cur.fetchall()
            if len(t) == 0:
                response.append({"content": "The form does not exist any longer.", "ephemeral": True})
            else:
                data = t[0][0]
                if data.startswith("stopped-"):
                    response.append({"content": "The form is not accpeting new entries at this moment.", "ephemeral": True})
                else:
                    if data.split("|")[-1] == "1":
                        cur.execute(f"SELECT userid FROM formentry WHERE userid = {userid} AND formid = {formid}")
                        p = cur.fetchall()
                        if len(p) > 0:
                            response.append({"content": "You can not submit more than once.", "ephemeral": True})
                        else:
                            p = data.split("|")[:-1]
                            d = []
                            for pp in p:
                                d.append(b64d(pp))
                            response.append({"modal": FormModal(formid, d, None, "Submit Form"), "ephemeral": ephemeral})
                    else:
                        p = data.split("|")[:-1]
                        d = []
                        for pp in p:
                            d.append(b64d(pp))
                        response.append({"modal": FormModal(formid, d, None, "Submit Form"), "ephemeral": ephemeral})
        
        if gticketid != None:
            cur.execute(f"SELECT categoryid, channelformat, msg, moderator FROM ticket WHERE guildid = {guildid} AND gticketid = {gticketid}")
            t = cur.fetchall()
            if len(t) == 0:
                response.append({"content": "The ticket does not exist any longer.", "ephemeral": True})
            else:
                cur.execute(f"SELECT COUNT(*) FROM ticketrecord")
                ttt = cur.fetchall()
                ticketid = 0
                if len(ttt) > 0:
                    ticketid = ttt[0][0]

                categoryid = t[0][0]
                name = b64d(t[0][1])
                name = name.replace("{ticketid}", str(ticketid))
                name = name.replace("{userid}", str(userid))
                name = name.replace("{username}", user.name)

                msg = b64d(t[0][2])

                try:
                    category = bot.get_channel(categoryid)
                    await category.set_permissions(user, view_channel = True, read_message_history = True, send_messages = True)
                    channel = await category.create_text_channel(name, reason = "Gecko Ticket")
                    me = bot.get_user(BOTID)
                    await channel.set_permissions(me, view_channel = True, read_message_history = True, send_messages = True)

                    moderators = t[0][3]
                    for mod in moderators.split(","):
                        if mod.startswith("@&"):
                            roleid = int(mod[2:])
                            try:
                                role = guild.get_role(roleid)
                                if role != None:
                                    await channel.set_permissions(role, view_channel = True, read_message_history = True, send_messages = True)
                            except:
                                import traceback
                                traceback.print_exc()
                        else:
                            modid = int(mod[1:])
                            try:
                                mod = guild.get_member(modid)
                                if mod != None:
                                    await channel.set_permissions(mod, view_channel = True, read_message_history = True, send_messages = True)
                            except:
                                import traceback
                                traceback.print_exc()
                    await channel.set_permissions(guild.default_role, view_channel = False)

                    embed = discord.Embed(title = "Ticket", description = msg, color = GECKOCLR)
                    embed.timestamp = datetime.now()
                    embed.set_footer(text = f"Gecko Ticket • ID: {ticketid} ", icon_url = GECKOICON)
                    view = View(timeout = None)
                    uniq = f"{randint(1,100000)}{int(time()*100000)}"
                    custom_id = "GeckoTicket-close-"+str(ticketid)+"-"+uniq
                    button = GeckoButton("Close Ticket", None, BTNSTYLE["red"], False, custom_id)
                    view.add_item(button)
                    cur.execute(f"INSERT INTO buttonview VALUES ({-ticketid}, '{custom_id}')")
                    await channel.send(embed = embed, view = view)

                    cur.execute(f"INSERT INTO ticketrecord VALUES ({ticketid}, {gticketid}, {userid}, {guildid}, {channel.id}, '', 0, 0)")
                    conn.commit()

                    response.append({"content": f"Ticket created <#{channel.id}>. ID: {ticketid}", "ephemeral": True})
                
                except:
                    import traceback
                    traceback.print_exc()
                    response.append({"content": "An error occurred while creating the ticket.", "ephemeral": True})

        if roles != None:
            ret = ""
            r = roles.replace(" ","").split(",")
            for rr in r:
                rmv = False
                if rr.find("-") != -1:
                    rmv = True
                    rr = rr.replace("-","")
                try:
                    rr = int(rr[3:-1])
                    role = guild.get_role(rr)
                    if role is None:
                        continue
                    if not rmv:
                        ret += f"{role.mention} has been added.\n"
                        await user.add_roles(role, reason = "Gecko Button Role")
                    else:
                        ret += f"{role.mention} has been removed.\n"
                        await user.remove_roles(role, reason = "Gecko Button Role")
                except:
                    import traceback
                    traceback.print_exc()
                    pass
            response.append({"content": ret, "ephemeral": True})

        if len(response) == 0:
            await interaction.response.send_message("I think it's a button for **decoration** use only, as the creator didn't tell me what to do when you click it.", ephemeral = True)

        elif len(response) == 1:
            res = response[0]
            if "content" in res.keys():
                await interaction.response.send_message(content = res["content"], ephemeral = res["ephemeral"])
            elif "embed" in res.keys():
                await interaction.response.send_message(embed = res["embed"], ephemeral = res["ephemeral"])
            elif "modal" in res.keys():
                await interaction.response.send_modal(res["modal"])
        
        elif len(response) > 1:
            if response[0] == "content" and response[1] == "embed":
                await interaction.response.send_message(content = res["content"], embed = res["embed"], ephemeral = res["ephemeral"])

class ManageButton(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("button", "Manage button")

    @commands.Cog.listener()
    async def on_ready(self):
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT customid FROM buttonview")
        d = cur.fetchall()
        for dd in d:
            view = View(timeout=None)
            if dd[0].startswith("GeckoButton"):
                view.add_item(GeckoButton("", None, BTNSTYLE["blurple"], False, dd[0]))
            elif dd[0].startswith("GeckoTicket"):
                view.add_item(GeckoButton("", None, BTNSTYLE["blurple"], False, dd[0]))
            elif dd[0].startswith("GeckoConnectFourGame"):
                view.add_item(ConnectFourJoinButton("", dd[0]))
            self.bot.add_view(view)

    @manage.command(name="create", description="Staff - Create a button")
    async def create(self, ctx, label: discord.Option(str, "Button label", required = True),
            color: discord.Option(str,"Button color, default blurple", required = False, choices = ["blurple", "grey", "green", "red"]),
            emoji: discord.Option(str, "Button emoji", required = False),
            disabled: discord.Option(str, "Whether button can be clicked or not, default Yes", required = False, choices = ["Yes", "No"]),
            ephemeral: discord.Option(str,"Whether the action on click is only visible to the clicker, default No", required = False, choices = ["Yes", "No"]),
            url: discord.Option(str, "URL to open on click", required = False),
            content: discord.Option(str, "Content of message to send on click", required = False),
            embedid: discord.Option(int, "ID of embed to send on click", required = False),
            formid: discord.Option(int, "ID of form to display on click", required = False),
            gticketid: discord.Option(str, "ID of guild ticket category", required = False),
            roles: discord.Option(str, "Roles to assign / unassign on click, separate with ',', start with '-' to unassign", required = False)):
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guildid = ctx.guild.id

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT COUNT(*) FROM button WHERE guildid = {guildid} AND buttonid > 0")
        c = cur.fetchall()
        if len(c) > 0:
            premium = GetPremium(ctx.guild)
            cnt = c[0][0]
            if cnt >= 100 and premium >= 2:
                await ctx.respond("Max buttons: 100.\n\nIf you are looking for more buttons, contact Gecko Moderator in support server", ephemeral = True)
                return
            elif cnt >= 30 and premium == 1:
                await ctx.respond("Premium Tier 1: 30 buttons.\nPremium Tier 2: 100 buttons.\n\nFind out more by using `/premium`", ephemeral = True)
                return
            elif cnt >= 10 and premium == 0:
                await ctx.respond("Free guilds: 10 buttons.\nPremium Tier 1: 30 buttons.\nPremium Tier 2: 100 buttons.\n\nFind out more by using `/premium`", ephemeral = True)
                return
        
        if content != None:
            content = content.replace("\\n", "\n")
            
        data = {}

        if label != None and len(label) > 75:
            await ctx.respond(f"The maximum length of label is 75, current {len(label)}", ephemeral = True)
            return
        data["label"] = label
        
        if not color in ["blurple", "grey", "green", "red"]:
            color = "blurple"
        data["color"] = color

        if emoji != None:
            botuser = ctx.guild.get_member(BOTID)
            if not botuser.guild_permissions.add_reactions:
                await ctx.respond("I don't have permission to add reactions, which will be used to test whether an emoji is valid.", ephemeral = True)
                return
            channel = ctx.channel
            message = await channel.send("Emoji test")
            try:
                await message.add_reaction(emoji)
                await message.delete()
            except:
                await ctx.respond(f"Emoji {emoji} is invalid.", ephemeral = True)
                await message.delete()
                return
        data["emoji"] = emoji
        
        if disabled == "Yes":
            disabled = True
        else:
            disabled = False
        data["disabled"] = disabled
        
        if ephemeral == "No":
            ephemeral = False
        else:
            ephemeral = True
        data["ephemeral"] = ephemeral
        
        if url != None and validators.url(url) != True:
            await ctx.respond(f"Invalid URL {url}!", ephemeral = True)
            return
        data["url"] = url

        if content != None and len(content) > 2000:
            await ctx.respond(f"The maximum length of content is 2000, current {len(content)}", ephemeral = True)
            return
        data["content"] = content
        
        if embedid != None:
            try:
                embedid = int(embedid)
            except:
                await ctx.respond("Invalid embed ID!", ephemeral = True)
                return
            cur.execute(f"SELECT data FROM embed WHERE guildid = {ctx.guild.id} AND embedid = {embedid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("Embed not found.", ephemeral = True)
                return
        data["embedid"] = embedid
        
        if formid != None:
            if embedid != None or content != None:
                await ctx.respond("Forms cannot be bound to buttons when content / embeds are already linked.\nBut content and embeds can exist at the same time.", ephemeral = True)
                return

            try:
                formid = int(formid)
            except:
                await ctx.respond("Invalid form ID!", ephemeral = True)
                return
            cur.execute(f"SELECT data FROM form WHERE guildid = {ctx.guild.id} AND formid = {formid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("Form not found.", ephemeral = True)
                return
        data["formid"] = formid

        if gticketid != None:
            try:
                if gticketid.startswith("g"):
                    gticketid = int(gticketid[1:])
            except:
                await ctx.respond("Invalid guild ticket category ID!", ephemeral = True)
                return
            cur.execute(f"SELECT gticketid FROM ticket WHERE guildid = {ctx.guild.id} AND gticketid = {gticketid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("Guild ticket category not found.", ephemeral = True)
                return
        data["gticketid"] = gticketid

        if roles != None:
            r = roles.replace(" ","").replace("-","").split(",")
            for rr in r:
                if not rr.startswith("<@&") or not rr.endswith(">"):
                    await ctx.respond(f"Invalid role {rr}!", ephemeral = True)
                    return

        data["roles"] = roles

        data = b64e(json.dumps(data))
        cur.execute(f"SELECT COUNT(*) FROM button")
        t = cur.fetchall()
        buttonid = 0
        if len(t) > 0:
            buttonid = t[0][0]
        cur.execute(f"INSERT INTO button VALUES ({buttonid}, {guildid}, '{data}')")
        conn.commit()

        await ctx.respond(f"Button created. Button ID: {buttonid}.\nUse `/button send` to post it.")
        await log("Button", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) created button #{buttonid}", guildid)

    @manage.command(name="edit", description="Staff - Edit a button. Use 'None' to clear a parameter.")
    async def edit(self, ctx, buttonid: discord.Option(int, "Button ID, provided when button was created", required = True),
            label: discord.Option(str, "Button label", required = False),
            color: discord.Option(str,"Button color, default blurple", required = False, choices = ["blurple", "grey", "green", "red"]),
            emoji: discord.Option(str, "Button emoji", required = False),
            disabled: discord.Option(str, "Whether button can be clicked or not, default Yes", required = False, choices = ["Yes", "No"]),
            ephemeral: discord.Option(str,"Whether the action on click is only visible to the clicker, default No", required = False, choices = ["Yes", "No"]),
            url: discord.Option(str, "URL to open on click", required = False),
            content: discord.Option(str, "Content of message to send on click", required = False),
            embedid: discord.Option(int, "ID of embed to send on click", required = False),
            formid: discord.Option(int, "ID of form to display on click", required = False),
            gticketid: discord.Option(str, "ID of guild ticket category", required = False),
            roles: discord.Option(str, "Roles to assign / unassign on click, separate with space, start with '-' to unassign", required = False)):
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guildid = ctx.guild.id

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        
        if content != None:
            content = content.replace("\\n", "\n")

        try:
            buttonid = int(buttonid)
        except:
            await ctx.respond("Invalid button ID!", ephemeral = True)
            return
        cur.execute(f"SELECT data FROM button WHERE guildid = {ctx.guild.id} AND buttonid = {buttonid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Button not found.", ephemeral = True)
            return
        data = json.loads(b64d(t[0][0]))        

        if label != None:
            if len(label) > 75:
                await ctx.respond(f"The maximum length of label is 75, current {len(label)}", ephemeral = True)
                return
            data["label"] = label
        
        if color in ["blurple", "grey", "green", "red"]:
            data["color"] = color
        if color == "None":
            data["color"] = "blurple"

        if emoji == "None":
            data["emoji"] = None
        elif emoji != None:
            botuser = ctx.guild.get_member(BOTID)
            if not botuser.guild_permissions.add_reactions:
                await ctx.respond("I don't have permission to add reactions, which will be used to test whether an emoji is valid.", ephemeral = True)
                return
            channel = ctx.channel
            message = await channel.send("Emoji test")
            try:
                await message.add_reaction(emoji)
                await message.delete()
            except:
                await ctx.respond(f"Emoji {emoji} is invalid.", ephemeral = True)
                await message.delete()
                return
            data["emoji"] = emoji
        
        if disabled != None:
            if disabled == "Yes":
                disabled = True
            else:
                disabled = False
            data["disabled"] = disabled
        
        if ephemeral != None:
            if ephemeral == "No":
                ephemeral = False
            else:
                ephemeral = True
            data["ephemeral"] = ephemeral
        
        if url == "None":
            data["url"] = None
        elif url != None:
            if validators.url(url) != True:
                await ctx.respond(f"Invalid URL {url}!", ephemeral = True)
                return
            data["url"] = url

        if content != None:
            if len(content) > 2000:
                await ctx.respond(f"The maximum length of content is 2000, current {len(content)}", ephemeral = True)
                return
            data["content"] = content
        if content == "None":
            data["content"] = None
        
        if embedid == "None":
            data["embedid"] = None
        elif embedid != None:
            try:
                embedid = int(embedid)
            except:
                await ctx.respond("Invalid embed ID!", ephemeral = True)
                return
            cur.execute(f"SELECT data FROM embed WHERE guildid = {ctx.guild.id} AND embedid = {embedid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("Embed not found.", ephemeral = True)
                return
            data["embedid"] = embedid
        
        if formid == "None":
            data["formid"] = None
        elif formid != None:
            if embedid != None or content != None:
                await ctx.respond("Forms cannot be bound to buttons when content / embeds are already linked.\nBut content and embeds can exist at the same time.", ephemeral = True)
                return

            try:
                formid = int(formid)
            except:
                await ctx.respond("Invalid form ID!", ephemeral = True)
                return
            cur.execute(f"SELECT data FROM form WHERE guildid = {ctx.guild.id} AND formid = {formid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("Form not found.", ephemeral = True)
                return
            data["formid"] = formid

        if gticketid == "None":
            data["gticketid"] = None
        elif gticketid != None:
            try:
                if gticketid.startswith("g"):
                    gticketid = int(gticketid[1:])
            except:
                await ctx.respond("Invalid guild ticket category ID!", ephemeral = True)
                return
            cur.execute(f"SELECT gticketid FROM ticket WHERE guildid = {ctx.guild.id} AND gticketid = {gticketid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("Guild ticket category not found.", ephemeral = True)
                return
            data["gticketid"] = gticketid

        if roles == "None":
            data["roles"] = None
        elif roles != None:
            r = roles.replace(" ","").replace("-","").split(",")
            for rr in r:
                if not rr.startswith("<@&") or not rr.endswith(">"):
                    await ctx.respond(f"Invalid role {rr}!", ephemeral = True)
                    return
            data["roles"] = roles

        data = b64e(json.dumps(data))
        cur.execute(f"UPDATE button SET data = '{data}' WHERE guildid = {guildid} AND buttonid = {buttonid}")
        conn.commit()

        await ctx.respond(f"Button #{buttonid} edited.")
        await log("Button", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) edited button #{buttonid}", guildid)

    @manage.command(name="delete", description="Staff - Delete a button from database, previously posted button will become invalid.")
    async def delete(self, ctx, buttonid: discord.Option(int, "Button ID, provided when button was created", required = True)):
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guildid = ctx.guild.id

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        try:
            buttonid = int(buttonid)
        except:
            await ctx.respond("Invalid button ID!", ephemeral = True)
            return
            
        conn = newconn()
        cur = conn.cursor()
        
        cur.execute(f"SELECT data FROM button WHERE guildid = {ctx.guild.id} AND buttonid = {buttonid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Button not found.", ephemeral = True)
            return
        
        cur.execute(f"UPDATE button SET data = '', guildid = -1 WHERE guildid = {ctx.guild.id} AND buttonid = {buttonid}")
        conn.commit()

        await ctx.respond(f"Button #{buttonid} deleted.")
        await log("Button", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) deleted button #{buttonid}", guildid)
    
    @manage.command(name="get", description="Staff - Get ID of buttons in a message.")
    async def get(self, ctx, msglink: discord.Option(str, "Link to the message", required = True)):
        await ctx.defer()    
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
        if guildid != ctx.guild.id:
            await ctx.respond(f"The message isn't sent in the guild you are sending this command.", ephemeral = True)
            return
        view = None
        try:
            channel = ctx.guild.get_channel(channelid)
            if channel is None:
                await ctx.respond(f"I cannot fetch the message as I cannot access the channel.", ephemeral = True)
                return
            message = await channel.fetch_message(msgid)
            if message is None:
                await ctx.respond(f"I cannot fetch the message.", ephemeral = True)
                return
            if message.author.id != BOTID:
                await ctx.respond(f"The message isn't sent by Gecko.", ephemeral = True)
                return
            view = View.from_message(message, timeout = None)
            
            if view is None or len(view.children) == 0:
                await ctx.respond(f"No button is included in the message.", ephemeral = True)
                return
        except:
            await ctx.respond(f"Something wrong occurred.", ephemeral = True)
            return
            
        msg = ""
        conn = newconn()
        cur = conn.cursor()
        for d in view.children:
            if not d.custom_id.startswith("GeckoButton"):
                continue
            buttonid = -1
            try:
                buttonid = int(d.custom_id.split("-")[1])
            except:
                continue
            cur.execute(f"SELECT data FROM button WHERE buttonid = {buttonid} AND guildid = {ctx.guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                continue
            data = json.loads(b64d(t[0][0]))
            label = data["label"]
            if label != d.label:
                msg += f"`{label}` (`{d.label}` in message) -> #{buttonid}\n"
            else:
                msg += f"`{label}` -> #{buttonid}\n"
        if msg == "":
            await ctx.respond(f"No button is included in the message.", ephemeral = True)
            return

        embed=discord.Embed(title="Button -> Button ID", description=msg, color=GECKOCLR)
        await ctx.respond(embed = embed)

    @manage.command(name="list", description="Staff - List all buttons in this guild.")
    async def show(self, ctx):
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        
        cur.execute(f"SELECT buttonid, data FROM button WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("There's no button created in this guild. Use `/button create` to create one.")
            return
        
        msg = f"Below are all buttons created using Gecko in {ctx.guild}.\nOnly button id and label is shown.\n\n"
        for tt in t:
            data = json.loads(b64d(tt[1]))
            label = data["label"]
            msg += f"Button **#{tt[0]}**: {label}\n"
        
        if len(msg) > 2000:
            f = io.BytesIO()
            f.write(msg.encode())
            f.seek(0)
            await ctx.respond(file=discord.File(fp=f, filename='Buttons.MD'))
        else:
            embed=discord.Embed(title=f"Buttons in {ctx.guild}", description=msg, color=GECKOCLR)
            await ctx.respond(embed = embed)     

    @manage.command(name="clear", description="Staff - Clear all buttons in a message")
    async def clear(self, ctx, msglink: discord.Option(str, "Link to the message", required = True)):
        await ctx.defer()    
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

    @manage.command(name="send", description="Staff - Send buttons.")
    async def send(self, ctx, channel: discord.Option(discord.TextChannel, "Channel to send the button", required = True),
        buttonid: discord.Option(str, "Button ID, separate with space, e.g. '1 2 3'", required = True)):

        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        
        channelid = channel.id

        conn = newconn()
        cur = conn.cursor()
        
        buttonid = buttonid.split(" ")
        
        view = View(timeout = None)

        if len(buttonid) > 25:
            await ctx.respond(f"One message can contain at most 25 buttons.", ephemeral = True)
            return

        for i in range(len(buttonid)):
            try:
                buttonid[i] = int(buttonid[i])
                btnid = buttonid[i]

                cur.execute(f"SELECT data FROM button WHERE buttonid = {btnid} AND guildid = {ctx.guild.id}")
                t = cur.fetchall()
                if len(t) == 0:
                    await ctx.respond(f"Button with ID {btnid} not found.", ephemeral = True)
                    return
                data = json.loads(b64d(t[0][0]))
                color = data["color"]
                label = data["label"]
                url = data["url"]
                style = BTNSTYLE[color]
                uniq = f"{randint(1,100000)}{int(time()*100000)}"
                custom_id = "GeckoButton-"+str(btnid)+"-"+uniq
                if url != None:
                    custom_id = None
                button = GeckoButton(label, url, style, data["disabled"], custom_id)
                view.add_item(button)
                cur.execute(f"INSERT INTO buttonview VALUES ({btnid}, '{custom_id}')")
                conn.commit()
            except:
                await ctx.respond(f"Button ID {buttonid[i]} is invalid.", ephemeral = True)
                return
                
        try:
            if channel is None:
                raise Exception("No access to channel.")
            
            message = await channel.send(view = view)

            await ctx.respond(f"Buttons sent at <#{channelid}>.")
            await log(f"Button", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) sent buttons {buttonid} at {channel} ({channelid})", ctx.guild.id)

        except:
            await ctx.respond(f"I cannot send message at <#{channelid}>.", ephemeral = True)

    @manage.command(name="attach", description = "Staff - Attach buttons to an existing message sent by Gecko (Text / Embed)")
    async def attach(self, ctx, msglink: discord.Option(str, "Link to the message", required = True),
            buttonid: discord.Option(str, "Button ID, separate with space, e.g. '1 2 3'", required = True)):

        await ctx.defer()    
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

        conn = newconn()
        cur = conn.cursor()
        view = View.from_message(message, timeout = None)
        
        buttonid = buttonid.split(" ")
        if len(view.children) + len(buttonid) > 25:
            await ctx.respond(f"One message can contain at most 25 buttons (Existing buttons are counted, use `/button clear` to delete existing buttons)", ephemeral = True)
            return

        for i in range(len(buttonid)):
            try:
                buttonid[i] = int(buttonid[i])
                btnid = buttonid[i]

                cur.execute(f"SELECT data FROM button WHERE buttonid = {btnid} AND guildid = {ctx.guild.id}")
                t = cur.fetchall()
                if len(t) == 0:
                    await ctx.respond(f"Button with ID {btnid} not found.", ephemeral = True)
                    return
                data = json.loads(b64d(t[0][0]))
                color = data["color"]
                label = data["label"]
                url = data["url"]
                style = BTNSTYLE[color]
                uniq = f"{randint(1,100000)}{int(time()*100000)}"
                custom_id = "GeckoButton-"+str(btnid)+"-"+uniq
                if url != None:
                    custom_id = None
                button = GeckoButton(label, url, style, data["disabled"], custom_id)
                view.add_item(button)
                cur.execute(f"INSERT INTO buttonview VALUES ({btnid}, '{custom_id}')")
                conn.commit()
            except:
                import traceback
                traceback.print_exc()
                await ctx.respond(f"Button ID {buttonid[i]} is invalid.", ephemeral = True)
                return

        try:
            await message.edit(content = message.content, embeds = message.embeds, view = view)
            await ctx.respond(f"Buttons attached to [message]({'/'.join(msglink)[-1]}).")
            await log(f"Button", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) attached buttons {buttonid} to message {msgid}", ctx.guild.id)
        except:
            await ctx.respond(f"I cannot edit the [message]({'/'.join(msglink)[-1]}).", ephemeral = True)

    @manage.command(name="update", description = "Staff - Update the labels of buttons to the latest ones.")
    async def update(self, ctx, msglink: discord.Option(str, "Link to the message", required = True)):
        
        await ctx.defer()    
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
        
        conn = newconn()
        cur = conn.cursor()
        
        view = View.from_message(message, timeout = None)
        newview = View(timeout = None)
        for child in view.children:
            if not child.custom_id.startswith("GeckoButton"):
                newview.add_item(child)
                continue
            btnid = -1
            try:
                btnid = int(child.custom_id.split("-")[1])
            except:
                newview.add_item(child)
                continue
            cur.execute(f"SELECT data FROM button WHERE buttonid = {btnid} AND guildid = {ctx.guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond(f"Button with ID {btnid} not found.", ephemeral = True)
                return
            data = json.loads(b64d(t[0][0]))
            color = data["color"]
            label = data["label"]
            url = data["url"]
            style = BTNSTYLE[color]
            uniq = f"{randint(1,100000)}{int(time()*100000)}"
            custom_id = "GeckoButton-"+str(btnid)+"-"+uniq
            if url != None:
                custom_id = None
            button = GeckoButton(label, url, style, data["disabled"], custom_id)
            newview.add_item(button)
            cur.execute(f"DELETE FROM buttonview WHERE buttonid = {btnid} AND customid = '{child.custom_id}'")
            cur.execute(f"INSERT INTO buttonview VALUES ({btnid}, '{custom_id}')")
            conn.commit()

        await message.edit(content = message.content, embeds = message.embeds, view = newview)
        await ctx.respond(f"Buttons in [message]({'/'.join(msglink)[-1]}) are updated.")  

bot.add_cog(ManageButton(bot))