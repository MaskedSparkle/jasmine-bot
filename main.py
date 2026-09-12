import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import json
import traceback
import feedparser
from flask import Flask
import threading
import datetime

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Jasmine is alive! 🌸 BAN DM Custom"

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

def format_message(template: str, member: discord.Member = None, user: discord.User = None, author: discord.Member = None, guild: discord.Guild = None, reason: str = None):
    if not template:
        return ""
    result = template
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        target = member or user
        if target:
            account_age = (now - target.created_at).days if hasattr(target, 'created_at') and target.created_at else 0
            result = result.replace("{member.mention}", target.mention if hasattr(target, 'mention') else str(target))
            result = result.replace("{member.name}", target.name)
            result = result.replace("{user.name}", target.name)
            result = result.replace("{member.id}", str(target.id))
            result = result.replace("{user.id}", str(target.id))
            result = result.replace("{account_age}", str(account_age))
            if member and member.joined_at:
                result = result.replace("{join_date}", member.joined_at.strftime("%Y-%m-%d %H:%M"))
        if author:
            result = result.replace("{author.mention}", author.mention)
            result = result.replace("{author.name}", author.name)
        if guild:
            result = result.replace("{guild.name}", guild.name)
            result = result.replace("{member_count}", str(guild.member_count))
            result = result.replace("{guild.id}", str(guild.id))
        if reason:
            result = result.replace("{reason}", reason)
            result = result.replace("{ban.reason}", reason)
        else:
            result = result.replace("{reason}", "Szabályszegés")
            result = result.replace("{ban.reason}", "Szabályszegés")
    except: pass
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

    def get_guild_platform_data(self, guild_id):
        gid = str(guild_id)
        if gid not in self.platform_data:
            self.platform_data[gid] = {"last_youtube_link": None, "last_tiktok_link": None, "greeted_users": []}
        if "greeted_users" not in self.platform_data[gid]:
            self.platform_data[gid]["greeted_users"] = []
        return self.platform_data[gid]

    def get_guild_config(self, guild_id):
        gid = str(guild_id)
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
                "ban_message": "🚫 Sajnálom {member.name}, de ki lettél bannolva a **{guild.name}** szerverről!\n\n**Indok:** {reason}\n\nEz nem általam történt, én csak egy értesítő bot vagyok. Aki bannolt az Kamila (a hugom) vagy egy staff/tulajdonos.\n\nÚgy tudsz visszajönni, ha egy tulajdonos vagy staff unbanol téged. 🌸\n\nHa kérdésed van, írj a szerver tulajdonosának!",
                "kick_message": "👢 Szia {member.name}! Ki lettél kickelve a **{guild.name}**-ről!\n\n**Indok:** {reason}\n\nEz Kamila miatt történt (3 figyelmeztetés után). Vissza tudsz jönni, de figyelj a szabályokra! 🌸"
            }
        defaults = {
            "welcome_enabled": True, "leave_enabled": True, "greeting_enabled": True, "dm_enabled": True, "ban_dm_enabled": True,
            "greeting_mode": "once", "greeting_trigger": "sziasztok",
            "welcome_message": "Szia {member.mention}! Üdv!",
            "leave_message": "{member.name} kilépett...",
            "greeting_message": "Szia {author.mention}! 🌸",
            "dm_message": "Szia {member.name}! Üdv!",
            "ban_message": "🚫 Ki lettél bannolva a {guild.name}-ről! Indok: {reason}",
            "kick_message": "👢 Ki lettél kickelve a {guild.name}-ről! Indok: {reason}"
        }
        for k, v in defaults.items():
            if k not in self.guild_config[gid]:
                self.guild_config[gid][k] = v
        return self.guild_config[gid]

    def find_channel_by_name(self, guild, keywords):
        for ch in guild.text_channels:
            name = ch.name.lower()
            for kw in keywords:
                if kw in name:
                    return ch.id
        return None

    async def setup_hook(self):
        print("🔧 Jasmine setup_hook BAN DM...")

        @self.tree.command(name="setwelcome", description="Üdvözlő csatorna")
        @app_commands.describe(channel="Csatorna")
        async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["welcome_channel"] = channel.id
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Welcome: {channel.mention}", ephemeral=True)

        @self.tree.command(name="setleave", description="Kilépő csatorna")
        @app_commands.describe(channel="Csatorna")
        async def setleave(interaction: discord.Interaction, channel: discord.TextChannel):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["leave_channel"] = channel.id
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Leave: {channel.mention}", ephemeral=True)

        @self.tree.command(name="setyoutube", description="YouTube csatorna")
        @app_commands.describe(channel="Csatorna", channel_id="YT Channel ID")
        async def setyoutube(interaction: discord.Interaction, channel: discord.TextChannel, channel_id: str = None):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["youtube_channel"] = channel.id
            if channel_id: cfg["youtube_channel_id"] = channel_id
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ YouTube: {channel.mention}", ephemeral=True)

        @self.tree.command(name="settiktok", description="TikTok csatorna")
        @app_commands.describe(channel="Csatorna")
        async def settiktok(interaction: discord.Interaction, channel: discord.TextChannel):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["tiktok_channel"] = channel.id
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ TikTok: {channel.mention}", ephemeral=True)

        @self.tree.command(name="setstream", description="Stream csatorna")
        @app_commands.describe(channel="Csatorna")
        async def setstream(interaction: discord.Interaction, channel: discord.TextChannel):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["stream_channel"] = channel.id
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Stream: {channel.mention}", ephemeral=True)

        @self.tree.command(name="setwelcomemsg", description="Belépő üzenet személyre szabása")
        @app_commands.describe(message="{member.mention} {member.name} {guild.name} {member_count} {account_age} {join_date}")
        async def setwelcomemsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["welcome_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Welcome msg:\n```{message}```", ephemeral=True)

        @self.tree.command(name="setleavemsg", description="Kilépő üzenet")
        @app_commands.describe(message="{member.name} {guild.name} {member_count}")
        async def setleavemsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["leave_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Leave msg:\n```{message}```", ephemeral=True)

        @self.tree.command(name="setdmmsg", description="DM üdvözlés belépésnél (privát)")
        @app_commands.describe(message="{member.mention} {guild.name} {member_count} {account_age}")
        async def setdmmsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["dm_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ DM msg:\n```{message}```", ephemeral=True)

        @self.tree.command(name="setbandmmsg", description="BAN DM üzenet személyre szabása (Kamila bannol -> Jasmine DM)")
        @app_commands.describe(message="Használhatsz: {member.name} {guild.name} {reason}")
        async def setbandmmsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["ban_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ BAN DM beállítva:\n```{message}```\nPlaceholderek: {{member.name}} {{member.mention}} {{guild.name}} {{reason}}", ephemeral=True)

        @self.tree.command(name="setkickdmmsg", description="KICK DM üzenet személyre szabása")
        @app_commands.describe(message="{member.name} {guild.name} {reason}")
        async def setkickdmmsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["kick_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ KICK DM:\n```{message}```", ephemeral=True)

        @self.tree.command(name="setgreeting", description="Köszönés beállítása")
        @app_commands.describe(trigger="Mire reagáljon pl: szia", message="{author.mention}", mode="Egyszer vagy mindig")
        @app_commands.choices(mode=[app_commands.Choice(name="Egyszer", value="once"), app_commands.Choice(name="Mindig", value="always")])
        async def setgreeting(interaction: discord.Interaction, trigger: str, message: str, mode: str = "once"):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["greeting_trigger"] = trigger.lower()
            cfg["greeting_message"] = message
            cfg["greeting_mode"] = mode
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Greeting: `{trigger}` -> `{message}` | {mode}", ephemeral=True)

        @self.tree.command(name="setgreetingmsg", description="Gyors greeting szöveg")
        @app_commands.describe(message="{author.mention}")
        async def setgreetingmsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["greeting_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Greeting:\n```{message}```", ephemeral=True)

        @self.tree.command(name="togglewelcome", description="Welcome ki/be")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def togglewelcome(interaction: discord.Interaction, state: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["welcome_enabled"] = state == "on"
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Welcome: {'BE' if cfg['welcome_enabled'] else 'KI'}", ephemeral=True)

        @self.tree.command(name="toggleleave", description="Leave ki/be")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def toggleleave(interaction: discord.Interaction, state: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["leave_enabled"] = state == "on"
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Leave: {'BE' if cfg['leave_enabled'] else 'KI'}", ephemeral=True)

        @self.tree.command(name="togglegreeting", description="Szia köszönés ki/be")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def togglegreeting(interaction: discord.Interaction, state: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["greeting_enabled"] = state == "on"
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Greeting: {'BE' if cfg['greeting_enabled'] else 'KI'}", ephemeral=True)

        @self.tree.command(name="toggledm", description="DM üdvözlés ki/be")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def toggledm(interaction: discord.Interaction, state: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["dm_enabled"] = state == "on"
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ DM: {'BE' if cfg['dm_enabled'] else 'KI'}", ephemeral=True)

        @self.tree.command(name="togglebandm", description="BAN DM ki/be - Kamila bannol -> Jasmine DM")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def togglebandm(interaction: discord.Interaction, state: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["ban_dm_enabled"] = state == "on"
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ BAN DM: {'BE' if cfg['ban_dm_enabled'] else 'KI'} | Ha Kamila bannol, Jasmine DM-et küld!", ephemeral=True)

        @self.tree.command(name="jasmineconfig", description="Összes beállítás")
        async def jasmineconfig(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            cfg = self.get_guild_config(interaction.guild.id)
            embed = discord.Embed(title=f"🌸 Jasmine Config - {interaction.guild.name}", color=discord.Color.pink())
            def ch_mention(cid):
                if not cid: return "Nincs"
                ch = interaction.guild.get_channel(cid)
                return ch.mention if ch else f"ID:{cid}"
            embed.add_field(name="Welcome", value=f"{ch_mention(cfg.get('welcome_channel'))} | {'BE' if cfg.get('welcome_enabled') else 'KI'}", inline=False)
            embed.add_field(name="Welcome msg", value=f"```{cfg.get('welcome_message')[:800]}```", inline=False)
            embed.add_field(name="Leave", value=f"{ch_mention(cfg.get('leave_channel'))} | {'BE' if cfg.get('leave_enabled') else 'KI'}", inline=False)
            embed.add_field(name="Leave msg", value=f"```{cfg.get('leave_message')[:500]}```", inline=False)
            embed.add_field(name="DM", value=f"{'BE' if cfg.get('dm_enabled') else 'KI'}", inline=True)
            embed.add_field(name="DM msg", value=f"```{cfg.get('dm_message')[:500]}```", inline=False)
            embed.add_field(name="BAN DM", value=f"{'BE' if cfg.get('ban_dm_enabled') else 'KI'}", inline=True)
            embed.add_field(name="BAN msg", value=f"```{cfg.get('ban_message')[:800]}```", inline=False)
            embed.add_field(name="KICK msg", value=f"```{cfg.get('kick_message')[:500]}```", inline=False)
            embed.add_field(name="Greeting", value=f"`{cfg.get('greeting_trigger')}` | {cfg.get('greeting_mode')} | {'BE' if cfg.get('greeting_enabled') else 'KI'}", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

        @self.tree.command(name="ping", description="Teszt")
        async def ping(interaction: discord.Interaction):
            await interaction.response.send_message("🌸 Jasmine Pong! BAN DM működik! ✅", ephemeral=True)

        # Platform commands
        @self.tree.command(name="stream", description="Stream élő")
        @app_commands.describe(link="Link")
        async def stream_cmd(interaction: discord.Interaction, link: str):
            await interaction.response.defer()
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            channel = interaction.guild.get_channel(cfg.get("stream_channel")) if cfg.get("stream_channel") else interaction.channel
            embed = discord.Embed(title="🟣 Élő adás!", description=link, color=discord.Color.purple())
            await channel.send(content="@everyone Élő! 🔔", embed=embed)
            await interaction.followup.send(f"✅ {channel.mention}", ephemeral=True)

        @self.tree.command(name="video", description="YouTube videó")
        @app_commands.describe(link="Link")
        async def video_cmd(interaction: discord.Interaction, link: str):
            await interaction.response.defer()
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            channel = interaction.guild.get_channel(cfg.get("youtube_channel")) if cfg.get("youtube_channel") else interaction.channel
            embed = discord.Embed(title="🔴 Új YouTube Videó!", description=link, color=discord.Color.red())
            await channel.send(content="@everyone Új videó! 🎬", embed=embed)
            await interaction.followup.send(f"✅ {channel.mention}", ephemeral=True)

        @self.tree.command(name="tiktok", description="TikTok")
        @app_commands.describe(link="Link")
        async def tiktok_cmd(interaction: discord.Interaction, link: str):
            await interaction.response.defer()
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            channel = interaction.guild.get_channel(cfg.get("tiktok_channel")) if cfg.get("tiktok_channel") else interaction.channel
            embed = discord.Embed(title="📱 Új TikTok!", description=link, color=discord.Color.dark_embed())
            await channel.send(content="@everyone Új TikTok! 🎶", embed=embed)
            await interaction.followup.send(f"✅ {channel.mention}", ephemeral=True)

        try:
            synced = await self.tree.sync()
            print(f"✅ Jasmine sync: {len(synced)} -> {', '.join([c.name for c in synced])}")
        except Exception as e:
            print(f"❌ Sync hiba: {e}\n{traceback.format_exc()}")

        self.check_platforms.start()

    async def on_ready(self):
        print(f"✨ Jasmine {self.user} | {len(self.guilds)} szerveren - BAN DM ON")
        for guild in self.guilds:
            try: await self.tree.sync(guild=guild)
            except: pass

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

    # BAN ES KICK DM - Ez a lényeg!
    async def on_member_ban(self, guild, user):
        cfg = self.get_guild_config(guild.id)
        if not cfg.get("ban_dm_enabled"):
            return
        
        # Reason kinyerése audit logból
        reason = "Szabályszegés / Kamila általi bannolás"
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    reason = entry.reason or "Nincs megadva"
                    if entry.user.id == self.user.id:
                        reason = f"{reason} (Jasmine)"
                    else:
                        # Ha Kamila bannolt
                        if "kamila" in entry.user.name.lower() or entry.user.bot:
                            reason = f"{reason} - Kamila biztonsági rendszer"
                    break
        except: pass

        tmpl = cfg.get("ban_message")
        text = format_message(tmpl, user=user, guild=guild, reason=reason)
        embed = discord.Embed(title="🚫 Bannolva lettél!", description=text, color=discord.Color.red())
        embed.set_footer(text=f"{guild.name} | Jasmine értesítő 🌸")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        try:
            await user.send(embed=embed)
            print(f"✅ BAN DM elküldve: {user.name} ({guild.name}) - {reason}")
        except discord.Forbidden:
            print(f"❌ BAN DM nem ment: {user.name} letiltotta a DM-et")
        except Exception as e:
            print(f"❌ BAN DM hiba: {e}")

    async def on_member_remove(self, member):
        # Először nézzük hogy kick volt-e vagy sima leave
        cfg = self.get_guild_config(member.guild.id)
        
        # Kick detection audit logból
        is_kick = False
        kick_reason = "3 figyelmeztetés / szabályszegés"
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    is_kick = True
                    kick_reason = entry.reason or "Kamila kick (3 warn)"
                    break
        except: pass

        if is_kick and cfg.get("ban_dm_enabled"):
            # Kick DM küldése
            tmpl = cfg.get("kick_message")
            text = format_message(tmpl, member=member, guild=member.guild, reason=kick_reason)
            embed = discord.Embed(title="👢 Kickelve lettél!", description=text, color=discord.Color.orange())
            embed.set_footer(text=f"{member.guild.name} | Visszajöhetsz, de figyelj a szabályokra!")
            try:
                await member.send(embed=embed)
                print(f"✅ KICK DM: {member.name}")
            except: pass

        # Normál leave üzenet csatornába
        if not cfg.get("leave_enabled"):
            return
        channel_id = cfg.get("leave_channel") or cfg.get("welcome_channel")
        channel = member.guild.get_channel(channel_id) if channel_id else None
        if channel:
            tmpl = cfg.get("leave_message")
            text = format_message(tmpl, member=member, guild=member.guild)
            embed = discord.Embed(title="🥀 Elhagyott minket...", description=text, color=discord.Color.dark_gray())
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            try: await channel.send(embed=embed)
            except: pass

    async def on_member_join(self, member):
        cfg = self.get_guild_config(member.guild.id)
        # Ban check - ha bannolt, ne üdvözölje, hanem ban DM volt már
        try:
            bans = [b.user.id async for b in member.guild.bans()]
            if member.id in bans:
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
    bot = Jasmine()
    bot.run(token)
