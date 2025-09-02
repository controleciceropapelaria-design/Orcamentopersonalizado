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