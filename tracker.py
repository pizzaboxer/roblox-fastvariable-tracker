#!/usr/bin/env python3
import analyzer
import discord_webhook
import json
import os
import requests
import time

webhookUrl = ""
state = {}

with open("state.json", "r") as file:
    state = json.load(file)

print(f"current version: {state['version']} ({state['versionGuid']})")
print("")

if not os.path.exists("records"):
    os.makedirs("records")

while True:
    print("checking for new version...", flush=True, end="")
    versionInfo = requests.get("https://clientsettingscdn.roblox.com/v2/client-version/WindowsStudio64/channel/zintegration").json()

    if versionInfo["version"] == state["version"]:
        print(" done! (no new version)")
        time.sleep(60 * 10)
        continue

    print(f" done! (new version: {state['version']} -> {versionInfo['version']})")

    oldVersionGuid = state["versionGuid"]
    newVersionGuid = versionInfo["clientVersionUpload"]

    oldFlags = []
    newFlags = []

    addedFlags = []
    removedFlags = []

    with open(f"records/{oldVersionGuid}.txt", "r") as file:
        for line in file.readlines():
            oldFlags.append(line.strip())

    filename = f"records/{newVersionGuid}.txt"
    if os.path.isfile(filename):
        with open(filename, "r") as file:
            for line in file.readlines():
                newFlags.append(line.strip())
    else:
        print("")
        newFlags = analyzer.analyze_version(newVersionGuid)

        with open(filename, "w") as file:
            for flag in newFlags:
                file.write(flag + "\n")

    for flag in oldFlags:
        if not flag in newFlags:
            removedFlags.append(flag)

    for flag in newFlags:
        if not flag in oldFlags:
            addedFlags.append(flag)

    print("")

    messageLines = []

    if len(addedFlags):
        print("these flags were added:")

        messageLines.append("These flags were added:")
        messageLines.append("```cs")

        for flag in addedFlags:
            print(flag)
            messageLines.append(flag)

        messageLines.append("```")
    else:
        print("no flags were added")
        messageLines.append("No flags were added.")

    print("")

    if len(removedFlags):
        print("these flags were removed:")

        messageLines.append("These flags were removed: ")
        messageLines.append("```cs")

        for flag in removedFlags:
            print(flag)
            messageLines.append(flag)

        messageLines.append("```")
    else:
        print("no flags were removed")
        messageLines.append("No flags were removed.")

    print("")

    if len(webhookUrl):
        webhook = discord_webhook.DiscordWebhook(url=webhookUrl)
        embed = discord_webhook.DiscordEmbed(title=f"New version deployed! ({state['version']} -> {versionInfo['version']})", description='\n'.join(messageLines), color="8acc0e")
        webhook.add_embed(embed)
        webhook.execute()

    state["version"] = versionInfo["version"]
    state["versionGuid"] = versionInfo["clientVersionUpload"]

    with open("state.json", "w") as file:
        json.dump(state, file, indent=4)