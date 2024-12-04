import discord
from discord.ext import commands
import logging
from utils.database import get_config
import asyncio

# Configuração de logs
logger = logging.getLogger(__name__)

class LimparMensagens(commands.Cog):
    """Comando para limpar mensagens no canal."""

    def __init__(self, bot):
        self.bot = bot
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"
        self.cargo_autorizado = self.safe_get_config("TAG_STAFF", is_int=True)
        self.max_limite_tudo = 1000  # Limite máximo para "tudo"

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

    def create_embed(self, description, color=0xFF8000):
        """Cria um embed padronizado com o lema."""
        embed = discord.Embed(description=description, color=color)
        embed.set_footer(text=self.lema)
        return embed

    async def verificar_permissao(self, ctx):
        """Verifica se o autor do comando possui permissão para limpar mensagens."""
        if not self.cargo_autorizado:
            logger.warning("TAG_STAFF não configurado. Nenhum cargo autorizado pode executar este comando.")
            await ctx.send(
                embed=self.create_embed("⚠️ Nenhum cargo autorizado configurado. Procure o programador.", color=0xFF0000)
            )
            return False

        autorizado = any(role.id == self.cargo_autorizado for role in ctx.author.roles)
        if not autorizado:
            logger.warning(f"Usuário {ctx.author} tentou usar o comando sem permissão.")
            await ctx.send(
                embed=self.create_embed("⚠️ Você não tem permissão para executar este comando.", color=0xFF0000),
                delete_after=30,
            )
        return autorizado

    @commands.command(name="limpar")
    async def limpar(self, ctx, quantidade: str):
        """Comando principal para limpar mensagens."""
        if not await self.verificar_permissao(ctx):
            return

        # Validação da entrada
        if quantidade.lower() in ["all", "tudo"]:
            if not await self.confirmar_limpeza(ctx, "Deseja limpar todas as mensagens do canal?"):
                return
            total_deleted = await self.limpar_todas_mensagens(ctx)
        else:
            try:
                numero_de_mensagens = int(quantidade)
                if numero_de_mensagens <= 0:
                    raise ValueError
                total_deleted = await self.limpar_por_quantidade(ctx, numero_de_mensagens)
            except ValueError:
                await ctx.send(
                    embed=self.create_embed(
                        "⚠️ Por favor, forneça um número válido ou use `tudo` para apagar todas as mensagens.",
                        color=0xFF0000,
                    ),
                    delete_after=30,
                )
                return

        await self.enviar_feedback(ctx, total_deleted)

    async def confirmar_limpeza(self, ctx, message):
        """Confirmação de limpeza para ações críticas."""
        embed = self.create_embed(f"{message} Responda: `Sim` ou `Não`.", color=0xFFFF00)
        confirmation_message = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["sim", "não", "s", "n"]

        try:
            response = await self.bot.wait_for("message", timeout=30, check=check)
            await response.delete()
            await confirmation_message.delete()
            return response.content.lower() in ["sim", "s"]
        except asyncio.TimeoutError:
            await ctx.send(
                embed=self.create_embed("⚠️ Tempo esgotado. Ação cancelada.", color=0xFF0000),
                delete_after=30,
            )
            return False

    async def limpar_todas_mensagens(self, ctx):
        """Limpa todas as mensagens do canal, com limite máximo."""
        total_deleted = 0
        while total_deleted < self.max_limite_tudo:
            deleted = await ctx.channel.purge(limit=100)
            total_deleted += len(deleted)
            if len(deleted) < 100:  # Se deletou menos de 100, não há mais mensagens para apagar
                break

        if total_deleted >= self.max_limite_tudo:
            logger.warning(f"Limite máximo de {self.max_limite_tudo} mensagens atingido no canal '{ctx.channel.name}'.")

        # Log no terminal
        logger.info(f"{total_deleted} mensagens apagadas no canal '{ctx.channel.name}' por {ctx.author}.")
        return total_deleted

    async def limpar_por_quantidade(self, ctx, quantidade):
        """Limpa a quantidade especificada de mensagens."""
        deleted = await ctx.channel.purge(limit=quantidade)
        # Log no terminal
        logger.info(f"{len(deleted)} mensagens apagadas no canal '{ctx.channel.name}' por {ctx.author}.")
        return len(deleted)

    async def enviar_feedback(self, ctx, total_deleted):
        """Envia uma mensagem de feedback sobre a limpeza realizada."""
        embed = self.create_embed(f"**{total_deleted} mensagens** foram apagadas por {ctx.author.mention}.", color=0x00FF00)
        await ctx.send(embed=embed, delete_after=30)


async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(LimparMensagens(bot))
