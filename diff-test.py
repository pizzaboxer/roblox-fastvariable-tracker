#!/usr/bin/env python3
firstVersionGuid = input("enter a version guid: ")
secondVersionGuid = input("enter a version guid to compare against: ")

firstFlags = []
secondFlags = []

addedFlags = []
removedFlags = []

with open(f"records/{firstVersionGuid}.txt") as file:
    for line in file.readlines():
        firstFlags.append(line.strip())

with open(f"records/{secondVersionGuid}.txt") as file:
    for line in file.readlines():
        secondFlags.append(line.strip())

for flag in firstFlags:
    if not flag in secondFlags:
        removedFlags.append(flag)

for flag in secondFlags:
    if not flag in firstFlags:
        addedFlags.append(flag)

print("")

if len(addedFlags):
    print("these flags were added:")
    for flag in addedFlags:
        print(flag)
else:
    print("no flags were added")

print("")

if len(removedFlags):
    print("these flags were removed:")
    for flag in removedFlags:
        print(flag)