from utils.database import get_embed_color
import discord
from discord.ext import commands
import logging
from utils.database import get_config

# Configuração de logs
logger = logging.getLogger(__name__)

class SayCommand(commands.Cog):
    """Comando para o bot repetir mensagens no canal atual ou em um canal específico."""

    def __init__(self, bot):
        self.bot = bot
        self.allowed_server_id = self.safe_get_config("SERVIDOR", is_int=True)
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"

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

    def create_embed(self, description, color=get_embed_color()):
        """Cria um embed padronizado com o lema."""
        embed = discord.Embed(description=description, color=color)
        embed.set_footer(text=self.lema)
        return embed

    async def safe_validate_message(self, ctx, message: str):
        """Valida uma mensagem antes do envio."""
        if not message.strip():
            await ctx.send(embed=self.create_embed(
                description="⚠️ A mensagem não pode estar vazia.",
                color=get_embed_color()
            ), delete_after=10)
            return False

        if len(message) > 2000:
            await ctx.send(embed=self.create_embed(
                description="⚠️ A mensagem excede o limite de 2000 caracteres.",
                color=get_embed_color()
            ), delete_after=10)
            return False

        return True

    @commands.command(name="say", aliases=["falar"])
    async def say(self, ctx, *, message: str):
        """Comando para o bot repetir uma mensagem no canal atual."""
        # Verificar permissões do bot no canal
        if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            logger.warning(f"Sem permissão para enviar mensagens no canal '{ctx.channel.name}'.")
            try:
                await ctx.author.send("⚠️ Não tenho permissão para enviar mensagens neste canal.")
            except discord.Forbidden:
                logger.error(f"Falha ao informar {ctx.author} sobre permissões insuficientes.")
            return

        # Verificar autorização de servidor
        if ctx.guild and ctx.guild.id != self.allowed_server_id:
            await ctx.send(embed=self.create_embed(
                description=f"{ctx.author.mention}, este comando não pode ser usado neste servidor.",
                color=get_embed_color()
            ))
            return

        # Validar mensagem
        if not await self.safe_validate_message(ctx, message):
            return

        # Enviar mensagem no canal atual
        try:
            await ctx.send(message)
            logger.info(f"Comando 'say' executado por {ctx.author} ({ctx.author.id}) no canal '{ctx.channel.name}': {message}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem no comando 'say': {e}")

        # Tentar apagar a mensagem original, se possível
        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                logger.warning(f"Falha ao apagar mensagem original de {ctx.author}.")

    @commands.command(name="sayto", aliases=["falarpara"])
    async def say_to(self, ctx, channel: discord.TextChannel, *, message: str):
        """Comando para o bot repetir uma mensagem em um canal específico."""
        # Verificar permissões no canal de destino
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(embed=self.create_embed(
                description=f"⚠️ Não tenho permissão para enviar mensagens no canal {channel.mention}.",
                color=get_embed_color()
            ), delete_after=10)
            return

        # Validar mensagem
        if not await self.safe_validate_message(ctx, message):
            return

        # Enviar mensagem no canal especificado
        try:
            await channel.send(message)
            logger.info(f"Comando 'sayto' executado por {ctx.author} ({ctx.author.id}): {message} -> Canal '{channel.name}'")

            # Feedback para o autor do comando
            feedback = self.create_embed(
                description=f"Mensagem enviada para {channel.mention}.",
                color=get_embed_color()
            )
            await ctx.send(embed=feedback, delete_after=10)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para o canal '{channel.name}': {e}")
            await ctx.send(embed=self.create_embed(
                description="⚠️ Ocorreu um erro ao tentar enviar a mensagem. Tente novamente mais tarde.",
                color=get_embed_color()
            ), delete_after=10)

async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(SayCommand(bot))
