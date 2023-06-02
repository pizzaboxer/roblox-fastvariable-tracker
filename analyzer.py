import glob
import io
import os
import re
import requests
import shutil
import zipfile

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
        for package in packages:
            print(f"downloading {package['Name']}...", flush=True, end="")

            archive = requests.get(f"{setupBaseUrl}/{versionGuid}-{package['Name']}").content

            with zipfile.ZipFile(io.BytesIO(archive)) as zObject:
                zObject.extractall(f"{baseDirectory}{package['Directory']}")

            print(" done!", flush=True)

    print("")
    print("finding lua fastflags...", end="")

    for filename in glob.glob(f"{baseDirectory}/ExtraContent/**/*.lua", recursive=True):
        with open(filename, "r", encoding="utf-8") as file:
            contents = file.read()
            results = luaRegex.findall(contents)
        
            for result in results:
                flagName = f"F{result[0]}{result[1]}"

                if flagName in luaFlags:
                    continue

                if printFinds:
                    print(f"found {flagName} in {filename}")
                
                luaFlags.append(flagName)

    print(" done!")

    print("")

    with open(f"{baseDirectory}/RobloxStudioBeta.exe", "rb") as file:
        binary = file.read()
    
    print(f"RobloxStudioBeta.exe is {len(binary):,} bytes long")

    print("finding location of known fflag... ", end="")
    knownFlagLocation = binary.find(b"DebugDisplayFPS")
    print(f"done! ({hex(knownFlagLocation)})")

    print("finding location of where fflag is loaded... ", end="")

    knownFlagLoadLocation = 0
    currentPosition = 0
    while True:
        # lea rcx, ds:[<offset>]
        leaAddress = binary.find(b"\x48\x8D\x0D", currentPosition)

        if leaAddress == -1:
            break

        # skip if next instruction is not a jmp
        if binary[leaAddress+7] != 0xE9:
            currentPosition = leaAddress + 3
            continue

        leaTargetOffset = int.from_bytes(binary[leaAddress+3:leaAddress+7], 'little', signed=True)
        leaTargetAddress = leaAddress + 0x7 + leaTargetOffset + leaOffset

        if leaTargetAddress != knownFlagLocation:
            # yeah idk im just trying random offsets lol
            if leaOffset > -0x0f00:
                leaOffset -= 0x0100
                continue

            leaOffset = 0
            currentPosition = leaAddress + 3
        else:
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

    fvarTypes = {}
    fvarTypes[fflagRegisterLocation]            = "FFlag"
    fvarTypes[fflagRegisterLocation + 0x20 * 1] = "SFFlag"
    fvarTypes[fflagRegisterLocation + 0x20 * 2] = "FInt"
    fvarTypes[fflagRegisterLocation + 0x20 * 3] = "FLog"
    fvarTypes[fflagRegisterLocation + 0x20 * 4] = "FString"

    if verbose:
        print("")

        for fvarTypeLocation, fvarType in fvarTypes.items():
            print(f"{fvarType} : {hex(fvarTypeLocation)}")

        print("")

    print("finding c++ fastflags...", end="")

    currentPosition = 0
    while True:
        # jmp <offset> - instruction is 5 bytes in size
        jmpAddress = binary.find(b"\xE9", currentPosition)

        if jmpAddress == -1:
            break

        targetJmpOffset = int.from_bytes(binary[jmpAddress+1:jmpAddress+5], 'little', signed=True)
        targetJmpAddress = jmpAddress + 0x5 + targetJmpOffset

        fvarType = fvarTypes.get(targetJmpAddress)

        if fvarType is None:
            currentPosition = jmpAddress + 1
            continue
        
        leaAddress = jmpAddress - 0x7
        targetLeaOffset = int.from_bytes(binary[leaAddress+3:leaAddress+7], 'little')
        targetLeaAddress = leaAddress + 0x7 + targetLeaOffset + leaOffset

        flagName = ""

        if fvarType != "SFFlag":
            # mov r8d, 0x2
            movAddress = jmpAddress - 0x14
            movFlag = binary[movAddress+2]

            if movFlag == 2:
                flagName += "D"

        flagName += fvarType

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
