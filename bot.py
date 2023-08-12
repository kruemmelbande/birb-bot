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
def getUserVotes(user):
    votes={}
    for user in users:
        if users[user]["votesFor"] in votes:
            votes[users[user]["votesFor"]]+=1
        else:
            votes[users[user]["votesFor"]]=1
    return votes

def rebuildHirearchy(ctx):
    votes=getUserVotes(users)
    for user in users:
        #if a user has more than 2 votes, they become a pack leader, and everybody who voted for them becomes owned by them.
        #no more than 5 users can join a pack
        currentUser=discord.utils.get(ctx.guild.members, id=users[user]["id"])
        if discord.utils.get(ctx.guild.roles, name="Bot Override") in currentUser.roles:
            #bot override role is present, we dont do anything
            continue
        if votes[users[user]["id"]]>2:
            #user is a pack leader
            #check if they already have the role
            role=discord.utils.get(ctx.guild.roles, name="Pack Leader")

            if role not in ctx.author.roles:
                ctx.author.add_roles(role)
            for userb in users:
                if users[userb]["votesFor"]==users[user]["id"]:
                    users[userb]["isOwned"]=True
                    users[userb]["owner"]=users[user]["id"]
        else:
            #user is not a pack leader
            #check if they have the role
            role=discord.utils.get(ctx.guild.roles, name="Pack Leader")
            if role in ctx.author.roles:
                ctx.author.remove_roles(role)
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
            json.dump(users,f)
    except Exception as e:
        print("Unable to save userdb")
        print(e)
        exit()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

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
    #check if user is in database
    returnstring=""
    if str(user.id) not in ctx.guild.members:
        returnstring="User not found"
        ctx.respond(returnstring, ephemeral=True)
        return
    if str(user.id) not in users:
        users[str(user.id)]=userTemplate
        users[str(user.id)]["id"]=user.id
    if users[str(user.id)]["isOwned"]==True:
        returnstring="You cannot vote for a user who is owned by another user"
        ctx.respond(returnstring, ephemeral=True)
        return
    voter=ctx.author
    votee=user
    #check if the person that gets voted is already at the vote limit
    if users[str(user.id)]["votesFor"]>=5:
        await ctx.respond(f"{ctx.author.mention}, {user.mention} already has the maximum amount of votes", ephemeral=True)
        return
    #check if the user votes for themselves
    if voter.id==votee.id:
        await ctx.respond(f"{ctx.author.mention}, you cannot vote for yourself", ephemeral=True)
        return
    if users[str(voter.id)]["isVoting"]==True:
        returnstring="Vote changed from "+str(discord.utils.get(ctx.guild.members, id=users[str(voter.id)]["votesFor"]).mention)+" to "+str(user.mention)
        users[str(voter.id)]["votesFor"]=user.id
    else:
        returnstring="Vote registered for "+str(user.mention)
        users[str(voter.id)]["isVoting"]=True
        users[str(voter.id)]["votesFor"]=user.id
    rebuildHirearchy(ctx)
    saveUserdb()
    await ctx.respond(returnstring, ephemeral=True)
    
# @bot.slash_command(name="test", description="Test command")
# async def test(ctx, inputstring: str):
#     print(inputstring)
#     await ctx.respond(f"Test {ctx.author.mention}, you said: {inputstring}")
#     #get back the message, that the user sent
    
bot.run(token)