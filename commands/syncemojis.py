import discord
import sqlite3
from discord.ext import commands
from utils.database import get_config

class SyncEmojisCommand(commands.Cog):
    """
    Comando para sincronizar emojis do servidor com a base de dados.
    Apenas o dono do bot pode usar este comando.
    """

    def __init__(self, bot):
        self.bot = bot

    def update_database(self, emojis, table_name):
        """
        Atualiza a base de dados com os emojis fornecidos.

        :param emojis: Lista de dicionários contendo identifier e emoji_code.
        :param table_name: Nome da tabela onde os emojis serão armazenados.
        """
        try:
            conn = sqlite3.connect("bot.db")
            cursor = conn.cursor()

            # Cria a tabela se não existir
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    identifier TEXT UNIQUE,
                    emoji_code TEXT
                )
            """)
            conn.commit()

            # Insere ou atualiza os emojis na tabela
            for emoji in emojis:
                cursor.execute(f"""
                    INSERT INTO {table_name} (identifier, emoji_code)
                    VALUES (?, ?)
                    ON CONFLICT(identifier) DO UPDATE SET
                        emoji_code = excluded.emoji_code
                """, (emoji["identifier"], emoji["emoji_code"]))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao atualizar a tabela {table_name}: {e}")

    @commands.command(name="syncemojis")
    async def sync_emojis(self, ctx):
        """
        Sincroniza emojis do servidor na base de dados.
        """
        # Verifica se o comando está sendo executado no servidor correto
        allowed_server_id = 1315754008136384572
        if ctx.guild.id != allowed_server_id:
            await ctx.send("Este comando só pode ser usado no servidor autorizado.")
            return

        # Verifica se o usuário é o dono
        owner_id = int(get_config("DONO"))
        if ctx.author.id != owner_id:
            await ctx.send("Apenas o dono do bot pode usar este comando.")
            return

        # Define prefixos e tabelas correspondentes
        emoji_categories = {
            "music_": "emojis_music",
            "error_": "emojis_errors",
            "fun_": "emojis_fun",
            "number_": "emojis_numbers",
            "clan_": "emojis_clan_management",
            "staff_": "emojis_server_staff",
        }

        added_emojis = {table: 0 for table in emoji_categories.values()}

        try:
            # Itera pelos emojis do servidor e organiza por categorias
            emojis_to_update = {table: [] for table in emoji_categories.values()}
            for emoji in ctx.guild.emojis:
                for prefix, table in emoji_categories.items():
                    if emoji.name.startswith(prefix):
                        emojis_to_update[table].append({
                            "identifier": emoji.name,
                            "emoji_code": str(emoji)
                        })
                        added_emojis[table] += 1

            # Atualiza o banco de dados para cada categoria
            for table, emojis in emojis_to_update.items():
                self.update_database(emojis, table)

            # Mensagem de confirmação
            results = "\n".join([f"{table}: {count} emojis sincronizados." for table, count in added_emojis.items()])
            await ctx.send(f"Sincronização concluída:\n{results}")

            # Logs adicionais
            print("Sincronização de emojis completa.")
            for table, emojis in emojis_to_update.items():
                print(f"Emojis para {table}: {emojis}")

        except Exception as e:
            await ctx.send(f"Erro ao sincronizar emojis: {e}")
            print(f"Erro ao sincronizar emojis: {e}")

async def setup(bot):
    """
    Adiciona o cog SyncEmojisCommand ao bot.
    """
    await bot.add_cog(SyncEmojisCommand(bot))
