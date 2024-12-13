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
            await ctx.send("❌ **Apenas o dono do bot pode usar este comando.**")
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
            error = traceback.format_exception(type(e), e, e.__traceback__)
            await ctx.send(f"\u274C **Erro:**\n```{''.join(error)}```")
            return

        # Retorna a saída do código
        output = stdout.getvalue()
        if result is None:
            if output:
                await ctx.send(f"\u2705 **Resultado:**\n```{output}```")
            else:
                await ctx.send("\u2705 **Executado com sucesso, sem saída.**")
        else:
            await ctx.send(f"\u2705 **Resultado:**\n```{output}{result}```")

# Adicionar o cog ao bot
async def setup(bot):
    await bot.add_cog(Eval(bot))
