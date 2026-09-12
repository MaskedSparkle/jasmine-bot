import discord
from discord import app_commands
from discord.ext import commands, tasks
import os, json, traceback, feedparser, threading, datetime
from flask import Flask

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Jasmine FINAL FIXED - BAN DM Debug"

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
def save_data(d):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}
def save_config(c):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Config save error: {e}")

def format_message(template, member=None, user=None, author=None, guild=None, reason=None):
    if not template: return ""
    result = template
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        target = member or user
        if target:
            result = result.replace("{member.mention}", target.mention if hasattr(target,'mention') else f"<@{target.id}>")
            result = result.replace("{member.name}", target.name)
            result = result.replace("{user.name}", target.name)
            result = result.replace("{member.id}", str(target.id))
            result = result.replace("{user.id}", str(target.id))
            if hasattr(target,'created_at') and target.created_at:
                age = (now - target.created_at).days
                result = result.replace("{account_age}", str(age))
        if author:
            result = result.replace("{author.mention}", author.mention)
            result = result.replace("{author.name}", author.name)
        if guild:
            result = result.replace("{guild.name}", guild.name)
            result = result.replace("{member_count}", str(guild.member_count))
        result = result.replace("{reason}", reason or "Szabályszegés / Kamila biztonsági rendszer")
        result = result.replace("{ban.reason}", reason or "Szabályszegés")
    except Exception as e:
        print(f"format_message hiba: {e}")
    return result

class Jasmine(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.bans = True
        intents.guilds = True
        super().__init__(command_prefix='!', intents=intents)
        self.platform_data = load_data()
        self.guild_config = load_config()

    def get_guild_platform_data(self, gid):
        gid = str(gid)
        if gid not in self.platform_data:
            self.platform_data[gid] = {"last_youtube_link": None, "last_tiktok_link": None, "greeted_users": []}
        if "greeted_users" not in self.platform_data[gid]:
            self.platform_data[gid]["greeted_users"] = []
        return self.platform_data[gid]

    def get_guild_config(self, gid):
        gid = str(gid)
        if gid not in self.guild_config:
            self.guild_config[gid] = {
                "youtube_channel": None, "tiktok_channel": None, "welcome_channel": None,
                "leave_channel": None, "stream_channel": None,
                "youtube_channel_id": "UCcKLZHpGu8yp8nQi17lwmmg",
                "tiktok_rss": "https://www.tiktok.com/@masked_sparkle/rss",
                "welcome_enabled": True, "leave_enabled": True, "greeting_enabled": True,
                "dm_enabled": True, "ban_dm_enabled": True,
                "greeting_mode": "once", "greeting_trigger": "sziasztok",
                "welcome_message": "Szia {member.mention}! De örülök, hogy megérkeztél a **{guild.name}**-re! ✨\nTe vagy a(z) {member_count}. tag! 🐾",
                "leave_message": "Jaj, **{member.name}** elhagyott minket a **{guild.name}**-ről... 🥀\nMár csak {member_count}-en maradtunk. 💔",
                "greeting_message": "Szia {author.mention}! 🌸",
                "dm_message": "Szia {member.mention}! 💌 Örülök, hogy csatlakoztál a **{guild.name}**-hez! Érezd nagyon jól magad nálunk! 🌸✨",
                "ban_message": "🚫 Sajnálom {member.name}, de ki lettél bannolva a **{guild.name}** szerverről!\n\n**Indok:** {reason}\n\nEz nem általam történt, én csak egy értesítő bot vagyok. Aki bannolt az Kamila (a hugom) vagy egy staff/tulajdonos.\n\nÚgy tudsz visszajönni, ha egy tulajdonos vagy staff unbanol téged. 🌸",
                "kick_message": "👢 Szia {member.name}! Ki lettél kickelve a **{guild.name}**-ről!\n\n**Indok:** {reason}\n\nEz Kamila miatt történt (3 figyelmeztetés után). Vissza tudsz jönni, de figyelj a szabályokra! 🌸"
            }
        
        if "ban_dm_enabled" not in self.guild_config[gid]:
            self.guild_config[gid]["ban_dm_enabled"] = True
        if "ban_message" not in self.guild_config[gid]:
            self.guild_config[gid]["ban_message"] = "🚫 Ki lettél bannolva a {guild.name}-ről! Indok: {reason}"
        if "kick_message" not in self.guild_config[gid]:
            self.guild_config[gid]["kick_message"] = "👢 Kickelve lettél a {guild.name}-ről! {reason}"
        return self.guild_config[gid]

    async def setup_hook(self):
        print("🔧 Jasmine FINAL setup_hook...")

        @self.tree.command(name="setbandmmsg", description="BAN DM szöveg")
        @app_commands.describe(message="{member.name} {guild.name} {reason}")
        async def setbandmmsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["ban_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ BAN DM:\n```{message}```", ephemeral=True)

        @self.tree.command(name="togglebandm", description="BAN DM ki/be")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def togglebandm(interaction: discord.Interaction, state: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["ban_dm_enabled"] = state == "on"
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ BAN DM: {'BE' if cfg['ban_dm_enabled'] else 'KI'}", ephemeral=True)

        @self.tree.command(name="testbandm", description="TESZT - BAN DM küldése valakinek ban nélkül")
        @app_commands.describe(member="Kinek küldje a teszt DM-et")
        async def testbandm(interaction: discord.Interaction, member: discord.Member):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            if not cfg.get("ban_dm_enabled", True):
                await interaction.followup.send("❌ BAN DM ki van kapcsolva! `/togglebandm on`", ephemeral=True); return

            tmpl = cfg.get("ban_message")
            text = format_message(tmpl, member=member, guild=interaction.guild, reason="TESZT - nem vagy tényleg bannolva, ez csak egy teszt!")
            embed = discord.Embed(title="🚫 TESZT BAN DM", description=text, color=discord.Color.red())
            embed.set_footer(text=f"{interaction.guild.name} | TESZT")
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)

            try:
                await member.send(embed=embed)
                await interaction.followup.send(f"✅ TESZT DM elküldve neki: {member.mention}\nHa nem kapta meg, letiltotta a DM-et (Privacy Settings)!", ephemeral=True)
                print(f"✅ TEST BAN DM OK: {member.name}")
            except discord.Forbidden:
                await interaction.followup.send(f"❌ {member.mention} letiltotta a DM-et! Discord -> Privacy -> Allow direct messages BE kell!", ephemeral=True)
                print(f"❌ TEST BAN DM FORBIDDEN: {member.name} DM tiltva")
            except Exception as e:
                await interaction.followup.send(f"❌ Hiba: {e}\n{traceback.format_exc()[:1000]}", ephemeral=True)
                print(f"❌ TEST BAN DM hiba: {e}\n{traceback.format_exc()}")

        @self.tree.command(name="jasmineconfig", description="Összes beállítás")
        async def jasmineconfig(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            cfg = self.get_guild_config(interaction.guild.id)
            embed = discord.Embed(title=f"🌸 Jasmine Config - {interaction.guild.name}", color=discord.Color.pink())
            embed.add_field(name="BAN DM", value=f"{'BE ✅' if cfg.get('ban_dm_enabled') else 'KI ❌'}", inline=False)
            embed.add_field(name="BAN msg", value=f"```{cfg.get('ban_message')[:900]}```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

        @self.tree.command(name="ping", description="Teszt")
        async def ping(interaction: discord.Interaction):
            await interaction.response.send_message("🌸 Pong! BAN DM FINAL FIXED ✅ /testbandm", ephemeral=True)

        
        @self.tree.command(name="setwelcome", description="Welcome csatorna")
        @app_commands.describe(channel="Csatorna")
        async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["welcome_channel"] = channel.id
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Welcome: {channel.mention}", ephemeral=True)

        @self.tree.command(name="setwelcomemsg", description="Welcome msg")
        @app_commands.describe(message="Szöveg")
        async def setwelcomemsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["welcome_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Welcome msg: ```{message}```", ephemeral=True)

        try:
            synced = await self.tree.sync()
            print(f"✅ Jasmine sync: {len(synced)} -> {', '.join([c.name for c in synced])}")
        except Exception as e:
            print(f"❌ Sync hiba: {e}\n{traceback.format_exc()}")

        self.check_platforms.start()

    async def on_ready(self):
        print(f"✨ Jasmine {self.user} | {len(self.guilds)} szerveren - BAN DM FINAL")
        for guild in self.guilds:
            try:
                await self.tree.sync(guild=guild)
                print(f"✅ Guild sync {guild.name}")
            except Exception as e:
                print(f"❌ Guild {guild.name} sync hiba: {e}")

    async def on_message(self, message):
        if message.author.bot: return
        if not message.guild: return
        cfg = self.get_guild_config(message.guild.id)
        pdata = self.get_guild_platform_data(message.guild.id)
        if cfg.get("greeting_enabled"):
            trigger = cfg.get("greeting_trigger", "sziasztok").lower()
            if trigger in message.content.lower():
                greeted = pdata["greeted_users"]
                uid = message.author.id
                mode = cfg.get("greeting_mode", "once")
                should = mode == "always" or uid not in greeted
                if should and mode == "once" and uid not in greeted:
                    greeted.append(uid)
                    if len(greeted) > 1000: greeted = greeted[-500:]
                    pdata["greeted_users"] = greeted
                    save_data(self.platform_data)
                if should:
                    text = format_message(cfg.get("greeting_message"), author=message.author, guild=message.guild)
                    try: await message.channel.send(text)
                    except: pass
        await self.process_commands(message)

    async def on_member_ban(self, guild, user):
        print(f"🔨 [BAN EVENT] {user.name} ({user.id}) bannolva a {guild.name} szerveren")
        cfg = self.get_guild_config(guild.id)
        print(f"   BAN DM enabled: {cfg.get('ban_dm_enabled')}")
        if not cfg.get("ban_dm_enabled"):
            print("   -> BAN DM KI van kapcsolva, kilépek")
            return
        
        reason = "Szabályszegés / Kamila általi bannolás"
        banned_by_name = "Ismeretlen"
        try:
            
            async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    reason = entry.reason or "Nincs indok"
                    banned_by_name = entry.user.name if entry.user else "Ismeretlen"
                    print(f"   📋 Audit log találat: bannolta {banned_by_name} | indok: {reason}")
                    break
        except discord.Forbidden:
            print("   ❌ NINCS View Audit Log jogom! Adj jogot a botnak!")
            reason = "Kamila biztonsági rendszer (audit log nincs engedélyezve)"
        except Exception as e:
            print(f"   ❌ Audit log hiba: {e}\n{traceback.format_exc()}")
        
        tmpl = cfg.get("ban_message", "🚫 Bannolva lettél a {guild.name} szerverről! Indok: {reason}")
        text = format_message(tmpl, user=user, guild=guild, reason=reason)
        
        embed = discord.Embed(title="🚫 Bannolva lettél!", description=text, color=discord.Color.red())
        embed.add_field(name="Szerver", value=guild.name, inline=True)
        embed.add_field(name="Indok", value=reason[:1000], inline=False)
        embed.add_field(name="Bannolta", value=banned_by_name, inline=True)
        embed.set_footer(text=f"{guild.name} | Jasmine értesítő 🌸")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        
        try:
            await user.send(embed=embed)
            print(f"   ✅ BAN DM ELKÜLDVE: {user.name} -> DM ment!")
        except discord.Forbidden:
            print(f"   ❌ BAN DM FORBIDDEN: {user.name} letiltotta a DM-et! (Privacy Settings -> Allow DMs)")
            
            try:
                log_ch_id = cfg.get("welcome_channel") or cfg.get("leave_channel")
                if log_ch_id:
                    ch = guild.get_channel(log_ch_id)
                    if ch and ch.permissions_for(guild.me).send_messages:
                        await ch.send(f"⚠ {user.name} ({user.id}) bannolva lett, de nem tudtam DM-et küldeni neki mert letiltotta a DM-et! Indok: {reason}")
            except Exception as e:
                print(f"   Log csatorna hiba: {e}")
        except Exception as e:
            print(f"   ❌ BAN DM ISMERETLEN HIBA: {e}\n{traceback.format_exc()}")

    async def on_member_remove(self, member):
        cfg = self.get_guild_config(member.guild.id)
        # Kick detection
        is_kick = False
        kick_reason = "3 figyelmeztetés / szabályszegés"
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    is_kick = True
                    kick_reason = entry.reason or "Kamila kick"
                    print(f"👢 KICK detect: {member.name} kickelve | {kick_reason}")
                    break
        except: pass

        if is_kick and cfg.get("ban_dm_enabled"):
            tmpl = cfg.get("kick_message")
            text = format_message(tmpl, member=member, guild=member.guild, reason=kick_reason)
            embed = discord.Embed(title="👢 Kickelve lettél!", description=text, color=discord.Color.orange())
            embed.set_footer(text=f"{member.guild.name} | Visszajöhetsz, de figyelj a szabályokra!")
            try:
                await member.send(embed=embed)
                print(f"✅ KICK DM: {member.name}")
            except Exception as e:
                print(f"❌ KICK DM hiba: {e}")

        if not cfg.get("leave_enabled", True):
            return
        channel_id = cfg.get("leave_channel") or cfg.get("welcome_channel")
        channel = member.guild.get_channel(channel_id) if channel_id else None
        if channel:
            tmpl = cfg.get("leave_message", "{member.name} kilépett")
            text = format_message(tmpl, member=member, guild=member.guild)
            embed = discord.Embed(title="🥀 Elhagyott minket...", description=text, color=discord.Color.dark_gray())
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            try: await channel.send(embed=embed)
            except: pass

    async def on_member_join(self, member):
        cfg = self.get_guild_config(member.guild.id)
        try:
            bans = [b.user.id async for b in member.guild.bans()]
            if member.id in bans:
                print(f"🚫 {member.name} bannolt, nem üdvözlöm")
                return
        except: pass

        if cfg.get("welcome_enabled"):
            channel_id = cfg.get("welcome_channel")
            channel = member.guild.get_channel(channel_id) if channel_id else None
            if not channel:
                for ch in member.guild.text_channels:
                    if ch.permissions_for(member.guild.me).send_messages:
                        channel = ch; break
            if channel:
                tmpl = cfg.get("welcome_message")
                text = format_message(tmpl, member=member, guild=member.guild)
                embed = discord.Embed(title="🌸 Új csillag érkezett!", description=text, color=discord.Color.pink())
                if member.display_avatar:
                    embed.set_thumbnail(url=member.display_avatar.url)
                try: await channel.send(embed=embed)
                except: pass

        if cfg.get("dm_enabled"):
            try:
                tmpl = cfg.get("dm_message")
                text = format_message(tmpl, member=member, guild=member.guild)
                embed = discord.Embed(title="💌 Szia!", description=text, color=discord.Color.pink())
                await member.send(embed=embed)
            except: pass

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
                    target = guild.get_channel(cfg.get("youtube_channel")) if cfg.get("youtube_channel") else None
                    if not target:
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                target = ch; break
                    if target:
                        embed = discord.Embed(title="🔴 Új YouTube Videó!", description=f"**{latest.title}**\n{latest.link}", color=discord.Color.red())
                        await target.send(content="@everyone Új YouTube videó! 🎬", embed=embed)
        except: pass

    async def check_tiktok_for_guild(self, guild):
        cfg = self.get_guild_config(guild.id)
        pdata = self.get_guild_platform_data(guild.id)
        rss = cfg.get("tiktok_rss")
        try:
            feed = feedparser.parse(rss)
            if feed.entries:
                latest = feed.entries[0]
                if pdata["last_tiktok_link"] is None:
                    pdata["last_tiktok_link"] = latest.link
                    save_data(self.platform_data)
                elif latest.link != pdata["last_tiktok_link"]:
                    pdata["last_tiktok_link"] = latest.link
                    save_data(self.platform_data)
                    target = guild.get_channel(cfg.get("tiktok_channel")) if cfg.get("tiktok_channel") else None
                    if target:
                        embed = discord.Embed(title="📱 Új TikTok!", description=f"{latest.title}\n{latest.link}", color=discord.Color.dark_embed())
                        await target.send(content="@everyone Új TikTok! 🎶", embed=embed)
        except: pass

if __name__ == "__main__":
    token = os.getenv("JASMINE_TOKEN") or os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Nincs token!")
    else:
        bot = Jasmine()
        bot.run(token)
