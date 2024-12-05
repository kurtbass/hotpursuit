import os

def remove_duplicate_imports(base_path: str, target_line: str):
    """
    Remove linhas duplicadas de importação em todos os arquivos dentro de uma pasta e subpastas.

    :param base_path: Caminho base do projeto para começar a busca.
    :param target_line: A linha de importação a ser deduplicada.
    """
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Remove duplicadas mantendo apenas a primeira ocorrência
                seen = False
                updated_lines = []
                for line in lines:
                    if line.strip() == target_line:
                        if not seen:
                            updated_lines.append(line)  # Mantenha a primeira ocorrência
                            seen = True
                        # Ignore as duplicadas
                    else:
                        updated_lines.append(line)

                # Escreve as alterações no arquivo
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(updated_lines)
                print(f"Atualizado: {file_path}")

# Caminho base do projeto
project_path = "caminho/para/seu/projeto"

# Linha de importação a ser deduplicada
import_line = "from utils.database import get_embed_color"

# Executar o script
remove_duplicate_imports(project_path, import_line)
