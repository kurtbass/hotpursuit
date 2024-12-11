import os
import subprocess

def descompile_pycache(root_dir, output_dir):
    """
    Descompila todos os arquivos .pyc encontrados nos diretórios e subdiretórios de root_dir.
    Os arquivos descompilados são salvos na estrutura correspondente em output_dir.

    :param root_dir: Diretório raiz onde estão os diretórios __pycache__.
    :param output_dir: Diretório onde os arquivos descompilados serão salvos.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".pyc"):
                input_path = os.path.join(root, file)

                # Determina o caminho de saída correspondente ao diretório original
                relative_path = os.path.relpath(root, root_dir)
                target_dir = os.path.join(output_dir, relative_path.replace("__pycache__", ""))
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # Define o caminho do arquivo descompilado
                output_file = os.path.join(target_dir, file.replace(".cpython-", ".").replace(".pyc", ".py"))

                try:
                    # Executa o comando de descompilação usando uncompyle6
                    subprocess.run(
                        ["uncompyle6", "-o", target_dir, input_path],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    print(f"Descompilado com sucesso: {input_path} -> {output_file}")
                except subprocess.CalledProcessError as e:
                    print(f"Erro ao descompilar {input_path}: {e.stderr.decode('utf-8')}")

if __name__ == "__main__":
    # Diretório raiz contendo os __pycache__
    root_directory = "./"
    # Diretório onde os arquivos descompilados serão salvos
    output_directory = "./restored"

    descompile_pycache(root_directory, output_directory)
