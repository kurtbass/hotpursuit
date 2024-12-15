from utils.database import get_embed_color
import discord
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class PermissoesHelper:
    """
    Auxiliar para verificar permissões de usuários para o comando evento.
    """

    def __init__(self, bot, tag_staff, tag_membro, lema):
        """
        Inicializa o helper de permissões.

        :param bot: Instância do bot do Discord.
        :param tag_staff: ID do cargo de staff autorizado.
        :param tag_membro: ID do cargo de membro autorizado.
        :param lema: Rodapé padrão dos embeds.
        """
        self.bot = bot
        self.tag_staff = tag_staff
        self.tag_membro = tag_membro
        self.lema = lema

    def create_embed(self, title: str, description: str, color=None) -> discord.Embed:
        """
        Cria um embed padronizado com título, descrição e cor.

        :param title: Título do embed.
        :param description: Conteúdo do embed.
        :param color: Cor do embed (padrão: cor configurada ou aleatória).
        :return: Um objeto discord.Embed.
        """
        embed = discord.Embed(title=title, description=description, color=color or get_embed_color())
        embed.set_footer(text=self.lema)
        return embed

    async def check_permissions(self, ctx: commands.Context) -> bool:
        """
        Verifica se o usuário possui as permissões necessárias para executar o comando.

        :param ctx: Contexto do comando.
        :return: True se o usuário tiver permissão, False caso contrário.
        """
        # Verificar se o comando está sendo executado em um servidor
        if not ctx.guild:
            logger.warning(f"Comando executado fora de um servidor por {ctx.author}.")
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Este comando só pode ser usado em servidores.",
                discord.Color.red()
            ))
            return False

        # Verificar se o cargo de STAFF está configurado
        if not self.tag_staff:
            logger.warning("Nenhum cargo STAFF configurado no banco de dados.")
            await ctx.send(embed=self.create_embed(
                "Erro de Configuração",
                "⚠️ Nenhum cargo STAFF configurado. Entre em contato com o programador.",
                discord.Color.red()
            ))
            return False

        # Verificar se o usuário possui o cargo de STAFF
        if not hasattr(ctx.author, 'roles'):
            logger.error(f"Erro ao acessar os cargos do autor {ctx.author}.")
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Não foi possível verificar suas permissões. Tente novamente mais tarde.",
                discord.Color.red()
            ))
            return False

        if not any(role.id == self.tag_staff for role in ctx.author.roles):
            logger.info(f"Usuário {ctx.author} tentou usar o comando sem permissão.")
            await ctx.send(embed=self.create_embed(
                "Sem Permissão",
                "⚠️ Você não tem permissão para executar este comando.\n"
                "Entre em contato com um administrador para obter ajuda.",
                discord.Color.red()
            ))
            return False

        # Log de permissão concedida
        logger.info(f"Permissão concedida ao usuário {ctx.author}.")
        return True
