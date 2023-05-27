import glob
import io
import os
import re
import requests
import shutil
import zipfile

# versionGuid = input("enter a version guid to scan: ")

def analyze_version(versionGuid):
    verbose = False
    printFinds = False

    cppFlags = []
    luaFlags = []
    leaOffset = 0 # -0x600 # -0xc00
    luaRegex = re.compile(r"game:(?:Get|Define)Fast(Flag|Int|String)\(\"(\w+)\"")

    print(f"analyzing {versionGuid}")

    baseDirectory = f"versions/{versionGuid}"
    setupBaseUrl = "https://setup.rbxcdn.com/channel/zintegration"

    packages = [
        {
            "Name": "RobloxStudio.zip",
            "Directory": "/"
        },
        {
            "Name": "extracontent-luapackages.zip",
            "Directory": "/ExtraContent/LuaPackages/"
        },
        {
            "Name": "extracontent-scripts.zip",
            "Directory": "/ExtraContent/Scripts/"
        },
    ]

    if not os.path.exists(baseDirectory):
        print("")
        # print("=== downloading files ===")
        for package in packages:
            print(f"downloading {package['Name']}...", flush=True, end="")

            archive = requests.get(f"{setupBaseUrl}/{versionGuid}-{package['Name']}").content
            with zipfile.ZipFile(io.BytesIO(archive)) as zObject:
                zObject.extractall(f"{baseDirectory}{package['Directory']}")

            print(" done!", flush=True)

    print("")
    # print("=== scanning for lua fastflags ===")
    print("finding lua fastflags...", end="")

    for filename in glob.glob(f"{baseDirectory}/ExtraContent/**/*.lua", recursive=True):
        with open(filename, "r", encoding="utf-8") as file:
            contents = file.read()
            results = luaRegex.findall(contents)
        
            for result in results:
                flagName = f"F{result[0]}{result[1]}"
                if not flagName in luaFlags:
                    if printFinds:
                        print(f"found {flagName} in {filename}")
                    luaFlags.append(flagName)

    print(" done!")

    print("")
    # print("=== scanning for c++ fastflags ===")

    binary = open(f"{baseDirectory}/RobloxStudioBeta.exe", "rb").read()
    binaryLength = len(binary)

    print(f"RobloxStudioBeta.exe is {binaryLength:,} bytes long")

    print("finding location of known fflag... ", end="")
    knownFlagLocation = binary.find(b"DebugDisplayFPS")
    print(f"done! ({hex(knownFlagLocation)})")

    print("finding location of where fflag is loaded... ", end="")

    knownFlagLoadLocation = 0
    currentPosition = 1
    while currentPosition != 0:
        # lea rcx, ds:[<offset>]
        leaAddress = binary.find(b"\x48\x8D\x0D", currentPosition)
        
        # skip if next instruction is not a jmp
        if binary[leaAddress+7] != 0xE9:
            currentPosition = leaAddress + 3
            continue

        leaTargetOffset = int.from_bytes(binary[leaAddress+3:leaAddress+7], 'little', signed=True)
        leaTargetAddress = leaAddress + 0x7 + leaTargetOffset + leaOffset

        if leaTargetAddress != knownFlagLocation:
            # print(f"potential location at {hex(matchedAddress)} did not match :( ({hex(targetAddress)} != {hex(knownFlagLocation)})")

            # yeah idk im just trying random offsets lol
            if leaOffset > -0x0f00:
                leaOffset -= 0x0100
                continue

            leaOffset = 0
            currentPosition = leaAddress + 3
        else:
            # print(f"found location at {hex(matchedAddress)}!")
            knownFlagLoadLocation = leaAddress
            break

    if knownFlagLoadLocation == 0:
        print("failed! (could not find known flag load location)")
        exit()

    print(f"done! ({hex(knownFlagLoadLocation)})")

    if verbose:
        print(f"got lea offset as {hex(leaOffset)}")

    # find address of subroutine that registers fflag names
    jmpLocation = knownFlagLoadLocation + 0x07
    targetJmpOffset = int.from_bytes(binary[jmpLocation+1:jmpLocation+5], 'little')
    fflagRegisterLocation = jmpLocation + 0x05 + targetJmpOffset

    varTypeData = {
        "FFlag": {
            "Address": fflagRegisterLocation,
            "CanBeDynamic": True
        },

        "SFFlag": {
            "Address": fflagRegisterLocation + 0x20 * 1,
            "CanBeDynamic": False
        },

        "FInt": {
            "Address": fflagRegisterLocation + 0x20 * 2,
            "CanBeDynamic": True
        },

        "FLog": {
            "Address": fflagRegisterLocation + 0x20 * 3,
            "CanBeDynamic": True
        },

        "FString": {
            "Address": fflagRegisterLocation + 0x20 * 4,
            "CanBeDynamic": True
        }
    }

    varTypeLocations = [varTypeData[varType]["Address"] for varType in varTypeData]

    if verbose:
        print("")
    # print("=== addresses ===")

    if verbose:
        for varTypeName, varTypeInfo in varTypeData.items():
            print(f"{varTypeName} : {hex(varTypeInfo['Address'])}")

    if verbose:
        print("")
    # print("=== finding all fflags ===")
    print("finding c++ fastflags...", end="")

    currentPosition = 1
    while currentPosition != 0:
        # jmp <offset> - instruction is 5 bytes in size
        jmpAddress = binary.find(b"\xE9", currentPosition)
        targetJmpOffset = int.from_bytes(binary[jmpAddress+1:jmpAddress+5], 'little', signed=True)
        targetJmpAddress = jmpAddress + 0x5 + targetJmpOffset

        # if jmpAddress == 0x3175664:
        #     print("bleh")

        if not targetJmpAddress in varTypeLocations:
            # print(f"potential location at {hex(jmpAddress)} did not match :( ({hex(targetJmpAddress)} != {hex(fflagRegisterLocation)})")
            currentPosition = jmpAddress + 1
            continue

        varType = [varType for varType in varTypeData.keys() if varTypeData[varType]["Address"] == targetJmpAddress][0]
        
        leaAddress = jmpAddress - 0x7
        targetLeaOffset = int.from_bytes(binary[leaAddress+3:leaAddress+7], 'little')
        targetLeaAddress = leaAddress + 0x7 + targetLeaOffset + leaOffset

        flagName = ""

        if varTypeData[varType]["CanBeDynamic"]:
            # mov r8d, 0x2
            movAddress = jmpAddress - 0x14
            movFlag = binary[movAddress+2]

            if movFlag == 2:
                flagName += "D"

        flagName += varType

        stringIndex = targetLeaAddress
        while binary[stringIndex] != 0:
            flagName += chr(binary[stringIndex])
            stringIndex += 1

        if printFinds:
            print(f"found {flagName} at {hex(jmpAddress)}")

        if not flagName in cppFlags:
            cppFlags.append(flagName)

        currentPosition = jmpAddress + 1

    print(" done!")

    print("")
    # print("=== results ===")
    print(f"found {len(cppFlags)} c++ fastflags")
    print(f"found {len(luaFlags)} lua fastflags")

    finalFlagList = sorted(cppFlags + luaFlags)

    for index in range(0, len(finalFlagList)):
        flagName = finalFlagList[index]
            
        if flagName in cppFlags:
            flagName = f"[C++] {flagName}"
        else:
            flagName = f"[Lua] {flagName}"

        finalFlagList[index] = flagName

    print("")
    print(f"finished analyzing flags for {versionGuid}")

    shutil.rmtree(baseDirectory)

    return finalFlagList