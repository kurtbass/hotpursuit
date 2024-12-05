import asyncio
import discord
from discord.ext import commands
from utils.database import fetchone, execute_query, get_config
import random

class EmbedColor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                pass
        return discord.Colour.random()

    @commands.command(name="embedcolor", aliases=["cor", "mudarcor"])
    async def embedcolor(self, ctx, *, color: str = None):
        """
        Comando para alterar a cor padrão das embeds.
        Somente o dono configurado no banco de dados pode usá-lo.
        """
        lema = get_config("LEMA") or "Bot oficial"

        # Obter o ID do dono do banco de dados
        owner_id = get_config("DONO")
        if not owner_id or str(ctx.author.id) != owner_id:
            embed = discord.Embed(
                title="🔒 Acesso Negado",
                description="Você não tem permissão para usar este comando.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)
            return

        current_color = self.get_embed_color()

        if color is None:  # Caso nenhuma cor seja fornecida, exibe o menu
            embed = discord.Embed(
                title="🎨 Mudar Cor Padrão da Embed",
                description="1️⃣ **Alterar Cor**\n2️⃣ **Cor Aleatória**\n\nDigite o número da opção desejada.",
                color=current_color
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30)
                if msg.content.strip() == "1":
                    await self.prompt_color(ctx, lema)
                elif msg.content.strip() == "2":
                    await self.set_random_color(ctx, lema)
                else:
                    await self.invalid_option(ctx, lema)
            except asyncio.TimeoutError:
                await self.timeout_error(ctx, lema)
        else:
            # Caso a cor seja fornecida como argumento
            await self.process_color_input(ctx, color, lema)

    async def prompt_color(self, ctx, lema):
        """
        Solicita uma nova cor ao usuário.
        """
        embed = discord.Embed(
            title="🎨 Escolher Nova Cor",
            description="Digite a cor desejada no formato **HEX** (exemplo: FF8000 ou #FF8000).",
            color=self.get_embed_color()
        )
        embed.set_footer(text=lema)
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            await self.process_color_input(ctx, msg.content.strip(), lema)
        except asyncio.TimeoutError:
            await self.timeout_error(ctx, lema)

    async def process_color_input(self, ctx, color, lema):
        """
        Processa a entrada de cor fornecida pelo usuário.
        """
        color = color.strip().lower()

        if color in ["random", "aleatorio", "aleatório", "0"]:
            await self.set_random_color(ctx, lema)
        else:
            # Valida e define a nova cor
            if color.startswith("#"):
                color = color[1:]  # Remove o símbolo '#' se presente

            if len(color) == 6 and all(c in "0123456789abcdef" for c in color.lower()):
                execute_query("UPDATE configs SET value = ? WHERE key = ?", (f"{color.upper()}", "EMBED_COLOR"))
                embed = discord.Embed(
                    title="✅ Cor Alterada com Sucesso",
                    description=f"A cor padrão das embeds foi alterada para **#{color.upper()}**.",
                    color=discord.Colour(int(color, 16))
                )
                embed.set_footer(text=lema)
                await ctx.send(embed=embed)
            else:
                await self.invalid_color_error(ctx, lema)

    async def set_random_color(self, ctx, lema):
        """
        Define uma cor aleatória e atualiza no banco de dados como 'random'.
        """
        execute_query("UPDATE configs SET value = ? WHERE key = ?", ("random", "EMBED_COLOR"))

        embed = discord.Embed(
            title="🎲 Cor Aleatória Definida",
            description="A cor padrão das embeds foi definida como **aleatória**.",
            color=discord.Colour.random()
        )
        embed.set_footer(text=lema)
        await ctx.send(embed=embed)

    async def invalid_option(self, ctx, lema):
        """
        Envia uma mensagem de erro para opção inválida.
        """
        embed = discord.Embed(
            title="❌ Opção Inválida",
            description="Você digitou uma opção inválida. Tente novamente.",
            color=discord.Colour.red()
        )
        embed.set_footer(text=lema)
        await ctx.send(embed=embed)

    async def timeout_error(self, ctx, lema):
        """
        Envia uma mensagem de erro para tempo esgotado.
        """
        embed = discord.Embed(
            title="⏳ Tempo Esgotado",
            description="Você demorou muito para responder. Tente novamente.",
            color=discord.Colour.red()
        )
        embed.set_footer(text=lema)
        await ctx.send(embed=embed)

    async def invalid_color_error(self, ctx, lema):
        """
        Envia uma mensagem de erro para cor inválida.
        """
        embed = discord.Embed(
            title="❌ Cor Inválida",
            description="A cor fornecida é inválida. Certifique-se de usar o formato **HEX** (exemplo: FF8000).",
            color=discord.Colour.red()
        )
        embed.set_footer(text=lema)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EmbedColor(bot))
