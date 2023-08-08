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

#just do a hello world as a /command
#to set the command, that the bot should listen to, use the decorator
@discord.slash_command(guild_ids=[config["guildID"]],description="Test command2")
@default_permissions(manage_messages=True)
async def hello(ctx):
    await ctx.send("Hello World!")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command(name="test", description="Test command")
async def test(ctx):
    await ctx.respond(f"Test {ctx.author.mention}")
    #get back the message, that the user sent
    
bot.run(token)