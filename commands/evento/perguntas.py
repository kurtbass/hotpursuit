from utils.database import get_embed_color
import discord
import asyncio
import logging

logger = logging.getLogger(__name__)

class PerguntasHelper:
    """
    Auxiliar para lidar com perguntas, confirmações e coleta de informações
    para o comando de evento.
    """

    def __init__(self, bot, lema):
        """
        Inicializa o PerguntasHelper com o bot e o lema padrão.

        :param bot: Instância do bot do Discord.
        :param lema: Mensagem padrão para o rodapé dos embeds.
        """
        self.bot = bot
        self.lema = lema

    def create_embed(self, title, description, color=get_embed_color(), image_url=None):
        """
        Cria um embed padronizado com título, descrição, cor e uma imagem opcional.

        :param title: Título do embed.
        :param description: Conteúdo do embed.
        :param color: Cor do embed (padrão: laranja).
        :param image_url: URL da imagem opcional.
        :return: Um objeto discord.Embed.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=self.lema)
        if image_url:
            embed.set_image(url=image_url)
        return embed

    async def ask_question(self, ctx, question, timeout=300):
        """
        Faz uma pergunta ao usuário e aguarda uma resposta.

        :param ctx: Contexto do comando.
        :param question: Texto da pergunta.
        :param timeout: Tempo limite para responder (padrão: 300 segundos).
        :return: Resposta do usuário ou None em caso de timeout.
        """
        await ctx.send(embed=self.create_embed("Pergunta", question))
        try:
            response = await self.bot.wait_for(
                "message",
                timeout=timeout,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            return response.content.strip()
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("Tempo Esgotado", "O comando foi cancelado.", get_embed_color()))
            return None

    async def confirm_action(self, ctx, question):
        """
        Confirma uma ação com "Sim" ou "Não".

        :param ctx: Contexto do comando.
        :param question: Pergunta de confirmação.
        :return: True se o usuário confirmar, False caso contrário.
        """
        response = await self.ask_question(ctx, f"{question} (Sim/Não)")
        return response and response.lower() in ["sim", "s"]

    async def ask_image(self, ctx):
        """
        Solicita ao usuário um link ou anexo de imagem.

        :param ctx: Contexto do comando.
        :return: URL da imagem fornecida ou None em caso de timeout.
        """
        await ctx.send(embed=self.create_embed("Imagem", "Envie o link ou anexe a imagem."))
        try:
            response = await self.bot.wait_for(
                "message",
                timeout=300,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            if response.attachments:
                return response.attachments[0].url
            elif response.content.startswith("http"):
                return response.content
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("Tempo Esgotado", "O comando foi cancelado.", get_embed_color()))
            return None

    async def ask_color(self, ctx):
        """
        Solicita ao usuário uma cor em formato hexadecimal.

        :param ctx: Contexto do comando.
        :return: Cor em formato inteiro ou cor padrão (get_embed_color()) em caso de erro.
        """
        while True:
            response = await self.ask_question(ctx, "Digite o código hexadecimal da cor (Ex: get_embed_color()):")
            if not response:
                # Caso o usuário não responda, retornamos a cor padrão
                await ctx.send(embed=self.create_embed("Erro", "Nenhuma resposta fornecida. Usando cor padrão.", get_embed_color()))
                return get_embed_color()
            try:
                # Tentativa de converter a entrada para hexadecimal
                return int(response.lstrip("#"), 16)
            except ValueError:
                # Feedback claro sobre o formato incorreto
                await ctx.send(embed=self.create_embed(
                    "Erro", "⚠️ Código de cor inválido. Por favor, insira um código hexadecimal válido (Ex: FF8000()).", get_embed_color()
                ))

    async def collect_event_details(self, ctx):
        """
        Coleta todas as informações do evento por meio de interações com o usuário.

        :param ctx: Contexto do comando.
        :return: Dicionário contendo as informações do evento ou None se algo for cancelado.
        """
        event_data = {}

        # Coletar título
        event_data["titulo"] = await self.ask_question(ctx, "Qual o título do evento?")
        if not event_data["titulo"]:
            return None

        # Coletar descrição
        event_data["descricao"] = await self.ask_question(ctx, "Qual a descrição do evento?")
        if not event_data["descricao"]:
            return None

        # Coletar data
        event_data["data"] = await self.ask_question(ctx, "Qual a data do evento? (Exemplo: 15/12/2023)")
        if not event_data["data"]:
            return None

        # Coletar horário
        event_data["horario"] = await self.ask_question(ctx, "Qual o horário do evento? (Exemplo: 14h00)")
        if not event_data["horario"]:
            return None

        # Coletar banner opcional
        if await self.confirm_action(ctx, "Deseja incluir um banner na mensagem?"):
            event_data["banner_url"] = await self.ask_image(ctx)
        else:
            event_data["banner_url"] = None

        # Coletar cor do embed opcional
        if await self.confirm_action(ctx, "Deseja mudar a cor da embed?"):
            event_data["cor"] = await self.ask_color(ctx)
        else:
            event_data["cor"] = get_embed_color()

        return event_data
