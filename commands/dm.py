from utils.database import get_embed_color
import discord
from discord.ext import commands
import asyncio
from utils.database import get_config
import logging

# Configuração de logs
logger = logging.getLogger(__name__)

class DirectMessageCommand(commands.Cog):
    """Comando para enviar mensagens diretas para usuários."""

    def __init__(self, bot):
        self.bot = bot
        self.staff_role_id = self.safe_get_config("TAG_STAFF", is_int=True)
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"
        self.default_color = get_embed_color()

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

    def create_embed(self, title=None, description=None, color=None, image_url=None):
        """Cria um embed padronizado."""
        embed = discord.Embed(title=title, description=description, color=color or self.default_color)
        embed.set_footer(text=self.lema)
        if image_url:
            embed.set_image(url=image_url)
        return embed

    async def safe_ask_question(self, ctx, question, timeout=60):
        """Faz uma pergunta e aguarda a resposta do usuário."""
        try:
            await ctx.send(embed=self.create_embed(description=question))
            response = await self.bot.wait_for(
                "message",
                timeout=timeout,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            return response.content.strip()
        except asyncio.TimeoutError:
            await ctx.send(
                embed=self.create_embed(
                    description=f"{ctx.author.mention}, o tempo para responder expirou. O comando foi cancelado.",
                    color=get_embed_color(),
                )
            )
            return None

    async def safe_get_recipient(self, ctx, user_input):
        """Busca um destinatário pelo ID, menção ou nome."""
        try:
            if user_input.isdigit():
                user = ctx.guild.get_member(int(user_input))
                if user:
                    return user

            if user_input.startswith("<@") and user_input.endswith(">"):
                user_id = int(user_input.strip("<@!>"))
                user = ctx.guild.get_member(user_id)
                if user:
                    return user

            user_input_lower = user_input.lower()
            user = discord.utils.find(
                lambda u: user_input_lower in (u.name.lower(), u.display_name.lower()),
                ctx.guild.members
            )
            return user
        except Exception as e:
            logger.error(f"Erro ao buscar destinatário: {e}")
            await ctx.send(embed=self.create_embed(
                description="Erro ao tentar localizar o destinatário. Tente novamente.",
                color=get_embed_color()
            ))
            return None

    async def send_message(self, ctx, recipient, content=None, embed=None):
        """Envia mensagem a um destinatário."""
        try:
            if content:
                await recipient.send(content=content)
            elif embed:
                await recipient.send(embed=embed)
            await ctx.send(
                embed=self.create_embed(
                    description=f"A mensagem foi enviada com sucesso para {recipient.mention}.",
                    color=get_embed_color(),
                )
            )
        except discord.Forbidden:
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Não foi possível enviar a mensagem. O destinatário pode ter desativado mensagens privadas.",
                    color=get_embed_color(),
                )
            )
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem: {e}")
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Ocorreu um erro inesperado ao tentar enviar a mensagem.",
                    color=get_embed_color(),
                )
            )

    @commands.command(name="dm", aliases=["directmessage"])
    async def dm(self, ctx, *, user_input=None):
        """Comando para enviar mensagens diretas."""
        # Verificar permissão do autor
        if not any(role.id == self.staff_role_id for role in ctx.author.roles):
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Você não tem permissão para usar este comando.",
                    color=get_embed_color(),
                )
            )
            return

        # Coletar destinatário
        if not user_input:
            user_input = await self.safe_ask_question(ctx, "Mencione ou forneça o ID/nome do membro que receberá a mensagem.")
            if not user_input:
                return

        recipient = await self.safe_get_recipient(ctx, user_input)
        if not recipient:
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Destinatário não encontrado. Verifique o nome ou ID fornecido.",
                    color=get_embed_color(),
                )
            )
            return

        # Escolher tipo de mensagem
        message_type = await self.safe_ask_question(ctx, "Deseja enviar uma mensagem **normal** ou em **embed**? Responda com `normal` ou `embed`.")
        if not message_type or message_type.lower() not in ["normal", "embed"]:
            await ctx.send(
                embed=self.create_embed(
                    description="⚠️ Tipo de mensagem inválido. O comando foi cancelado.",
                    color=get_embed_color(),
                )
            )
            return

        # Envio de mensagem normal
        if message_type.lower() == "normal":
            message_content = await self.safe_ask_question(ctx, "Digite a mensagem que deseja enviar.")
            if not message_content:
                return
            await self.send_message(ctx, recipient, content=message_content)

        # Envio de mensagem embed
        elif message_type.lower() == "embed":
            title = await self.safe_ask_question(ctx, "Digite o título da mensagem.")
            description = await self.safe_ask_question(ctx, "Digite o conteúdo da mensagem.")
            color_input = await self.safe_ask_question(ctx, "Digite a cor do embed (Exemplo: get_embed_color() ou #get_embed_color()).")

            include_banner = await self.safe_ask_question(ctx, "Deseja incluir um banner na mensagem? Responda com `sim` ou `não`.")
            banner_url = None
            if include_banner and include_banner.lower() in ["sim", "s"]:
                banner_url = await self.safe_ask_question(ctx, "Envie o link da imagem do banner.")

            color = self.default_color
            if color_input:
                try:
                    color = int(color_input.lstrip("#"), 16)
                except ValueError:
                    pass

            embed = self.create_embed(title=title, description=description, color=color, image_url=banner_url)
            await self.send_message(ctx, recipient, embed=embed)


async def setup(bot):
    """Carrega o comando no bot."""
    await bot.add_cog(DirectMessageCommand(bot))
