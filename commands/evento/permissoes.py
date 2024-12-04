import discord
import logging

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

    def create_embed(self, title, description, color=0xFF8000):
        """
        Cria um embed padronizado com título, descrição e cor.

        :param title: Título do embed.
        :param description: Conteúdo do embed.
        :param color: Cor do embed (padrão: laranja).
        :return: Um objeto discord.Embed.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=self.lema)
        return embed

    async def check_permissions(self, ctx):
        """
        Verifica se o usuário possui as permissões necessárias para executar o comando.

        :param ctx: Contexto do comando.
        :return: True se o usuário tiver permissão, False caso contrário.
        """
        # Se a configuração de TAG_STAFF não estiver configurada
        if not self.tag_staff:
            logger.warning("Nenhum cargo de STAFF configurado no banco de dados.")
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ Nenhum cargo STAFF configurado. Procure o programador.", 0xFF0000
            ))
            return False

        # Verificar se o usuário tem o cargo de staff
        if not any(role.id == self.tag_staff for role in ctx.author.roles):
            logger.warning(f"Usuário {ctx.author} tentou usar o comando sem permissão.")
            await ctx.send(embed=self.create_embed(
                "Sem Permissão", "⚠️ Você não tem permissão para executar este comando.", 0xFF0000
            ))
            return False

        # Permissão concedida
        return True
