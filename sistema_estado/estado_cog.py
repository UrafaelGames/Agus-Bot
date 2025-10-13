import discord
from discord.ext import commands

class SistemaEstado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.estado_actual = {"tipo": "playing", "nombre": "agus!ayuda"}
        self.canal_logs_id = 1422599371664396399

    async def enviar_log(self, mensaje):
        try:
            canal_logs = self.bot.get_channel(self.canal_logs_id)
            if canal_logs:
                await canal_logs.send(f"[ESTADO_DEBUG] {mensaje}")
        except Exception as e:
            print(f"Error enviando log: {e}")

    @commands.command(name="estado")
    @commands.has_permissions(administrator=True)
    async def cambiar_estado(self, ctx, tipo: str, *, nombre: str):
        tipos_validos = ["playing", "watching", "streaming", "listening", "competing"]
        
        if tipo.lower() not in tipos_validos:
            await ctx.send(f"❌ Tipo de estado no válido. Usa: {', '.join(tipos_validos)}")
            await self.enviar_log(f"Intento de cambio de estado fallido - Tipo inválido: {tipo}")
            return

        self.estado_actual = {"tipo": tipo.lower(), "nombre": nombre}
        
        try:
            if tipo.lower() == "playing":
                await self.bot.change_presence(activity=discord.Game(name=nombre))
            elif tipo.lower() == "watching":
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=nombre))
            elif tipo.lower() == "streaming":
                await self.bot.change_presence(activity=discord.Streaming(name=nombre, url=""))
            elif tipo.lower() == "listening":
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=nombre))
            elif tipo.lower() == "competing":
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=nombre))
            
            await ctx.send(f"✅ Estado cambiado a: **{tipo} {nombre}**")
            await self.enviar_log(f"Estado cambiado por {ctx.author.id} - {tipo} {nombre}")
            
        except Exception as e:
            await ctx.send(f"❌ Error cambiando estado: {e}")
            await self.enviar_log(f"Error cambiando estado: {e}")

    @commands.command(name="estadoinfo")
    async def estado_info(self, ctx):
        embed = discord.Embed(
            title="🤖 Estado Actual del Bot",
            color=0x00ff00
        )
        embed.add_field(name="Tipo", value=self.estado_actual["tipo"], inline=True)
        embed.add_field(name="Nombre", value=self.estado_actual["nombre"], inline=True)
        embed.add_field(name="Comando", value="`:estado <tipo> <nombre>`", inline=False)
        embed.add_field(name="Tipos válidos", value="playing, watching, streaming, listening, competing", inline=False)
        
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            if self.estado_actual["tipo"] == "playing":
                await self.bot.change_presence(activity=discord.Game(name=self.estado_actual["nombre"]))
            elif self.estado_actual["tipo"] == "watching":
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=self.estado_actual["nombre"]))
            elif self.estado_actual["tipo"] == "streaming":
                await self.bot.change_presence(activity=discord.Streaming(name=self.estado_actual["nombre"], url=""))
            elif self.estado_actual["tipo"] == "listening":
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=self.estado_actual["nombre"]))
            elif self.estado_actual["tipo"] == "competing":
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=self.estado_actual["nombre"]))
            
            await self.enviar_log("Estado establecido al iniciar el bot")
        except Exception as e:
            error_msg = f"Error estableciendo estado al iniciar: {e}"
            print(error_msg)
            await self.enviar_log(error_msg)

async def setup(bot):
    await bot.add_cog(SistemaEstado(bot))