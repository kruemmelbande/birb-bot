import discord, json
from sys import exit
import datetime
import asyncio
import os
import time
import math
intents=discord.Intents.all()
bot = discord.Bot(intents=intents)

version="0.1.5"
jsonversion=4

userTemplate={
    "votesFor":0,
    "isVoting":False,
    "isOwned":False,
    "isOwner":False,
    "consentLeader":True
}
def loadUserdb():
    global users, userdb, packs
    try:
        with open("userdb.json","r") as f:
            userdb=json.load(f)
            try:
                jsonver=userdb["version"]
            except:
                jsonver="No version found"
            if jsonver!=jsonversion:
                print(f"CRITICAL: Userdb is non-valid version! Expected {jsonversion}, got {jsonver}", flush=True)
            users=userdb["users"]
            packs=userdb["packs"]
    except Exception as e:
        print("Unable to load userdb", flush=True)
        print(e, flush=True)
        exit()
    return users

async def longresponse(ctx, message):
    if len(message)<2000:
        print(f"VERBOSE: Message is of length {len(message)}", flush=True)
        await ctx.respond(message, ephemeral=True)
        return
    print(len(message), flush=True)
    segments= math.ceil(len(message)/2000)
    print(f"VERBOSE: Sending {segments} messages", flush=True)
    for i in range(segments):
        if i*2000>len(message):
            await ctx.respond(message[i*2000:], ephemeral=True)
        else:
            await ctx.respond(message[i*2000:(i+1)*2000], ephemeral=True)
        await asyncio.sleep(1)

def saveUserdb():
    global users, packs, jsonversion
    try:
        with open("userdb.json","w") as f:
            #print(json.dumps(users, indent=4))
            userdb={"users":users,"packs":packs,"version":jsonversion}
            json.dump(userdb,f,indent=4)
            print(f"[{datetime.datetime.now()}] Saved userdb", flush=True)
    except Exception as e:
        print("Unable to save userdb", flush=True)
        print(e, flush=True)
        exit()

try:
    #load config
    with open("config.json","r") as f:
        config=json.load(f)
except Exception as e:
    print("Unable to load config", flush=True)
    print(e, flush=True)
    exit()
try:
    #parse config
    token=config["token"]
except Exception as e:
    print("Error while parsing config", flush=True)
    print(e)
    exit
    
def isElivated(ctx):
    #check if the user has the admin role
    for role in ctx.author.roles:
        if role.name=="Bot Leader":
            return True
    return False

def hasRole(ctx, role):
    for rolea in ctx.author.roles:
        if rolea.name==role:
            return True
    return False

def getUserVotes():
    global users
    votes={}
    for user in users:
        
        if not int(user) in votes:
            votes[int(user)]=0
        if users[user]["isVoting"]==False:
            continue
        if users[user]["votesFor"] in votes:
            votes[users[user]["votesFor"]]+=1
        else:
            votes[users[user]["votesFor"]]=1
    votes[0]=0
    return votes

async def rebuildHirearchy(ctx):
    global users
    #add all users to the database
    for user in guild.members:
        if not str(user.id) in users:
            newUser=userTemplate.copy()
            users[str(user.id)]=newUser
            print(f"Added {user.name} to database", flush=True)
    for user in users.copy():
        if not int(user) in [user.id for user in guild.members]:
            print(f"Removed {user} from database", flush=True)
            users.pop(user)
            if user in users:
                print("CRITICAL: Unable to remove user from database", flush=True)
                exit()
    #remove all references to users that are not in the database
    for user in users:
        if users[user]["isOwned"]==True and users[user]["isVoting"]==False:
            print(f"Invalid state: {user} is owned, but has no owner", flush=True)
            users[user]["isOwned"]=False
        if (not str(users[user]["votesFor"]) in [str(user) for user in users]) and users[user]["isVoting"]==True:
            print(f"Removed reference to {users[user]['votesFor']} from {user}", flush=True)
            users[user]["votesFor"]=0
            users[user]["isVoting"]=False

        if users[user]["isVoting"]:
            if users[str(users[user]["votesFor"])]["consentLeader"]==False:
                users[user]["votesFor"]=0
                users[user]["isVoting"]=False
                print(f"Removed vote for {users[user]['votesFor']} because they are not votable", flush=True)
                continue
            if users[str(users[user]["votesFor"])]["isOwned"]==True:
                users[user]["votesFor"]=0
                users[user]["isVoting"]=False
                print(f"Removed vote for {users[user]['votesFor']} because they are owned", flush=True)
            
    saveUserdb()
    now=datetime.datetime.now()
    print(f"[{now}] Rebuilding hirearchy because of {ctx.author.name}", flush=True)
    votes=getUserVotes()
    for user in users:
        currentUser=discord.utils.get(guild.members, id=int(user))
        if users[user]["isVoting"]:
            currentTarget=discord.utils.get(guild.members, id=int(users[user]["votesFor"]))
            if currentTarget==None:
                print(f"CRITICAL: Target {users[user]['votesFor']} ({user}) not found", flush=True)
            if currentTarget.bot:
                users[user]["votesFor"]=0
                users[user]["isVoting"]=False
                print(f"Removed vote for {currentUser.name} because they are a bot", flush=True)
        if currentUser==None:
            print(f"CRITICAL: User {user} not found", flush=True)
        print(f"VERBOSE {user}: {currentUser}", flush=True)
        print(f"VERBOSE {currentUser.name}", flush=True)
        userRoles=[role.name for role in currentUser.roles]
        print(f"VERBOSE Checking {currentUser.name} with roles {userRoles} ", flush=True)
        if votes[int(user)]>=2:
            print(f"{user} is a pack leader", flush=True)
            users[user]["isOwner"]=True
            users[user]["isOwned"]=False
            users[user]["votesFor"]=0
            users[user]["isVoting"]=False
        else:
            users[user]["isOwner"]=False
        if votes[users[user]["votesFor"]]>=2:
            users[user]["isOwned"]=True
            users[user]["isOwner"]=False
        else:
            users[user]["isOwned"]=False
        #if a user has more than 2 votes, they become a pack leader, and everybody who voted for them becomes owned by them.
        #no more than 5 users can join a pack

        if "Bot Override" in userRoles:
            print("VERBOSE User is a bot override, skipping", flush=True)
            continue
        print(f"VERBOSE User has {votes[currentUser.id]} votes", flush=True)
        if votes[currentUser.id]>=2:
            #user is a pack leader
            #check if they already have the role
            if not "Pack Leader" in userRoles:
                await currentUser.add_roles(discord.utils.get(guild.roles, name="Pack Leader"))
                print(f"Added role to {currentUser.name}", flush=True)
            for userb in users:
                if users[userb]["votesFor"]==int(user):
                    users[userb]["isOwned"]=True
        else:
            #user is not a pack leader
            #check if they have the role
            if "Pack Leader" in userRoles:
                await currentUser.remove_roles(discord.utils.get(guild.roles, name="Pack Leader"))
                print(f"Removed role from {currentUser.name}", flush=True)
                for userb in users:
                    #check if the user is owned by the user
                    if users[userb]["votesFor"]==int(user):
                        users[userb]["isOwned"]=False
        if users[user]["isOwned"] or users[user]["isOwner"]:
            if not "Pack Avali" in userRoles:
                await currentUser.add_roles(discord.utils.get(guild.roles, name="Pack Avali"))
                print(f"Added Pack Avali to {currentUser.name}", flush=True)
        else:
            if "Pack Avali" in userRoles:
                await currentUser.remove_roles(discord.utils.get(guild.roles, name="Pack Avali"))
                print(f"Removed Pack Avali from {currentUser.name}", flush=True)
                
    saveUserdb()

def wrapper_buildHirearchy(ctx):
    asyncio.run_coroutine_threadsafe(rebuildHirearchy(ctx), bot.loop)

def sanatize_markdown(string):
    return string.replace("\\","\\\\").replace("*","\\*").replace("_","\\_").replace("~","\\~").replace("`","\\`")

def getUserName(ctx, id):
    id=int(id)
    for user in guild.members:
        if user.id==id:
            #get the user nickname and username
            if user.display_name==user.name:
                name=user.name
            else:
                name=f"{user.display_name} ({user.name})"
            return sanatize_markdown(name)
    print(f"ERROR: Username with id {id} was unable to be resolved", flush=True)
    #return "This message is just here for testing. (stop looking pls)" #okay, so, cuz you were so nice to look, ill actually accept it. Hi github <3
    wrapper_buildHirearchy(ctx)
    saveUserdb()
    return "`An error occured. Please run the command again. If the issue persists, contact Aoki (@kruemmelbande)`"

def getActualUserName(id):
    if id==0 or id=="0":
        print("ERROR: Tried to get username of 0", flush=True)
        return "`Well... So, this is akward... You tried looking for a user, but you didnt specify anybody.... Please tell aoki to fix this, you should never see this message.`"
    id=int(id)
    for user in guild.members:
        if user.id==id:
            return user.name
    return f"User with id {id} not found. Either you tried to vote for somebody who is not on the server, or this is a bug. (lets be real, its probably a bug)"
users={}

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}', flush=True)
    global guild
    loadUserdb()
    guildID=config["guildID"]
    guildID=int(guildID)
    guild=discord.utils.get(bot.guilds, id=guildID)
    print(f"Guild: {guild.name}", flush=True)

@bot.slash_command(name="estop", description="Stops the bot")
async def estop(ctx):
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used estop", flush=True)
    if not isElivated(ctx):
        print(f"{ctx.author.name} tried to stop the bot without permission", flush=True)
        await ctx.respond("You do not have permission to use this command", ephemeral=True)
        return
    await ctx.respond("Stopping bot", ephemeral=True)
    await bot.close()
    exit()

@bot.slash_command(name="kickfrompack", description="Kick a user from your pack")
async def kickfrompack(ctx, user: discord.Member):
    global users
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used kickfrompack", flush=True)
    #am i a pack leader?
    if not users[str(ctx.author.id)]["isOwner"]:
        await ctx.respond("You are not a pack leader", ephemeral=True)
        return
    #is the user owned by me?
    if not users[str(user.id)]["votesFor"]==ctx.author.id:
        await ctx.respond("You do not own this user", ephemeral=True)
        return
    #remove the user from my pack
    users[str(user.id)]["isOwned"]=False
    users[str(user.id)]["votesFor"]=0
    users[str(user.id)]["isVoting"]=False
    await rebuildHirearchy(ctx)
    saveUserdb()
    await ctx.respond(f"{user.mention} has been kicked from your pack", ephemeral=True)

@bot.slash_command(name="buildhirearchy", description="This command is for internal use only.")
async def buildHirearchy(ctx):
    if not isElivated(ctx):
        await ctx.respond("You do not have permission to use this command", ephemeral=True)
        return
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used rebuildhirearchy", flush=True)
    await rebuildHirearchy(ctx)
    saveUserdb()
    await ctx.respond("Hirearchy rebuilt", ephemeral=True)
    await hirearchy(ctx)


@bot.slash_command(name="hirearchy", description="Shows the current hirearchy")
async def hirearchy(ctx):
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used hirearchy", flush=True)
    votes=getUserVotes()
    leaders=[user for user in votes if votes[user]>=2]
    singles=[user for user in votes if votes[user]==1]
    returnstring="####Pack Leaders###\n"
    for leader in leaders:
        returnstring+=getUserName(ctx,leader)+"\n"
        for user in users:
            if users[user]["votesFor"]==leader:
                returnstring+= "  -" + getUserName(ctx, user) + "\n"
        returnstring += "\n"
    returnstring+="####Single Votes###"
    for single in singles:
        for user in users:
            if users[user]["votesFor"]==single:
                returnstring+= "\n" + getUserName(ctx, user) + " => " + getUserName(ctx, users[user]["votesFor"])

    await longresponse(ctx, returnstring)
    
@bot.slash_command(name="bonkme", description="Gives you the NSFW role")
async def bonkme(ctx):
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used bonkme", flush=True)
    role=discord.utils.get(guild.roles, name="Bonk")

    if hasRole(ctx, "Anti Horny Tabs"):
        await ctx.respond("You do not have permission to use this command", ephemeral=True)
        print(f"{ctx.author.name} tried to get bonk role without permission", flush=True)
        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
        return

    
    if role in ctx.author.roles:
        await ctx.author.remove_roles(role)
        await ctx.respond("*unbonks*, no more horny for you!", ephemeral=True) #ephemeral=True means that only the user who used the command can see the response
    else:
        await ctx.author.add_roles(role)
        print(f"Added role to {ctx.author.name}", flush=True)
        await ctx.respond("*bonk*, you now have access to the bonk worthy channels", ephemeral=True) #ephemeral=True means that only the user who used the command can see the response

@bot.slash_command(name="update", description="For internal use only")
async def update(ctx):
    if not isElivated(ctx):
        print(f"{ctx.author.name} tried to update the bot without permission", flush=True)
        await ctx.respond("You do not have permission to use this command", ephemeral=True)
        return
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used update", flush=True)
    # await ctx.respond("This command is not tested yet, so at the moment, it is disabled", ephemeral=True)
    # return
    saveUserdb()
    
    os.system("rm -rf ./birb-bot")
    os.system(f"cp ./bot.py ./backups/bot.{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.py")
    os.system("git clone https://github.com/kruemmelbande/birb-bot") #move this to the config
    return 
    os.system("cp ./birb-bot/bot.py bot.py")
    await ctx.respond("The bot has been updated, and will restart...", ephemeral=True)
    asyncio.sleep(3)
    os.system("systemctl restart birbbot.service birbbot.timer")
    exit()

@bot.slash_command(name="restart", description="For internal use only")
async def restart(ctx):
    if not isElivated(ctx):
        print(f"{ctx.author.name} tried to restart the bot without permission", flush=True)
        await ctx.respond("You do not have permission to use this command", ephemeral=True)
        return
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used restart", flush=True)
    await ctx.respond("The bot will restart...", ephemeral=True)
    saveUserdb()
    asyncio.sleep(3)
    os.system("systemctl restart birbbot.service birbbot.timer")

@bot.slash_command(name="help", description="Explains how to use the bot")
async def help(ctx):
    await ctx.respond("""Available commands:```
/hirearchy - Shows the current hirearchy
/vote <user> - Vote for a user
/bonkme - Gives you the NSFW role
/kickfrompack <user> - Kick a user from your pack
```
Commands are usable in any channels. Your message will only be visible to you.
Only the listed commands are available, and all other commands are for internal use only (you couldnt use them even if you wanted to).

You can vote for a user, and once 2-5 people vote for the same user, a pack will be created for them.
All avalis in a pack will get the "Pack Avali" role, and the pack leader will get the "Pack Leader" role.
Those roles will give you additional rights in the server.

You can only vote for an avali, if you and the avali are not in a pack yet.
If you would like to remove your vote, vote for yourself.

If you are a pack leader and wish to kick a user from your pack, use /kickfrompack <user>

You can show who votes for who, and which packs exist with /hirearchy (all votes are public)

For issues or questions, contact Aoki (@kruemmelbande), or open an issue on the <[github page](https://github.com/kruemmelbande/birb-bot/issues)>
```
Birb Bot Version: """+version+"""
Uptime: """ + str(datetime.timedelta(seconds=time.time()-starttime))+"""
```""", ephemeral=True)

@bot.slash_command(name="usersettings", description="Change your user settings")
async def usersettings(ctx, setting: discord.Option(str, choices=["LeaderConsent","removeVote"])):
    global users
    if setting=="LeaderConsent":
        print(f"[{datetime.datetime.now()}] {ctx.author.name} used consentleader", flush=True)
        if users[str(ctx.author.id)]["consentLeader"]==True:
            users[str(ctx.author.id)]["consentLeader"]=False
            await ctx.respond("You are not votable anymore", ephemeral=True)
        else:
            users[str(ctx.author.id)]["consentLeader"]=True
            await ctx.respond("You are now votable", ephemeral=True)
        await rebuildHirearchy(ctx)
        saveUserdb()
    elif setting=="removeVote":
        print(f"[{datetime.datetime.now()}] {ctx.author.name} used removevote", flush=True)
        if users[str(ctx.author.id)]["isVoting"]==True:
            users[str(ctx.author.id)]["isVoting"]=False
            users[str(ctx.author.id)]["votesFor"]=0
            await ctx.respond("Your vote has been removed", ephemeral=True)
        else:
            await ctx.respond("You are not voting for anyone", ephemeral=True)
        await rebuildHirearchy(ctx)
        saveUserdb()
    else:
        await ctx.respond("Unknown setting", ephemeral=True)
        return

@bot.slash_command(name="vote", description="Vote for a user")
async def vote(ctx, user: discord.Member):
    global users
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used vote", flush=True)
    
    #check if user is in database
    returnstring=""
    for usera in guild.members:
        if user.id == usera.id:
            targetUser=usera
            print("User found", flush=True)
            break
    else:
        #print(user.id, flush=True)
        #print([user.id for user in guild.members], flush=True) 
        await ctx.respond(f"User {user.id} not found", ephemeral=True)
        return
    if targetUser.bot:
        await ctx.respond("You cannot vote for a bot", ephemeral=True)
        return
    if not users[str(targetUser.id)]["consentLeader"]:
        await ctx.respond("This user has chosen to not be a pack leader", ephemeral=True)
        return
    if not str(targetUser.id) in users:
        print(f"User {targetUser.id} not in database", flush=True)
        #print([i for i in users], flush=True)
        #print(targetUser.id, flush=True)
        newUser=userTemplate.copy()
        users[str(targetUser.id)]=newUser
        saveUserdb()
        print("User added to database", flush=True)
    votes=getUserVotes()
    if users[str(targetUser.id)]["isOwned"]==True:
        returnstring="You cannot vote for a user who is already in a pack."
        if votes[users[str(targetUser.id)]["votesFor"]]<5:
            print(f"VERBOSE: Target user: {targetUser.id} - Target pack leader: {users[str(targetUser.id)]['votesFor']} what is happening? {users[str(targetUser.id)]}", flush=True)
            returnstring+=f" The pack this user belongs to however, has a slot available. To join use /vote {getActualUserName(users[str(targetUser.id)]['votesFor'])}"
        await ctx.respond(returnstring, ephemeral=True)
        return
    voter=ctx.author
    votee=targetUser
    if not str(voter.id) in users:
        users[str(voter.id)]=userTemplate.copy()
        print("Voter not in database", flush=True)
        saveUserdb()

    if users[str(votee.id)]["isOwned"]==True:
        returnstring="You cannot vote for a user who is owned by another user"
        await ctx.respond(returnstring, ephemeral=True)
        return
    if users[str(voter.id)]["isOwner"]==True:
        returnstring="You cannot vote for another user, while you own a user yet."
        await ctx.respond(returnstring, ephemeral=True)
        return
    
    #check if the person that gets voted is already at the vote limit
    if votes[votee.id]>=5:
        await ctx.respond(f"{ctx.author.mention}, {targetUser.mention} already has the maximum amount of votes", ephemeral=True)
        return
    #check if the user votes for themselves
    if voter.id==votee.id:
        await ctx.respond(f"{ctx.author.mention}, you cannot vote for yourself. Your current vote will be removed", ephemeral=True)
        users[str(voter.id)]["isVoting"]=False
        users[str(voter.id)]["votesFor"]=0
        return
    if users[str(voter.id)]["isVoting"]==True and users[str(voter.id)]["votesFor"]!=0:
        returnstring="Vote changed from "+str(discord.utils.get(guild.members, id=users[str(voter.id)]["votesFor"]).mention)+" to "+str(targetUser.mention)
        users[str(voter.id)]["votesFor"]=targetUser.id
        users[str(voter.id)]["isVoting"]=True
    else:
        saveUserdb()
        returnstring="Vote registered for "+str(targetUser.mention)
        users[str(voter.id)]["isVoting"]=True
        saveUserdb()
        users[str(voter.id)]["votesFor"]=targetUser.id
        #print(voter, flush=True)
        #print(voter.id, flush=True)
    saveUserdb()
    print("Rebuilding hirearchy", flush=True)
    await rebuildHirearchy(ctx)
    saveUserdb()
    await ctx.respond(returnstring, ephemeral=True)
    return



@bot.slash_command(name="tests", description="My internal testing command, here for everyone to see, cuz i aint using a debugger")
async def tests(ctx, string: str):
    if not isElivated(ctx):
        await ctx.respond("You do not have permission to use this command", ephemeral=True)
        return
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used tests", flush=True)
    if string=="exceptions":
        await ctx.respond("Testing exceptions", ephemeral=True)
        raise Exception("Test exception")
        print("Exception raised", flush=True)
        await ctx.respond("An exception has been raised", ephemeral=True)
        return
    elif string=="longmessage":
        longstring="".join([f"This is a really long message! {i}\n" for i in range(100)])
        await longresponse(ctx, longstring)
    else:
        await ctx.respond("Unknown test", ephemeral=True)
        return

 
# @bot.slash_command(name="test", description="Test command")
# async def test(ctx, inputstring: str):
#     print(inputstring)
#     await ctx.respond(f"Test {ctx.author.mention}, you said: {inputstring}")
#     #get back the message, that the user sent
time.sleep(5)

starttime=time.time()
bot.run(token)