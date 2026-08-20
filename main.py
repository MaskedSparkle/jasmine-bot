import discord
from discord.ext import commands
import datetime

class Jasmine(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def on_member_join(self, member):
        # A 123456789 helyére írd be a köszöntő csatorna ID-ját!
        channel = self.get_channel(1539791346880221196) 
        if not channel:
            return
        
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

    async def on_member_remove(self, member):
        # A 123456789 helyére írd be azt a csatornát, ahová a búcsút szeretnéd!
        channel = self.get_channel(1539791383815258172) 
        if not channel:
            return
        
        embed = discord.Embed(
            title="🥀 Egy túlélő elhagyott minket...",
            description=f"Jaj, {member.name} útra kelt... Nagyon fog hiányozni a Never SMP világából! 💔\nRemélem, még viszontlátjuk egymást valamikor... ✨",
            color=discord.Color.dark_gray()
        )
        
        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Jasmine, a szerver tündérkéje 🌸")
        
        await channel.send(embed=embed)

if __name__ == "__main__":
    bot = Jasmine()
    # Ide tedd be Jasmine tokenjét:
    bot.run("MTUzOTc4ODk0NTU0MDUxMzgzMg.G8d4EK.r-hDF_4X8twdVj89MgdCW4-Ovlig1acUSf1gvg")
