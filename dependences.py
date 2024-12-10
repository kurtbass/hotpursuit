import os
import pkgutil
import pkg_resources

def list_project_dependencies(project_path):
    """
    Analisa arquivos Python no projeto para identificar módulos importados e compara com os pacotes instalados.
    """
    project_modules = set()
    installed_modules = {pkg.key for pkg in pkg_resources.working_set}

    # Analisa todos os arquivos .py no diretório do projeto
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                for _, module_name, _ in pkgutil.iter_modules():
                    if f"import {module_name}" in content or f"from {module_name}" in content:
                        project_modules.add(module_name)

                # Adiciona módulos não listados em `pkgutil.iter_modules`
                for line in content.splitlines():
                    if line.startswith("import ") or line.startswith("from "):
                        module_name = line.split()[1].split(".")[0]
                        project_modules.add(module_name)

    # Determina quais módulos estão no projeto e quais estão instalados
    used_installed_modules = project_modules.intersection(installed_modules)
    unused_installed_modules = installed_modules - project_modules

    return used_installed_modules, unused_installed_modules, project_modules

def generate_requirements_file(used_modules, imported_modules):
    """
    Gera o arquivo requirements.txt com base nos módulos usados e importados.
    """
    # Combina os módulos usados e importados
    all_dependencies = set(used_modules).union(imported_modules)

    # Obtém as versões dos módulos instalados
    requirements = []
    for dist in pkg_resources.working_set:
        if dist.key in all_dependencies:
            requirements.append(f"{dist.key}=={dist.version}")

    # Salva o arquivo requirements.txt
    with open("requirements.txt", "w", encoding="utf-8") as req_file:
        req_file.write("\n".join(sorted(requirements)))

    print("Arquivo 'requirements.txt' gerado com sucesso!")

# Caminho do projeto
project_path = os.getcwd()  # Altere para o caminho do seu projeto, se necessário

# Analisa as dependências
used_modules, _, project_modules = list_project_dependencies(project_path)

# Gera o arquivo requirements.txt
generate_requirements_file(used_modules, project_modules)
