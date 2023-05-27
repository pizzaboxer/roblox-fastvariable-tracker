#!/usr/bin/env python3
import analyzer

versionGuid = input("enter a version guid to scan: ")
newFlags = analyzer.analyze_version(versionGuid)

with open(f"records/{versionGuid}.txt", "w") as file:
    for flag in newFlags:
        file.write(flag + "\n")