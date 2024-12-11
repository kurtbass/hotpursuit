from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
from utils.database import get_embed_color
import discord
from discord.ext import commands
import asyncio
import logging
from utils.database import get_config

# Configuração de logs
logger = logging.getLogger(__name__)

class Reuniao(commands.Cog):
    """Comando para organizar e enviar reuniões."""

    def __init__(self, bot):
        self.bot = bot
        self.em_execucao = False
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"
        self.tag_staff = self.safe_get_config("TAG_STAFF", is_int=True)
        self.tag_membro = self.safe_get_config("TAG_MEMBRO", is_int=True)

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

    def create_embed(self, title=None, description=None, color=get_embed_color(), image_url=None):
        """Cria um embed padronizado."""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=self.lema)
        if image_url:
            embed.set_image(url=image_url)
        return embed

    async def safe_send_embed(self, ctx, description, color=get_embed_color()):
        """Envia um embed padronizado."""
        embed = self.create_embed(description=description, color=color)
        await ctx.send(embed=embed)

    @commands.command(name="reuniao")
    async def reuniao(self, ctx):
        """Comando principal para criar reuniões."""
        if self.em_execucao:
            await self.safe_send_embed(ctx, "⚠️ Já existe uma reunião em execução. Aguarde até que finalize.", color=get_embed_color())
            return

        if not self.tag_staff:
            await self.safe_send_embed(ctx, "⚠️ Nenhum cargo STAFF foi configurado. Procure o programador.", color=get_embed_color())
            return

        self.em_execucao = True
        try:
            tema = await self.safe_ask_question(ctx, "Digite o tema da reunião:")
            if not tema:
                return

            pauta = await self.safe_ask_question(ctx, "Digite a pauta da reunião:")
            if not pauta:
                return

            data = await self.safe_ask_question(ctx, "Qual a data da reunião? (Exemplo: 15/12/2023)")
            if not data:
                return

            horario = await self.safe_ask_question(ctx, "Qual o horário da reunião? (Exemplo: 14h00)")
            if not horario:
                return

            banner_url = None
            if await self.safe_confirm(ctx, "Deseja incluir um banner na mensagem?"):
                banner_url = await self.safe_ask_image(ctx)

            cor_embed = get_embed_color()
            if await self.safe_confirm(ctx, "Deseja mudar a cor da embed?"):
                cor_embed = await self.safe_ask_color(ctx)

            # Criar embed
            embed = self.create_embed(
                title=f"📢 Reunião: {tema}",
                description=f"**Pauta:** {pauta}\n📅 **Data:** {data}\n⏰ **Horário:** {horario}",
                color=cor_embed,
                image_url=banner_url
            )

            await ctx.send(embed=embed)

            # Confirmar envio
            if not await self.safe_confirm(ctx, "A mensagem está correta?"):
                await self.safe_send_embed(ctx, "⚠️ Cancelando o comando. Corrija as informações e tente novamente.", color=get_embed_color())
                return

            # Selecionar destinatários
            destinatarios = await self.safe_select_recipients(ctx)
            if not destinatarios:
                await self.safe_send_embed(ctx, "⚠️ Nenhum destinatário foi selecionado. Comando cancelado.", color=get_embed_color())
                return

            # Enviar mensagens
            enviadas, erros = await self.safe_send_messages(destinatarios, embed)
            await self.safe_send_embed(ctx, f"✅ Reunião enviada para {enviadas} membros. Erros: {erros}.", color=get_embed_color())

        finally:
            self.em_execucao = False

    async def safe_ask_question(self, ctx, question):
        """Pergunta ao usuário e retorna a resposta."""
        await self.safe_send_embed(ctx, question)
        try:
            response = await self.bot.wait_for(
                "message",
                timeout=300,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            return response.content
        except asyncio.TimeoutError:
            await self.safe_send_embed(ctx, "⚠️ Tempo esgotado. O comando foi cancelado.", color=get_embed_color())
            return None

    async def safe_confirm(self, ctx, message):
        """Confirmação para ações críticas."""
        response = await self.safe_ask_question(ctx, f"{message} (Sim/Não)")
        return response and response.lower() in ["sim", "s"]

    async def safe_ask_image(self, ctx):
        """Solicita um link ou anexo para um banner."""
        await self.safe_send_embed(ctx, "Envie o link ou anexe a imagem para o banner.")
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
            await self.safe_send_embed(ctx, "⚠️ Tempo esgotado. O comando foi cancelado.", color=get_embed_color())
            return None

    async def safe_ask_color(self, ctx):
        """Solicita uma cor para a embed."""
        response = await self.safe_ask_question(ctx, "Digite o código hexadecimal da cor (Ex: get_embed_color()):")
        try:
            return int(response.lstrip("#"), 16)
        except ValueError:
            await self.safe_send_embed(ctx, "⚠️ Código de cor inválido. Usando cor padrão.", color=get_embed_color())
            return get_embed_color()

    async def safe_select_recipients(self, ctx):
        """Seleciona destinatários da reunião."""
        opcoes = (
            "1 Staff\n"
            "2 Membros do Clã\n"
            "3 Cargo Específico\n"
            "4 Todos os Membros\n"
            "5 Membros Específicos\n"
            "6 Membro Específico"
        )
        while True:
            await self.safe_send_embed(ctx, f"Escolha uma opção de destinatário:\n{opcoes}")
            try:
                resposta = await self.bot.wait_for(
                    "message",
                    timeout=300,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                )
                escolha = resposta.content.strip()

                if escolha == "1":  # Staff
                    cargo_staff = discord.utils.get(ctx.guild.roles, id=self.tag_staff)
                    return [m for m in ctx.guild.members if cargo_staff in m.roles] if cargo_staff else []

                elif escolha == "2":  # Membros do Clã
                    cargo_membro = discord.utils.get(ctx.guild.roles, id=self.tag_membro)
                    return [m for m in ctx.guild.members if cargo_membro in m.roles] if cargo_membro else []

                elif escolha == "3":  # Cargo Específico
                    cargo_id = await self.safe_ask_question(ctx, "Digite o ID do cargo:")
                    cargo = discord.utils.get(ctx.guild.roles, id=int(cargo_id))
                    return [m for m in ctx.guild.members if cargo in m.roles] if cargo else []

                elif escolha == "4":  # Todos os Membros
                    return ctx.guild.members

                elif escolha == "5":  # Membros Específicos
                    ids = await self.safe_ask_question(ctx, "Digite os IDs dos membros separados por vírgula:")
                    ids = [int(i.strip()) for i in ids.split(",")]
                    return [m for m in ctx.guild.members if m.id in ids]

                elif escolha == "6":  # Membro Específico
                    member_id = await self.safe_ask_question(ctx, "Digite o ID do membro:")
                    member = ctx.guild.get_member(int(member_id))
                    return [member] if member else []

                else:
                    await self.safe_send_embed(ctx, "⚠️ Opção inválida. Escolha novamente.")
            except asyncio.TimeoutError:
                await self.safe_send_embed(ctx, "⚠️ Tempo esgotado. O comando foi cancelado.", color=get_embed_color())
                return []

    async def safe_send_messages(self, members, embed):
        """Envia mensagens para os destinatários."""
        enviadas, erros = 0, 0
        for member in members:
            try:
                await member.send(embed=embed)
                enviadas += 1
            except Exception:
                erros += 1
        return enviadas, erros


async def setup(bot):
    """Carrega o cog no bot."""
    await bot.add_cog(Reuniao(bot))
