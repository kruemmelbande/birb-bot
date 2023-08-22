import discord, json
from discord import default_permissions
from sys import exit
import datetime
import asyncio
intents=discord.Intents.all()
bot = discord.Bot(intents=intents)


intents.members = True
userTemplate={
    "id":0,
    "votesFor":0,
    "isVoting":False,
    "isOwned":False,
    "isOwner":False
}
 
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
        
        if not users[user]["id"] in votes:
            votes[users[user]["id"]]=0
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
    for user in ctx.guild.members:
        if not str(user.id) in users:
            newUser=userTemplate.copy()
            newUser["id"]=user.id
            users[str(user.id)]=newUser
            print(f"Added {user.name} to database", flush=True)
    saveUserdb()
    now=datetime.datetime.now()
    print(f"[{now}] Rebuilding hirearchy because of {ctx.author.name}", flush=True)
    votes=getUserVotes()
    for user in users:
        currentUser=discord.utils.get(ctx.guild.members, id=users[user]["id"])
        userRoles=[role.name for role in currentUser.roles]
        print(f"VERBOSE Checking {currentUser.name} with roles {userRoles}, flush=True")
        if votes[users[user]["id"]]>=2:
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
                await currentUser.add_roles(discord.utils.get(ctx.guild.roles, name="Pack Leader"))
                print(f"Added role to {currentUser.name}", flush=True)
            for userb in users:
                if users[userb]["votesFor"]==users[user]["id"]:
                    users[userb]["isOwned"]=True
                    users[userb]["owner"]=users[user]["id"]
        else:
            #user is not a pack leader
            #check if they have the role
            if "Pack Leader" in userRoles:
                await ctx.author.remove_roles(discord.utils.get(ctx.guild.roles, name="Pack Leader"))
                print(f"Removed role from {currentUser.name}", flush=True)
                for userb in users:
                    if users[userb]["owner"]==users[user]["id"]:
                        users[userb]["isOwned"]=False
                        users[userb]["owner"]=0
        if users[user]["isOwned"] or users[user]["isOwner"]:
            if not "Pack Avali" in userRoles:
                await currentUser.add_roles(discord.utils.get(ctx.guild.roles, name="Pack Avali"))
                print(f"Added Pack Avali to {currentUser.name}", flush=True)
        else:
            if "Pack Avali" in userRoles:
                await currentUser.remove_roles(discord.utils.get(ctx.guild.roles, name="Pack Avali"))
                print(f"Removed Pack Avali from {currentUser.name}", flush=True)
                
    saveUserdb()
def getUserName(ctx, id):
    for user in ctx.guild.members:
        if user.id==id:
            #get the user nickname and username
            if user.display_name==user.name:
                return user.name
            return f"{user.display_name} ({user.name})"
    return "User not found"
        
users={}
def loadUserdb():
    global users
    try:
        with open("userdb.json","r") as f:
            users=json.load(f)
    except Exception as e:
        print("Unable to load userdb", flush=True)
        print(e, flush=True)
        exit()
    return users

def saveUserdb():
    global users
    try:
        with open("userdb.json","w") as f:
            json.dump(users,f,indent=4)
            print(f"[{datetime.datetime.now()}] Saved userdb", flush=True)
    except Exception as e:
        print("Unable to save userdb", flush=True)
        print(e, flush=True)
        exit()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}', flush=True)
    loadUserdb()

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
        returnstring+=discord.utils.get(ctx.guild.members, id=leader).name+"\n"
        for user in users:
            if users[user]["votesFor"]==leader:
                returnstring+= "  -" + getUserName(ctx, users[user]["id"]) + "\n"
        returnstring += "\n"
    returnstring+="####Single Votes###"
    for single in singles:
        for user in users:
            if users[user]["votesFor"]==single:
                returnstring+= "\n" + getUserName(ctx, users[user]["id"]) + " => " + getUserName(ctx, users[user]["votesFor"])

    await ctx.respond(returnstring, ephemeral=True)
    
@bot.slash_command(name="bonkme", description="Gives you the NSFW role")
async def bonkme(ctx):
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used bonkme", flush=True)
    role=discord.utils.get(ctx.guild.roles, name="Bonk")

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

@bot.slash_command(name="vote", description="Vote for a user")
async def vote(ctx, user: discord.Member):
    global users
    print(f"[{datetime.datetime.now()}] {ctx.author.name} used vote", flush=True)
    votes=getUserVotes()
    #check if user is in database
    returnstring=""
    for usera in ctx.guild.members:
        if user.id == usera.id:
            targetUser=usera
            print("User found", flush=True)
            break
    else:
        print(user.id, flush=True)
        print([user.id for user in ctx.guild.members], flush=True) 
        await ctx.respond("User not found", ephemeral=True)
        return
    if not str(targetUser.id) in users:
        print("User not in database", flush=True)
        print([i for i in users], flush=True)
        print(targetUser.id, flush=True)
        newUser=userTemplate.copy()
        newUser["id"]=targetUser.id
        users[str(targetUser.id)]=newUser
        saveUserdb()
    if users[str(targetUser.id)]["isOwned"]==True:
        returnstring="You cannot vote for a user who is owned by another user"
        await ctx.respond(returnstring, ephemeral=True)
        return
    voter=ctx.author
    votee=targetUser
    if not str(voter.id) in users:
        users[str(voter.id)]=userTemplate.copy()
        users[str(voter.id)]["id"]=voter.id
        print("Voter not in database", flush=True)
        saveUserdb()
    votes=getUserVotes()
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
    if users[str(voter.id)]["isVoting"]==True:
        returnstring="Vote changed from "+str(discord.utils.get(ctx.guild.members, id=users[str(voter.id)]["votesFor"]).mention)+" to "+str(targetUser.mention)
        users[str(voter.id)]["votesFor"]=targetUser.id
    else:
        saveUserdb()
        returnstring="Vote registered for "+str(targetUser.mention)
        users[str(voter.id)]["isVoting"]=True
        saveUserdb()
        users[str(voter.id)]["votesFor"]=targetUser.id
        print(voter, flush=True)
        print(voter.id, flush=True)
    saveUserdb()
    print("Rebuilding hirearchy", flush=True)
    await rebuildHirearchy(ctx)
    saveUserdb()
    await ctx.respond(returnstring, ephemeral=True)
    return
    
# @bot.slash_command(name="test", description="Test command")
# async def test(ctx, inputstring: str):
#     print(inputstring)
#     await ctx.respond(f"Test {ctx.author.mention}, you said: {inputstring}")
#     #get back the message, that the user sent
    
bot.run(token)