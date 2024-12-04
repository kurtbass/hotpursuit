import discord
from discord.ext import commands
import asyncio
import logging
from utils.database import get_config

# Configuração de logs
logger = logging.getLogger(__name__)

class UsernameCommand(commands.Cog):
    """Comando para alterar o nome do bot."""

    def __init__(self, bot):
        self.bot = bot
        self.allowed_ids = [
            self.safe_get_config("DONO", is_int=True),
            self.safe_get_config("SUBDONO", is_int=True)
        ]
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"
        self.timeout = 60  # Tempo padrão para respostas

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
        """Utilitário para enviar mensagens embed."""
        embed = self.create_embed(title, description, color)
        await ctx.send(embed=embed)

    def validate_username(self, username):
        """Valida o nome do bot."""
        if not username:
            return False, "O nome não pode estar vazio."
        if len(username) > 32:
            return False, "O nome deve ter no máximo 32 caracteres."
        if username == self.bot.user.name:
            return False, "O novo nome não pode ser igual ao nome atual."
        return True, None

    @commands.command(name="username", aliases=["setname"])
    async def username(self, ctx, *, new_name=None):
        """Comando para alterar o nome do bot."""
        if ctx.author.id not in self.allowed_ids:
            await self.send_embed(ctx, "Sem Permissão", f"{ctx.author.mention}, você não tem permissão para usar este comando.", 0xFF0000)
            logger.warning(f"Usuário {ctx.author} tentou alterar o nome do bot sem permissão.")
            return

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        # Solicitar novo nome, se não fornecido
        if not new_name:
            await self.send_embed(ctx, "Trocar Nome do Bot", f"{ctx.author.mention}, envie o novo nome para o bot. Você tem {self.timeout} segundos.")
            try:
                msg = await self.bot.wait_for("message", timeout=self.timeout, check=check)
                new_name = msg.content.strip()
                await msg.delete()  # Remove a mensagem do usuário
            except asyncio.TimeoutError:
                await self.send_embed(ctx, "Tempo Esgotado", f"{ctx.author.mention}, o tempo para enviar o novo nome expirou. O comando foi cancelado.", 0xFF0000)
                logger.warning(f"Tempo esgotado para resposta do comando 'username' de {ctx.author}.")
                return

        # Validar novo nome
        is_valid, error_message = self.validate_username(new_name)
        if not is_valid:
            await self.send_embed(ctx, "Erro", f"{ctx.author.mention}, {error_message}", 0xFF0000)
            logger.warning(f"Nome inválido '{new_name}' fornecido por {ctx.author} no comando 'username'.")
            return

        # Tentar alterar o nome
        try:
            await self.bot.user.edit(username=new_name)
            await self.send_embed(ctx, "Nome do Bot Alterado", f"{ctx.author.mention}, o nome do bot foi alterado para `{new_name}` com sucesso!", 0x00FF00)
            logger.info(f"Nome do bot alterado para '{new_name}' por {ctx.author} ({ctx.author.id}).")
        except discord.Forbidden:
            await self.send_embed(ctx, "Erro", f"{ctx.author.mention}, o bot não tem permissão para alterar o nome.", 0xFF0000)
            logger.error(f"Permissões insuficientes para alterar o nome do bot. Usuário: {ctx.author} ({ctx.author.id}).")
        except discord.HTTPException as e:
            await self.send_embed(ctx, "Erro", f"{ctx.author.mention}, ocorreu um erro ao alterar o nome do bot. Tente novamente mais tarde.", 0xFF0000)
            logger.error(f"Erro de API ao alterar o nome do bot: {e}")
        except Exception as e:
            await self.send_embed(ctx, "Erro", f"{ctx.author.mention}, ocorreu um erro inesperado: {e}", 0xFF0000)
            logger.error(f"Erro inesperado ao alterar o nome do bot: {e}")


async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(UsernameCommand(bot))
