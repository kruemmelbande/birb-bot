import discord, json
from discord import default_permissions
from sys import exit

intents=discord.Intents.all()
bot = discord.Bot(intents=intents)


intents.members = True
class user:
    def __init__(self, userID):
        self.votesfor=[]
        self.owns=[]
        self.userID=userID
    def isOwnedBy(self, userID):
        return userID in self.owns
    def isVotedBy(self, userID):
        return userID in self.votesfor
    def addVote(self, userID):
        self.votesfor.append(userID)
    def getUserID(self):
        return self.userID
    def addSubuser(self, userID):
        self.owns.append(userID)
 
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

# @bot.slash_command(name="test", description="Test command")
# async def test(ctx, inputstring: str):
#     print(inputstring)
#     await ctx.respond(f"Test {ctx.author.mention}, you said: {inputstring}")
#     #get back the message, that the user sent
    
bot.run(token)