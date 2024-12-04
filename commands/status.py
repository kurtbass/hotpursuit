import discord
from discord.ext import commands
import asyncio
import logging
from utils.database import execute_query, get_config

# Configuração de logs
logger = logging.getLogger(__name__)

class StatusCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_ids = [self.safe_get_config("DONO", is_int=True)]
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"
        self.timeout = 60
        self.default_streaming_url = "https://www.twitch.tv/seu_canal"

    def safe_get_config(self, key, is_int=False):
        """Obtém uma configuração do banco de forma segura."""
        try:
            value = get_config(key)
            if not value:
                logger.warning(f"Configuração '{key}' não encontrada no banco.")
                return None
            return int(value) if is_int else value
        except Exception as e:
            logger.error(f"Erro ao carregar configuração '{key}': {e}")
            return None

    def create_embed(self, title, description, color=0xFF8000):
        """Cria um embed padronizado com o lema."""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=self.lema)
        return embed

    async def send_embed(self, ctx, title, description, color=0xFF8000):
        """Envia um embed padronizado."""
        embed = self.create_embed(title, description, color)
        return await ctx.send(embed=embed)

    async def wait_for_response(self, ctx, check, error_message=None):
        """Espera por uma resposta do usuário."""
        try:
            return await self.bot.wait_for("message", timeout=self.timeout, check=check)
        except asyncio.TimeoutError:
            if error_message:
                await self.send_embed(ctx, "Tempo Esgotado", error_message, 0xFF0000)
            return None

    async def validate_choice(self, ctx, response, valid_choices, choice_type):
        """Valida escolhas do usuário."""
        choice = response.content.strip()
        if choice not in valid_choices:
            await self.send_embed(ctx, "Erro", f"Escolha inválida. {choice_type} disponíveis: {', '.join(valid_choices)}.", 0xFF0000)
            return None
        return choice

    @commands.command(name="status")
    async def status(self, ctx):
        """Comando para alterar o status do bot e salvar no banco."""
        if ctx.author.id not in self.allowed_ids:
            await self.send_embed(ctx, "Sem Permissão", f"{ctx.author.mention}, você não tem permissão para usar este comando.", 0xFF0000)
            return

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        # Escolher tipo de status
        valid_types = {"1": "Jogando", "2": "Transmitindo", "3": "Ouvindo", "4": "Assistindo"}
        await self.send_embed(ctx, "Escolha o Tipo de Status", "1. Jogando\n2. Transmitindo\n3. Ouvindo\n4. Assistindo")
        response = await self.wait_for_response(ctx, check, "O comando foi cancelado por falta de resposta.")
        if not response:
            return
        status_type = await self.validate_choice(ctx, response, valid_types.keys(), "Tipos")
        if not status_type:
            return

        # Mensagem do status
        await self.send_embed(ctx, "Mensagem do Status", "Digite a mensagem para o status.")
        response = await self.wait_for_response(ctx, check, "O comando foi cancelado por falta de resposta.")
        if not response:
            return
        status_message = response.content.strip()

        # Estado do bot
        discord_status = discord.Status.online
        if status_type != "2":
            valid_states = {"1": "Online", "2": "Ocupado", "3": "Ausente", "4": "Offline"}
            await self.send_embed(ctx, "Selecione o Estado do Bot", "1. Online\n2. Ocupado\n3. Ausente\n4. Offline")
            response = await self.wait_for_response(ctx, check, "O comando foi cancelado por falta de resposta.")
            if not response:
                return
            status_state = await self.validate_choice(ctx, response, valid_states.keys(), "Estados")
            if not status_state:
                return

            status_map = {"1": discord.Status.online, "2": discord.Status.dnd, "3": discord.Status.idle, "4": discord.Status.invisible}
            discord_status = status_map[status_state]

        # Configurar atividade
        activity = None
        if status_type == "1":
            activity = discord.Game(name=status_message)
        elif status_type == "2":
            await self.send_embed(ctx, "URL de Transmissão", "Digite a URL ou `padrão` para usar uma URL padrão.")
            response = await self.wait_for_response(ctx, check)
            if not response:
                return
            url = response.content.strip()
            activity = discord.Streaming(name=status_message, url=self.default_streaming_url if url.lower() == "padrão" else url)
        elif status_type == "3":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status_message)
        elif status_type == "4":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status_message)

        # Salvar no banco de dados apenas a linha 2
        try:
            execute_query(
                "UPDATE status SET status_type = ?, status_message = ?, status_status = ? WHERE id = 2",
                (status_type, status_message, str(discord_status))
            )
            logger.info(f"Status atualizado na linha 2: {status_message} ({discord_status})")
        except Exception as e:
            logger.error(f"Erro ao salvar status no banco de dados: {e}")
            await self.send_embed(ctx, "Erro", "Ocorreu um erro ao salvar o status no banco de dados.", 0xFF0000)
            return

        # Aplicar status
        try:
            await self.bot.change_presence(activity=activity, status=discord_status)
            await self.send_embed(ctx, "Status Atualizado", f"Novo status definido como:\n**{status_message}**", 0x00FF00)
        except Exception as e:
            logger.error(f"Erro ao alterar o status do bot: {e}")
            await self.send_embed(ctx, "Erro", "Ocorreu um erro ao tentar alterar o status.", 0xFF0000)


async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(StatusCommand(bot))
