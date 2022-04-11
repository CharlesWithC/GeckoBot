# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Update Stats on advertisement websites

import requests, json, settings

config_txt = open("./ad.conf","r").read()
config = json.loads(config_txt)

def UpdateAdStatus(server_count, shard_count, user_count):
    try:
        print("Updating bot stats for advertisement websites...")
        requests.post(f"https://top.gg/api/bots/{settings.BOTID}/stats", 
            data={"server_count": server_count, "shard_count": shard_count},
            headers={"Authorization": config["topgg"]})

        requests.post(f"https://discords.com/bots/api/bot/{settings.BOTID}", 
            data={"server_count": server_count},
            headers={"Authorization": config["discords"]})

        requests.post(f"https://discordbotlist.com/api/v1/bots/{settings.BOTID}/stats", 
            data={"guilds": server_count, "users": user_count},
            headers={"Authorization": config["discordbotlist"]})
        print("Bot stats update finished.")
    except:
        pass