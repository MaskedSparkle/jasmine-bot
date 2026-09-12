import discord
from discord import app_commands
from discord.ext import commands, tasks
import os, json, traceback, feedparser, threading, datetime, time
from flask import Flask

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Jasmine FINAL - Discord Bridge Last Moment DM"

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
    except: pass
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
    except: pass

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
        self.last_bridge = {}  # spam védelem

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
                "leave_message": "Jaj, **{member.name}** elhagyott minket a **{guild.name}**-ről... 🥀",
                "greeting_message": "Szia {author.mention}! 🌸",
                "dm_message": "Szia {member.mention}! 💌 Üdv a **{guild.name}**-en! 🌸✨",
                "ban_message": "🚫 Sajnálom {member.name}, de ki lettél bannolva a **{guild.name}** szerverről!\n\n**Indok:** {reason}\n\nEzt Kamila intézte (a hugom) vagy egy staff. Ha vissza akarsz jönni, írj egy staffnak! 🌸",
                "kick_message": "👢 Szia {member.name}! Kickelve lettél a {guild.name}-ről! Indok: {reason}"
            }
        if "ban_dm_enabled" not in self.guild_config[gid]:
            self.guild_config[gid]["ban_dm_enabled"] = True
        return self.guild_config[gid]

    async def setup_hook(self):
        print("🔧 Jasmine FINAL DISCORD BRIDGE setup...")

        @self.tree.command(name="setbandmmsg", description="BAN DM szöveg - utolsó pillanat")
        @app_commands.describe(message="{member.name} {guild.name} {reason}")
        async def setbandmmsg(interaction: discord.Interaction, message: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["ban_message"] = message
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ BAN DM (utolsó pillanat):\n```{message}```", ephemeral=True)

        @self.tree.command(name="togglebandm", description="BAN DM ki/be - utolsó pillanat")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def togglebandm(interaction: discord.Interaction, state: str):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["ban_dm_enabled"] = state == "on"
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ BAN DM utolsó pillanat: {'BE' if cfg['ban_dm_enabled'] else 'KI'}", ephemeral=True)

        @self.tree.command(name="testbandm", description="TESZT BAN DM - utolsó pillanat")
        @app_commands.describe(member="Kinek")
        async def testbandm(interaction: discord.Interaction, member: discord.Member):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            tmpl = cfg.get("ban_message")
            text = format_message(tmpl, member=member, guild=interaction.guild, reason="TESZT - nem vagy bannolva!")
            embed = discord.Embed(title="🚫 TESZT - Utolsó pillanat BAN DM", description=text, color=discord.Color.red())
            embed.set_footer(text=f"{interaction.guild.name} | TESZT | Jasmine utolsó pillanat")
            try:
                await member.send(embed=embed)
                await interaction.followup.send(f"✅ DM ment: {member.mention}", ephemeral=True)
                print(f"✅ TEST BAN DM OK: {member.name}")
            except discord.Forbidden:
                await interaction.followup.send(f"❌ {member.mention} DM tiltva!", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)

        @self.tree.command(name="jasmineconfig", description="Config - utolsó pillanat")
        async def jasmineconfig(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            cfg = self.get_guild_config(interaction.guild.id)
            embed = discord.Embed(title=f"🌸 Jasmine LAST MOMENT - {interaction.guild.name}", color=discord.Color.pink())
            embed.add_field(name="BAN DM (utolsó pillanat)", value=f"{'BE ✅' if cfg.get('ban_dm_enabled') else 'KI ❌'}", inline=False)
            embed.add_field(name="BAN msg", value=f"```{cfg.get('ban_message')[:900]}```", inline=False)
            embed.add_field(name="Hogyan működik?", value="Kamila ír BRIDGE_BAN jelet Discord csatornába -> Jasmine azonnal DM-el amíg még a szerveren van (ban előtt 3mp) -> Kamila bannol", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

        @self.tree.command(name="ping", description="Teszt")
        async def ping(interaction: discord.Interaction):
            await interaction.response.send_message("🌸 Pong! LAST MOMENT DISCORD BRIDGE ✅", ephemeral=True)

        @self.tree.command(name="setwelcome", description="Welcome csatorna")
        @app_commands.describe(channel="Csatorna")
        async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel):
            await interaction.response.defer(ephemeral=True)
            if not interaction.user.guild_permissions.administrator: return
            cfg = self.get_guild_config(interaction.guild.id)
            cfg["welcome_channel"] = channel.id
            save_config(self.guild_config)
            await interaction.followup.send(f"✅ Welcome: {channel.mention}", ephemeral=True)

        try:
            synced = await self.tree.sync()
            print(f"✅ Jasmine sync: {len(synced)} -> {', '.join([c.name for c in synced])}")
        except Exception as e:
            print(f"❌ Sync hiba: {e}\n{traceback.format_exc()}")

        self.check_platforms.start()

    async def on_ready(self):
        print(f"✨ Jasmine FINAL DISCORD BRIDGE {self.user} | {len(self.guilds)} szerveren")
        for g in self.guilds:
            try: await self.tree.sync(guild=g)
            except: pass

    async def on_message(self, message):
        # DISCORD BRIDGE - Kamila jele
        if message.author.bot and message.content.startswith("BRIDGE_BAN|"):
            try:
                parts = message.content.split("|")
                # BRIDGE_BAN|guild_id|user_id|reason|banned_by
                if len(parts) < 5:
                    return
                guild_id = int(parts[1])
                user_id = int(parts[2])
                reason = parts[3]
                banned_by = parts[4]

                # Spam védelem - 5mp-en belül ugyanazt a usert ne dolgozzuk fel újra
                key = f"{guild_id}_{user_id}"
                now = time.time()
                if key in self.last_bridge and now - self.last_bridge[key] < 5:
                    return
                self.last_bridge[key] = now

                guild = self.get_guild(guild_id)
                if not guild:
                    print(f"🌉 BRIDGE: guild {guild_id} nem található")
                    return

                cfg = self.get_guild_config(guild_id)
                if not cfg.get("ban_dm_enabled"):
                    print(f"🌉 BRIDGE: BAN DM KI van kapcsolva {guild.name}-en")
                    return

                # Keressük a member-t - MÉG A SZERVEREN VAN! Ez a lényeg!
                member = guild.get_member(user_id)
                if not member:
                    print(f"🌉 BRIDGE: {user_id} már nincs a szerveren (túl késő, Kamila már bannolt?)")
                    return

                print(f"🌉 DISCORD BRIDGE érkezett! {member.name} bannolva lesz {guild.name}-en | Indok: {reason} | Utolsó pillanat DM küldése!")

                tmpl = cfg.get("ban_message")
                text = format_message(tmpl, member=member, guild=guild, reason=reason)
                embed = discord.Embed(title="🚫 Bannolva leszel - utolsó pillanat!", description=text, color=discord.Color.red())
                embed.add_field(name="Szerver", value=guild.name, inline=True)
                embed.add_field(name="Indok", value=reason[:1000], inline=False)
                embed.add_field(name="Bannolta", value=banned_by, inline=True)
                embed.set_footer(text=f"{guild.name} | Jasmine utolsó pillanat értesítő 🌸 | Most fogsz kikerülni!")
                if guild.icon:
                    embed.set_thumbnail(url=guild.icon.url)

                try:
                    await member.send(embed=embed)
                    print(f"✅ 🌉 LAST MOMENT DM ELKÜLDVE: {member.name} ({guild.name}) | Még a szerveren volt! | {reason}")
                    # Töröljük a bridge üzenetet hogy ne spam-eljen a log
                    try:
                        await message.delete()
                    except: pass
                except discord.Forbidden:
                    print(f"❌ 🌉 LAST MOMENT DM FORBIDDEN: {member.name} letiltotta a DM-et")
                except Exception as e:
                    print(f"❌ 🌉 LAST MOMENT DM hiba: {e}\n{traceback.format_exc()}")

            except Exception as e:
                print(f"BRIDGE feldolgozási hiba: {e}\n{traceback.format_exc()}")
            return

        # BRIDGE KICK
        if message.author.bot and message.content.startswith("BRIDGE_KICK|"):
            try:
                parts = message.content.split("|")
                guild_id = int(parts[1])
                user_id = int(parts[2])
                reason = parts[3]
                guild = self.get_guild(guild_id)
                if not guild: return
                member = guild.get_member(user_id)
                if not member: return
                cfg = self.get_guild_config(guild_id)
                tmpl = cfg.get("kick_message", "👢 Kickelve lettél a {guild.name}-ről! {reason}")
                text = format_message(tmpl, member=member, guild=guild, reason=reason)
                embed = discord.Embed(title="👢 Kickelve leszel!", description=text, color=discord.Color.orange())
                try:
                    await member.send(embed=embed)
                    print(f"✅ 🌉 KICK DM: {member.name}")
                    await message.delete()
                except: pass
            except: pass
            return

        # Normál üzenetek
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
        # BACKUP - ha a bridge valamiért nem ment volna
        print(f"🔨 [BAN EVENT BACKUP] {user.name} bannolva {guild.name}-en")
        cfg = self.get_guild_config(guild.id)
        if not cfg.get("ban_dm_enabled"):
            return
        # Ha az utolsó 10mp-ben volt bridge erre a userre, ne küldjünk duplán
        key = f"{guild.id}_{user.id}"
        if key in self.last_bridge and time.time() - self.last_bridge[key] < 15:
            print(f"   -> Már küldtem bridge-en keresztül, backup nem kell")
            return
        reason = "Kamila biztonsági rendszer"
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    reason = entry.reason or "Nincs indok"
                    break
        except: pass
        tmpl = cfg.get("ban_message")
        text = format_message(tmpl, user=user, guild=guild, reason=reason)
        embed = discord.Embed(title="🚫 Bannolva lettél! (backup)", description=text, color=discord.Color.red())
        try:
            await user.send(embed=embed)
            print(f"   ✅ BACKUP BAN DM ment: {user.name}")
        except:
            print(f"   ❌ BACKUP DM nem ment (már nincs szerveren) - ezért kell a bridge!")

    async def on_member_join(self, member):
        cfg = self.get_guild_config(member.guild.id)
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
                try: await channel.send(embed=embed)
                except: pass
        if cfg.get("dm_enabled"):
            try:
                tmpl = cfg.get("dm_message")
                text = format_message(tmpl, member=member, guild=member.guild)
                await member.send(embed=discord.Embed(title="💌 Szia!", description=text, color=discord.Color.pink()))
            except: pass

    @tasks.loop(minutes=5)
    async def check_platforms(self):
        pass
    @check_platforms.before_loop
    async def before_check_platforms(self):
        await self.wait_until_ready()

if __name__ == "__main__":
    token = os.getenv("JASMINE_TOKEN") or os.getenv("DISCORD_TOKEN")
    bot = Jasmine()
    bot.run(token)
