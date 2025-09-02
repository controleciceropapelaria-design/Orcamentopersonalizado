# orcamento_pro/calculations.py
"""
Módulo para a lógica de negócios principal (cálculos de custos).
As funções são "puras" e testáveis: recebem dados como entrada e
retornam resultados, sem depender do estado da UI (st.session_state).
"""
import pandas as pd
import numpy as np
import re

def calculate_offset_cover_cost(
    quantity: int,
    paper_name: str,
    df_paper_purchases: pd.DataFrame,
    df_impression_table: pd.DataFrame
) -> dict:
    """
    Calcula o custo unitário da capa para produtos de policromia (Offset).
    Retorna um dicionário com os detalhes do custo ou uma mensagem de erro.
    """
    if df_impression_table.empty:
        return {"error": "Tabela de impressão para este produto está vazia ou não foi carregada."}
    # Encontrar a faixa de custo de serviço/impressão
    try:
        # Encontra a primeira faixa onde a quantidade do orçamento é menor ou igual ao limite da faixa
        service_row = df_impression_table[df_impression_table['LAMINAS'] >= quantity].iloc[0]
        total_sheets = int(service_row['QTD_FLS'])
        impression_cost_total = service_row['VALOR ML']
    except IndexError:
        # Se a quantidade for maior que todas as faixas, usa a última
        service_row = df_impression_table.iloc[-1]
        total_sheets = int(service_row['QTD_FLS'])
        impression_cost_total = service_row['VALOR ML']
    # Encontrar o custo do papel
    paper_row = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_name]
    if paper_row.empty:
        return {"error": f"Papel '{paper_name}' não encontrado nos registros de compra."}
    paper_unit_price = paper_row.iloc[0]['ValorUnitario']
    paper_cost_total = paper_unit_price * total_sheets
    # Calcular custos unitários
    impression_cost_unit = impression_cost_total / quantity
    paper_cost_unit = paper_cost_total / quantity
    total_cost_unit = paper_cost_unit + impression_cost_unit
    return {
        "total_cost_unit": total_cost_unit,
        "paper_cost_unit": paper_cost_unit,
        "service_cost_unit": impression_cost_unit,
        "total_sheets": total_sheets,
        "paper_name": paper_name,
        "error": None
    }

def calculate_leather_cover_cost(paper_name: str, df_paper_purchases: pd.DataFrame) -> dict:
    """
    Calcula o custo unitário para capas de couro sintético (baseado apenas no custo do material).
    Assume um consumo de 1 unidade de material por unidade de produto final.
    """
    paper_row = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_name]
    if paper_row.empty:
        return {"error": f"Material '{paper_name}' não encontrado nos registros de compra."}
    cost = paper_row.iloc[0]['ValorUnitario']
    return {"total_cost_unit": cost, "paper_name": paper_name, "error": None}

def calculate_digital_cover_cost(
    product_name: str,
    paper_name: str,
    impression_type: str,
    budget_quantity: int,
    df_paper_purchases: pd.DataFrame
) -> dict:
    """
    Calcula o custo unitário da capa para produtos de policromia (Digital).
    """
    # Dimensões do produto
    formatos_abertos = {
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
    base_product = product_name.replace(" - POLICROMIA", "").strip()
    if base_product not in formatos_abertos:
        return {"error": f"Formato do produto '{base_product}' não encontrado."}
    larg_capa, alt_capa = formatos_abertos[base_product]['larg'], formatos_abertos[base_product]['alt']
    
    # Determinar o formato útil de impressão
    if "17X24" in base_product or "20X28" in base_product:
        util_l, util_a = 56, 33
        formato_preco = '56x33'
    else:
        util_l, util_a = 47, 33
        formato_preco = '47x33'
    
    # Determinar o tipo de impressão
    tipo_impressao = None
    for tipo in ['4/0', '4/1', '1/0', '1/1']:
        if tipo in impression_type:
            tipo_impressao = tipo
            break
    if not tipo_impressao:
        return {"error": "Tipo de impressão digital não especificado."}
    
    # Preço unitário da impressão digital
    PRECO_DIGITAL = {
        '47x33': {
            '4/0': 1.16,
            '4/1': 1.40,
            '1/0': 0.24,
            '1/1': 0.48
        },
        '56x33': {
            '4/0': 2.32,
            '4/1': 2.80,
            '1/0': 0.48,
            '1/1': 0.96
        }
    }
    preco_unitario = PRECO_DIGITAL[formato_preco][tipo_impressao]
    
    # Calcular o número de capas por folha útil
    def max_por_folha(folha_l, folha_a, peca_l, peca_a):
        h1 = (folha_l // peca_l) * (folha_a // peca_a)
        h2 = (folha_l // peca_a) * (folha_a // peca_l)
        return max(h1, h2) if h1 > 0 or h2 > 0 else 0
    
    capas_por_folha_util = max_por_folha(util_l, util_a, larg_capa, alt_capa)
    if capas_por_folha_util == 0:
        return {"error": "Não é possível encaixar capas na folha útil."}
    
    # Folhas úteis necessárias
    folhas_uteis_necessarias = int(np.ceil(budget_quantity / capas_por_folha_util))
    
    # Custo total da impressão
    custo_impressao_total = folhas_uteis_necessarias * preco_unitario
    custo_impressao_unitario = custo_impressao_total / budget_quantity
    
    # Custo do papel
    df_paper = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_name]
    if df_paper.empty:
        return {"error": f"Papel '{paper_name}' não encontrado nos registros de compra."}
    paper_price = df_paper.iloc[0]['ValorUnitario']
    match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', paper_name.replace('g/m2', '').replace('gsm', ''))
    if not match:
        return {"error": "Dimensões do papel não encontradas."}
    papel_l = float(match.group(1))
    papel_a = float(match.group(2))
    if papel_l < papel_a:
        papel_l, papel_a = papel_a, papel_l
    pecas_h = int(papel_l // util_l)
    pecas_v = int(papel_a // util_a)
    total_pecas = pecas_h * pecas_v
    if total_pecas == 0:
        return {"error": "Não é possível encaixar folhas úteis no papel."}
    folhas_papel = int(np.ceil(folhas_uteis_necessarias / total_pecas))
    custo_papel_total = folhas_papel * paper_price
    custo_papel_unitario = custo_papel_total / budget_quantity
    
    # Custo total
    total_cost_unit = custo_papel_unitario + custo_impressao_unitario
    return {
        "total_cost_unit": total_cost_unit,
        "paper_cost_unit": custo_papel_unitario,
        "service_cost_unit": custo_impressao_unitario,
        "total_sheets": folhas_papel,
        "paper_name": paper_name,
        "error": None
    }

def calculate_component_cost(
    item_name: str,
    df_component_data: pd.DataFrame,
    df_paper_purchases: pd.DataFrame,
    budget_quantity: int,
    component_type: str  # Ex: 'Miolo', 'Bolsa'
) -> dict:
    """
    Calcula o custo de um componente padrão (ex: Miolo Pautado).
    """
    item_row = df_component_data[df_component_data[component_type] == item_name].iloc[0]
    paper_needed = item_row['Papel']
    total_paper_sheets = item_row.get('QuantidadePapel', 0)
    approved_quantity = item_row.get('QuantidadeAprovada', 1)
    impression_cost_total = item_row.get('ValorImpressao', 0)
    if approved_quantity <= 0:
        approved_quantity = 1 # Evita divisão por zero
    sheets_per_unit = total_paper_sheets / approved_quantity
    df_paper = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_needed]
    if df_paper.empty:
        return {"error": f"Papel '{paper_needed}' para o componente não encontrado."}
    paper_price = df_paper.iloc[0]['ValorUnitario']
    last_nf_date_ts = df_paper.iloc[0]['DataEmissaoNF']
    last_nf_date = pd.to_datetime(last_nf_date_ts).strftime('%d/%m/%Y') if pd.notna(last_nf_date_ts) else "N/A"
    paper_cost_unit = paper_price * sheets_per_unit
    service_cost_unit = impression_cost_total / budget_quantity if budget_quantity > 0 else 0
    total_cost = paper_cost_unit + service_cost_unit
    return {
        "total_cost_unit": total_cost,
        "paper_cost_unit": paper_cost_unit,
        "service_cost_unit": service_cost_unit,
        "paper_name": paper_needed,
        "last_nf_date": last_nf_date,
        "error": None
    }

def calculate_custom_component_cost(
    paper_name: str,
    utilization: float,
    service_cost_total: float,
    budget_quantity: int,
    df_paper_purchases: pd.DataFrame
) -> dict:
    """
    Calcula o custo de um componente personalizado.
    'Utilization' é o aproveitamento (quantas unidades se faz com uma folha).
    """
    if utilization <= 0:
        utilization = 1 # Evita divisão por zero
    df_paper = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_name]
    if df_paper.empty:
        return {"error": f"Papel '{paper_name}' para componente personalizado não encontrado."}
    paper_price = df_paper.iloc[0]['ValorUnitario']
    last_nf_date_ts = df_paper.iloc[0]['DataEmissaoNF']
    last_nf_date = pd.to_datetime(last_nf_date_ts).strftime('%d/%m/%Y') if pd.notna(last_nf_date_ts) else "N/A"
    paper_cost_unit = paper_price / utilization
    service_cost_unit = service_cost_total / budget_quantity if budget_quantity > 0 else 0
    total_cost = paper_cost_unit + service_cost_unit
    return {
        "total_cost_unit": total_cost,
        "paper_cost_unit": paper_cost_unit,
        "service_cost_unit": service_cost_unit,
        "paper_name": paper_name,
        "last_nf_date": last_nf_date,
        "error": None
    }