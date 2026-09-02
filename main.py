import discord
from discord.ext import commands, tasks
import datetime
import os
import feedparser  
import aiohttp    

class Jasmine(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.bans = True
        super().__init__(command_prefix='!', intents=intents)
        
      
        self.last_youtube_link = None
        self.was_twitch_live = False
        self.last_tiktok_link = None
        
       
        self.greeted_users = set()

    async def setup_hook(self):
     
        self.check_platforms.start()

    async def on_ready(self):
        print(f"Jasmine sikeresen bejelentkezett mint {self.user} ✨")

   
    async def on_message(self, message):
   
        if message.author.bot:
            return

        content_lower = message.content.lower()

      
        if "sziasztok" in content_lower:
            if message.author.id not in self.greeted_users:
                self.greeted_users.add(message.author.id)
                await message.channel.send(f"Szia {message.author.mention}! 🌸")

     
        owner_keywords = ["ki itt a tulaj", "ki a tulaj", "ki a tulajdonos", "ki csinálta a szervert", "ki a fönök", "ki a szerver tulajdonosa"]
        if any(keyword in content_lower for keyword in owner_keywords):
            
            cassidy_id = 1047920915641548921 
            await message.channel.send(f"<@{cassidy_id}> a tulaj ✨")

      
        await self.process_commands(message)

    
    @tasks.loop(minutes=5)
    async def check_platforms(self):
        await self.check_youtube()
        await self.check_tiktok()

    @check_platforms.before_loop
    async def before_check_platforms(self):
        await self.wait_until_ready()


    async def check_youtube(self):
        channel_id = "UCcKLZHpGu8yp8nQi17lwmmg" 
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                latest = feed.entries[0]
                if self.last_youtube_link is None:
                    self.last_youtube_link = latest.link
                elif latest.link != self.last_youtube_link:
                    self.last_youtube_link = latest.link
                    
                    
                    video_id = ""
                    if "watch?v=" in latest.link:
                        video_id = latest.link.split("watch?v=")[1].split("&")[0]
                    elif "/shorts/" in latest.link:
                        video_id = latest.link.split("/shorts/")[1].split("?")[0]

                    channel = self.get_channel(1497351931360841820) 
                    if channel:
                        embed = discord.Embed(
                            title="🔴 Új YouTube Videó érkezett!",
                            description=f"**{latest.title}**\n\nÚj tartalom került ki a csatornámra, lessétek meg bátran! ✨\n\n👉 **Nézzétek meg itt:** {latest.link}",
                            color=discord.Color.red()
                        )
                       
                        if video_id:
                            embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")

                        embed.set_footer(text="Jasmine értesítője 🌸")
                        await channel.send(content="Sziasztok @everyone! Új YouTube videó van! 🎬", embed=embed)
        except Exception as e:
            print(f"Hiba a YouTube ellenőrzésekor: {e}")

   
    async def check_tiktok(self):
        tiktok_rss = "https://www.tiktok.com/@masked_sparkle/rss" 
        try:
            feed = feedparser.parse(tiktok_rss)
            if feed.entries:
                latest = feed.entries[0]
                if self.last_tiktok_link is None:
                    self.last_tiktok_link = latest.link
                elif latest.link != self.last_tiktok_link:
                    self.last_tiktok_link = latest.link
                    
                    channel = self.get_channel(1510603200284328037) 
                    if channel:
                        embed = discord.Embed(
                            title="📱 Új TikTok Tartalom!",
                            description=f"**{latest.title}**\n\nÚj videót toltam ki TikTokra! Csekkoljátok le! 💖\n\n👉 **Itt éritek el:** {latest.link}",
                            color=discord.Color.dark_embed()
                        )
                        embed.set_footer(text="Jasmine értesítője ✨")
                        await channel.send(content="Sziasztok @everyone! Új TikTok tartalom érkezett! 🎶", embed=embed)
        except Exception as e:
            pass 

    async def on_member_join(self, member):
        is_banned = False
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target and entry.target.id == member.id:
                    is_banned = True
                    break
        except discord.Forbidden:
            pass
        
        if not is_banned:
            try:
                bans = [ban_entry.user.id async for ban_entry in member.guild.bans()]
                if member.id in bans:
                    is_banned = True
            except (discord.Forbidden, discord.HTTPException):
                pass

        if is_banned:
            try:
                ban_embed = discord.Embed(
                    title="🚫 Sajnálom, de nem tudsz belépni!",
                    description="Szia! Bocsi, de te nem fogsz tudni bejönni a szerverre, ugyanis téged bannoltak nem átalam én csak egy üdvözlö bot vagyok aki ki bannolt volna az vagy a hugom kamila vagy egy staff/Tulajdonos ugy tudsz vissza jönni ha tulajdonos vagy staff unbanol téged 🌸",
                    color=discord.Color.red()
                )
                await member.send(embed=ban_embed)
            except discord.Forbidden:
                pass
            return

        channel = self.get_channel(1539791346880221196) 
        if channel:
            member_count = member.guild.member_count
            join_date = member.joined_at.strftime("%Y-%m-%d - %H:%M") if member.joined_at else "Ismeretlen"
            
            embed = discord.Embed(
                title="🌸 Új csillag érkezett a Never SMP-re! 🌸",
                description=f"Szia {member.mention}! De örülök, hogy megérkeztél! ✨\nLégy nagyon boldog nálunk! 🐾",
                color=discord.Color.pink()
            )
            embed.add_field(name="Túlélő ID", value=f"`{member.id}`", inline=False)
            embed.add_field(name="Csatlakozás ideje", value=f"{join_date}", inline=True)
            embed.add_field(name="Túlélők száma", value=f"{member_count}. tag vagy! 💖", inline=True)
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Jasmine, a szerver tündérkéje ✨")
            await channel.send(embed=embed)

        try:    
            dm_embed = discord.Embed(
                title="💌 Szia kedves Túlélő!",
                description="Örülök, hogy csatlakoztál a **Never SMP**-hez. Érezd nagyon jól magad nálunk! 🌸✨",
                color=discord.Color.pink()
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    async def on_member_remove(self, member):
        channel = self.get_channel(1539791383815258172) 
        if channel:
            new_member_count = member.guild.member_count - 1

            embed = discord.Embed(
                title="🥀 Egy túlélő elhagyott minket...",
                description=f"Jaj, **{member.name}** útra kelt... Nagyon fog hiányozni a Never SMP világából! 💔",
                color=discord.Color.dark_gray()
            )
            embed.add_field(name="Jelenlegi túlélők", value=f"Már csak **{new_member_count}**-en maradtunk a szerveren. 🥺", inline=False)
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Jasmine, a szerver tündérkéje 🌸")
            await channel.send(embed=embed)

    # --- KÉZI PARANCSOK ---
    @commands.command(name="stream")
    @commands.has_permissions(administrator=True)
    async def stream_alert(self, ctx, *, link: str = "https://www.twitch.tv/maskedsparkle"):
        channel = self.get_channel(1497351886360023048)
        if channel:
            embed = discord.Embed(
                title="🟣 Új Twitch Élőadás!",
                description=f"Hahó mindenki! Élőbe mentem a Twitchen, gyertek minél többen! 💖\n\n👉 **Kattints ide a nézéshez:** {link}",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Jasmine értesítője ✨")
            await channel.send(content="Helló @everyone! Élő adás van! 🔔", embed=embed)
        await ctx.message.delete()

    @commands.command(name="video")
    @commands.has_permissions(administrator=True)
    async def video_alert(self, ctx, *, link: str = "https://www.youtube.com/@Sparkle_fix"):
        channel = self.get_channel(1497351931360841820)
        if channel:
            embed = discord.Embed(
                title="🔴 Új YouTube Videó érkezett!",
                description=f"Új tartalom került ki a csatornámra, lessétek meg bátran! ✨\n\n👉 **Nézzétek meg itt:** {link}",
                color=discord.Color.red()
            )
            
            if "watch?v=" in link:
                v_id = link.split("watch?v=")[1].split("&")[0]
                embed.set_image(url=f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg")
            elif "/shorts/" in link:
                v_id = link.split("/shorts/")[1].split("?")[0]
                embed.set_image(url=f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg")

            embed.set_footer(text="Jasmine értesítője 🌸")
            await channel.send(content="Sziasztok @everyone! Új YouTube videó van! 🎬", embed=embed)
        await ctx.message.delete()

    @commands.command(name="tiktok")
    @commands.has_permissions(administrator=True)
    async def tiktok_alert(self, ctx, *, link: str = "https://www.tiktok.com/@masked_sparkle"):
        channel = self.get_channel(1510603200284328037)
        if channel:
            embed = discord.Embed(
                title="📱 Új TikTok Tartalom!",
                description=f"Új videót vagy live-ot toltam ki TikTokra! Csekkoljátok le! 💖\n\n👉 **Itt éritek el:** {link}",
                color=discord.Color.dark_embed()
            )
            embed.set_footer(text="Jasmine értesítője ✨")
            await channel.send(content="Sziasztok @everyone! Új TikTok tartalom érkezett! 🎶", embed=embed)
        await ctx.message.delete()

if __name__ == "__main__":
    token = os.getenv("JASMINE_TOKEN") 
    bot = Jasmine()
    bot.run(token)
