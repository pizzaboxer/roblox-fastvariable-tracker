# roblox-fastvariable-tracker

> [!IMPORTANT]
> This project has been migrated to [MaximumADHD's Roblox Client Tracker](https://github.com/MaximumADHD/Roblox-Client-Tracker/). Please use that from now on.
> 
> ([source code](https://github.com/MaximumADHD/RCT-Source/blob/main/src/Routines/ScanFastFlags.cs) / [dumped list](https://github.com/MaximumADHD/Roblox-Client-Tracker/blob/roblox/FVariables.txt))

tool that spits out all the fastvariables in a specific roblox studio version, designed for constant tracking overtime to easily see what new stuff roblox is working on, etc

loosely inspired by [maximumadhd's roblox client tracker](https://github.com/MaximumADHD/Roblox-Client-Tracker) though this focuses specifically on fastvariables, tracks lua ones too, as well as fastlog vars, and isn't restricted to being run on windows

because this is specific to studio this won't capture every fastvariable that exists, but it'll capture most ones

this is basically my piss poor attempt at binary reverse engineering in over a year since i have to navigate through x86 assembly for this, though figuring out stuff was fun

here's what the files do:
 - analyzer.py holds the code that performs the actual fastvariable analysis
 - analyzer-test.py is just used to analyze one specified version
 - diff-test.py is used to generate a fastvariable diff between two versions
 - tracker.py is the actual tracker itself that runs 24/7

btw if you wanna set up the tracker you'll have to manually prepare it first by putting the info for the latest version into state.json and using analyzer-test.py to get the variables for it

currently set up to upload the full list of variables as a [github gist](https://gist.github.com/pizzaboxer/a627b8e9f41353fb251a54517378d662) as well as deliver notifications to a webhook in the [latte softworks](https://latte.to) discord server ([#fastvariables](https://discord.com/channels/892211155303538748/1112095036876783638))
