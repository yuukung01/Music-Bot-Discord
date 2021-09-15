import discord
from discord.ext import commands 
from music import Player

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
  print(f"{bot.user.name} พร้อมใช้งานแล้ว")

bot.run("ODg3NDE3MDM5MTc2NzYxNDA1.YUD1hQ.u0B3Rhlcn33PCOfxHkW9wh4XEuw")