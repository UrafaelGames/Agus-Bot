import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import json
import os

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rol_admin_id = 1390486534410604737
        self.canal_logs_id = 1422599371664396399
        self.data_file = "data/advertencias.json"
        self.ensure_data_file()
        self.load_data()

    def ensure_data_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({}, f)

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                self.advertencias_data = json.load(f)
        except:
            self.advertencias_data = {}
            self.save_data()

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.advertencias_data, f, indent=4)

    def get_user_warnings(self, user_id):
        user_id = str(user_id)
        if user_id not in self.advertencias_data:
            self.advertencias_data[user_id] = []
        return self.advertencias_data[user_id]

    async def enviar_log(self, embed):
        try:
            canal_logs = self.bot.get_channel(self.canal_logs_id)
            if canal_logs:
                await canal_logs.send(embed=embed)
        except Exception as e:
            print(f"Error enviando log: {e}")

    def tiene_permisos_admin(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        
        admin_role = ctx.guild.get_role(self.rol_admin_id)
        if admin_role and admin_role in ctx.author.roles:
            return True
        
        return False

    async def verificar_permisos(self, ctx):
        if not self.tiene_permisos_admin(ctx):
            await ctx.send("❌ No tienes permisos para usar este comando.")
            return False
        return True

    async def obtener_rol_silencio(self, guild):
        muted_role = discord.utils.get(guild.roles, name="Silenciado")
        if not muted_role:
            muted_role = await guild.create_role(
                name="Silenciado",
                color=discord.Color(0x666666),
                reason="Rol para usuarios silenciados"
            )
            
            for channel in guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        
        return muted_role

    async def aplicar_silenciar(self, miembro, guild):
        try:
            muted_role = await self.obtener_rol_silencio(guild)
            await miembro.add_roles(muted_role)
   
            embed_log = discord.Embed(
                title="🔇 SILENCIO AUTOMÁTICO",
                color=0xff6600,
                timestamp=datetime.now()
            )
            embed_log.add_field(name="Usuario", value=f"{miembro.mention} (`{miembro.id}`)", inline=True)
            embed_log.add_field(name="Razón", value="3 advertencias acumuladas", inline=True)
            embed_log.add_field(name="Duración", value="1 minuto", inline=True)
            embed_log.set_footer(text="Sistema automático de moderación")
            
            await self.enviar_log(embed_log)
            
            # Esperar 1 minuto y quitar silencio
            await asyncio.sleep(60)
            await miembro.remove_roles(muted_role)
            
        except Exception as e:
            print(f"Error aplicando silencio: {e}")

    @commands.command(name="adv")
    async def advertir(self, ctx, miembro: discord.Member, *, razon: str = "Sin razón especificada"):
        if not await self.verificar_permisos(ctx):
            return

        user_warnings = self.get_user_warnings(miembro.id)
        warning_data = {
            "moderador": ctx.author.id,
            "razon": razon,
            "fecha": datetime.now().isoformat(),
            "id_advertencia": len(user_warnings) + 1
        }
        user_warnings.append(warning_data)
        self.save_data()

        total_warnings = len(user_warnings)

        embed = discord.Embed(
            title="⚠️ ADVERTENCIA",
            color=0xff9900
        )
        embed.add_field(name="Usuario", value=miembro.mention, inline=True)
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Advertencia", value=f"{total_warnings}/3", inline=True)
        embed.add_field(name="Razón", value=razon, inline=False)
        embed.set_footer(text=f"ID: {miembro.id}")

        await ctx.send(embed=embed)

        embed_log = discord.Embed(
            title="📝 ADVERTENCIA REGISTRADA",
            color=0xff9900,
            timestamp=datetime.now()
        )
        embed_log.add_field(name="Usuario", value=f"{miembro.mention} (`{miembro.id}`)", inline=True)
        embed_log.add_field(name="Moderador", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
        embed_log.add_field(name="Advertencias", value=f"{total_warnings}/3", inline=True)
        embed_log.add_field(name="Razón", value=razon, inline=False)
        
        await self.enviar_log(embed_log)

        if total_warnings >= 3:
            await ctx.send(f"🚨 {miembro.mention} ha alcanzado 3 advertencias. Silenciando por 1 minuto...")
            await self.aplicar_silenciar(miembro, ctx.guild)
            
            self.advertencias_data[str(miembro.id)] = []
            self.save_data()

    @commands.command(name="userid")
    async def user_id(self, ctx, miembro: discord.Member = None):
        if not await self.verificar_permisos(ctx):
            return

        if not miembro:
            miembro = ctx.author

        await ctx.send(f"🆔 **ID de {miembro.display_name}:** `{miembro.id}`")

    @commands.command(name="kick")
    async def expulsar(self, ctx, miembro: discord.Member, *, razon: str = "Sin razón especificada"):
        if not await self.verificar_permisos(ctx):
            return

        if miembro == ctx.author:
            await ctx.send("❌ No puedes expulsarte a ti mismo.")
            return

        if miembro == self.bot.user:
            await ctx.send("❌ No puedo expulsarme a mí mismo.")
            return

        embed = discord.Embed(
            title="👢 USUARIO EXPULSADO",
            color=0xff9900
        )
        embed.add_field(name="Usuario", value=miembro.mention, inline=True)
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Razón", value=razon, inline=False)
        embed.set_footer(text=f"ID: {miembro.id}")

        # Mensaje al usuario
        kick_msg = (
            f"**Has sido expulsado del servidor {ctx.guild.name}**\n\n"
            f"**Razón:** {razon}\n"
            f"**Moderador:** {ctx.author.display_name}\n"
            f"**Tu ID:** `{miembro.id}`\n\n"
            f"📝 **Puedes volver a unirte si así lo deseas.**"
        )

        try:
            await miembro.send(kick_msg)
        except:
            pass

        await miembro.kick(reason=razon)
        await ctx.send(embed=embed)

        # Log de expulsión
        embed_log = discord.Embed(
            title="👢 EXPULSIÓN",
            color=0xff9900,
            timestamp=datetime.now()
        )
        embed_log.add_field(name="Usuario", value=f"{miembro.display_name} (`{miembro.id}`)", inline=True)
        embed_log.add_field(name="Moderador", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
        embed_log.add_field(name="Razón", value=razon, inline=False)
        embed_log.set_footer(text="Sistema de moderación")
        
        await self.enviar_log(embed_log)

    @commands.command(name="mute")
    async def silenciar(self, ctx, miembro: discord.Member, duracion: str = "10m", *, razon: str = "Sin razón especificada"):
        if not await self.verificar_permisos(ctx):
            return

        if miembro == ctx.author:
            await ctx.send("❌ No puedes silenciarte a ti mismo.")
            return

        if miembro == self.bot.user:
            await ctx.send("❌ No puedo silenciarme a mí mismo.")
            return

        # duraciom = segundos
        duracion_segundos = 0
        try:
            if duracion.endswith('m'):
                duracion_segundos = int(duracion[:-1]) * 60
            elif duracion.endswith('h'):
                duracion_segundos = int(duracion[:-1]) * 3600
            elif duracion.endswith('d'):
                duracion_segundos = int(duracion[:-1]) * 86400
            else:
                duracion_segundos = int(duracion)
        except ValueError:
            await ctx.send("❌ Formato de duración inválido. Usa: `10m` (minutos), `2h` (horas), `1d` (días)")
            return

        tiempo_fin = datetime.now() + timedelta(seconds=duracion_segundos)

        try:
            muted_role = await self.obtener_rol_silencio(ctx.guild)
            await miembro.add_roles(muted_role)

            embed = discord.Embed(
                title="🔇 USUARIO SILENCIADO",
                color=0x666666
            )
            embed.add_field(name="Usuario", value=miembro.mention, inline=True)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="Duración", value=duracion, inline=True)
            embed.add_field(name="Fin del mute", value=f"<t:{int(tiempo_fin.timestamp())}:R>", inline=True)
            embed.add_field(name="Razón", value=razon, inline=False)
            embed.set_footer(text=f"ID: {miembro.id}")

            await ctx.send(embed=embed)

            # Log de silencio
            embed_log = discord.Embed(
                title="🔇 SILENCIO MANUAL",
                color=0x666666,
                timestamp=datetime.now()
            )
            embed_log.add_field(name="Usuario", value=f"{miembro.mention} (`{miembro.id}`)", inline=True)
            embed_log.add_field(name="Moderador", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
            embed_log.add_field(name="Duración", value=duracion, inline=True)
            embed_log.add_field(name="Fin del mute", value=f"<t:{int(tiempo_fin.timestamp())}:R>", inline=True)
            embed_log.add_field(name="Razón", value=razon, inline=False)
            
            await self.enviar_log(embed_log)

            await asyncio.sleep(duracion_segundos)
            try:
                await miembro.remove_roles(muted_role)
                
            
                embed_log_desmute = discord.Embed(
                    title="DESMUTE AUTOMÁTICO",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed_log_desmute.add_field(name="Usuario", value=f"{miembro.display_name} (`{miembro.id}`)", inline=True)
                embed_log_desmute.add_field(name="Razón", value="Fin del silencio temporal", inline=True)
                
                await self.enviar_log(embed_log_desmute)
                
            except:
                pass

        except Exception as e:
            await ctx.send(f"❌ Error al silenciar: {e}")

    @commands.command(name="unmute")
    async def desilenciar(self, ctx, miembro: discord.Member):
        if not await self.verificar_permisos(ctx):
            return

        try:
            muted_role = await self.obtener_rol_silencio(ctx.guild)
            
            if muted_role not in miembro.roles:
                await ctx.send("❌ Este usuario no está silenciado.")
                return

            await miembro.remove_roles(muted_role)

            embed = discord.Embed(
                title="USUARIO DESILENCIADO",
                color=0x00ff00
            )
            embed.add_field(name="Usuario", value=miembro.mention, inline=True)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"ID: {miembro.id}")

            await ctx.send(embed=embed)

            embed_log = discord.Embed(
                title="DESMUTE MANUAL",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed_log.add_field(name="Usuario", value=f"{miembro.mention} (`{miembro.id}`)", inline=True)
            embed_log.add_field(name="Moderador", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
            
            await self.enviar_log(embed_log)

        except Exception as e:
            await ctx.send(f"❌ Error al desilenciar: {e}")

    @commands.command(name="ban")
    async def banear(self, ctx, miembro: discord.Member, *, razon: str = "Sin razón especificada"):
        if not await self.verificar_permisos(ctx):
            return

        if miembro == ctx.author:
            await ctx.send("❌ No puedes banearte a ti mismo.")
            return

        if miembro == self.bot.user:
            await ctx.send("❌ No puedo banearme a mí mismo.")
            return

        embed = discord.Embed(
            title="🔨 USUARIO BANEADO",
            color=0xff0000
        )
        embed.add_field(name="Usuario", value=miembro.mention, inline=True)
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Razón", value=razon, inline=False)
        embed.set_footer(text=f"ID: {miembro.id}")

        # mensaje apelacion md
        apelacion_msg = (
            f"🔨 **Has sido baneado del servidor {ctx.guild.name}**\n\n"
            f"**Razón:** {razon}\n"
            f"**Moderador:** {ctx.author.display_name}\n"
            f"**Tu ID:** `{miembro.id}`\n\n"
            f"📝 **Si crees que esto fue un error, puedes apelar aquí:**\n"
            f"proximamente\n\n"
            f"⚠️ **Incluye tu ID en la apelación:** `{miembro.id}`"
        )

        try:
            await miembro.send(apelacion_msg)
        except:
            pass

        await miembro.ban(reason=razon)
        await ctx.send(embed=embed)

        # Log de ban
        embed_log = discord.Embed(
            title="🔨 BAN PERMANENTE",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed_log.add_field(name="Usuario", value=f"{miembro.display_name} (`{miembro.id}`)", inline=True)
        embed_log.add_field(name="Moderador", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
        embed_log.add_field(name="Razón", value=razon, inline=False)
        embed_log.add_field(name="ID para apelación", value=f"`{miembro.id}`", inline=False)
        embed_log.set_footer(text="Sistema de moderación")
        
        await self.enviar_log(embed_log)

    @commands.command(name="bantemporal")
    async def ban_temporal(self, ctx, miembro: discord.Member, duracion: str, *, razon: str = "Sin razón especificada"):
        if not await self.verificar_permisos(ctx):
            return

        if miembro == ctx.author:
            await ctx.send("❌ No puedes banearte a ti mismo.")
            return

        if miembro == self.bot.user:
            await ctx.send("❌ No puedo banearme a mí mismo.")
            return

        duracion_segundos = 0
        try:
            if duracion.endswith('m'):
                duracion_segundos = int(duracion[:-1]) * 60
            elif duracion.endswith('h'):
                duracion_segundos = int(duracion[:-1]) * 3600
            elif duracion.endswith('d'):
                duracion_segundos = int(duracion[:-1]) * 86400
            else:
                duracion_segundos = int(duracion)
        except ValueError:
            await ctx.send("❌ Formato de duración inválido. Usa: `10m` (minutos), `2h` (horas), `1d` (días)")
            return

        tiempo_fin = datetime.now() + timedelta(seconds=duracion_segundos)

        embed = discord.Embed(
            title="⏰ BAN TEMPORAL",
            color=0xff6600
        )
        embed.add_field(name="Usuario", value=miembro.mention, inline=True)
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Duración", value=duracion, inline=True)
        embed.add_field(name="Fin del ban", value=f"<t:{int(tiempo_fin.timestamp())}:R>", inline=True)
        embed.add_field(name="Razón", value=razon, inline=False)
        embed.set_footer(text=f"ID: {miembro.id}")

        # mensaje md
        apelacion_msg = (
            f"⏰ **Has sido baneado temporalmente de {ctx.guild.name}**\n\n"
            f"**Duración:** {duracion}\n"
            f"**Razón:** {razon}\n"
            f"**Moderador:** {ctx.author.display_name}\n"
            f"**Tu ID:** `{miembro.id}`\n\n"
            f"📝 **Si crees que esto fue un error, puedes apelar aquí:**\n"
            f"proximamente\n\n"
            f"⚠️ **Incluye tu ID en la apelación:** `{miembro.id}`"
        )

        try:
            await miembro.send(apelacion_msg)
        except:
            pass

        await miembro.ban(reason=f"Temporal: {razon} - Duración: {duracion}")
        await ctx.send(embed=embed)

        # Log de ban temporal
        embed_log = discord.Embed(
            title="⏰ BAN TEMPORAL",
            color=0xff6600,
            timestamp=datetime.now()
        )
        embed_log.add_field(name="Usuario", value=f"{miembro.display_name} (`{miembro.id}`)", inline=True)
        embed_log.add_field(name="Moderador", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
        embed_log.add_field(name="Duración", value=duracion, inline=True)
        embed_log.add_field(name="Fin del ban", value=f"<t:{int(tiempo_fin.timestamp())}:R>", inline=True)
        embed_log.add_field(name="Razón", value=razon, inline=False)
        embed_log.add_field(name="ID para apelación", value=f"`{miembro.id}`", inline=False)
        
        await self.enviar_log(embed_log)

        # progarmar desban automatico
        await asyncio.sleep(duracion_segundos)
        try:
            await ctx.guild.unban(miembro)
            
            # Log de desban automático
            embed_log_desban = discord.Embed(
                title="✅ DESBAN AUTOMÁTICO",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed_log_desban.add_field(name="Usuario", value=f"{miembro.display_name} (`{miembro.id}`)", inline=True)
            embed_log_desban.add_field(name="Razón", value="Fin del ban temporal", inline=True)
            
            await self.enviar_log(embed_log_desban)
            
        except:
            pass

    @commands.command(name="unban")
    async def desbanear(self, ctx, user_id: int):
        if not await self.verificar_permisos(ctx):
            return

        try:
            usuario = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(usuario)

            embed = discord.Embed(
                title="USUARIO DESBANEADO",
                color=0x00ff00
            )
            embed.add_field(name="Usuario", value=usuario.mention, inline=True)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="ID", value=user_id, inline=True)

            await ctx.send(embed=embed)

            # Log de desban
            embed_log = discord.Embed(
                title="DESBAN MANUAL",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed_log.add_field(name="Usuario", value=f"{usuario.display_name} (`{user_id}`)", inline=True)
            embed_log.add_field(name="Moderador", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
            
            await self.enviar_log(embed_log)

        except discord.NotFound:
            await ctx.send("❌ Usuario no encontrado o no está baneado.")
        except Exception as e:
            await ctx.send(f"❌ Error al desbanear: {e}")

    @commands.command(name="advertencias")
    async def ver_advertencias(self, ctx, miembro: discord.Member = None):
        if not await self.verificar_permisos(ctx):
            return

        if not miembro:
            miembro = ctx.author

        user_warnings = self.get_user_warnings(miembro.id)
        
        embed = discord.Embed(
            title=f"📋 ADVERTENCIAS DE {miembro.display_name}",
            color=0xff9900
        )
        embed.add_field(name="Total", value=f"{len(user_warnings)}/3", inline=True)
        
        if user_warnings:
            for i, warning in enumerate(user_warnings[-5:], 1):  # mostrar ultimas 5 adv
                moderador = ctx.guild.get_member(warning["moderador"])
                mod_name = moderador.mention if moderador else f"ID: {warning['moderador']}"
                fecha = datetime.fromisoformat(warning["fecha"]).strftime("%d/%m/%Y %H:%M")
                
                embed.add_field(
                    name=f"Advertencia #{warning['id_advertencia']}",
                    value=f"**Mod:** {mod_name}\n**Razón:** {warning['razon']}\n**Fecha:** {fecha}",
                    inline=False
                )
        else:
            embed.add_field(name="Estado", value="✅ No tiene advertencias", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))