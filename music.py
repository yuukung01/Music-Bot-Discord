import asyncio
import youtube_dl
import pafy
import discord
from discord.ext import commands

class Player(commands.Cog) :
  def __init__(self, bot):
    self.bot = bot
    self.song_queue = {}

    self.setup()

  def setup(self):
    for guild in self.bot.guilds:
      self.song_queue[guild.id] = []

  async def check_queue(self, ctx):
    if len(self.song_queue[ctx.guild.id]) > 0:
      ctx.voice_client.stop()
      await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
      self.song_queue[ctx.guild.id].pop(0)

  async def search_song(self, amount, song, get_url=False):
    info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format": "bestaudio", "quiet": True}).extract_info(f"ytsearch{amount}:{song}",download=False, ie_key="YoutubeSearch"))
    if len(info["entries"]) == 0: return None

    return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

  async def play_song(self, ctx, song):
    url = pafy.new(song).getbestaudio().url
    ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
    ctx.voice_client.source.volume = 0.5

    @commands.command()
    async def join(self,ctx):
      if ctx.author.voice is None:
        return await ctx.send("คุณไม่ได้อยู่ในห้องดิสคอร์ด กรุณาเลือกห้องที่ต้องการถ้าคุณต้องการบอท WS")

      if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()

      await ctx.author.voice.channel.connect()

    @commands.command()
    async def leave(self,ctx):
      if ctx.voice_client is not None:
        return await ctx.voice_client.disconnect()

      await ctx.author.voice.channel.connect("บอท WS ไม่สามารถเชื่อมต่อแชแบลนี้ได้")

    @commands.command()
    async def play(self, ctx, *, song=None):
      if song is None:
        return await ctx.send("คุณสามารถนำเพลงมาใส่ได้เลย")

      if ctx.voice_client is None:
        return await ctx.send("บอท WS กำลังเล่นเพลง")

      #ถ้าเพลงไม่ใช่ url
      if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
        await ctx.send("กำลังค้นหาเพลง รอสักครู่")

        result = await self.search_song(1, song, get_url=True)
        
        if result is None:
          return await ctx.send("ขอโทษด้วย บอท WS ได้พยายามหาเพลงที่คุณให้มาไม่พบ")
        
        song = result[0]

      if ctx.voice_client.source is not None:
        queue_len = len(self.song_queue[ctx.guild.id])

        if queue_len < 100:
          self.song_queue[ctx.guild.id].append(song)
          return await ctx.send(f"บอท WS กำลังเล่นเพลงอยู่ เพลงที่เพิ่มเข้ามาจะเข้าไปอยู่ในรายการ: {queue_len+1}.")

        else:
          return await ctx.send("ขอโทษด้วย บอท WS สามารถรับรายการเพลงได้สูงสุด 100 เพลง รบกวนรอเพลงอื่นจบ")

      await self.play_song(ctx, song)
      await ctx.send(f"ตอนนี้กำลังเล่น: {song}")

    @commands.command()
    async def search(self, ctx, *, song=None):
      if song is None: return await ctx.send("คุณลืมใส่สิ่งที่คุณจะฟัง")

      await ctx.send("กำลังค้นหาเพลง รอสักครู่")

      info = await self.search_song(5, song)

      embed = discord.Embed(title=f"Results for '{song}':", description="*คุณสามารถใช้เป็น Url เพื่อสั่งเล่นเพลงได้นอกจากบอกชื่อ")

      amount = 0
      for entry in info["entries"]:
        embed.description += f"[{entry['title']}]({entry['webpage_ur;']})\n"
        amount += 1

      embed.set_footer(text=f"แสดงครั้งแรกผลลัพธ์ {amount}")
      await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx):
      if len(self.song_queue[ctx.guild.id]) == 0:
        return await ctx.send("ไม่มีเพลงเหลืออยู่ในรายการ")

      embed = discord.Embed(title="รายการเพลง", description="", colour=discord.colour.dark_gold())
      i = 1
      for url in self.song_queue[ctx.guild.id]:
        embed.description += f"{i}) {url}\n"

        i += 1

      embed.set_footer(text="ขอบคุณที่เรียกใช้งาน!")
      await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
      if ctx.voice_client is None:
        return await ctx.send("บอท WS ไม่ได้เปิดเพลงอยู่")

      if ctx.author.voice is None:
        return await ctx.send("คุณไม่ได้อยู่ในห้องดิสคอร์ด")

      if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
         return await ctx.send("บอท WS ไม่ได้เปิดเพลงให้คุณอยู่ตอนนี้")

      poll = discord.Embed(title=f"**โหวตเพื่อข้ามเพลง โดย - {ctx.author.name}#{ctx.authordiscriminator}",description="**80% ของในห้องนี้ โหวตข้าม**", colour=discord.Colour.blue())
      poll.add_field(name="ข้าม", value=":white_check_mark:")
      poll.add_field(name="ไม่ข้าม", value=":no_entry_sign:")
      poll.set_footer(name="การโหวตจะหมดเวลาใน 15 วินาที")

      poll_msg = await ctx.send(embed=poll)
      poll_id = poll_msg.id

      await poll_msg.add_reaction(u"\u2705") #ใช่
      await poll_msg.add_reaction(u"\U0001F6AB") #ไม่ใช่

      await asyncio.sleep(15) #โหวต 15 วินาที

      poll_msg = await ctx.channel.fetch_message(poll_id)

      votes = {u"\u2705": 0, u"\U0001F6AB": 0}
      reacted = []

      for reaction in poll_msg.reaction:
        if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
          async for user in reaction.users():
            if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot: 
              votes[reaction.emoji] += 1

              reacted.append(user.id)

      skip = False

      if votes[u"\u2705"] > 0:
        if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79: #80% หรือ สูงกว่า
          skip = True
          embed = discord.Embed(title="ทำการข้ามเรียบร้อย", description="***ทำการโหวตข้ามเรียบร้อย ทำการข้ามทันที***", colour="")

      if not skip:
        embed = discord.Embed(title="ทำการข้ามไม่สำเร็จ", description="***ทำการโหวตข้ามไม่สำเร็จ *\n\n ผลการโหวตข้ามไม่ถึง 80%***", colour="") 

      embed.set_footer(text="การโหวตได้สิ้นสุดแล้ว")  

      await poll_msg.clear_reactions()
      await poll_msg.edit(embed=embed)

      if skip:
        ctx.voice_client.stop()
        await self.check_queue(ctx)