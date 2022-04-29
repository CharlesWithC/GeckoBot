BOTID = 954034331230285838
DEVGUILD = 963808254071287848
GECKOCLR = 0x9E842E
TMPCLR = 0xB92025
BOTOWNER = 873178118213472286
FINANCE_LOG_CHANNEL = (955721720440975381, 956362780909375538)
ANNOUNCEMENT_CHANNEL = (955721720440975381, 965598253926187038)
LOG_CHANNEL = (955721720440975381, 955979951226646629)
GUILDUPD = (955721720440975381, 961993589175496784)
GECKOEMOJI = "<:gecko:960189082007371806>"
STATUS = {"online": ":green_circle: Online", "offline": ":black_circle: Offline", "idle": ":yellow_circle: Idle", "dnd": ":red_circle: Do Not Disturb"}

SUPPORT = "https://discord.gg/wNTaaBZ5qd"
TRANSLATE = "translate.charlws.com"

ETS2ID = 227300
ATSID = 270880

FINANCE_CHECKIN_BASE_REWARD = 400
RANK_EMOJI = ["", ":first_place:", ":second_place:", ":third_place:", ":four:", ":five:", \
    ":six:", ":seven:", ":eight:", ":nine:", ":ten:"]
from discord.enums import ButtonStyle
BTNSTYLE = {"blurple": ButtonStyle.blurple, "grey": ButtonStyle.grey, "gray": ButtonStyle.gray, 
    "green": ButtonStyle.green, "red": ButtonStyle.red}

GECKOICON = "https://cdn.discordapp.com/app-icons/954034331230285838/4ba646d5c588bb44787e5f4b93a86da9.png"
MUSIC_ICON = "https://cdn.discordapp.com/app-assets/954034331230285838/958539534830796851.png"
FFMPEG_OPTIONS = "-reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2"

SOLID = "<:solid:969525055006605312>"
ONETHREE = "<:onethree:969527265077628960>"
HALF = "<:half:969525054788472893>"
THREEONE = "<:threeone:969527265304121354>"
SPACE = "<:space:969525054603919402>"

import pyttsx3
VOICES = []
tts = pyttsx3.init()
voices = tts.getProperty('voices')
for voice in voices:
    VOICES.append(voice.id)