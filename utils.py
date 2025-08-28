# utils.py
import pandas as pd

# === FORMATOS ABERTOS (largura e altura em cm) ===
FORMATOS = {
    'CADERNETA 9X13': {'larg': 22, 'alt': 15.8},
    'CADERNETA 14X21': {'larg': 33.7, 'alt': 24.2},
    'REVISTA 9X13': {'larg': 19, 'alt': 14},
    'REVISTA 14X21': {'larg': 29, 'alt': 22},
    'REVISTA 19X25': {'larg': 40, 'alt': 26},
    'CADERNO WIRE-O 17X24': {'larg': 43.8, 'alt': 27.8},
    'CADERNO WIRE-O 20X28': {'larg': 49.2, 'alt': 31.3},
    'PLANNER WIRE-O A5': {'larg': 41, 'alt': 24.7},
    'BLOCO WIRE-O 12X20': {'larg': 31.4, 'alt': 23},
    'FICHARIO A6': {'larg': 35, 'alt': 19.5},
    'FICHARIO A5': {'larg': 45, 'alt': 26},
    'FICHARIO 17X24': {'larg': 49.2, 'alt': 28.4},
    'CADERNO ORGANIZADOR A5': {'larg': 41.5, 'alt': 24.7},
    'CADERNO ORGANIZADOR 17X24': {'larg': 46, 'alt': 27.7}
}

# === ALTURAS DAS FACAS (para couro sintético) ===
FACAS = {
    'CADERNETA 9X13': {'alturaFaca': 40},
    'CADERNETA 14X21': {'alturaFaca': 40},
    'REVISTA 9X13': {'alturaFaca': 40},
    'REVISTA 14X21': {'alturaFaca': 40},
    'REVISTA 19X25': {'alturaFaca': 47},
    'CADERNO WIRE-O 17X24': {'alturaFaca': 53},
    'CADERNO WIRE-O 20X28': {'alturaFaca': 53},
    'PLANNER WIRE-O A5': {'alturaFaca': 47},
    'BLOCO WIRE-O 12X20': {'alturaFaca': 40},
    'FICHARIO A6': {'alturaFaca': 40},
    'FICHARIO A5': {'alturaFaca': 50},
    'FICHARIO 17X24': {'alturaFaca': 53},
    'CADERNO ORGANIZADOR A5': {'alturaFaca': 50},
    'CADERNO ORGANIZADOR 17X24': {'alturaFaca': 53}
}

# === APROVEITAMENTO POR FORMATO (capas por folha bruta) ===
APROVEITAMENTO = {
    'CADERNETA 9X13': 16,
    'CADERNETA 14X21': 8,
    'PLANNER WIRE-O A5': 8,
    'FICHARIO A5': 8,
    'FICHARIO 17X24': 4,
    'CADERNO WIRE-O 17X24': 4,
    'CADERNO WIRE-O 20X28': 4,
    'FICHARIO A6': 6,
    'BLOCO WIRE-O 12X20': 8,
    'CADERNO ORGANIZADOR A5': 8,
    'CADERNO ORGANIZADOR 17X24': 4
}

def calcular_maximo_por_folha(folha_l, folha_a, peca_l, peca_a):
    h1 = (folha_l // peca_l) * (folha_a // peca_a)
    h2 = (folha_l // peca_a) * (folha_a // peca_l)
    return max(h1, h2)

def get_compativel_items(df, base_produto):
    """Retorna itens compatíveis com o produto ou 'Todos'"""
    if df.empty:
        return []
    items = df[df["Compatível"].isin([base_produto, "Todos"])]["Item"].tolist()
    return items

def calcular_folhas(base_produto, quantidade):
    """Calcula folhas necessárias para guarda/lâmina"""
    capas_por_folha = APROVEITAMENTO.get(base_produto, 8)
    qtd_total = quantidade + 5
    return int((qtd_total + capas_por_folha - 1) // capas_por_folha)

def calcular_capa(produto, papel, quantidade, impressao, tabela_df):
    """Calcula folhas ou m² necessários para a capa"""
    if not produto or not papel or not quantidade:
        return "Preencha todos os campos"

    base = produto.replace(" - COURO SINTÉTICO", "").replace(" - POLICROMIA", "").strip()
    formato = FORMATOS.get(base)
    if not formato:
        return "Erro: Produto inválido"

    larg, alt = formato['larg'], formato['alt']

    # COURO SINTÉTICO → m²
    if "COURO SINTÉTICO" in produto:
        faca = FACAS.get(base)
        if not faca:
            return "Erro: Faca não encontrada"
        altura_faca = faca['alturaFaca']
        capas_por_tira = calcular_maximo_por_folha(130, altura_faca, larg, alt)
        if capas_por_tira == 0:
            return "Erro: Não cabe"
        qtd_total = quantidade + 5
        qtd_tiras = (qtd_total + capas_por_tira - 1) // capas_por_tira
        m2 = round(qtd_tiras * (altura_faca / 100) * 1.3, 2)
        return f"{m2} m²"

    # OFFSET → tabela de milheiro
    elif impressao and "Offset" in impressao:
        col_map = {
            'CADERNETA 9X13': 'C9x13',
            'CADERNETA 14X21': 'C14x21',
            'REVISTA 9X13': 'C9x13',
            'REVISTA 14X21': 'C14x21',
            'PLANNER WIRE-O A5': 'Planner A5',
            'FICHARIO A5': 'Fichário A5',
            'FICHARIO 17X24': 'Fichário 17x24',
            'CADERNO WIRE-O 20X28': 'CADERNO WIRE-O 20X28'
        }
        col = col_map.get(base)
        if not col or col not in tabela_df.columns:
            return "Erro: Formato não na tabela"
        row = tabela_df[tabela_df[col] >= quantidade].iloc[0] if not tabela_df[tabela_df[col] >= quantidade].empty else tabela_df.iloc[-1]
        return f"{int(row['Folhas'])} folhas"

    # DIGITAL → aproveitamento
    elif impressao and "Digital" in impressao:
        try:
            match = papel.split('x')
            papel_l = float(match[-2].strip())
            papel_a = float(match[-1].split()[0])
        except:
            return "Erro: Leitura do papel"
        if papel_l < papel_a:
            papel_l, papel_a = papel_a, papel_l
        util_l, util_a = (56, 33) if "17X24" in base or "20X28" in base else (47, 33)
        qtd_h = papel_l // util_l
        qtd_v = papel_a // util_a
        total_pedacos = qtd_h * qtd_v
        capas_por_pedaco = calcular_maximo_por_folha(util_l, util_a, larg, alt)
        capas_por_folha = total_pedacos * capas_por_pedaco
        folhas = (quantidade + capas_por_folha - 1) // capas_por_folha
        return f"{int(folhas)} folhas"

    return "Erro: Dados insuficientes"