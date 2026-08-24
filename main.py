import discord
from discord.ext import commands
import datetime
import os

class Jasmine(commands.Bot):
def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.bans = True  # <--- ÍGY HELYES: intents.bans
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        print(f"Jasmine sikeresen bejelentkezett mint {self.user} ✨")

    async def on_member_join(self, member):
        is_banned = False
        
        # 1. Ellenőrizzük, hogy ki van-e tiltva (bannolva)
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

        # Ha ki van bannolva, Jasmine elküldi a DM-et, és megállítjuk a folyamatot
        if is_banned:
            try:
                ban_embed = discord.Embed(
                    title="🚫 Sajnálom, de nem tudsz belépni!",
                    description=f"Szia! Bocsi, de te nem fogsz tudni bejönni a szerverre, ugyanis téged bannoltak. Vagy a hugom, Kamila bannolt, vagy valamelyik staff, esetleg a tulajdonos.\n\nHa a tulaj úgy gondolja, akkor unbannol téged, de én nem tudlak, mert én csak egy bot vagyok, semmi más! 🌸",
                    color=discord.Color.red()
                )
                ban_embed.set_footer(text="Jasmine, a szerver tündérkéje ✨")
                await member.send(embed=ban_embed)
            except discord.Forbidden:
                pass
            return

        # 2. Normál, sikeres belépés (ha NINCS bannolva)
        channel = self.get_channel(1539791346880221196) 
        if channel:
            member_count = member.guild.member_count
            join_date = member.joined_at.strftime("%Y-%m-%d - %H:%M") if member.joined_at else "Ismeretlen"
            
            embed = discord.Embed(
                title="🌸 Új csillag érkezett a Never SMP-re! 🌸",
                description=f"Szia {member.mention}! De örülök, hogy megérkeztél! ✨\nLégy nagyon boldog nálunk, és érezd otthon magad ebben a kis világunkban! 🐾",
                color=discord.Color.pink()
            )
            
            embed.add_field(name="Túlélő ID", value=f"`{member.id}`", inline=False)
            embed.add_field(name="Csatlakozás ideje", value=f"{join_date}", inline=True)
            embed.add_field(name="Túlélők száma", value=f"{member_count}. tag vagy! 💖", inline=True)
            
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Jasmine, a szerver tündérkéje ✨")
            
            await channel.send(embed=embed)

        # Privát (DM) üzenet a normális tagoknak
        try:
            dm_embed = discord.Embed(
                title="💌 Szia kedves Túlélő!",
                description=f"Csak be akartam köszönni így privátban is! 😊 Örülök, hogy csatlakoztál a **Never SMP**-hez.\n\nHa bármi kérdésed van, vagy elakadsz, nyugodtan keress minket a szerveren. Érezd nagyon jól magad nálunk! 🌸✨",
                color=discord.Color.pink()
            )
            dm_embed.set_footer(text="Szeretettel: Jasmine 🐾")
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    async def on_member_remove(self, member):
        channel = self.get_channel(1539791383815258172) 
        if channel:
            embed = discord.Embed(
                title="🥀 Egy túlélő elhagyott minket...",
                description=f"Jaj, {member.name} útra kelt... Nagyon fog hiányozni a Never SMP világából! 💔\nRemélem, még viszontlátjuk egymást valamikor... ✨",
                color=discord.Color.dark_gray()
            )
            
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Jasmine, a szerver tündérkéje 🌸")
            
            await channel.send(embed=embed)

    # --- TWITCH ÉLŐ ÉRTESÍTÉS ---
    @commands.command(name="stream")
    @commands.has_permissions(administrator=True)
    async def stream_alert(self, ctx, platform: str = "twitch", *, link: str = "https://www.twitch.tv/maskedsparkle"):
        channel_id = 1497351886360023048 # Twitch csatorna ID
        channel = self.get_channel(channel_id)
        
        if not channel:
            await ctx.send("Nem találom a Twitch csatornát!")
            return

        embed = discord.Embed(
            title="🟣 Új Twitch Élőadás!",
            description=f"Hahó mindenki! Élőbe mentem a Twitchen, gyertek minél többen! 💖\n\n👉 **Kattints ide a nézéshez:** {link}",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Jasmine értesítője ✨")
        await channel.send(content="Helló @everyone! Élő adás van! 🔔", embed=embed)
        await ctx.message.delete()

    # --- YOUTUBE VIDEÓ ÉRTESÍTÉS ---
    @commands.command(name="video")
    @commands.has_permissions(administrator=True)
    async def video_alert(self, ctx, platform: str = "yt", *, link: str = "https://www.youtube.com/@Sparkle_fix"):
        channel_id = 1497351931360841820 # YouTube csatorna ID
        channel = self.get_channel(channel_id)
        
        if not channel:
            await ctx.send("Nem találom a YouTube csatornát!")
            return

        embed = discord.Embed(
            title="🔴 Új YouTube Videó érkezett!",
            description=f"Új tartalom került ki a csatornámra, lessétek meg bátran! ✨\n\n👉 **Nézzétek meg itt:** {link}",
            color=discord.Color.red()
        )
        embed.set_footer(text="Jasmine értesítője 🌸")
        await channel.send(content="Sziasztok @everyone! Új YouTube videó van! 🎬", embed=embed)
        await ctx.message.delete()

    # --- TIKTOK ÉRTESÍTÉS ---
    @commands.command(name="tiktok")
    @commands.has_permissions(administrator=True)
    async def tiktok_alert(self, ctx, *, link: str = "https://www.tiktok.com/@masked_sparkle"):
        channel_id = 1510603200284328037 # TikTok csatorna ID
        channel = self.get_channel(channel_id)
        
        if not channel:
            await ctx.send("Nem találom a TikTok csatornát!")
            return

        embed = discord.Embed(
            title="📱 Új TikTok Tartalom!",
            description=f"Új videót vagy live-ot toltam ki TikTokra! Csekkoljátok le! 💖\n\n👉 **Itt éritek el:** {link}",
            color=discord.Color.dark_embed()  # Javítva dark_theme()-ről
        )
        embed.set_footer(text="Jasmine értesítője ✨")
        await channel.send(content="Sziasztok @everyone! Új TikTok tartalom érkezett! 🎶", embed=embed)
        await ctx.message.delete()

if __name__ == "__main__":
    token = os.getenv("JASMINE_TOKEN") 
    bot = Jasmine()
    bot.run(token)
