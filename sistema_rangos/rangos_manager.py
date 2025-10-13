import json
import os
import asyncio
from datetime import datetime, timedelta, timezone
import discord
from collections import defaultdict

class RangosManager:
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/rangos_data.json"
        self.canal_debug_id = 1422599371664396399
        self.ensure_data_file()
        self.load_data()
        
        self.rangos = {
            "Novato": {
                "requisito": {"tiempo": 0, "mensajes": 0},
                "color": 0x808080
            },
            "Experimentado": {
                "requisito": {"tiempo": 30, "mensajes": 500},
                "color": 0x00ff00
            },
            "Experto": {
                "requisito": {"tiempo": 90, "mensajes": 1500},
                "color": 0x0000ff
            },
            "Pro": {
                "requisito": {"tiempo": 180, "mensajes": 3000},
                "color": 0xff9900
            },
            "Leyenda": {
                "requisito": {"tiempo": 365, "mensajes": 5000},
                "color": 0xff0000
            }
        }
        
        self.rango_order = ["Novato", "Experimentado", "Experto", "Pro", "Leyenda"]

    def ensure_data_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({}, f)

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                self.user_data = json.load(f)
        except:
            self.user_data = {}
            self.save_data()

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.user_data, f, indent=4)

    def get_user_data(self, user_id):
        user_id = str(user_id)
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "mensajes": 0,
                "fecha_union": datetime.now(timezone.utc).isoformat(),
                "ultimo_mensaje": None,
                "rango_actual": "Novato",
                "mensajes_historial": defaultdict(int)
            }
        return self.user_data[user_id]

    async def enviar_debug(self, mensaje):
        try:
            canal_debug = self.bot.get_channel(self.canal_debug_id)
            if canal_debug:
                await canal_debug.send(f"[RANGOS_DEBUG] {mensaje}")
        except Exception as e:
            print(f"Error enviando debug: {e}")

    async def verificar_rango_actual(self, member):
        for rango_nombre in self.rangos.keys():
            role = discord.utils.get(member.roles, name=rango_nombre)
            if role:
                return rango_nombre
        return "Novato"

    async def sincronizar_rango_discord(self, member):
        try:
            rango_discord = await self.verificar_rango_actual(member)
            user_data = self.get_user_data(member.id)
            
            if rango_discord != user_data["rango_actual"]:
                user_data["rango_actual"] = rango_discord
                self.save_data()
                await self.enviar_debug(f"Rango sincronizado para {member.id}: {rango_discord}")
            
            return rango_discord
            
        except Exception as e:
            await self.enviar_debug(f"Error sincronizando rango para {member.id}: {e}")
            return "Novato"

    async def asignar_rango_novato(self, member):
        if member.bot:
            return
            
        try:
            guild = member.guild
            novato_role = discord.utils.get(guild.roles, name="Novato")
            
            if not novato_role:
                novato_role = await guild.create_role(
                    name="Novato",
                    color=discord.Color(0x808080),
                    mentionable=False,
                    reason="Rango automático para nuevos miembros"
                )
                await self.enviar_debug(f"Rol Novato creado en {guild.name}")
            
            rango_actual = await self.verificar_rango_actual(member)
            if rango_actual == "Novato" and novato_role not in member.roles:
                await member.add_roles(novato_role)
                await self.enviar_debug(f"Usuario {member.id} se le asigno el rango Novato por entrar al servidor")
            
            user_data = self.get_user_data(member.id)
            if member.joined_at:
                user_data["fecha_union"] = member.joined_at.isoformat()
            else:
                user_data["fecha_union"] = datetime.now(timezone.utc).isoformat()
            user_data["rango_actual"] = rango_actual
            self.save_data()
            
        except Exception as e:
            await self.enviar_debug(f"Error asignando rango novato a {member.id}: {e}")

    async def inicializar_servidor(self, guild):
        await self.enviar_debug(f"Inicializando sistema de rangos en: {guild.name}")
        
        roles_creados = {}
        for rango_nombre in self.rangos.keys():
            role = discord.utils.get(guild.roles, name=rango_nombre)
            if not role:
                try:
                    role = await guild.create_role(
                        name=rango_nombre,
                        color=discord.Color(self.rangos[rango_nombre]["color"]),
                        mentionable=True,
                        reason="Sistema automático de rangos"
                    )
                    await self.enviar_debug(f"Rol creado: {rango_nombre}")
                except Exception as e:
                    await self.enviar_debug(f"Error creando rol {rango_nombre}: {e}")
                    continue
            roles_creados[rango_nombre] = role
        
        miembros_sincronizados = 0
        for member in guild.members:
            if not member.bot:
                try:
                    rango_actual = await self.sincronizar_rango_discord(member)
                    
                    rol_correcto = roles_creados.get(rango_actual)
                    if rol_correcto and rol_correcto not in member.roles:
                        for rango in self.rangos.keys():
                            if rango != rango_actual:
                                role_to_remove = discord.utils.get(guild.roles, name=rango)
                                if role_to_remove and role_to_remove in member.roles:
                                    await member.remove_roles(role_to_remove)
                        
                        await member.add_roles(rol_correcto)
                        await self.enviar_debug(f"Rol {rango_actual} restaurado para {member.id}")
                    
                    miembros_sincronizados += 1
                    
                except Exception as e:
                    await self.enviar_debug(f"Error sincronizando miembro {member.id}: {e}")
        
        await self.enviar_debug(f"{miembros_sincronizados} miembros sincronizados con sus rangos")

    async def procesar_mensaje(self, message):
        if message.author.bot:
            return
            
        user_data = self.get_user_data(message.author.id)
        user_data["mensajes"] += 1
        user_data["ultimo_mensaje"] = datetime.now(timezone.utc).isoformat()
        
        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        user_data["mensajes_historial"][hoy] += 1
        
        self.save_data()
        
        await self.verificar_rango(message.author, message.guild)

    async def verificar_rango(self, member, guild):
        if member.bot:
            return
            
        user_data = self.get_user_data(member.id)
        rango_actual = user_data["rango_actual"]
        
        # CORRECCIÓN: Hacer ambas fechas "aware" con zona horaria
        fecha_union = datetime.fromisoformat(user_data["fecha_union"])
        if fecha_union.tzinfo is None:
            fecha_union = fecha_union.replace(tzinfo=timezone.utc)
        
        tiempo_en_servidor = (datetime.now(timezone.utc) - fecha_union).days
        total_mensajes = user_data["mensajes"]
        
        current_index = self.rango_order.index(rango_actual)
        if current_index < len(self.rango_order) - 1:
            next_rango = self.rango_order[current_index + 1]
            requisitos = self.rangos[next_rango]["requisito"]
            
            if (tiempo_en_servidor >= requisitos["tiempo"] and 
                total_mensajes >= requisitos["mensajes"]):
                
                await self.asignar_nuevo_rango(member, guild, next_rango, user_data)
                return True
        
        return False

    async def asignar_nuevo_rango(self, member, guild, nuevo_rango, user_data):
        try:
            rol_actual = discord.utils.get(guild.roles, name=user_data["rango_actual"])
            nuevo_rol = discord.utils.get(guild.roles, name=nuevo_rango)
            
            if not nuevo_rol:
                await self.enviar_debug(f"Rol {nuevo_rango} no encontrado")
                return
            
            for rango in self.rangos.keys():
                role_to_remove = discord.utils.get(guild.roles, name=rango)
                if role_to_remove and role_to_remove in member.roles:
                    await member.remove_roles(role_to_remove)
            
            await member.add_roles(nuevo_rol)
            
            user_data["rango_actual"] = nuevo_rango
            user_data["ultimo_rango"] = datetime.now(timezone.utc).isoformat()
            self.save_data()
            
            await self.enviar_anuncio_rango(member, guild, nuevo_rango)
            await self.enviar_debug(f"Usuario {member.id} ha subido a {nuevo_rango}")
            
        except Exception as e:
            await self.enviar_debug(f"Error asignando rango a {member.id}: {e}")

    async def forzar_rango_comando(self, member, guild, rango, ejecutor):
        try:
            nuevo_rol = discord.utils.get(guild.roles, name=rango)
            
            if not nuevo_rol:
                await self.enviar_debug(f"Rol {rango} no encontrado para forzar")
                return False
            
            for rango_existente in self.rangos.keys():
                role_to_remove = discord.utils.get(guild.roles, name=rango_existente)
                if role_to_remove and role_to_remove in member.roles:
                    await member.remove_roles(role_to_remove)
            
            await member.add_roles(nuevo_rol)
            
            user_data = self.get_user_data(member.id)
            user_data["rango_actual"] = rango
            user_data["ultimo_rango"] = datetime.now(timezone.utc).isoformat()
            self.save_data()
            
            await self.enviar_debug(f"Usuario {member.id} forzado a rango {rango} por {ejecutor.id}")
            return True
            
        except Exception as e:
            await self.enviar_debug(f"Error forzando rango a {member.id}: {e}")
            return False

    async def enviar_anuncio_rango(self, member, guild, nuevo_rango):
        canal_avisos = self.bot.get_channel(1421709050659475466)
        if not canal_avisos:
            canal_avisos = guild.system_channel or guild.text_channels[0]
        
        if canal_avisos:
            embed = discord.Embed(
                title="🎉 ¡NUEVO RANGO ALCANZADO!",
                description=f"Felicidades {member.mention} has subido de rango!",
                color=self.rangos[nuevo_rango]["color"]
            )
            embed.add_field(name="📈 Rango Obtenido", value=f"**{nuevo_rango}**", inline=True)
            embed.add_field(name="⭐ Progreso", value=f"Siguiente rango: {self.get_next_rango(nuevo_rango)}", inline=True)
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            
            await canal_avisos.send(embed=embed)

    def get_next_rango(self, rango_actual):
        index = self.rango_order.index(rango_actual)
        if index < len(self.rango_order) - 1:
            return self.rango_order[index + 1]
        return "Máximo rango alcanzado"

    def get_user_stats(self, user_id):
        user_data = self.get_user_data(user_id)
        
        # CORRECCIÓN: Manejar correctamente las fechas con zona horaria
        fecha_union = datetime.fromisoformat(user_data["fecha_union"])
        if fecha_union.tzinfo is None:
            fecha_union = fecha_union.replace(tzinfo=timezone.utc)
        
        tiempo_en_servidor = (datetime.now(timezone.utc) - fecha_union).days
        
        return {
            "rango_actual": user_data["rango_actual"],
            "tiempo_dias": tiempo_en_servidor,
            "mensajes_totales": user_data["mensajes"],
            "proximo_rango": self.get_next_rango(user_data["rango_actual"]),
            "requisitos_proximo": self.rangos.get(self.get_next_rango(user_data["rango_actual"]), {}).get("requisito", {})
        }