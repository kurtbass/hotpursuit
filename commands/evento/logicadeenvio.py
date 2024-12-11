from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
from utils.database import get_embed_color
import discord
import logging
import asyncio

logger = logging.getLogger(__name__)

class LogicaEnvioHelper:
    """
    Auxiliar para lidar com a lógica de envio de mensagens no comando evento.
    """

    def __init__(self, bot, lema):
        """
        Inicializa o LogicaEnvioHelper.

        :param bot: Instância do bot do Discord.
        :param lema: Rodapé padrão dos embeds.
        """
        self.bot = bot
        self.lema = lema

    def create_embed(self, title, description, color=get_embed_color()):
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

    async def select_recipients(self, ctx, tag_staff, tag_membro):
        """
        Permite ao usuário selecionar os destinatários do evento.

        :param ctx: Contexto do comando.
        :param tag_staff: ID do cargo de staff.
        :param tag_membro: ID do cargo de membro.
        :return: Lista de membros selecionados.
        """
        opcoes = (
            "1 Staff\n"
            "2 Membros do Clã\n"
            "3 Cargo Específico\n"
            "4 Todos os Membros\n"
            "5 Membros Específicos\n"
            "6 Membro Específico"
        )
        while True:
            await ctx.send(embed=self.create_embed(
                "Escolha os Destinatários",
                f"Para quem você deseja enviar o evento?\n\n{opcoes}"
            ))

            try:
                resposta = await self.bot.wait_for(
                    "message",
                    timeout=300,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                )
                escolha = resposta.content.strip()

                if escolha == "1":  # Staff
                    cargo_staff = discord.utils.get(ctx.guild.roles, id=tag_staff)
                    return [m for m in ctx.guild.members if cargo_staff in m.roles] if cargo_staff else []

                elif escolha == "2":  # Membros do Clã
                    cargo_membro = discord.utils.get(ctx.guild.roles, id=tag_membro)
                    return [m for m in ctx.guild.members if cargo_membro in m.roles] if cargo_membro else []

                elif escolha == "3":  # Cargo Específico
                    cargo_id = await self.ask_question(ctx, "Digite o ID do cargo:")
                    try:
                        cargo = discord.utils.get(ctx.guild.roles, id=int(cargo_id))
                        return [m for m in ctx.guild.members if cargo in m.roles] if cargo else []
                    except ValueError:
                        await ctx.send(embed=self.create_embed(
                            "Erro", "⚠️ ID do cargo inválido. Tente novamente.", get_embed_color()
                        ))
                        continue

                elif escolha == "4":  # Todos os Membros
                    return list(ctx.guild.members)  # Garante que todos os membros do servidor serão selecionados

                elif escolha == "5":  # Membros Específicos
                    ids = await self.ask_question(ctx, "Digite os IDs dos membros separados por vírgula:")
                    try:
                        ids = [int(i.strip()) for i in ids.split(",")]
                        return [m for m in ctx.guild.members if m.id in ids]
                    except ValueError:
                        await ctx.send(embed=self.create_embed(
                            "Erro", "⚠️ IDs inválidos fornecidos. Tente novamente.", get_embed_color()
                        ))
                        continue

                elif escolha == "6":  # Membro Específico
                    member_id = await self.ask_question(ctx, "Digite o ID do membro:")
                    try:
                        member = ctx.guild.get_member(int(member_id))
                        return [member] if member else []
                    except ValueError:
                        await ctx.send(embed=self.create_embed(
                            "Erro", "⚠️ ID inválido. Tente novamente.", get_embed_color()
                        ))
                        continue

                else:
                    await ctx.send(embed=self.create_embed(
                        "Erro", "⚠️ Opção inválida. Por favor, escolha uma opção válida.", get_embed_color()
                    ))
            except asyncio.TimeoutError:
                await ctx.send(embed=self.create_embed(
                    "Tempo Esgotado", "⚠️ Tempo esgotado para responder. Tente novamente.", get_embed_color()
                ))
                return []

    async def send_event(self, members, embed):
        """
        Envia o evento para os membros selecionados.

        :param members: Lista de membros para enviar o evento.
        :param embed: Embed contendo os detalhes do evento.
        :return: Quantidade de mensagens enviadas e erros.
        """
        enviadas, erros = 0, 0
        for member in members:
            try:
                await member.send(embed=embed)
                enviadas += 1
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem para {member}: {e}")
                erros += 1
        return enviadas, erros

    async def ask_question(self, ctx, question):
        """
        Pergunta ao usuário e aguarda uma resposta.

        :param ctx: Contexto do comando.
        :param question: Pergunta a ser enviada.
        :return: Resposta do usuário ou None em caso de timeout.
        """
        await ctx.send(embed=self.create_embed("Pergunta", question))
        try:
            response = await self.bot.wait_for(
                "message",
                timeout=300,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            return response.content.strip()
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed(
                "Tempo Esgotado", "⚠️ O comando foi cancelado.", get_embed_color()
            ))
            return None
