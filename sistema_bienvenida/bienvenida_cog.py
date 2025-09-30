import discord
from discord.ext import commands

class BienvenidaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.canal_bienvenida_id = 1421349847302275075

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
            
        canal_bienvenida = self.bot.get_channel(self.canal_bienvenida_id)
        if not canal_bienvenida:
            return

        embed = discord.Embed(
            title="🎉 ¡BIENVENIDO/A AL SERVIDOR DE AGUSLOVERS!",
            description=f"¡Hola {member.mention}! Esperamos que disfrutes tu estadía en nuestra comunidad.",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📖 Reglas importantes",
            value="• Por favor lee las reglas del servidor\n• Respeta a todos los miembros\n• Disfruta y diviértete",
            inline=False
        )
        
        embed.add_field(
            name="💬 Comienza a chatear",
            value="Preséntate en el canal de presentaciones y comienza a conocer a la comunidad",
            inline=False
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text="¡Que tengas un gran día!")
        
        await canal_bienvenida.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BienvenidaCog(bot))