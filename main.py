import discord
from discord.ext import commands, tasks
import datetime
import os
import feedparser
import json
from flask import Flask
import threading

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Jasmine is alive! 🌸 Multi-Server"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

DATA_FILE = "jasmine_data.json"
CONFIG_FILE = "jasmine_config.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Config save error: {e}")

class Jasmine(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.bans = True
        intents.guilds = True
        super().__init__(command_prefix='!', intents=intents)

        self.platform_data = load_data() # {guild_id: {last_youtube_link, last_tiktok_link, greeted_users: []}}
        self.guild_config = load_config() # {guild_id: {youtube_channel, tiktok_channel, welcome_channel, leave_channel, stream_channel}}

    def get_guild_platform_data(self, guild_id):
        gid = str(guild_id)
        if gid not in self.platform_data:
            self.platform_data[gid] = {
                "last_youtube_link": None,
                "last_tiktok_link": None,
                "greeted_users": []
            }
        # ensure greeted_users is set-like
        if "greeted_users" not in self.platform_data[gid]:
            self.platform_data[gid]["greeted_users"] = []
        return self.platform_data[gid]

    def get_guild_config(self, guild_id):
        gid = str(guild_id)
        if gid not in self.guild_config:
            # alapértelmezett - megpróbál auto-detect
            self.guild_config[gid] = {
                "youtube_channel": None,
                "tiktok_channel": None,
                "welcome_channel": None,
                "leave_channel": None,
                "stream_channel": None,
                "youtube_channel_id": "UCcKLZHpGu8yp8nQi17lwmmg", # masked sparkle default
                "tiktok_rss": "https://www.tiktok.com/@masked_sparkle/rss"
            }
        return self.guild_config[gid]

    def find_channel_by_name(self, guild, keywords):
        for ch in guild.text_channels:
            name = ch.name.lower()
            for kw in keywords:
                if kw in name:
                    return ch.id
        return None

    async def setup_hook(self):
        self.check_platforms.start()

    async def on_ready(self):
        print(f"Jasmine sikeresen bejelentkezett mint {self.user} ✨ | {len(self.guilds)} szerveren")
        # auto config ha nincs beállítva
        for guild in self.guilds:
            cfg = self.get_guild_config(guild.id)
            changed = False
            if not cfg["youtube_channel"]:
                found = self.find_channel_by_name(guild, ["youtube", "video", "yt"])
                if found:
                    cfg["youtube_channel"] = found
                    changed = True
            if not cfg["tiktok_channel"]:
                found = self.find_channel_by_name(guild, ["tiktok", "tt"])
                if found:
                    cfg["tiktok_channel"] = found
                    changed = True
            if not cfg["welcome_channel"]:
                found = self.find_channel_by_name(guild, ["welcome", "üdv", "érkezett", "join"])
                if found:
                    cfg["welcome_channel"] = found
                    changed = True
            if not cfg["leave_channel"]:
                found = self.find_channel_by_name(guild, ["leave", "kilép", "goodbye"])
                if found:
                    cfg["leave_channel"] = found
                    changed = True
            if not cfg["stream_channel"]:
                found = self.find_channel_by_name(guild, ["stream", "live", "twitch", "élő"])
                if found:
                    cfg["stream_channel"] = found
                    changed = True
            if changed:
                save_config(self.guild_config)
        print("✅ Config auto-detect kész")

    async def on_message(self, message):
        if message.author.bot:
            return
        content_lower = message.content.lower()
        
        gdata = self.get_guild_platform_data(message.guild.id) if message.guild else None
        
        if "sziasztok" in content_lower and gdata:
            if message.author.id not in gdata["greeted_users"]:
                gdata["greeted_users"].append(message.author.id)
                # limit size
                if len(gdata["greeted_users"]) > 1000:
                    gdata["greeted_users"] = gdata["greeted_users"][-500:]
                save_data(self.platform_data)
                await message.channel.send(f"Szia {message.author.mention}! 🌸")
        
        owner_keywords = ["ki itt a tulaj", "ki a tulaj", "ki a tulajdonos", "ki csinálta a szervert", "ki a fönök", "ki a szerver tulajdonosa"]
        if any(keyword in content_lower for keyword in owner_keywords):
            cassidy_id = 1047920915641548921
            await message.channel.send(f"<@{cassidy_id}> a tulaj ✨")
        
        await self.process_commands(message)

    @tasks.loop(minutes=5)
    async def check_platforms(self):
        for guild in self.guilds:
            await self.check_youtube_for_guild(guild)
            await self.check_tiktok_for_guild(guild)

    @check_platforms.before_loop
    async def before_check_platforms(self):
        await self.wait_until_ready()

    async def check_youtube_for_guild(self, guild):
        cfg = self.get_guild_config(guild.id)
        pdata = self.get_guild_platform_data(guild.id)
        channel_id = cfg.get("youtube_channel_id", "UCcKLZHpGu8yp8nQi17lwmmg")
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                latest = feed.entries[0]
                if pdata["last_youtube_link"] is None:
                    pdata["last_youtube_link"] = latest.link
                    save_data(self.platform_data)
                elif latest.link != pdata["last_youtube_link"]:
                    pdata["last_youtube_link"] = latest.link
                    save_data(self.platform_data)
                    
                    video_id = ""
                    if "watch?v=" in latest.link:
                        video_id = latest.link.split("watch?v=")[1].split("&")[0]
                    elif "/shorts/" in latest.link:
                        video_id = latest.link.split("/shorts/")[1].split("?")[0]
                    
                    target_channel_id = cfg.get("youtube_channel") or self.find_channel_by_name(guild, ["youtube", "video"])
                    channel = guild.get_channel(target_channel_id) if target_channel_id else None
                    if not channel:
                        # fallback: első ahol tud írni
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                channel = ch
                                break
                    
                    if channel:
                        embed = discord.Embed(
                            title="🔴 Új YouTube Videó érkezett!",
                            description=f"**{latest.title}**\n\nÚj tartalom került ki a csatornámra, lessétek meg bátran! ✨\n\n👉 **Nézzétek meg itt:** {latest.link}",
                            color=discord.Color.red()
                        )
                        if video_id:
                            embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
                        embed.set_footer(text=f"Jasmine értesítője 🌸 | {guild.name}")
                        await channel.send(content="Sziasztok @everyone! Új YouTube videó van! 🎬", embed=embed)
        except Exception as e:
            print(f"[{guild.name}] YouTube hiba: {e}")

    async def check_tiktok_for_guild(self, guild):
        cfg = self.get_guild_config(guild.id)
        pdata = self.get_guild_platform_data(guild.id)
        tiktok_rss = cfg.get("tiktok_rss", "https://www.tiktok.com/@masked_sparkle/rss")
        try:
            feed = feedparser.parse(tiktok_rss)
            if feed.entries:
                latest = feed.entries[0]
                if pdata["last_tiktok_link"] is None:
                    pdata["last_tiktok_link"] = latest.link
                    save_data(self.platform_data)
                elif latest.link != pdata["last_tiktok_link"]:
                    pdata["last_tiktok_link"] = latest.link
                    save_data(self.platform_data)
                    
                    target_channel_id = cfg.get("tiktok_channel") or self.find_channel_by_name(guild, ["tiktok"])
                    channel = guild.get_channel(target_channel_id) if target_channel_id else None
                    if channel:
                        embed = discord.Embed(
                            title="📱 Új TikTok Tartalom!",
                            description=f"**{latest.title}**\n\nÚj videót toltam ki TikTokra! Csekkoljátok le! 💖\n\n👉 **Itt éritek el:** {latest.link}",
                            color=discord.Color.dark_embed()
                        )
                        embed.set_footer(text=f"Jasmine értesítője ✨ | {guild.name}")
                        await channel.send(content="Sziasztok @everyone! Új TikTok tartalom érkezett! 🎶", embed=embed)
        except Exception as e:
            pass

    async def on_member_join(self, member):
        # ban check
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
                    description="Szia! Bocsi, de te nem fogsz tudni bejönni a szerverre, ugyanis téged bannoltak nem általam én csak egy üdvözlő bot vagyok aki ki bannolt volna az vagy a hugom kamila vagy egy staff/Tulajdonos úgy tudsz vissza jönni ha tulajdonos vagy staff unbanol téged 🌸",
                    color=discord.Color.red()
                )
                await member.send(embed=ban_embed)
            except discord.Forbidden:
                pass
            return
        
        cfg = self.get_guild_config(member.guild.id)
        channel_id = cfg.get("welcome_channel") or self.find_channel_by_name(member.guild, ["welcome", "üdv", "általános", "general"])
        channel = member.guild.get_channel(channel_id) if channel_id else None
        if not channel:
            for ch in member.guild.text_channels:
                if ch.permissions_for(member.guild.me).send_messages:
                    channel = ch
                    break
        
        if channel:
            member_count = member.guild.member_count
            join_date = member.joined_at.strftime("%Y-%m-%d - %H:%M") if member.joined_at else "Ismeretlen"
            embed = discord.Embed(
                title="🌸 Új csillag érkezett!",
                description=f"Szia {member.mention}! De örülök, hogy megérkeztél a **{member.guild.name}**-re! ✨\nLégy nagyon boldog nálunk! 🐾",
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
                description=f"Örülök, hogy csatlakoztál a **{member.guild.name}**-hez. Érezd nagyon jól magad nálunk! 🌸✨",
                color=discord.Color.pink()
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    async def on_member_remove(self, member):
        cfg = self.get_guild_config(member.guild.id)
        channel_id = cfg.get("leave_channel") or cfg.get("welcome_channel")
        channel = member.guild.get_channel(channel_id) if channel_id else None
        if channel:
            new_member_count = member.guild.member_count
            embed = discord.Embed(
                title="🥀 Egy túlélő elhagyott minket...",
                description=f"Jaj, **{member.name}** útra kelt a **{member.guild.name}**-ről... Nagyon fog hiányozni! 💔",
                color=discord.Color.dark_gray()
            )
            embed.add_field(name="Jelenlegi túlélők", value=f"Már csak **{new_member_count}**-en maradtunk. 🥺", inline=False)
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Jasmine, a szerver tündérkéje 🌸")
            await channel.send(embed=embed)

    @commands.command(name="stream")
    @commands.has_permissions(administrator=True)
    async def stream_alert(self, ctx, *, link: str = "https://www.twitch.tv/maskedsparkle"):
        cfg = self.get_guild_config(ctx.guild.id)
        channel_id = cfg.get("stream_channel") or self.find_channel_by_name(ctx.guild, ["stream", "live"])
        channel = ctx.guild.get_channel(channel_id) if channel_id else ctx.channel
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
        cfg = self.get_guild_config(ctx.guild.id)
        channel_id = cfg.get("youtube_channel")
        channel = ctx.guild.get_channel(channel_id) if channel_id else ctx.channel
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
        cfg = self.get_guild_config(ctx.guild.id)
        channel_id = cfg.get("tiktok_channel")
        channel = ctx.guild.get_channel(channel_id) if channel_id else ctx.channel
        if channel:
            embed = discord.Embed(
                title="📱 Új TikTok Tartalom!",
                description=f"Új videót vagy live-ot toltam ki TikTokra! Csekkoljátok le! 💖\n\n👉 **Itt éritek el:** {link}",
                color=discord.Color.dark_embed()
            )
            embed.set_footer(text="Jasmine értesítője ✨")
            await channel.send(content="Sziasztok @everyone! Új TikTok tartalom érkezett! 🎶", embed=embed)
        await ctx.message.delete()

    @commands.command(name="setjasmine")
    @commands.has_permissions(administrator=True)
    async def set_jasmine(self, ctx, tip: str, channel: discord.TextChannel):
        """Beállítás: !setjasmine youtube/tiktok/welcome/leave/stream #csatorna"""
        cfg = self.get_guild_config(ctx.guild.id)
        tip = tip.lower()
        mapping = {
            "youtube": "youtube_channel",
            "yt": "youtube_channel",
            "tiktok": "tiktok_channel",
            "tt": "tiktok_channel",
            "welcome": "welcome_channel",
            "udv": "welcome_channel",
            "join": "welcome_channel",
            "leave": "leave_channel",
            "stream": "stream_channel",
            "live": "stream_channel"
        }
        if tip not in mapping:
            await ctx.send("❌ Használat: `!setjasmine youtube/tiktok/welcome/leave/stream #csatorna`\nPl: `!setjasmine youtube #youtube-értesítő`")
            return
        key = mapping[tip]
        cfg[key] = channel.id
        save_config(self.guild_config)
        await ctx.send(f"✅ {tip} csatorna beállítva: {channel.mention} ezen a szerveren: {ctx.guild.name}")

    @commands.command(name="jasmineconfig")
    @commands.has_permissions(administrator=True)
    async def jasmine_config(self, ctx):
        cfg = self.get_guild_config(ctx.guild.id)
        embed = discord.Embed(title=f"🌸 Jasmine config - {ctx.guild.name}", color=discord.Color.pink())
        for k, v in cfg.items():
            if "channel" in k and v:
                ch = ctx.guild.get_channel(v)
                embed.add_field(name=k, value=ch.mention if ch else f"ID: {v}", inline=True)
            elif "channel" not in k:
                embed.add_field(name=k, value=str(v)[:100], inline=True)
        await ctx.send(embed=embed)

if __name__ == "__main__":
    token = os.getenv("JASMINE_TOKEN")
    if not token:
        token = os.getenv("DISCORD_TOKEN")
    bot = Jasmine()
    bot.run(token)
