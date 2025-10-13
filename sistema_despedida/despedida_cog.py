import discord
from discord.ext import commands

class DespedidaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.canal_despedida_id = 1424069887911006340

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
            
        canal_despedida = self.bot.get_channel(self.canal_despedida_id)
        if not canal_despedida:
            return

        embed = discord.Embed(
            title="👋 ¡HASTA PRONTO!",
            description=f"{member.display_name} ha abandonado el servidor",
            color=0xff0000
        )
        
        embed.add_field(
            name="💔 Nos vemos",
            value="Esperamos que vuelvas pronto. ¡Te extrañaremos!",
            inline=False
        )
        
        embed.add_field(
            name="👥 Miembros restantes",
            value=f"Ahora somos {canal_despedida.guild.member_count} miembros",
            inline=True
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text="¡Que tengas un buen día!")
        
        await canal_despedida.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DespedidaCog(bot))