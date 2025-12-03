# orcamento_pro/storage.py
"""
Módulo para gerenciar o armazenamento de dados em arquivos CSV.
Abstrai as operações de leitura e escrita, garantindo que os
diretórios e arquivos necessários existam.
"""
import os
import pandas as pd
import streamlit as st
from pandas.errors import EmptyDataError # <--- ADICIONE ESTA LINHA
import requests
import base64

def get_github_token():
    """Retorna o token do GitHub via st.secrets ou None se não configurado."""
    try:
        return st.secrets["github_token"]
    except Exception:
        return None

def load_csv(file_path: str, columns: list) -> pd.DataFrame:
    """
    Carrega um arquivo CSV. Se não existir, cria um com as colunas especificadas.
    Se existir mas estiver vazio, retorna um DataFrame vazio com as colunas corretas.
    Garante que o diretório de dados exista.

    Args:
        file_path (str): O caminho para o arquivo CSV.
        columns (list): A lista de nomes de colunas para usar se o arquivo for criado.

    Returns:
        pd.DataFrame: O DataFrame carregado ou um novo DataFrame vazio.
    """
    data_dir = os.path.dirname(file_path)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Se o arquivo não existe, cria com o cabeçalho e retorna um DF vazio
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)
        return df

    # Se o arquivo existe, tenta ler
    try:
        return pd.read_csv(file_path)
    except EmptyDataError:
        # Se o arquivo existe mas está vazio (ou só tem cabeçalho), retorna um DF vazio
        return pd.DataFrame(columns=columns)
    except Exception as e:
        # Para outros erros, exibe a mensagem
        st.error(f"Erro inesperado ao carregar o arquivo {file_path}: {e}")
        return pd.DataFrame(columns=columns)


# O restante do arquivo storage.py continua igual...

def save_csv(df: pd.DataFrame, file_path: str):
    """
    Salva um DataFrame em um arquivo CSV, garantindo que o diretório exista.

    Args:
        df (pd.DataFrame): O DataFrame a ser salvo.
        file_path (str): O caminho de destino do arquivo CSV.
    """
    data_dir = os.path.dirname(file_path)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir)
    df.to_csv(file_path, index=False)


def initialize_session_state_df(key: str, file_path: str, columns: list):
    """
    Inicializa um DataFrame no st.session_state se ele não existir,
    carregando-o do arquivo CSV correspondente.

    Args:
        key (str): A chave para usar no st.session_state (ex: 'df_usuarios').
        file_path (str): O caminho para o arquivo CSV de origem.
        columns (list): As colunas a serem usadas se o arquivo precisar ser criado.
    """
    if key not in st.session_state:
        st.session_state[key] = load_csv(file_path, columns)

def save_csv_to_github(df, repo, path, token, branch="main", commit_message="Update CSV via Streamlit"):
    """
    Salva um DataFrame como CSV em um repositório do GitHub usando a API do GitHub.

    Args:
        df (pd.DataFrame): O DataFrame a ser salvo.
        repo (str): O repositório de destino no formato 'usuario/repo'.
        path (str): O caminho completo do arquivo no repositório (ex: 'dados/meu_arquivo.csv').
        token (str): Token de acesso pessoal do GitHub com permissão de escrita.
        branch (str): O branch onde o arquivo será salvo. Padrão é 'main'.
        commit_message (str): Mensagem de commit para a alteração. Padrão é 'Update CSV via Streamlit'.

    Returns:
        tuple: Código de status e resposta da API do GitHub.
    """
    # Lê o conteúdo atual (para pegar o SHA)
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    get_resp = requests.get(url, headers=headers, params={"ref": branch})
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    csv_content = df.to_csv(index=False).encode()
    b64_content = base64.b64encode(csv_content).decode()

    data = {
        "message": commit_message,
        "content": b64_content,
        "branch": branch,
    }
    if sha:
        data["sha"] = sha

    resp = requests.put(url, headers=headers, json=data)
    return resp.status_code, resp.json()

def save_usuarios_to_github(df, token, branch="main"):
    """
    Salva o DataFrame de usuários no GitHub.
    """
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/usuarios.csv"
    return save_csv_to_github(df, repo, path, token, branch, commit_message="Update usuarios.csv via Streamlit")

def save_clientes_to_github(df, token, branch="main"):
    """
    Salva o DataFrame de clientes no GitHub.
    """
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/clientes.csv"
    return save_csv_to_github(df, repo, path, token, branch, commit_message="Update clientes.csv via Streamlit")

def save_orcamentos_to_github(df, token, branch="main"):
    """
    Salva o DataFrame de orçamentos no GitHub.
    """
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/orcamentos_novo.csv"
    return save_csv_to_github(df, repo, path, token, branch, commit_message="Update orcamentos_novo.csv via Streamlit")

def save_templates_to_github(df, token, branch="main"):
    """
    Salva o DataFrame de templates no GitHub.
    """
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/templates.csv"
    return save_csv_to_github(df, repo, path, token, branch, commit_message="Update templates.csv via Streamlit")

def delete_file_from_github(repo, path, token, branch="main", commit_message="Delete file via Streamlit"):
    """
    Exclui um arquivo de um repositório do GitHub usando a API do GitHub.

    Args:
        repo (str): O repositório de destino no formato 'usuario/repo'.
        path (str): O caminho completo do arquivo no repositório (ex: 'dados/meu_arquivo.csv').
        token (str): Token de acesso pessoal do GitHub com permissão de escrita.
        branch (str): O branch onde o arquivo será excluído. Padrão é 'main'.
        commit_message (str): Mensagem de commit para a exclusão.

    Returns:
        tuple: Código de status e resposta da API do GitHub.
    """
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    # Primeiro, pega o SHA do arquivo
    get_resp = requests.get(url, headers=headers, params={"ref": branch})
    if get_resp.status_code != 200:
        return get_resp.status_code, get_resp.json()
    sha = get_resp.json().get("sha")
    data = {
        "message": commit_message,
        "sha": sha,
        "branch": branch
    }
    resp = requests.delete(url, headers=headers, json=data)
    return resp.status_code, resp.json()

def delete_cliente_from_github(nome_cliente, token, branch="main"):
    """
    Exclui o arquivo clientes.csv do GitHub e faz upload do novo CSV atualizado.
    """
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/clientes.csv"
    # Exclui o arquivo antigo
    delete_file_from_github(repo, path, token, branch, commit_message=f"Delete clientes.csv ({nome_cliente}) via Streamlit")
    # Faz upload do novo arquivo atualizado
    save_clientes_to_github(st.session_state.df_clientes, token, branch)

def delete_usuario_from_github(usuario, token, branch="main"):
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/usuarios.csv"
    delete_file_from_github(repo, path, token, branch, commit_message=f"Delete usuarios.csv ({usuario}) via Streamlit")
    save_usuarios_to_github(st.session_state.df_usuarios, token, branch)

def delete_orcamento_from_github(token, branch="main"):
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/orcamentos_novo.csv"
    delete_file_from_github(repo, path, token, branch, commit_message="Delete orcamentos_novo.csv via Streamlit")
    save_orcamentos_to_github(st.session_state.df_orcamentos, token, branch)

def delete_template_from_github(nome_template, token, branch="main"):
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/templates.csv"
    delete_file_from_github(repo, path, token, branch, commit_message=f"Delete templates.csv ({nome_template}) via Streamlit")
    save_templates_to_github(st.session_state.df_templates, token, branch)

def delete_proposta_pdf_from_github(filename, token, branch="main"):
    """
    Exclui um PDF de proposta da pasta Propostas no GitHub.
    """
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = f"Propostas/{filename}"
    return delete_file_from_github(repo, path, token, branch, commit_message=f"Delete proposta {filename} via Streamlit")

def delete_usuario_from_github(usuario, token, branch="main"):
    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
    path = "data/usuarios.csv"
    delete_file_from_github(repo, path, token, branch, commit_message=f"Delete usuarios.csv ({usuario}) via Streamlit")
    save_usuarios_to_github(st.session_state.df_usuarios, token, branch)