import os
import subprocess

def update_git_repo(commit_message="Atualização dos arquivos públicos"):
    try:
        # Adicionar todos os arquivos ao staging
        subprocess.run(["git", "add", "."], check=True)
        print("Todos os arquivos foram adicionados ao staging.")

        # Criar um commit
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"Commit realizado com a mensagem: '{commit_message}'")

        # Fazer push para o repositório remoto
        subprocess.run(["git", "push"], check=True)
        print("Push realizado com sucesso para o repositório remoto.")
    
    except subprocess.CalledProcessError as e:
        print(f"Erro durante a execução do comando: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# Exemplo de uso
if __name__ == "__main__":
    commit_message = input("Digite a mensagem para o commit: ") or "Atualização automática"
    update_git_repo(commit_message)
