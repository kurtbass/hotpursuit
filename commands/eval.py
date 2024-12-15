import discord
from discord.ext import commands
import traceback
import textwrap
from contextlib import redirect_stdout
import io
from utils.database import fetchone  # ou de onde você obtém a função fetchone

class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="eval")
    async def eval_code(self, ctx, *, code: str):
        """
        Comando para avaliar código Python.
        Insira o código dentro de três crases (```código aqui```).
        """
        # Verificar se o autor é o dono
        dono_id = fetchone("SELECT value FROM configs WHERE key = ?", ("DONO",))
        if not dono_id or str(ctx.author.id) != dono_id[0]:
            embed = discord.Embed(
                title="🔒 Acesso Negado",
                description="Apenas o dono do bot pode usar este comando.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Remover as crases do código (```python ... ```)
        if code.startswith("```") and code.endswith("```"):
            code = code[3:-3]  # Remove as crases de abertura e fechamento
            code = code.strip()  # Remove espaços adicionais

        # Configura o ambiente para capturar stdout
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            '__import__': __import__
        }
        env.update(globals())

        stdout = io.StringIO()
        result = None

        # Adicionar reação de carregamento
        try:
            await ctx.message.add_reaction("⏳")
        except discord.HTTPException:
            pass

        try:
            with redirect_stdout(stdout):
                # Avalia o código
                exec(
                    f'async def __eval():\n{textwrap.indent(code, "    ")}',
                    env
                )
                result = await env['__eval']()
        except Exception as e:
            # Captura erros e os exibe no Discord
            error = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            embed = discord.Embed(
                title="❌ Erro de Execução",
                description=f"```{error[:2000]}```",  # Limitar a saída a 2000 caracteres
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Retorna a saída do código
        output = stdout.getvalue()
        if result is None:
            if output.strip():
                embed = discord.Embed(
                    title="✅ Resultado",
                    description=f"```{output[:2000]}```",  # Limitar a saída a 2000 caracteres
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="✅ Executado com Sucesso",
                    description="Nenhuma saída gerada.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="✅ Resultado",
                description=f"```{output}{result}```"[:2000],  # Limitar a saída combinada
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        # Remover reação de carregamento
        try:
            await ctx.message.remove_reaction("⏳", self.bot.user)
        except discord.HTTPException:
            pass


async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(Eval(bot))
