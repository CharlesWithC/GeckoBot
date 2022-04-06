# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Help

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText
from base64 import b64encode, b64decode
from time import time
from random import randint
import io

from bot import bot
from settings import *
from functions import *
from db import newconn
from fuzzywuzzy import process

ABOUT = """Gecko is a **general purpose bot** which can help you moderate community and create fun.  

Games, Music and a lot of staff functions are supported.  
More functions are planned and being added.  
Use `/help` in bot for detailed help.

**Gecko Games**

**Finance** - earn coins by checking in daily and working  
**Connect Four** - chess game where two players battle  

**Gecko Music**

*Not only music, but also radio!*  
274 radio stations are supported, and you can request your desired station to be added.  

**Staff Functions**

Includes: button, embed, form, chat action, reaction role, staff management, server stats and voice channel recorder.  
**Button** - Create buttons of any kind, the layout and interaction are fully customizable! The interaction could be linked to simple text messages, embed messages or forms.  
**Embed** - Create and post embeds, the URL, thumbnails, images, footers etc are all customizable. Embeds are stored in the database and can be recovered at any time in case they are deleted accidentally.  
**Form** - Create forms with at most five input fields, which can be either a multi-line text box or a single-line input. Submissions will be updated in a staff channel and you can download all entries with one command.  
**Chat Action** - React emojis / Timeout / Kick / Ban a member when a keyword is detected, the emoji reactions always add fun.  
**Voice Channel Recorder** - Record all the speakers separately, to save a meeting or an interview.  
**Reaction Role** - Assign members a role when they react an emoji.  
**Server Stats** - Based on variables, fully customizable!  
**Staff Management** - Administrative and non-administrative staff, and a staff list for users to know the real staff.  

Gecko is developing fast, you are welcomed to join [Gecko Community](https://discord.gg/wNTaaBZ5qd) to discuss, submit feedbacks and share your ideas.  """

HELP = {
    "about": ABOUT,

    "help": "Receive this help message.\n\nUsage: `/help`",
##### GAMES
    "games": {
        "description": """It's Gecko Playground!
Finance games and connect four games are supported at the moment.
Check `games - finance` or `games - four` for detailed information.""",

##### FINANCE
        "finance": {
            "description": """This is Gecko Finance. Like your bank account.
Your coins can only be used in the server where you earned it.
There are various commands related to `games - finance`:
`balance` `checkin` `work` `claim` `richest`""",

            "balance": """Check your Gecko Finance Balance (It's virtual!) and your ranking in the server.
The balance can be used throughout the bot, in finance games and connect four games betting.

Usage: `/balance`""",

            "checkin": """Check in daily to earn coins.

Usage: `/checkin`""",

            "work": """Get job in Finance Games, finish it and receive coins.
If you are already working, you can't use this command.
If the reward of last job isn't claimed, this will claim it and you'll start working again.

Usage: `/work`""",

            "claim": """Claim your last job reward. 

Usage: `/claim`""",

            "richest": """Get the richest member leaderboard (Top 10) in the server.

Usage: `/richest`"""},

##### CONNECT FOUR
    "four": {
        "description": """**Connect Four** is a multiplayer board game where you win by getting four pieces in a row (can be horizontal, vertical or diagonal).
You place your pieces to the column the reaction emoji is represtenting to.
The pieces can only be placed on other colored pieces, not white ones (white are placeholder). Like there's gravity pulling them down.
You can **bet** your coins in this game, up to 10000 coins, winner take all the bet from the loser.

And due to **Discord API Ratelimit**, the game might be a bit *slow*. Please note the "**whose turn**" status and be patient.

Subcommands of `/four` group:
`start` `result` `leaderboard` `statistics`""",

        "start": """Create a match and wait for others to join it.
You can select your opponent by providing the `opponent` argument.
And bet your coins by setting the `bet` argument.

Usage: `/four start {optional: opponent} {optional: bet}`""",

        "result": """Get the result (win / lose / draw) and the final state (the chess board) of a game.
The game id is shown in each game and you must provide it to retrieve the result.

Usage: `/four result {required: gameid}""",

        "leaderboard": """Get the leaderboard of all **Connect Four** players, throughout all servers.

Usage: `/four leaderboard`""",

        "statistics": """Get your own **Connect Four** statistics, including wins / losses / draws and earnings.

Usage: `/four statistics`"""}
    },

##### STAFF
    "button": {
        "description": """**Gecko Button**, fully **customizable**.
You can ask the bot to send **embed** or show **form** or just send a **message** to the user who clicked the button.
The button **color** and **label** can be customized, and a **url** can be provided so that the clicker would open it.
Also you can **disable** the button, make the result **ephemeral** so that only the clicker would see it.

When you create a button, it's stored in database. And you need to send it to a channel. (This makes it easy to **recover** the button if it's deleted accidentally).
Multiple buttons can be sent together, and you could **attach** them to an existing message Gecko sent.
When you edit a button, if it's related to label / color / url, you could use `/button update {msglink}` to update the buttons in a message easily.
If you changed the button result, like embed / form / message to send, you don't need to update the button itself.

Subcommands of `/button` group:
`create` `edit` `delete` `get` `list` `clear` `send` `attach` `update`""",

        "create": """Create a button. If you want to know detailed information about **Gecko Button**, use `/help button`.
This will only create the button and store it in database. You need to use `/button send` or `/button attach` to post it.
You can provide none of the content / embed / form to make the button a decorative one.

Usage: `/button create {required: label} {optional: color, default blurple} {optional: emoji} {optional: disabled, default No} {optional: ephemeral, default Yes} {optional: url} {optional: content} {optional: embedid} {optional: formid}`""",

        "edit": """Edit the button by the given button ID provided when it's created.
If you forgot the button ID, use `/button get` to get all buttons in a message, or `/button list` to get all buttons created in the server.ButtonStyle()

Usage: `/button edit {required: buttonid} {required: label} {optional: color, default blurple} {optional: emoji} {optional: disabled, default No} {optional: ephemeral, default Yes} {optional: url} {optional: content} {optional: embedid} {optional: formid}`""",

        "delete": """Delete a button from database by the given button ID. 
**Note** This will only delete the button from database but not any button already posted. Posted buttons will no longer work and needed to be deleted manually.
To remove all buttons from a message, use `/button clear`. To add some buttons back, use `/button attach`.

Usage: `/button delete {required: buttonid}`""",

        "get": """Get all buttons included in a message by message link.
To get message link, right click or hold on the message, and select 'Message Link' from the popup.

Usage: `/button get {required: msglink}""",

        "list": """List all buttons created in the guild.
No argument is needed.

Usage: `/button list`""",

        "clear": """Clear all buttons included in a message by message link.
To get message link, right click or hold on the message, and select 'Message Link' from the popup.
Use `/button attach` to add some buttons back.

Usage: `/button clear {required: msglink}`""",

        "send": """Send button(s) in a channel.
You can either send single button, or multiple buttons in a row. The order of buttons is the same as the order you put their IDs.
To attach a button to an existing message, use `/button attach`.

Usage: `/button send {required: #channel} {required: buttonid}""",

        "attach": """Attach button(s) to an existing message.
You can either send single button, or multiple buttons in a row. The order of buttons is the same as the order you put their IDs.
**Note** The existing message must be sent by Gecko.

Usage: `/button attach {required: msglink} {required: buttonid}""",

        "update": """Update button layout in a message.
This will update the label / color / URL / disabled status of the button.
If you only changed the button interaction (content / embedid / formid), you don't need to run update.

Usage: `/button update {required: msglink}`"""},

    "chat": {
        "description": """**Gecko Chat Action**, take action when keyword is detected.
Chat Action supports timeout / kick / ban (they are all permanent), and reactions!
Gecko will automatically react emojis when it find a keyword in the message.

**Note** This function may have a slight delay due to **Discord API Ratelimit**

Subcommands of `/chat` group:
`add` `list` `remove`""",

        "add": """Add a chat action.
You can add multiple keywords using single command, separate them with ','.
For `react` actions, a valid emoji must be provided. You can only add one emoji using single command.

Usage: `/chat add {required: keywords} {required: action} {optional: emoji, required only when action is react}`""",

        "list": """List chat action.
For `timeout / kick / ban` actions, the keywords will be listed.
For `react` actions, Gecko will sort out the list, and show keywords after the emoji to be reacted.

Usage: `/chat list {required: action}`""",

        "remove": """Remove keywords from chat action.
You only need to provide the keywords to be removed, other keywords will not be affected.

Usage: `/chat remove {required: keywords} {required: action}"""},

    "form": {
        "description": """**Gecko Form**, submit forms without leaving Discord.
**Gecko Form** works with **Gecko Button**. When you create a form, you need to create a button whose interaction form id is the id of form you created. Then the form will popup when the member clicked the button.
At most 5 fields is supported which is limited by Discord, each field can either be short (single line) or long (multiple lines).
When a member submits a form, his entry will be updated in staff form channel. Use `/setchannel form` to set it up.
To download all entries, use `/form download`, which will send you a Markdown file with all entries included. You are suggested to use a Markdown viewer to open the file.

Subcommands of `/form` group:
`create` `edit` `delete` `list` `toggle` `entry` `download`""",

        "create": """Create a form.
By command argument, you can set the callback message - the message to send to members when they submit the form. And whether the form acceptes only one submission of each member (onetime).
Detailed information (the form fields) will be edited in a modal popped up.

To stop receiving new entries, use `/form toggle`. You are recommended to disabled the button by `/button edit` as well.

Usage: `/form create {optional: callback, default "Thanks for submitting the form"} {optional: onetime, default No}`""",

        "edit": """Edit a form by the given form id.
By command argument, you can set the callback message - the message to send to members when they submit the form. And whether the form acceptes only one submission of each member (onetime).
If you leave them empty, they will keep unchanged.
Detailed information (the form fields) will be edited in a modal popped up.

In case you forgot the form id, use `/form list` to get all forms created in the guild.

Usage: `/form edit {required: formid} {optional: callback, default "Thanks for submitting the form"} {optional: onetime, default No}`""",

        "delete": """Delete a form from database by the given form id.
This will delete the form and all entries! Make sure to back them up before deleting them.
After you deleted the form, the submit button will become invalid and you'd better delete it. 
If you only want to stop receiving new entries, use `/form toggle`

Usage: `/form delete {required: formid}`""",

        "list": """List all forms created in the guild.
No argument is needed .

Usage: `/form list`""",

        "toggle": """Toggle whether the form accepts new entries.
This will only disable the form. To disable the submit button, use `/button edit`

Usage: `/form toggle {required: formid}""",

        "entry": """For members, this command allows them to view their own submitted entry of a form.
For staff, this command allows them to view any users' entry of a form.

Usage: `/form entry {required: formid} {optional: user, only staff can use this argument}""",

        "download": """Download all entries of a submitted form.
Gecko will send you a Markdown file including all entries, you are suggested to open it using a Markdown viewer / editor.

Usage: `/form download {required: formid}`"""},

    "reaction_role": {
        "description": """**Gecko Reaction Role**, add role when members add a reaction.
An existing message is needed to react on, which doesn't need to be sent by Gecko.
You are recommended to use **Gecko Embed**, but you can use any messages sent in the guild.

**Note** The message should not be deleted, once deleted, the reaction role function will not work. And if you sent it again, members who reacted previously will lose their roles.
Emojis bound to the roles cannot be changed, neither removed, but you can append more roles at any time.

Subcommands of `/reaction_role` group:
`create` `append` `list`""",

        "create": """Tell Gecko that a message will be used for reaction roles.
And set a list of emojis to be bound to corresponding roles.

You are recommended to use **Gecko Embed**, but you can use any messages sent in the guild.
You can add more roles at any time, but there can be at most 20 roles (reactions).

Usage: `/reaction_role create {required: msglink} {required: rolebine, Role => Emoji, separate with space, like @role1 emoji1 @role2 emoji2...}""",

        "append": """Add more roles to a reaction role message.
There could be at most 20 roles (reactions).

Usage: `/reaction_role append {required: msglink} {required: rolebine, Role => Emoji, separate with space, like @role1 emoji1 @role2 emoji2...}""",

        "list": """List all active reaction role posts.
No argument is needed.

Usage: `/reaction_role list`"""},

    "staff": {
        "description": """**Staff Management**, **administrative** and **non-administrative**
There are two types of staff, **administrative** and **non-administrative**. 
**Administrative staff** can use all staff commands (except those can only be used by server owner).
**Non-administrative staff** cannot use staff commands, but they will be shown in **Staff List** so that members know they are safe to message.
**Example**: Community Moderators are administrative staff, while Community Helpers are non-administrative staff.

Subcommands of `/staff` group:
`list` `manage`""",
        
        "list": """List all recognized staff in the guild.
There's an optional argument `withid`, if set to `Yes`, the user id of staff will be displayed to prevent fake accounts.

Usage: `/staff list {optional: withid, default No}""",

        "manage": """Manage staff roles & users in the guild.
**Only server owner is allowed to use this command**
You can manage staff by roles, or by users. All users with staff roles will be included in staff list automatically.

Explanation of arguments:
Operation: Add / Remove
Target: Role / User. If set to role, obj need to be a list of roles ; If set to user, obj need to be a list of users.
Administrative: Yes / No. Whether the staff role / user can use staff commands.
Obj: A list of roles / users, decided by target.

Usage: `/staff manage {required: operation} {required: target} {required: administrative} {required: obj}"""},

    "stats_display": {
        "description": """**Stats Display**, or **Server Stats**
This show your server statistics by using a category and some channels.
You may notice the channels are voice channels, yes they are, but a lock is displayed for all members, except the server owner.
And it's based on **variables** and fully customizable! Variables are defined in {} brackets.

Supported variables:
{time: [strftime]} - e.g. {time: %A, %b %-d} | [strftime format help](https://strftime.org/)
{members} - total members in the guild
{online} - online members in the guild
{@role} - number of user who have @role
{@role online} - number of online user who have @role

**Note** Gecko updates server stats one guild by one guild each minute, so there might be a delay on updates.

Subcommands of `/stats_display` group:
`setup` `create` `edit` `delete` `destroy`""",

        "setup": """Automatically set everything related to **Server Stats** up.
This includes, creating a `Server Stats` channel and move it to the top, and creating two default stats channel:
``` - {time: %A, %b %-d}
 - {online} / {members} Online```

**Note** The setup must be done before customizing the server stats channels.

No argument is required for this command.

Usage: `/stats_display setup`""",

        "create": """Create a new stats channel and configure it based on your own configuration.
To get help about configuration, use `/help stats_display`. 

Usage: `/stats_display create {required: config}`""",

        "edit": """Edit an existing stats channel (update the configuration)
You need to provide the channel ID because hashtags aren't supported for Voice Channels.
To get it, enable Developer Mode for your Discord. There's a lot of tutorial on the Internet.

Usage: `/stats_display edit {required: channelid} {required: (new) config}""",

        "delete": """Delete a stats channel.
This will delete the channel and Gecko will no longer update stats of it.
You need to provide the channel ID because hashtags aren't supported for Voice Channels.
To get it, enable Developer Mode for your Discord. There's a lot of tutorial on the Internet.

Usage: `/stats_display delete {required: channelid}""",

        "destroy": """Disable server stats function and delete the category and all stats channels.
Be careful! This operation cannot be undone!

No argument is required for this command.

Usage: `/stats_display destroy`"""},

    "vcrecord": {
        "description": """**Gecko Voice Channel Recorder**, AKA **GeckoVCR**
**GeckoVCR** helps you record the conversation in a voice channel. The recording will be separated by each member.

**Use cases**
Staff meeting, staff applicant interview etc

**Privacy Warning** 
You should always ask whether the attendents would like their voice to be recorded, and make sure they all agreed before starting **GeckoVCR**.
**Disclaimer**: *Gecko and developer are not responsible for any legal issues caused by abusing. We have the right to disable VCR function for any guild once abusing is reported.*

**Note**
Gecko sends you all the audio files through DM once the recording is finished. No data is stored on Gecko server.

**One more thing**
Music will have to be stopped before VCR is started.
Gecko locks music function when VCR starts.""",

        "join": """Let Gecko join the voice channel you are in and lock music function.
This will not start recording immediately.
Use `/vcrecord start` to start recording.

Usage: `/vcrecord join`""",

        "leave": """Let Gecko leave the voice channel, and if it's being recorded, stop the recording and send you the recorded audio files through DM.
        
Usage: `/vcrecord leave`""",

        "start": """Start recording the voice channel.
Gecko must have joined the voice channel before recording starts.

Usage: `/vcrecord start`""",

        "stop": """Stop recording the voice channel and send you the audio files.
Make sure your DM is open!

Usage: `/vcrecord stop`"""},

    "setup": """Send the server owner a DM about the necessary things needed to be done when Gecko is added to a guild.
This command can only be executed by the server owner.

Usage: `/setup`""",

    "setchannel": """Set the channel where certain stuff will be done.
For detailed information, use `/setup`.
This command can only be executed by the server owner.

Usage: `/setchannel {required: #channel}`""",

    "music": {
        "description": """**Gecko Music**, and **Radio**
For music function, staff can use `/play` to play a song immediately, members can use `/queue` to queue up a song.
Use `/next` to switch to the next song, and `/dequeue` to remove a song from the list.
Use `/current` to see the current playing song, and `/playlist` to see the current song and next up songs.
Staff can toggle whether the `current song` update will be sent in the music channel, decide where Gecko will play the music and pause / resume the music.
Loopback (playlist) playing is supported. favourite (AKA `fav`) lists are also supported.

For radio function, only staff can set which station Gecko will be playing, there's a list of 274 radio stations. They are shown in the autocomplete options, or you can use `/radiolist` to get a full list of them.
Radio streams are endless and Gecko won't switch to the next song. Staff need to use `/play` or `/next` to switch back to music mode.

Subcommands of `/music` group
`join` `leave` `pause` `resume` `toggle` `clear` `loop` 

Music commands without group (no `/music` prefix is needed)
`play` `next` `queue` `dequeue` `playlist` `current` `radio` `radiolist`""",

        "join": """**Staff only command**
Join the voice channel you are in and start playing the songs in the playlist, if there are.

Usage: `/music join`""",

        "leave": """**Staff only command**
Leave the voice channel and save the playlist.

Usage: `/music leave`""",

        "pause": """**Staff only command**
Pause the music.

Usage: `/music pause`""",

        "resume": """**Staff only command**
Resume the music.

Usage: `/music resume`""",

        "toggle": """**Staff only command**
Toggle whether `current song` update will be posted in the music channel.

Usage: `/music toggle`""",

        "clear": """**Staff only command**
Clear the playlist.

Usage: `/music clear`""",

        "loop": """**Staff only command**
Toggle loop playback of playlist.

Usage: `/music toggle`""",

        "play": """**Staff only command**
Play a music while stopping the song being played at the moment.
If loop playback is enabled, the current song will be moved to the end of the list.
Search suggestion is enabled, so you can type the keywords and see if there's any result.

Usage: `/play {required: song}`""",

        "next": """*This command can be used by anyone*
Switch to the next song.

Usage: `/next`""",

        "queue": """Queue up a song which will appear in the playlist.
Search suggestion is enabled, so you can type the keywords and see if there's any result.

Usage: `/queue {required: song}`""",

        "dequeue": """Remove a song from the playlist.
The song must be selected from the autocomplete results.

Usage: `/dequeue {required: song}`""",

        "fav": """Add the current song to your own favourite list, or enter a song name to add it to the list.

Usage: `/fav {optional: song}`""",

        "unfav": """Remove a song from your favourite list.
The song must be selected from the autocomplete results.

Usage: `/unfav {required: song}`""",

        "favlist": """Get your own favourite song list.

Usage: `/favlist`""",

        "qfav": """Select a song from your favourite list and add it to the queue.

Usage: `/qfav {required: song}`""",

        "playlist": """Get the current song and all next-up songs.

Usage: `/playlist`""",

        "current": """Get the current song and the member who requested it.

Usage: `/current`""",

        "radio": """**Staff only command**
Save the current playlist, and start playing radio.
There are 274 radio stations supported. They are shown in the autocomplete options, or you can use `/radiolist` to get a full list of them.
Radio streams are endless and Gecko won't switch to the next song. You need to use `/play` or `/next` to switch back to music mode.

*If your desired radio station isn't in the list, you could join [Gecko Community](https://discord.gg/wNTaaBZ5qd) and submit the station name & stream link (There must be a stream link otherwise it will not be accepted.) If the radio station is accepted, it will be added to the radiolist very soon.*

Usage: `/radio {required: radio station}`""",

        "radiolist": """Get a list of supported radio station.

Usage: `/radiolist`"""
    }
}

commands = {"help": "Get this help message.\n\nUsage: `/help`"}
for category in HELP.keys():
    if type(HELP[category]) is dict:
        for subcategory in HELP[category]:
            if type(HELP[category][subcategory]) is dict:
                for command in HELP[category][subcategory]:
                    commands[f"{category} - {subcategory} - {command}"] = HELP[category][subcategory][command]
            else:
                commands[f"{category} - {subcategory}"] = HELP[category][subcategory]
    else: # no subcategory
        commands[f"{category}"] = HELP[category]

ckey = list(commands.keys())
for cmd in ckey:
    if cmd.endswith(" - description"):
        commands[cmd.replace(" - description", "")] = commands[cmd]
        del commands[cmd]

async def HelpAutocomplete(ctx: discord.AutocompleteContext):
    if ctx.value.replace(" ","") == "":
        return list(commands.keys())[:10]
    d = process.extract(ctx.value.lower(), commands.keys(), limit = 10)
    ret = []
    for dd in d:
        ret.append(dd[0])
    return ret[:10]

@bot.slash_command(name="about", description="About Gecko")
async def help(ctx):
    await ctx.respond(HELP["about"])

@bot.slash_command(name="help", description="Get help.")
async def help(ctx, cmd: discord.Option(str, "Type category or command to get detailed help. Use only autocomplete options.", required = True, autocomplete = HelpAutocomplete)):
    if cmd in commands.keys():
        await ctx.respond(embed = discord.Embed(title = cmd, description=commands[cmd], color = GECKOCLR))
    else:
        await ctx.respond(f"Command not found. Please select one from the autocomplete options.", ephemeral = True)