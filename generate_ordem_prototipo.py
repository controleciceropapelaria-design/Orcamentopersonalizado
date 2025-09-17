from fpdf import FPDF
from datetime import datetime, timedelta

def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generate_ordem_prototipo_pdf(proposal_data, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    # Logo e título
    logo_path = "logo_cicero.png"
    if logo_path:
        pdf.image(logo_path, x=10, y=8, w=35)
    pdf.set_font("Times", "B", 18)
    pdf.set_xy(0, 15)
    pdf.cell(0, 12, "ORDEM DE PROTÓTIPO", ln=True, align="C")
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, 28, 200, 28)

    # Data da ordem e prazo de entrega
    data_ordem = datetime.now().strftime("%d/%m/%Y")
    try:
        data_base = datetime.strptime(data_ordem, "%d/%m/%Y")
        data_entrega = (data_base + timedelta(days=7)).strftime("%d/%m/%Y")
    except Exception:
        data_entrega = ""

    # Bloco de informações principais
    pdf.set_font("Times", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(38, 7, "Nº Orçamento:", 0, 0, "L", 1)
    pdf.set_font("Times", "", 11)
    pdf.cell(40, 7, f"{proposal_data.get('numero_orcamento', '')}", 0, 0, "L", 1)
    pdf.set_font("Times", "B", 11)
    pdf.cell(22, 7, "Versão:", 0, 0, "L", 1)
    pdf.set_font("Times", "", 11)
    pdf.cell(20, 7, f"{proposal_data.get('versao_orcamento', 1)}", 0, 0, "L", 1)
    pdf.set_font("Times", "B", 11)
    pdf.cell(32, 7, "Data da Ordem:", 0, 0, "L", 1)
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 7, data_ordem, 0, 1, "L", 1)

    pdf.set_font("Times", "B", 11)
    pdf.cell(38, 7, "Entrega Protótipo:", 0, 0, "L", 1)
    pdf.set_font("Times", "", 11)
    pdf.cell(40, 7, data_entrega, 0, 0, "L", 1)
    pdf.set_font("Times", "B", 11)
    pdf.cell(22, 7, "Cliente:", 0, 0, "L", 1)
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 7, proposal_data.get('cliente', ''), 0, 1, "L", 1)

    pdf.set_font("Times", "B", 11)
    pdf.cell(38, 7, "Contato Comercial:", 0, 0, "L", 1)
    pdf.set_font("Times", "", 11)
    pdf.cell(40, 7, proposal_data.get('atendente', ''), 0, 0, "L", 1)
    pdf.set_font("Times", "B", 11)
    pdf.cell(22, 7, "Produto:", 0, 0, "L", 1)
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 7, proposal_data.get('produto', ''), 0, 1, "L", 1)

    pdf.set_font("Times", "B", 11)
    pdf.cell(38, 7, "Qtd. Protótipos:", 0, 0, "L", 1)
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 7, "2", 0, 1, "L", 1)

    # Linha divisória fina
    pdf.set_line_width(0.2)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # Descrição técnica do produto
    pdf.ln(2)
    pdf.set_font("Times", "B", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, "Descrição Técnica do Produto", ln=True)
    pdf.set_font("Times", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(250, 250, 250)
    pdf.multi_cell(0, 6, proposal_data.get('descrição', ''), fill=True)

    # Observações para produção (centralizado e largura máxima)
    pdf.ln(2)
    pdf.set_font("Times", "B", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.w - 2 * pdf.l_margin, 7, "Observações para Produção", ln=True, align="C")
    pdf.set_font("Times", "", 10)
    pdf.set_text_color(0, 0, 0)
    obs_text = (
        "Produzir 2 protótipos conforme especificações acima para aprovação do cliente antes da produção em escala. "
        "Atenção: Não iniciar produção sem aprovação formal do cliente."
    )
    y_obs = pdf.get_y()
    y_limit = pdf.h - pdf.b_margin - 35
    obs_lines = pdf.multi_cell(pdf.w - 2 * pdf.l_margin, 6, obs_text, align="C", split_only=True)
    obs_height = len(obs_lines) * 6
    if y_obs + obs_height > y_limit:
        pdf.add_page()
        y_obs = pdf.get_y()
    pdf.set_y(y_obs)
    pdf.multi_cell(pdf.w - 2 * pdf.l_margin, 6, obs_text, align="C")

    # Assinatura centralizada (ajuste para sempre caber e centralizar)
    pdf.set_font("Times", "B", 11)
    y_assin = pdf.get_y()
    if y_assin > pdf.h - pdf.b_margin - 25:
        pdf.add_page()
        y_assin = pdf.get_y()
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.w - 2 * pdf.l_margin, 7, "Assinatura do Responsável pela Aprovação:", ln=True, align="C")
    pdf.ln(7)
    pdf.set_font("Times", "", 11)
    assinatura_line = "_________________________________________"
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.w - 2 * pdf.l_margin, 7, assinatura_line, ln=True, align="C")
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.w - 2 * pdf.l_margin, 7, proposal_data.get('cliente', ''), ln=True, align="C")

    pdf.output(output_path)
