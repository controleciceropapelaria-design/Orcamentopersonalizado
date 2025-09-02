# orcamento_pro/auth.py
"""
Módulo para autenticação e gerenciamento de usuários.
Encapsula toda a lógica de login, registro e manipulação de senhas.
"""
import bcrypt
import pandas as pd
import streamlit as st
import storage
import config

def hash_password(password: str) -> str:
    """Gera o hash de uma senha usando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se uma senha corresponde ao seu hash."""
    # Garante que o hash é uma string válida antes de codificar
    if not isinstance(hashed_password, str):
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def login_user(username, password) -> tuple[bool, str]:
    """
    Tenta autenticar um usuário, verificando o status e a senha.
    Retorna uma tupla: (sucesso, mensagem).
    """
    users_df = st.session_state.df_usuarios
    if users_df is None or users_df.empty:
        return False, "Nenhum usuário cadastrado."

    user_record = users_df[users_df["usuario"] == username]

    if user_record.empty:
        return False, "Usuário ou senha incorretos."

    user_data = user_record.iloc[0]
    
    # Verifica se o status é 'ativo'
    if user_data["status"] != "ativo":
        return False, "Usuário pendente de aprovação ou inativo."

    # Verifica a senha
    if verify_password(password, user_data["senha_hashed"]):
        # Se o login for bem-sucedido, atualiza o estado da sessão
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.full_name = user_data["nome_completo"]
        st.session_state.role = user_data["role"]
        return True, "Login bem-sucedido."
    else:
        return False, "Usuário ou senha incorretos."


def register_user(username, password, full_name) -> tuple[bool, str]:
    """
    Registra um novo usuário com status 'pendente' e role 'user'.
    """
    users_df = st.session_state.df_usuarios
    if username in users_df["usuario"].values:
        return False, "Usuário já existe."

    hashed = hash_password(password)
    new_user = pd.DataFrame([{
        "usuario": username,
        "senha_hashed": hashed,
        "nome_completo": full_name,
        "role": "user",      # Role padrão
        "status": "pendente" # Status padrão
    }])
    
    new_user = new_user.reindex(columns=config.COLUNAS_USUARIOS)

    st.session_state.df_usuarios = pd.concat([users_df, new_user], ignore_index=True)
    storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
    return True, "Usuário cadastrado com sucesso! Aguarde a aprovação do administrador."