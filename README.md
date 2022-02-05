# AConveyorBeltOfDeath
A Streamlabs Chatbot plugin utilizing the Twitch channel point API for randomized queueing. Developed for twitch.tv/AdamVsEverything 's RimWorld and Darkest Dungeon streams

# Notes
This is a squirrley little thing. It was developed with one person in mind, and I worked personally with them setting it up. I made improvements based on that setup process, but for the moment you may run into some fuss getting it up and running. It uses Python2.7 as a base, as required by Streamlabs Chatbot, but uses a python3-based Twitch API library, so the PY2 script runs a PY3 script, and they communicate over Stdin/Stdout. Gross. But effective.

# Setup
1. Install Python 3.9 or newer from https://www.python.org/downloads/release/python-390/
2. Perform initial Streamlabs Chatbot Desktop setup for the Scripts tab, as documented here: https://streamlabs.com/content-hub/post/chatbot-scripts-desktop
3. Go to https://dev.twitch.tv , access your console, and create a new application. Take note of the Client ID and Client Secret. Set the OAuth Redirect URL to http://localhost:17563
4. Download the script from GitHub as a .ZIP file. Import the chatbot script to SLCB, but don't enable it. First, perform initial set up of the options. You must fill out the AppID and Secret on the "App Settings" tab, then click the "One-Time Setup" button (FYI: This button runs "pip install twitchAPI" in your python 3 installation.)
5. Set up other settings under their tabs. Note that this script MUST create the Channel point rewards FOR YOU, and will attempt to do so the first time you start it. If they are set up in the Twitch Dashboard, it will not work! This is a Twitch imposed limitation. You can edit all parameters of the reward after the script creates it, though changing the name will require you change the name in the script settings as well. Make sure to save settings using the button at the bottom.
6. Play around from here!

# Setting Meanings

I'm omitting things that are very straightfoward. Most options in the UI have hover text that explain them

## Queue Settings
"Clear All Winner Entries" - This causes the plugin to Accept **all** Redemptions from a user when they're drawn, not just the ticket that won

"Ticket growth per day" - This causes redemptions to grow in value over time. Values greater than 1 are mathematically uninteresting, but putting in a value of 0.2 would make each Redemption grow a new Ticket every 5 days, so older entries have a better shot

"Refund old entries" and "Max entry age before purge" - Causes the plugin to Reject redemptions when they reach a specified number of days old, refunding the channel points. Useful to avoid clogging the queue with folks who aren't around anymore

"Use Viewer List" + "Only Pick Viewers" -- Does what it says on the tin. Tickets for people not currently in the Twitch viewer list will be ignored

"Use Viewer List" + "Viewer Advantage Factor" -- Multiplies tickets of people currently in chat by the factor. Greater than 1 confers an advantage, less than one a disadvantage. 

"Restrict Duplicate Selection" + "Clear used name list" -- Maintains a plain text file of people who have already been selected, and refuses to select them again until the Clear button is pressed. This text file can be edited ("used_viewers.ini", will be generated at runtime with first viewer, or you can create it yourself) if desired. One username per line.

## Redemption Settings

"Reward X name" - Name of the reward to create / use with Twitch channel points

"Reward X value" - How many Entries for the specified reward. E.G. if Reward 1 is worth 1 entry and costs 5000, Reward 2 might be worth 3 entries and cost 14500. Used to combat spam from mass redemptions, or have cheap redemptions with cooldowns/limits. When displaying stats, clicking an X entry button is treated identically to having clicked the 1 entry button X times.

"Enable Xth Redemption" - Toggles for if the extra redemptions are in use

## X Command 

"Command" - Chat command that triggers that functionality. 

"Permission Level" - What it says on the tin

"Response" - How the bot will respond. Use {format codes} to include parameters determined by the script. A list of available codes for each response is available by hovering the text box.

"Cooldown" - Max response frequency across all users

"User cooldown" - Max response frequency for any given user



# License

This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License. See https://creativecommons.org/licenses/by-sa/4.0/ for licensing terms
