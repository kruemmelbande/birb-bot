import discord, json
from discord import default_permissions
from sys import exit

intents=discord.Intents.all()
bot = discord.Bot(intents=intents)


intents.members = True
userTemplate={
    "id":0,
    "votesFor":0,
    "isVoting":False,
    "isOwned":False,
    "owner":0
}
 
try:
    #load config
    with open("config.json","r") as f:
        config=json.load(f)
except Exception as e:
    print("Unable to load config")
    print(e)
    exit()
try:
    #parse config
    token=config["token"]
except Exception as e:
    print("Error while parsing config")
    print(e)
    exit
    
def getUserVotes():
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
    return votes

async def rebuildHirearchy(ctx):
    global users
    votes=getUserVotes()
    print("votes: ", votes)
    print("users: ", users)
    for user in users:
        #if a user has more than 2 votes, they become a pack leader, and everybody who voted for them becomes owned by them.
        #no more than 5 users can join a pack
        currentUser=discord.utils.get(ctx.guild.members, id=users[user]["id"])
        userRoles=[role.name for role in currentUser.roles]
        print(f"Checking {currentUser.name} with roles {userRoles}")
        if "Bot Override" in userRoles:
            print("User is a bot override, skipping")
            continue
        print(f"User has {votes[currentUser.id]} votes")
        if votes[currentUser.id]>2:
            #user is a pack leader
            #check if they already have the role
            if not "Pack Leader" in userRoles:
                await currentUser.add_roles(discord.utils.get(ctx.guild.roles, name="Pack Leader"))
                print(f"Added role to {currentUser.name}")
            for userb in users:
                if users[userb]["votesFor"]==users[user]["id"]:
                    users[userb]["isOwned"]=True
                    users[userb]["owner"]=users[user]["id"]
        else:
            #user is not a pack leader
            #check if they have the role
            if "Pack Leader" in userRoles:
                await ctx.author.remove_roles(discord.utils.get(ctx.guild.roles, name="Pack Leader"))
                print(f"Removed role from {currentUser.name}")
                for userb in users:
                    if users[userb]["owner"]==users[user]["id"]:
                        users[userb]["isOwned"]=False
                        users[userb]["owner"]=0
        
users={}
def loadUserdb():
    global users
    try:
        with open("userdb.json","r") as f:
            users=json.load(f)
    except Exception as e:
        print("Unable to load userdb")
        print(e)
        exit()
    return users

def saveUserdb():
    global users
    try:
        with open("userdb.json","w") as f:
            json.dump(users,f,indent=4)
            print("Saved userdb")
    except Exception as e:
        print("Unable to save userdb")
        print(e)
        exit()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    loadUserdb()

# @bot.slash_command(name="testcommand", description="This command is ONLY FOR TESTING. DO NOT USE THIS, OR YOU WILL BE BANNED.")
# async def ifyouusethisiwillbanyouthisisforadmins(ctx):
#     await rebuildHirearchy(ctx)
#     await ctx.respond("Rebuilt hirearchy", ephemeral=True)
#     return

@bot.slash_command(name="bonkme", description="Gives you the NSFW role")
async def bonkme(ctx):
    role=discord.utils.get(ctx.guild.roles, name="Bonk")

    if role in ctx.author.roles:
        await ctx.author.remove_roles(role)
        await ctx.respond("*unbonks*, no more horny for you!", ephemeral=True) #ephemeral=True means that only the user who used the command can see the response
    else:
        await ctx.author.add_roles(role)
        print(f"Added role to {ctx.author.name}")
        await ctx.respond("*bonk*, you now have access to the bonk worthy channels", ephemeral=True) #ephemeral=True means that only the user who used the command can see the response

@bot.slash_command(name="vote", description="Vote for a user")
async def vote(ctx, user: discord.Member):
    global users
    #check if user is in database
    returnstring=""
    votes=getUserVotes()
    for usera in ctx.guild.members:
        if user.id == usera.id:
            targetUser=usera
            print("User found")
            break
    else:
        print(user.id)
        print([user.id for user in ctx.guild.members]) 
        await ctx.respond("User not found", ephemeral=True)
        return
    if not str(targetUser.id) in users:
        print("User not in database")
        print([i for i in users])
        print(targetUser.id)
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
        print("Voter not in database")
        saveUserdb()
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
        print(voter)
        print(voter.id)
    saveUserdb()
    print("Rebuilding hirearchy")
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