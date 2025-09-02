# orcamento_pro/calculations.py
"""
Módulo para a lógica de negócios principal (cálculos de custos).
As funções são "puras" e testáveis: recebem dados como entrada e
retornam resultados, sem depender do estado da UI (st.session_state).
"""
import pandas as pd
import numpy as np

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
        # O custo do serviço é implícito no custo do papel, este cálculo é sobre o consumo de papel
    except IndexError:
        # Se a quantidade for maior que todas as faixas, usa a última
        service_row = df_impression_table.iloc[-1]
        total_sheets = int(service_row['QTD_FLS'])
        # Não há custo de serviço explícito na tabela, o custo vem do papel

    # Encontrar o custo do papel
    paper_row = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_name]
    if paper_row.empty:
        return {"error": f"Papel '{paper_name}' não encontrado nos registros de compra."}

    paper_unit_price = paper_row.iloc[0]['ValorUnitario']
    paper_cost_total = paper_unit_price * total_sheets

    # Calcular custos unitários (neste caso, é apenas o custo do papel dividido pela quantidade)
    total_cost_unit = paper_cost_total / quantity

    return {
        "total_cost_unit": total_cost_unit,
        "paper_cost_unit": total_cost_unit, # Custo é só o papel
        "service_cost_unit": 0, # Serviço não é um valor monetário separado neste cálculo
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