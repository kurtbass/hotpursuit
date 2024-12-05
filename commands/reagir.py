from utils.database import get_embed_color
import discord
from discord.ext import commands
import logging
from utils.database import get_config

# Configuração de logs
logger = logging.getLogger(__name__)

class ReagirCommand(commands.Cog):
    """Comando para adicionar reações a mensagens específicas."""

    def __init__(self, bot):
        self.bot = bot
        self.staff_role_id = self.safe_get_config("TAG_STAFF", is_int=True)
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"
        self.default_color = get_embed_color()

    def safe_get_config(self, key, is_int=False):
        """Obtém uma configuração do banco de forma segura."""
        try:
            value = get_config(key)
            return int(value) if value and is_int else value
        except Exception as e:
            logger.error(f"Erro ao carregar configuração '{key}': {e}")
            return None

    def create_embed(self, title=None, description=None, color=None):
        """Cria um embed padronizado."""
        embed = discord.Embed(title=title, description=description, color=color or self.default_color)
        embed.set_footer(text=self.lema)
        return embed

    @commands.command(name="reagir")
    async def reagir(self, ctx: commands.Context, message_id: int, emoji: str):
        """
        Adiciona uma reação personalizada a uma mensagem específica.

        Args:
            ctx (commands.Context): Contexto do comando.
            message_id (int): ID da mensagem alvo.
            emoji (str): Emoji a ser adicionado.
        """
        # Validação de permissões
        if not any(role.id == self.staff_role_id for role in ctx.author.roles):
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Você não tem permissão para usar este comando.",
                    color=get_embed_color()
                )
            )
            return

        try:
            # Buscar a mensagem e adicionar reação
            message = await ctx.channel.fetch_message(message_id)
            await message.add_reaction(emoji)
            await ctx.send(
                embed=self.create_embed(
                    description=f"✅ Reação {emoji} adicionada com sucesso à mensagem `{message_id}`.",
                    color=get_embed_color()
                )
            )
        except discord.NotFound:
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Mensagem não encontrada. Verifique o ID informado.",
                    color=get_embed_color()
                )
            )
        except discord.Forbidden:
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Permissões insuficientes para adicionar a reação.",
                    color=get_embed_color()
                )
            )
        except discord.HTTPException as e:
            logger.error(f"Erro ao adicionar reação: {e}")
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Não foi possível adicionar a reação. Verifique se o emoji é válido.",
                    color=get_embed_color()
                )
            )
        except Exception as e:
            logger.error(f"Erro inesperado ao adicionar reação: {e}")
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Ocorreu um erro inesperado ao tentar adicionar a reação.",
                    color=get_embed_color()
                )
            )


# Função obrigatória para carregar o cog
async def setup(bot: commands.Bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(ReagirCommand(bot))
