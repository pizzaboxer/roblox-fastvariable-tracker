# roblox-fastvariable-tracker

tool that spits out all the fastvariables in a specific roblox version, designed for constant tracking overtime to easily see what new stuff roblox is working on, etc

loosely inspired by [maximumadhd's roblox client tracker](https://github.com/MaximumADHD/Roblox-Client-Tracker) though this focuses specifically on fastvariables, tracks lua ones too, and isn't restricted to being run on windows

this is basically my piss poor attempt at binary reverse engineering in over a year since i have to navigate through x86 assembly for this, though figuring out stuff was fun

here's what the files do:
 - analyzer.py holds the code that performs the actual fastvariable analysis
 - analyzer-test.py is just used to analyze one specified version
 - diff-test.py is used to generate a fastvariable diff between two versions
 - tracker.py is the actual tracker itself that runs 24/7

btw if you wanna set up the tracker you'll have to manually prepare it first by putting the info for the latest version into state.json and using analyzer-test.py to get the variables for it

currently set up to deliver notifications to a webhook in the [latte softworks](https://latte.to) discord server ([#fastvariables](https://discord.com/channels/892211155303538748/1112095036876783638))