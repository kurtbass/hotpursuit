from utils.database import fetchone, execute_query
from utils.config import get_lema
import discord
from discord.ext import commands
import asyncio
import logging

# Configuração de logs
logger = logging.getLogger(__name__)

class EmbedColor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lema, self.lema_img, self.nome_cla = get_lema()

    def get_embed_color(self) -> discord.Colour:
        """
        Obtém a cor da tabela 'configs' com a key 'EMBED_COLOR'.
        Retorna um objeto discord.Colour com a cor definida ou aleatória.
        """
        query = "SELECT value FROM configs WHERE key = ?"
        result = fetchone(query, ("EMBED_COLOR",))

        if result and isinstance(result[0], str):
            if result[0].lower() == "random":
                return discord.Colour.random()
            try:
                return discord.Colour(int(result[0].lstrip("#"), 16))
            except ValueError:
                logger.warning(f"Valor inválido em 'EMBED_COLOR': {result[0]}")
        return discord.Colour.random()

    def validate_color(self, color: str) -> discord.Colour:
        """
        Valida uma string de cor em formato HEX ou retorna uma cor aleatória.
        """
        if color.lower() in ["random", "aleatorio", "aleatório"]:
            return discord.Colour.random()
        if color.startswith("#"):
            color = color[1:]
        if len(color) == 6 and all(c in "0123456789abcdefABCDEF" for c in color):
            return discord.Colour(int(color, 16))
        return None

    @commands.command(name="embedcolor", aliases=["cor", "mudarcor"])
    async def embedcolor(self, ctx, *, color: str = None):
        """
        Comando para alterar a cor padrão das embeds.
        Somente o dono configurado no banco de dados pode usá-lo.
        """
        # Verificar se o autor é o dono
        owner_id = fetchone("SELECT value FROM configs WHERE key = ?", ("DONO",))
        if not owner_id or str(ctx.author.id) != str(owner_id[0]):
            embed = discord.Embed(
                title="🔒 Acesso Negado",
                description="Você não tem permissão para usar este comando.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
            return

        current_color = self.get_embed_color()

        if not color:
            # Exibir menu se nenhuma cor foi fornecida
            embed = discord.Embed(
                title="🎨 Mudar Cor Padrão da Embed",
                description=(
                    "1️⃣ **Alterar Cor**\n"
                    "2️⃣ **Cor Aleatória**\n\n"
                    "Digite o número da opção desejada."
                ),
                color=current_color
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30)
                if msg.content.strip() == "1":
                    await self.prompt_color(ctx)
                elif msg.content.strip() == "2":
                    await self.set_random_color(ctx)
                else:
                    await self.invalid_option(ctx)
            except asyncio.TimeoutError:
                await self.timeout_error(ctx)
        else:
            # Processar entrada diretamente
            await self.process_color_input(ctx, color)

    async def prompt_color(self, ctx):
        """
        Solicita uma nova cor ao usuário.
        """
        embed = discord.Embed(
            title="🎨 Escolher Nova Cor",
            description="Digite a cor desejada no formato **HEX** (exemplo: FF8000 ou #FF8000).",
            color=self.get_embed_color()
        )
        embed.set_footer(text=self.lema, icon_url=self.lema_img)
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            await self.process_color_input(ctx, msg.content.strip())
        except asyncio.TimeoutError:
            await self.timeout_error(ctx)

    async def process_color_input(self, ctx, color):
        """
        Processa a entrada de cor fornecida pelo usuário.
        """
        validated_color = self.validate_color(color)
        if validated_color:
            # Atualiza o banco com a nova cor
            execute_query("UPDATE configs SET value = ? WHERE key = ?", (color.upper(), "EMBED_COLOR"))
            embed = discord.Embed(
                title="✅ Cor Alterada com Sucesso",
                description=f"A cor padrão das embeds foi alterada para **#{color.upper()}**.",
                color=validated_color
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
        else:
            await self.invalid_color_error(ctx)

    async def set_random_color(self, ctx):
        """
        Define uma cor aleatória e atualiza no banco de dados como 'random'.
        """
        execute_query("UPDATE configs SET value = ? WHERE key = ?", ("random", "EMBED_COLOR"))
        embed = discord.Embed(
            title="🎲 Cor Aleatória Definida",
            description="A cor padrão das embeds foi definida como **aleatória**.",
            color=discord.Colour.random()
        )
        embed.set_footer(text=self.lema, icon_url=self.lema_img)
        await ctx.send(embed=embed)

    async def invalid_option(self, ctx):
        """
        Envia uma mensagem de erro para opção inválida.
        """
        embed = discord.Embed(
            title="❌ Opção Inválida",
            description="Você digitou uma opção inválida. Tente novamente.",
            color=discord.Colour.red()
        )
        embed.set_footer(text=self.lema, icon_url=self.lema_img)
        await ctx.send(embed=embed)

    async def timeout_error(self, ctx):
        """
        Envia uma mensagem de erro para tempo esgotado.
        """
        embed = discord.Embed(
            title="⏳ Tempo Esgotado",
            description="Você demorou muito para responder. Tente novamente.",
            color=discord.Colour.red()
        )
        embed.set_footer(text=self.lema, icon_url=self.lema_img)
        await ctx.send(embed=embed)

    async def invalid_color_error(self, ctx):
        """
        Envia uma mensagem de erro para cor inválida.
        """
        embed = discord.Embed(
            title="❌ Cor Inválida",
            description="A cor fornecida é inválida. Certifique-se de usar o formato **HEX** (exemplo: FF8000).",
            color=discord.Colour.red()
        )
        embed.set_footer(text=self.lema, icon_url=self.lema_img)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EmbedColor(bot))
