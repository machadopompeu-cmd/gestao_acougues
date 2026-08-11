import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
import math
import json
import numpy as np
from fpdf import FPDF

# =========================================================================
# 1. CONFIGURAÇÃO VISUAL E ESTILIZAÇÃO DA INTERFACE (UI/UX)
# =========================================================================
st.set_page_config(page_title="Gestão de Açougues - Renato Frigotudo & Associados", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
        color: #0F172A; 
    }
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] select {
        border: 1px solid #94A3B8 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 6px 12px !important;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stNumberInput"] input:focus {
        border-color: #1E3A8A !important;
        box-shadow: 0 0 0 2px rgba(30, 58, 138, 0.2) !important;
    }
    label {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    div.stButton > button,
    div.stDownloadButton > button {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #1E3A8A !important;
        padding: 8px 18px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: #1D4ED8 !important;
        color: #FFFFFF !important;
        border-color: #1D4ED8 !important;
    }
    form button,
    div.stFormSubmitButton > button {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #1E3A8A !important;
        font-weight: 700 !important;
    }
    form button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #1D4ED8 !important;
    }
    h1, h2, h3, h4 {
        color: #0F172A !important; 
        font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 2px solid #1E293B;
    }
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] div.stButton > button,
    section[data-testid="stSidebar"] div.stDownloadButton > button,
    section[data-testid="stSidebar"] a {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border: 1px solid #3B82F6 !important;
        width: 100% !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover,
    section[data-testid="stSidebar"] div.stDownloadButton > button:hover {
        background-color: #1D4ED8 !important;
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================================
# 2. CONEXÃO AO BANCO DE DADOS E INICIALIZAÇÃO DE TABELAS
# =========================================================================
def get_connection():
    if "DB_URL" in st.secrets:
        import psycopg2
        url = st.secrets["DB_URL"]
        if "?" in url:
            url = url.split("?")[0]
        return psycopg2.connect(url)
    else:
        return sqlite3.connect("desossa_db.db")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = "psycopg2" in str(type(conn))
    
    if is_postgres:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                login TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                ativo INTEGER DEFAULT 1
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_desossa (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                empresa_id INTEGER DEFAULT NULL,
                UNIQUE(nome, empresa_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cortes_padrao (
                id SERIAL PRIMARY KEY,
                tipo_desossa TEXT NOT NULL,
                nome_corte TEXT NOT NULL,
                empresa_id INTEGER DEFAULT NULL,
                UNIQUE(tipo_desossa, nome_corte, empresa_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acoes (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER,
                data_acao TEXT,
                tipo_animal TEXT,
                peso_bruto REAL,
                preco_animal_kg REAL,
                ossos_muxiba REAL,
                quebra_nao_identificada REAL,
                exsudato_escorrimento REAL,
                p_cartao REAL DEFAULT 0.0,
                p_impostos REAL DEFAULT 0.0,
                p_embalagens REAL DEFAULT 0.0,
                p_comissao REAL DEFAULT 0.0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fichas_tecnicas (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER,
                produto TEXT NOT NULL,
                referencia TEXT DEFAULT 'Produto Processado',
                rendimento_kg REAL DEFAULT 0.0,
                rendimento_assada_kg REAL DEFAULT 0.0,
                peso_unidade_kg REAL DEFAULT 0.0,
                qtd_por_pacote REAL DEFAULT 1.0,
                unidades_produzidas REAL DEFAULT 1.0,
                perda_pct REAL DEFAULT 0.0,
                insumos_ali_json TEXT,
                insumos_nao_ali_json TEXT,
                precificacao_json TEXT,
                data_criacao TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ncg_registros (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER,
                titulo TEXT,
                data_registro TEXT,
                dados_financeiros_json TEXT,
                prazos_json TEXT,
                calculos_json TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cortes (
                id SERIAL PRIMARY KEY,
                acao_id INTEGER,
                nome_corte TEXT,
                qualidade TEXT,
                peso REAL,
                preco_venda REAL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                ativo INTEGER DEFAULT 1
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_desossa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                empresa_id INTEGER DEFAULT NULL,
                UNIQUE(nome, empresa_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cortes_padrao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_desossa TEXT NOT NULL,
                nome_corte TEXT NOT NULL,
                empresa_id INTEGER DEFAULT NULL,
                UNIQUE(tipo_desossa, nome_corte, empresa_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER,
                data_acao TEXT,
                tipo_animal TEXT,
                peso_bruto REAL,
                preco_animal_kg REAL,
                ossos_muxiba REAL,
                quebra_nao_identificada REAL,
                exsudato_escorrimento REAL,
                p_cartao REAL DEFAULT 0.0,
                p_impostos REAL DEFAULT 0.0,
                p_embalagens REAL DEFAULT 0.0,
                p_comissao REAL DEFAULT 0.0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fichas_tecnicas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER,
                produto TEXT NOT NULL,
                referencia TEXT DEFAULT 'Produto Processado',
                rendimento_kg REAL DEFAULT 0.0,
                rendimento_assada_kg REAL DEFAULT 0.0,
                peso_unidade_kg REAL DEFAULT 0.0,
                qtd_por_pacote REAL DEFAULT 1.0,
                unidades_produzidas REAL DEFAULT 1.0,
                perda_pct REAL DEFAULT 0.0,
                insumos_ali_json TEXT,
                insumos_nao_ali_json TEXT,
                precificacao_json TEXT,
                data_criacao TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ncg_registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER,
                titulo TEXT,
                data_registro TEXT,
                dados_financeiros_json TEXT,
                prazos_json TEXT,
                calculos_json TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cortes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acao_id INTEGER,
                nome_corte TEXT,
                qualidade TEXT,
                peso REAL,
                preco_venda REAL
            )
        """)

    conn.commit()

    # Inserção de registro padrão do Excel se tabela de fichas estiver vazia
    cursor.execute("SELECT COUNT(*) FROM fichas_tecnicas")
    if cursor.fetchone()[0] == 0:
        ins_ali_default = json.dumps([
            {"cod": "001", "produto": "COSTELA", "qtd_bruta": 21.0, "unidade": "KG", "preco_bruto": 24.90, "rendimento": 1.0},
            {"cod": "002", "produto": "PAPRICA DEFUMADA", "qtd_bruta": 0.2, "unidade": "KG", "preco_bruto": 29.00, "rendimento": 1.0},
            {"cod": "003", "produto": "SAL GROSSO", "qtd_bruta": 0.3, "unidade": "KG", "preco_bruto": 6.00, "rendimento": 1.0},
            {"cod": "004", "produto": "AMACIANTE DE CARNES", "qtd_bruta": 0.4, "unidade": "KG", "preco_bruto": 19.00, "rendimento": 1.0}
        ])
        
        ins_nao_ali_default = json.dumps([
            {"cod": "101", "produto": "GAS", "qtd_bruta": 0.25, "unidade": "UNID", "preco_bruto": 130.00, "rendimento": 1.0},
            {"cod": "102", "produto": "EMBALAGEM", "qtd_bruta": 1.0, "unidade": "UNID", "preco_bruto": 70.00, "rendimento": 1.0}
        ])
        
        precif_default = json.dumps({
            "imposto_pct": 5.0,
            "tx_cartao_pct": 5.0,
            "comissao_pct": 3.51,
            "outros_custos_var_pct": 1.0,
            "desp_fixas_pct": 2.0,
            "margem_lucro_pct": 31.6724,
            "desconto_simulado_pct": 0.0,
            "opcao_cer": "Custo/kg Total Depois de Assada"
        })
        
        if is_postgres:
            cursor.execute("""
                INSERT INTO fichas_tecnicas (
                    empresa_id, produto, referencia, rendimento_kg, rendimento_assada_kg,
                    peso_unidade_kg, qtd_por_pacote, unidades_produzidas, perda_pct,
                    insumos_ali_json, insumos_nao_ali_json, precificacao_json, data_criacao
                ) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("COSTELA ASSADA", "Produto Processado", 21.9, 14.226, 0.118, 4.0, 120.0, 0.350411, ins_ali_default, ins_nao_ali_default, precif_default, str(datetime.date.today())))
        else:
            cursor.execute("""
                INSERT INTO fichas_tecnicas (
                    empresa_id, produto, referencia, rendimento_kg, rendimento_assada_kg,
                    peso_unidade_kg, qtd_por_pacote, unidades_produzidas, perda_pct,
                    insumos_ali_json, insumos_nao_ali_json, precificacao_json, data_criacao
                ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("COSTELA ASSADA", "Produto Processado", 21.9, 14.226, 0.118, 4.0, 120.0, 0.350411, ins_ali_default, ins_nao_ali_default, precif_default, str(datetime.date.today())))

    conn.commit()
    conn.close()

init_db()

def get_tipos_desossa(empresa_id):
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = "psycopg2" in str(type(conn))
    
    if empresa_id == 0:
        cursor.execute("SELECT DISTINCT nome FROM tipos_desossa ORDER BY nome ASC")
    else:
        if is_postgres:
            cursor.execute("SELECT DISTINCT nome FROM tipos_desossa WHERE empresa_id IS NULL OR empresa_id = %s ORDER BY nome ASC", (empresa_id,))
        else:
            cursor.execute("SELECT DISTINCT nome FROM tipos_desossa WHERE empresa_id IS NULL OR empresa_id = ? ORDER BY nome ASC", (empresa_id,))
    tipos = [r[0] for r in cursor.fetchall()]
    conn.close()
    return tipos

# =========================================================================
# 3. CONTROLE DE ESTADOS DO FORMULÁRIO E CABEÇALHO
# =========================================================================
def init_form_states():
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    if "cortes_temp" not in st.session_state:
        st.session_state.cortes_temp = []

def reset_form_states():
    st.session_state.form_version += 1
    st.session_state.cortes_temp = []

def exibir_cabecalho(nome_empresa_usuaria=None):
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        logo_encontrada = None
        for nome_possivel in ["logo_renato.jpeg", "logo_renato.jpg", "LOGO FINALIZADA.jpeg", "logo_renato.png"]:
            if os.path.exists(nome_possivel):
                logo_encontrada = nome_possivel
                break
                
        if logo_encontrada:
            st.image(logo_encontrada, width=120)
        else:
            st.markdown("### 🍖 [LOGO]")
            
    with col_info:
        cabecalho_principal = "RENATO FRIGOTUDO & ASSOCIADOS"
        subtitulo_empresa = nome_empresa_usuaria.upper() if nome_empresa_usuaria else "PORTAL DE ACESSO"

        st.markdown(
            f"""
            <div style="padding-top: 5px;">
                <h1 style="margin: 0; color: #1E3A8A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 28px; font-weight: 800; letter-spacing: 1px;">
                    {cabecalho_principal}
                </h1>
                <h3 style="margin: 4px 0 0 0; color: #0F172A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 18px; font-weight: 700;">
                    🏢 Empresa Usuária: {subtitulo_empresa}
                </h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px; border-top: 3px solid #1E3A8A;'>", unsafe_allow_html=True)

# =========================================================================
# 4. GERADORES DE RELATÓRIOS EM PDF
# =========================================================================
def gerar_pdf_relatorio_ficha_tecnica(
    nome_empresa, produto, referencia, rend_crua, rend_assada, peso_unid, unid_prod, qtd_pacote,
    insumos_ali, insumos_nao_ali, precif_params, calc_res
):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    pdf.set_fill_color(30, 58, 138)
    pdf.rect(10, 8, 190, 12, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", style="B", size=10)
    pdf.set_xy(10, 10)
    pdf.cell(190, 8, f"RENATO FRIGOTUDO & ASSOCIADOS - FICHA TÉCNICA DA {produto.upper()}", ln=1, align="C")

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Arial", style="B", size=8.5)
    pdf.set_xy(10, 22)
    data_str = datetime.date.today().strftime("%d/%m/%Y")
    pdf.cell(190, 5, f"Empresa: {nome_empresa.upper()} | Produto: {produto.upper()} | Ref: {referencia} | Data: {data_str}", ln=1, align="C")
    pdf.ln(3)

    pdf.set_font("Arial", style="B", size=8)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(92, 5, "PARÂMETROS DE PRODUÇÃO", 1, 0, 'C', True)
    pdf.cell(6, 5, "", 0, 0)
    pdf.cell(92, 5, "RESUMO DE CUSTOS DA TABELA", 1, 1, 'C', True)

    pdf.set_font("Arial", size=7.5)
    perda_pct = (1.0 - (rend_assada / rend_crua)) * 100.0 if rend_crua > 0 else 0.0

    prod_rows = [
        ("Rendimento kg", f"{rend_crua:.3f}"),
        ("Rendimento Depois de Assada kg", f"{rend_assada:.3f}"),
        ("Perda %", f"{perda_pct:.2f}%"),
        ("Peso da Unidade KG", f"{peso_unid:.3f}"),
        ("Unidades Produzidas", f"{int(unid_prod)}"),
        ("Quantidade no Pacote", f"{int(qtd_pacote)}")
    ]

    custo_rows = [
        ("Custo Total Insumos Alimentícios", f"R$ {calc_res['tot_ali_custo']:,.2f}"),
        ("Custo Total Não Alimentícios", f"R$ {calc_res['tot_nao_ali_custo']:,.2f}"),
        ("CUSTO TOTAL DA ORDEM", f"R$ {calc_res['custo_total']:,.2f}"),
        ("Custo/Kg Crua", f"R$ {calc_res['custo_kg_crua']:,.2f}"),
        ("Custo/kg Total Depois de Assada", f"R$ {calc_res['custo_kg_assada']:,.2f}"),
        ("Custo da Unidade / Pacote", f"R$ {calc_res['custo_unidade']:,.2f} / R$ {calc_res['custo_pacote']:,.2f}")
    ]

    for i in range(len(prod_rows)):
        pdf.cell(52, 4.5, prod_rows[i][0], 1, 0, 'L')
        pdf.cell(40, 4.5, prod_rows[i][1], 1, 0, 'R')
        pdf.cell(6, 4.5, "", 0, 0)
        pdf.cell(52, 4.5, custo_rows[i][0], 1, 0, 'L')
        pdf.cell(40, 4.5, custo_rows[i][1], 1, 1, 'R')

    pdf.ln(3)

    pdf.set_font("Arial", style="B", size=8)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(190, 5, f"PRECIFICAÇÃO DA {produto.upper()} (POR KG)", 1, 1, 'C', True)

    pdf.set_font("Arial", style="B", size=7)
    headers_prec = ["Componente da Formação do Preço", "Alíquota (%)", "R$ / KG (Venda Normal)", "R$ / KG (c/ Desconto)"]
    w_prec = [70, 35, 42.5, 42.5]
    for k, h in enumerate(headers_prec):
        pdf.cell(w_prec[k], 5, h, 1, 0, 'C', True)
    pdf.ln()

    pdf.set_font("Arial", size=7)
    p_data = [
        ("Custo de Aquisição (CER)", f"{calc_res['cer_pct']:.2f}%", f"R$ {calc_res['cer']:,.2f}", f"R$ {calc_res['cer']:,.2f}"),
        ("Imposto", f"{precif_params['imposto_pct']:.2f}%", f"R$ {calc_res['val_imp']:,.2f}", f"R$ {calc_res['f_imp']:,.2f}"),
        ("Tx. de Cartão e Antecipação", f"{precif_params['tx_cartao_pct']:.2f}%", f"R$ {calc_res['val_cart']:,.2f}", f"R$ {calc_res['f_cart']:,.2f}"),
        ("Comissão", f"{precif_params['comissao_pct']:.2f}%", f"R$ {calc_res['val_com']:,.2f}", f"R$ {calc_res['f_com']:,.2f}"),
        ("Outros Custos Variáveis e Oper.", f"{precif_params['outros_custos_var_pct']:.2f}%", f"R$ {calc_res['val_outros']:,.2f}", f"R$ {calc_res['f_outros']:,.2f}"),
        ("Margem de Contribuição", f"{calc_res['margem_contrib_pct']:.2f}%", f"R$ {calc_res['margem_contrib_rs']:,.2f}", f"R$ {calc_res['margem_contrib_desc']:,.2f}"),
        ("Partic. Despesas Fixas e não Oper.", f"{precif_params['desp_fixas_pct']:.2f}%", f"R$ {calc_res['val_fixas']:,.2f}", f"R$ {calc_res['f_fixas']:,.2f}"),
        ("Margem de Lucro", f"{precif_params['margem_lucro_pct']:.2f}%", f"R$ {calc_res['val_lucro']:,.2f}", f"R$ {calc_res['lucro_desc']:,.2f}")
    ]

    for comp, aliq, val_n, val_d in p_data:
        pdf.cell(w_prec[0], 4.5, comp, 1, 0, 'L')
        pdf.cell(w_prec[1], 4.5, aliq, 1, 0, 'R')
        pdf.cell(w_prec[2], 4.5, val_n, 1, 0, 'R')
        pdf.cell(w_prec[3], 4.5, val_d, 1, 1, 'R')

    pdf.set_font("Arial", style="B", size=7.5)
    pdf.cell(w_prec[0], 5, "SOMA DAS ALÍQUOTAS / PREÇO DE VENDA:", 1, 0, 'L', True)
    pdf.cell(w_prec[1], 5, f"{calc_res['soma_aliquotas']*100:.2f}%", 1, 0, 'R', True)
    pdf.cell(w_prec[2], 5, f"R$ {calc_res['pv']:,.2f} / KG", 1, 0, 'R', True)
    pdf.cell(w_prec[3], 5, f"R$ {calc_res['pv_desc']:,.2f} / KG", 1, 1, 'R', True)

    pdf.cell(w_prec[0], 5, "MARKUP APLICADO:", 1, 0, 'L', True)
    pdf.cell(w_prec[1], 5, f"{calc_res['markup']*100:.2f}%", 1, 0, 'R', True)
    pdf.cell(w_prec[2] + w_prec[3], 5, f"LUCRO C/ DESCONTO: R$ {calc_res['lucro_desc']:,.2f} / KG", 1, 1, 'C', True)

    return pdf.output(dest='S').encode('latin1')

def gerar_pdf_relatorio_ncg(nome_empresa, dados_fin, prazos, calcs, liquidez, diag):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    pdf.set_fill_color(30, 58, 138)
    pdf.rect(10, 8, 190, 12, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", style="B", size=10)
    pdf.set_xy(10, 10)
    pdf.cell(190, 8, "RENATO FRIGOTUDO & ASSOCIADOS - ANÁLISE DE NECESSIDADE DE CAPITAL DE GIRO", ln=1, align="C")

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Arial", style="B", size=8.5)
    pdf.set_xy(10, 22)
    data_str = datetime.date.today().strftime("%d/%m/%Y")
    pdf.cell(190, 5, f"Empresa: {nome_empresa.upper()} | Data de Emissão: {data_str}", ln=1, align="C")
    pdf.ln(3)

    pdf.set_font("Arial", style="B", size=8)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(190, 5, "1. DADOS FINANCEIROS DA EMPRESA", 1, 1, 'C', True)

    pdf.set_font("Arial", size=7.5)
    dfin_rows = [
        ("Faturamento Bruto Mensal", f"R$ {dados_fin['fat']:,.2f}"),
        ("Custo da Mercadoria Vendida (CMV)", f"R$ {dados_fin['cmv']:,.2f}"),
        ("Contas a Receber Acumuladas", f"R$ {dados_fin['receber']:,.2f}"),
        ("Estoque Atual", f"R$ {dados_fin['estoque']:,.2f}"),
        ("Contas a Pagar (Fornecedores)", f"R$ {dados_fin['pagar']:,.2f}"),
        ("Reserva Financeira (Caixa)", f"R$ {dados_fin['caixa']:,.2f}")
    ]
    for desc, val in dfin_rows:
        pdf.cell(100, 4.2, desc, 1, 0, 'L')
        pdf.cell(90, 4.2, val, 1, 1, 'R')

    pdf.ln(3)
    pdf.set_font("Arial", style="B", size=8)
    pdf.cell(190, 5, "2. PRAZOS MÉDIOS OPERACIONAIS E CICLO FINANCEIRO", 1, 1, 'C', True)

    pdf.set_font("Arial", size=7.5)
    prazos_rows = [
        ("Prazo Médio de Estoque (PME)", f"{prazos['pme_atual']:.1f} dias", f"{prazos['pme_prop']:.1f} dias"),
        ("Prazo Médio de Recebimento (PMR)", f"{prazos['pmr_atual']:.1f} dias", f"{prazos['pmr_prop']:.1f} dias"),
        ("Prazo Médio de Pagamento (PMP)", f"{prazos['pmp_atual']:.1f} dias", f"{prazos['pmp_prop']:.1f} dias"),
        ("CICLO FINANCEIRO (dias)", f"{calcs['ciclo_atual']:.1f} dias", f"{calcs['ciclo_prop']:.1f} dias"),
        ("NECESSIDADE DE CAPITAL DE GIRO (NCG)", f"R$ {calcs['ncg_atual']:,.2f}", f"R$ {calcs['ncg_prop']:,.2f}")
    ]
    for desc, ca, cp in prazos_rows:
        pdf.cell(90, 4.2, desc, 1, 0, 'L')
        pdf.cell(50, 4.2, f"Atual: {ca}", 1, 0, 'C')
        pdf.cell(50, 4.2, f"Proposto: {cp}", 1, 1, 'C')

    return pdf.output(dest='S').encode('latin1')

# =========================================================================
# 5. MÓDULO FICHA TÉCNICA REESTRUTURADO (CONFORME ARQUIVO XLSX)
# =========================================================================
def render_modulo_ficha_tecnica():
    st.header("📋 Módulo de Ficha Técnica & Precificação")
    emp_id_ativo = st.session_state.empresa_id

    conn = get_connection()
    is_postgres = "psycopg2" in str(type(conn))

    st.subheader("🔍 Buscar ou Selecionar Ficha Técnica Armazenada")
    col_search1, col_search2 = st.columns([3, 1])
    
    termo_busca = col_search1.text_input("Buscar por Nome do Produto / Ficha Técnica", value="")

    if emp_id_ativo == 0:
        if termo_busca.strip():
            query_ft = "SELECT * FROM fichas_tecnicas WHERE LOWER(produto) LIKE %s ORDER BY produto ASC" if is_postgres else f"SELECT * FROM fichas_tecnicas WHERE LOWER(produto) LIKE '%{termo_busca.lower().strip()}%' ORDER BY produto ASC"
            df_ft_db = pd.read_sql_query(query_ft, conn, params=(f"%{termo_busca.lower().strip()}%",) if is_postgres else None)
        else:
            df_ft_db = pd.read_sql_query("SELECT * FROM fichas_tecnicas ORDER BY produto ASC", conn)
    else:
        if termo_busca.strip():
            query_ft = "SELECT * FROM fichas_tecnicas WHERE (empresa_id IS NULL OR empresa_id = %s) AND LOWER(produto) LIKE %s ORDER BY produto ASC" if is_postgres else f"SELECT * FROM fichas_tecnicas WHERE (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) AND LOWER(produto) LIKE '%{termo_busca.lower().strip()}%' ORDER BY produto ASC"
            df_ft_db = pd.read_sql_query(query_ft, conn, params=(emp_id_ativo, f"%{termo_busca.lower().strip()}%") if is_postgres else None)
        else:
            query_ft = "SELECT * FROM fichas_tecnicas WHERE (empresa_id IS NULL OR empresa_id = %s) ORDER BY produto ASC" if is_postgres else f"SELECT * FROM fichas_tecnicas WHERE (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) ORDER BY produto ASC"
            df_ft_db = pd.read_sql_query(query_ft, conn, params=(emp_id_ativo,) if is_postgres else None)

    opcoes_fichas = ["➕ Criar Nova Ficha Técnica"]
    if not df_ft_db.empty:
        opcoes_fichas += [f"#{r['id']} - {r['produto']}" for _, r in df_ft_db.iterrows()]

    ficha_selecionada = st.selectbox("Selecione a Ficha para Editar ou Visualizar", opcoes_fichas)

    if "ft_items_ali" not in st.session_state:
        st.session_state.ft_items_ali = []
    if "ft_items_nao_ali" not in st.session_state:
        st.session_state.ft_items_nao_ali = []
    if "ft_id_carregada" not in st.session_state:
        st.session_state.ft_id_carregada = None

    if col_search2.button("📥 Carregar Ficha"):
        if ficha_selecionada == "➕ Criar Nova Ficha Técnica":
            st.session_state.ft_id_carregada = None
            st.session_state.ft_items_ali = []
            st.session_state.ft_items_nao_ali = []
            st.session_state.ft_produto = "NOVO PRODUTO"
            st.session_state.ft_ref = "Produto Processado"
            st.session_state.ft_rend_crua = 21.900
            st.session_state.ft_rend_assada = 14.226
            st.session_state.ft_peso_unid = 0.118
            st.session_state.ft_unid_prod = 120.0
            st.session_state.ft_qtd_pacote = 4.0
            st.session_state.ft_precif = {
                "imposto_pct": 5.0, "tx_cartao_pct": 5.0, "comissao_pct": 3.51,
                "outros_custos_var_pct": 1.0, "desp_fixas_pct": 2.0, "margem_lucro_pct": 31.6724,
                "desconto_simulado_pct": 0.0, "opcao_cer": "Custo/kg Total Depois de Assada"
            }
            st.success("Nova Ficha Técnica iniciada!")
            st.rerun()
        else:
            ft_id = int(ficha_selecionada.split(" - ")[0].replace("#", ""))
            row_ft = df_ft_db[df_ft_db['id'] == ft_id].iloc[0]
            st.session_state.ft_id_carregada = ft_id
            st.session_state.ft_produto = str(row_ft['produto'])
            st.session_state.ft_ref = str(row_ft.get('referencia', 'Produto Processado'))
            st.session_state.ft_rend_crua = float(row_ft['rendimento_kg'])
            st.session_state.ft_rend_assada = float(row_ft['rendimento_assada_kg'])
            st.session_state.ft_peso_unid = float(row_ft['peso_unidade_kg'])
            st.session_state.ft_unid_prod = float(row_ft['unidades_produzidas'])
            st.session_state.ft_qtd_pacote = float(row_ft['qtd_por_pacote'])

            try:
                st.session_state.ft_items_ali = json.loads(row_ft['insumos_ali_json']) if row_ft['insumos_ali_json'] else []
            except Exception:
                st.session_state.ft_items_ali = []

            try:
                st.session_state.ft_items_nao_ali = json.loads(row_ft['insumos_nao_ali_json']) if row_ft['insumos_nao_ali_json'] else []
            except Exception:
                st.session_state.ft_items_nao_ali = []

            try:
                st.session_state.ft_precif = json.loads(row_ft['precificacao_json']) if row_ft['precificacao_json'] else {}
            except Exception:
                st.session_state.ft_precif = {}
            st.success(f"Ficha Técnica #{ft_id} ({row_ft['produto']}) carregada com sucesso!")
            st.rerun()

    # Padrão inicial igual à aba COSTELA ASSADA do XLSx
    if "ft_produto" not in st.session_state:
        st.session_state.ft_produto = "COSTELA ASSADA"
        st.session_state.ft_ref = "Produto Processado"
        st.session_state.ft_rend_crua = 21.900
        st.session_state.ft_rend_assada = 14.226
        st.session_state.ft_peso_unid = 0.118
        st.session_state.ft_unid_prod = 120.0
        st.session_state.ft_qtd_pacote = 4.0
        st.session_state.ft_items_ali = [
            {"cod": "001", "produto": "COSTELA", "qtd_bruta": 21.0, "unidade": "KG", "preco_bruto": 24.90, "rendimento": 1.0},
            {"cod": "002", "produto": "PAPRICA DEFUMADA", "qtd_bruta": 0.2, "unidade": "KG", "preco_bruto": 29.00, "rendimento": 1.0},
            {"cod": "003", "produto": "SAL GROSSO", "qtd_bruta": 0.3, "unidade": "KG", "preco_bruto": 6.00, "rendimento": 1.0},
            {"cod": "004", "produto": "AMACIANTE DE CARNES", "qtd_bruta": 0.4, "unidade": "KG", "preco_bruto": 19.00, "rendimento": 1.0}
        ]
        st.session_state.ft_items_nao_ali = [
            {"cod": "101", "produto": "GAS", "qtd_bruta": 0.25, "unidade": "UNID", "preco_bruto": 130.00, "rendimento": 1.0},
            {"cod": "102", "produto": "EMBALAGEM", "qtd_bruta": 1.0, "unidade": "UNID", "preco_bruto": 70.00, "rendimento": 1.0}
        ]
        st.session_state.ft_precif = {
            "imposto_pct": 5.0, "tx_cartao_pct": 5.0, "comissao_pct": 3.51,
            "outros_custos_var_pct": 1.0, "desp_fixas_pct": 2.0, "margem_lucro_pct": 31.6724,
            "desconto_simulado_pct": 0.0, "opcao_cer": "Custo/kg Total Depois de Assada"
        }

    st.markdown("---")
    tab_ft, tab_prec = st.tabs(["🍖 Ficha Técnica / Ordem de Produção", "💲 Precificação do Produto (Por KG)"])

    with tab_ft:
        st.subheader("📌 Parâmetros de Produção & Rendimentos")
        col_f1, col_f2, col_f3 = st.columns(3)
        
        ft_produto = col_f1.text_input("Nome do Produto Processado", value=st.session_state.ft_produto)
        ft_ref = col_f2.text_input("Referência", value=st.session_state.ft_ref)
        ft_rend_crua = col_f3.number_input("Rendimento kg", min_value=0.001, value=st.session_state.ft_rend_crua, step=0.1, format="%.3f")

        col_f4, col_f5, col_f6, col_f7 = st.columns(4)
        ft_rend_assada = col_f4.number_input("Rendimento Depois de Assada kg", min_value=0.001, value=st.session_state.ft_rend_assada, step=0.1, format="%.3f")
        ft_peso_unid = col_f5.number_input("Peso da Unidade KG", min_value=0.001, value=st.session_state.ft_peso_unid, step=0.005, format="%.3f")
        ft_unid_prod = col_f6.number_input("Unidades Produzidas", min_value=1.0, value=st.session_state.ft_unid_prod, step=1.0)
        ft_qtd_pacote = col_f7.number_input("Quantidade no Pacote", min_value=1.0, value=st.session_state.ft_qtd_pacote, step=1.0)

        # Cálculo de Perda % Exato do Excel
        perda_pct = (1.0 - (ft_rend_assada / ft_rend_crua)) * 100.0 if ft_rend_crua > 0 else 0.0

        st.info(f"📊 **Perda no Processo:** `{perda_pct:.4f}%` | **Unidades Produzidas:** `{int(ft_unid_prod)}` | **Qtd p/ Pacote:** `{int(ft_qtd_pacote)}`")

        st.markdown("---")
        st.subheader("1. Insumos Alimentícios")
        
        with st.expander("➕ Adicionar Novo Insumo Alimentício"):
            with st.form("form_add_insumo_ali"):
                c_i1, c_i2, c_i3, c_i4, c_i5 = st.columns([3, 1.5, 1.5, 2, 1.5])
                add_ali_nome = c_i1.text_input("Produto Insumo")
                add_ali_qtd = c_i2.number_input("Qtd Bruta", min_value=0.0, value=1.0, step=0.1)
                add_ali_unid = c_i3.selectbox("Unidade", ["KG", "UNID", "G", "ML", "L"])
                add_ali_preco = c_i4.number_input("Preço Bruto (R$)", min_value=0.0, value=10.0, step=1.0)
                add_ali_rend = c_i5.number_input("Fator Rend.", min_value=0.01, value=1.0, step=0.1)
                
                if st.form_submit_button("Adicionar Item Alimentício") and add_ali_nome:
                    st.session_state.ft_items_ali.append({
                        "cod": f"{len(st.session_state.ft_items_ali)+1:03d}",
                        "produto": add_ali_nome.upper().strip(),
                        "qtd_bruta": add_ali_qtd,
                        "unidade": add_ali_unid,
                        "preco_bruto": add_ali_preco,
                        "rendimento": add_ali_rend
                    })
                    st.success(f"Insumo '{add_ali_nome}' adicionado!")
                    st.rerun()

        if st.session_state.ft_items_ali:
            rows_ali = []
            for idx, item in enumerate(st.session_state.ft_items_ali):
                ql = item['qtd_bruta'] * item['rendimento']
                pl = ql * item['preco_bruto']
                rows_ali.append({
                    "Cód": item.get('cod', f"{idx+1:03d}"),
                    "Produto": item['produto'],
                    "Qtd Bruta": item['qtd_bruta'],
                    "Unid": item['unidade'],
                    "Preço Bruto (R$)": item['preco_bruto'],
                    "Rendimento": item['rendimento'],
                    "Qtd Líquida": ql,
                    "Preço Líquido (R$)": pl
                })
            df_ali_view = pd.DataFrame(rows_ali)
            st.dataframe(df_ali_view.style.format({
                "Qtd Bruta": "{:.3f}", "Preço Bruto (R$)": "R$ {:.2f}", "Rendimento": "{:.2f}",
                "Qtd Líquida": "{:.3f}", "Preço Líquido (R$)": "R$ {:.2f}"
            }), use_container_width=True)

            col_del_ali, _ = st.columns([2, 3])
            idx_del_ali = col_del_ali.selectbox("Excluir Item Alimentício", range(len(st.session_state.ft_items_ali)), format_func=lambda i: f"{st.session_state.ft_items_ali[i]['produto']}")
            if col_del_ali.button("🗑️ Remover Item Selecionado", key="btn_del_ali"):
                st.session_state.ft_items_ali.pop(idx_del_ali)
                st.rerun()

        st.markdown("---")
        st.subheader("2. Insumos Não Alimentícios (Gás, Embalagens, etc.)")
        
        with st.expander("➕ Adicionar Novo Insumo Não Alimentício"):
            with st.form("form_add_insumo_nao_ali"):
                c_n1, c_n2, c_n3, c_n4, c_n5 = st.columns([3, 1.5, 1.5, 2, 1.5])
                add_nali_nome = c_n1.text_input("Produto / Consumível")
                add_nali_qtd = c_n2.number_input("Qtd Bruta", min_value=0.0, value=1.0, step=0.1)
                add_nali_unid = c_n3.selectbox("Unidade", ["UNID", "KG", "CX", "ROLO"])
                add_nali_preco = c_n4.number_input("Preço Bruto (R$)", min_value=0.0, value=50.0, step=1.0)
                add_nali_rend = c_n5.number_input("Fator Rend.", min_value=0.01, value=1.0, step=0.1)
                
                if st.form_submit_button("Adicionar Item Não Alimentício") and add_nali_nome:
                    st.session_state.ft_items_nao_ali.append({
                        "cod": f"{len(st.session_state.ft_items_nao_ali)+101:03d}",
                        "produto": add_nali_nome.upper().strip(),
                        "qtd_bruta": add_nali_qtd,
                        "unidade": add_nali_unid,
                        "preco_bruto": add_nali_preco,
                        "rendimento": add_nali_rend
                    })
                    st.success(f"Insumo '{add_nali_nome}' adicionado!")
                    st.rerun()

        if st.session_state.ft_items_nao_ali:
            rows_nao_ali = []
            for idx, item in enumerate(st.session_state.ft_items_nao_ali):
                ql = item['qtd_bruta'] * item['rendimento']
                pl = ql * item['preco_bruto']
                rows_nao_ali.append({
                    "Cód": item.get('cod', f"{idx+101:03d}"),
                    "Produto": item['produto'],
                    "Qtd Bruta": item['qtd_bruta'],
                    "Unid": item['unidade'],
                    "Preço Bruto (R$)": item['preco_bruto'],
                    "Rendimento": item['rendimento'],
                    "Qtd Líquida": ql,
                    "Preço Líquido (R$)": pl
                })
            df_nao_ali_view = pd.DataFrame(rows_nao_ali)
            st.dataframe(df_nao_ali_view.style.format({
                "Qtd Bruta": "{:.3f}", "Preço Bruto (R$)": "R$ {:.2f}", "Rendimento": "{:.2f}",
                "Qtd Líquida": "{:.3f}", "Preço Líquido (R$)": "R$ {:.2f}"
            }), use_container_width=True)

            col_del_nao_ali, _ = st.columns([2, 3])
            idx_del_nao_ali = col_del_nao_ali.selectbox("Excluir Item Não Alimentício", range(len(st.session_state.ft_items_nao_ali)), format_func=lambda i: f"{st.session_state.ft_items_nao_ali[i]['produto']}")
            if col_del_nao_ali.button("🗑️ Remover Item Selecionado", key="btn_del_nao_ali"):
                st.session_state.ft_items_nao_ali.pop(idx_del_nao_ali)
                st.rerun()

        # CÁLCULOS EXATOS DE ACORDO COM A ABA "COSTELA ASSADA" DO EXCEL
        tot_ali_custo = sum(item['qtd_bruta'] * item['rendimento'] * item['preco_bruto'] for item in st.session_state.ft_items_ali)
        tot_ali_qtd = sum(item['qtd_bruta'] * item['rendimento'] for item in st.session_state.ft_items_ali)
        tot_nao_ali_custo = sum(item['qtd_bruta'] * item['rendimento'] * item['preco_bruto'] for item in st.session_state.ft_items_nao_ali)

        custo_total = tot_ali_custo + tot_nao_ali_custo
        custo_kg_crua = custo_total / ft_rend_crua if ft_rend_crua > 0 else 0.0
        custo_kg_assada = custo_total / ft_rend_assada if ft_rend_assada > 0 else 0.0
        custo_unidade = custo_total / ft_unid_prod if ft_unid_prod > 0 else 0.0
        custo_pacote = custo_unidade * ft_qtd_pacote

        st.markdown("---")
        st.subheader("📊 Tabela de Custos (Conforme Modelo Excel 'COSTELA ASSADA')")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Custo Total", f"R$ {custo_total:,.2f}")
        m2.metric("Custo/Kg Crua", f"R$ {custo_kg_crua:,.2f}")
        m3.metric("Custo/kg Total Depois de Assada", f"R$ {custo_kg_assada:,.2f}")
        m4.metric("Custo da Unidade", f"R$ {custo_unidade:,.4f}")
        m5.metric("Custo do Pacote", f"R$ {custo_pacote:,.2f}")

    with tab_prec:
        st.subheader("💲 Formação do Preço de Venda por KG (Aba PRECIFIC COST ASSADA-KG)")
        
        precif_dict = st.session_state.ft_precif
        opcao_salva_cer = precif_dict.get("opcao_cer", "Custo/kg Total Depois de Assada")

        # Opção do Usuário Escolher o Custo Base para Precificação (CER)
        opcoes_cer_dict = {
            "Custo/kg Total Depois de Assada": (custo_kg_assada, f"Custo/kg Total Depois de Assada (R$ {custo_kg_assada:,.2f} / KG)"),
            "Custo/Kg Crua": (custo_kg_crua, f"Custo/Kg Crua (R$ {custo_kg_crua:,.2f} / KG)"),
            "Custo da Unidade": (custo_unidade, f"Custo da Unidade (R$ {custo_unidade:,.4f} / Unid)"),
            "Custo do Pacote": (custo_pacote, f"Custo do Pacote (R$ {custo_pacote:,.2f} / Pacote)"),
            "Outro Valor Manual": (0.0, "Inserir Outro Custo Manualmente")
        }

        keys_lista = list(opcoes_cer_dict.keys())
        index_def = keys_lista.index(opcao_salva_cer) if opcao_salva_cer in keys_lista else 0

        selecao_cer_chave = st.selectbox("📌 Selecione o Custo Base Selecionado para Precificação (CER):", options=keys_lista, index=index_def, format_func=lambda k: opcoes_cer_dict[k][1])

        if selecao_cer_chave == "Outro Valor Manual":
            cer_efetivo = st.number_input("Digite o Custo de Aquisição / Produção por KG (R$)", min_value=0.0, value=custo_kg_assada, step=0.1)
        else:
            cer_efetivo = opcoes_cer_dict[selecao_cer_chave][0]

        st.info(f"💡 **Custo Base Selecionado para Precificação (CER):** `R$ {cer_efetivo:,.4f}`")
        
        c_p1, c_p2, c_p3 = st.columns(3)
        p_imp = c_p1.number_input("Imposto (%)", min_value=0.0, value=float(precif_dict.get("imposto_pct", 5.0)), step=0.1)
        p_cart = c_p2.number_input("Tx. Cartão e Antecipação (%)", min_value=0.0, value=float(precif_dict.get("tx_cartao_pct", 5.0)), step=0.1)
        p_com = c_p3.number_input("Comissão (%)", min_value=0.0, value=float(precif_dict.get("comissao_pct", 3.51)), step=0.01)

        c_p4, c_p5, c_p6 = st.columns(3)
        p_outros = c_p4.number_input("Outros Custos Variáveis (%)", min_value=0.0, value=float(precif_dict.get("outros_custos_var_pct", 1.0)), step=0.1)
        p_fixas = c_p5.number_input("Partic. Despesas Fixas (%)", min_value=0.0, value=float(precif_dict.get("desp_fixas_pct", 2.0)), step=0.1)
        p_lucro = c_p6.number_input("Margem de Lucro (%)", min_value=0.0, value=float(precif_dict.get("margem_lucro_pct", 31.6724)), step=0.5)

        p_desconto_simulado = st.number_input("Simulação de Desconto para Venda (%)", min_value=0.0, max_value=100.0, value=float(precif_dict.get("desconto_simulado_pct", 0.0)), step=0.5)

        st.session_state.ft_precif = {
            "imposto_pct": p_imp, "tx_cartao_pct": p_cart, "comissao_pct": p_com,
            "outros_custos_var_pct": p_outros, "desp_fixas_pct": p_fixas,
            "margem_lucro_pct": p_lucro, "desconto_simulado_pct": p_desconto_simulado,
            "opcao_cer": selecao_cer_chave
        }

        # Fórmula exata da aba PRECIFIC COST ASSADA-KG
        soma_aliquotas = (p_imp + p_cart + p_com + p_outros + p_fixas + p_lucro) / 100.0
        pv = cer_efetivo / (1.0 - soma_aliquotas) if (1.0 - soma_aliquotas) > 0 else 0.0

        cer_pct = (cer_efetivo / pv) * 100.0 if pv > 0 else 0.0
        val_imp = pv * (p_imp / 100.0)
        val_cart = pv * (p_cart / 100.0)
        val_com = pv * (p_com / 100.0)
        val_outros = pv * (p_outros / 100.0)
        val_fixas = pv * (p_fixas / 100.0)
        val_lucro = pv * (p_lucro / 100.0)

        margem_contrib_pct = p_fixas + p_lucro
        margem_contrib_rs = pv * (margem_contrib_pct / 100.0)
        markup = (pv / cer_efetivo) - 1.0 if cer_efetivo > 0 else 0.0

        pv_desc = pv * (1.0 - (p_desconto_simulado / 100.0))
        f_imp = pv_desc * (p_imp / 100.0)
        f_cart = pv_desc * (p_cart / 100.0)
        f_com = pv_desc * (p_com / 100.0)
        f_outros = pv_desc * (p_outros / 100.0)
        f_fixas = pv_desc * (p_fixas / 100.0)

        margem_contrib_desc = pv_desc - (cer_efetivo + f_imp + f_cart + f_com + f_outros)
        lucro_desc = pv_desc - (cer_efetivo + f_imp + f_cart + f_com + f_outros + f_fixas)

        st.markdown("---")
        st.subheader("📈 Tabela de Composição do Preço de Venda")
        
        df_precif_tab = pd.DataFrame([
            {"Componente": f"Custo de Aquisição (CER - {selecao_cer_chave})", "Alíquota (%)": f"{cer_pct:.2f}%", "Venda Normal (R$/KG)": f"R$ {cer_efetivo:,.4f}", "c/ Desconto (R$/KG)": f"R$ {cer_efetivo:,.4f}"},
            {"Componente": "Imposto", "Alíquota (%)": f"{p_imp:.2f}%", "Venda Normal (R$/KG)": f"R$ {val_imp:,.2f}", "c/ Desconto (R$/KG)": f"R$ {f_imp:,.2f}"},
            {"Componente": "Tx. de Cartão e Antecipação", "Alíquota (%)": f"{p_cart:.2f}%", "Venda Normal (R$/KG)": f"R$ {val_cart:,.2f}", "c/ Desconto (R$/KG)": f"R$ {f_cart:,.2f}"},
            {"Componente": "Comissão", "Alíquota (%)": f"{p_com:.2f}%", "Venda Normal (R$/KG)": f"R$ {val_com:,.2f}", "c/ Desconto (R$/KG)": f"R$ {f_com:,.2f}"},
            {"Componente": "Outros Custos Variáveis e Oper.", "Alíquota (%)": f"{p_outros:.2f}%", "Venda Normal (R$/KG)": f"R$ {val_outros:,.2f}", "c/ Desconto (R$/KG)": f"R$ {f_outros:,.2f}"},
            {"Componente": "Margem de Contribuição", "Alíquota (%)": f"{margem_contrib_pct:.2f}%", "Venda Normal (R$/KG)": f"R$ {margem_contrib_rs:,.2f}", "c/ Desconto (R$/KG)": f"R$ {margem_contrib_desc:,.2f}"},
            {"Componente": "Partic. Despesas Fixas e não Oper.", "Alíquota (%)": f"{p_fixas:.2f}%", "Venda Normal (R$/KG)": f"R$ {val_fixas:,.2f}", "c/ Desconto (R$/KG)": f"R$ {f_fixas:,.2f}"},
            {"Componente": "Margem de Lucro", "Alíquota (%)": f"{p_lucro:.2f}%", "Venda Normal (R$/KG)": f"R$ {val_lucro:,.2f}", "c/ Desconto (R$/KG)": f"R$ {lucro_desc:,.2f}"}
        ])
        st.dataframe(df_precif_tab, use_container_width=True, hide_index=True)

        res1, res2, res3, res4 = st.columns(4)
        res1.metric("Soma das Alíquotas", f"{soma_aliquotas*100:.2f}%")
        res2.metric("PREÇO DE VENDA", f"R$ {pv:,.2f} / KG")
        res3.metric("MARKUP (%)", f"{markup*100:.2f}%")
        res4.metric(f"Lucro c/ Desconto ({p_desconto_simulado:.1f}%)", f"R$ {lucro_desc:,.2f} / KG")

    st.markdown("---")
    st.subheader("💾 Operações na Base de Dados & Relatório PDF")

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    calc_res_pdf = {
        'tot_ali_custo': tot_ali_custo, 'tot_ali_qtd': tot_ali_qtd, 'tot_nao_ali_custo': tot_nao_ali_custo,
        'custo_total': custo_total, 'custo_kg_crua': custo_kg_crua, 'custo_kg_assada': custo_kg_assada,
        'custo_unidade': custo_unidade, 'custo_pacote': custo_pacote, 'cer': cer_efetivo, 'cer_pct': cer_pct,
        'val_imp': val_imp, 'f_imp': f_imp, 'val_cart': val_cart, 'f_cart': f_cart,
        'val_com': val_com, 'f_com': f_com, 'val_outros': val_outros, 'f_outros': f_outros,
        'margem_contrib_pct': margem_contrib_pct, 'margem_contrib_rs': margem_contrib_rs, 'margem_contrib_desc': margem_contrib_desc,
        'val_fixas': val_fixas, 'f_fixas': f_fixas, 'val_lucro': val_lucro, 'lucro_desc': lucro_desc,
        'soma_aliquotas': soma_aliquotas, 'pv': pv, 'pv_desc': pv_desc, 'markup': markup
    }

    if col_btn1.button("💾 Salvar / Atualizar Ficha Técnica Completa"):
        cursor = conn.cursor()
        ins_ali_json_str = json.dumps(st.session_state.ft_items_ali)
        ins_nao_ali_json_str = json.dumps(st.session_state.ft_items_nao_ali)
        precif_json_str = json.dumps(st.session_state.ft_precif)
        data_hoje = str(datetime.date.today())

        if st.session_state.ft_id_carregada is not None:
            if is_postgres:
                cursor.execute("""
                    UPDATE fichas_tecnicas SET
                        produto = %s, referencia = %s, rendimento_kg = %s, rendimento_assada_kg = %s,
                        peso_unidade_kg = %s, qtd_por_pacote = %s, unidades_produzidas = %s, perda_pct = %s,
                        insumos_ali_json = %s, insumos_nao_ali_json = %s, precificacao_json = %s
                    WHERE id = %s
                """, (ft_produto.upper().strip(), ft_ref, ft_rend_crua, ft_rend_assada, ft_peso_unid, ft_qtd_pacote, ft_unid_prod, perda_pct/100.0, ins_ali_json_str, ins_nao_ali_json_str, precif_json_str, st.session_state.ft_id_carregada))
            else:
                cursor.execute("""
                    UPDATE fichas_tecnicas SET
                        produto = ?, referencia = ?, rendimento_kg = ?, rendimento_assada_kg = ?,
                        peso_unidade_kg = ?, qtd_por_pacote = ?, unidades_produzidas = ?, perda_pct = ?,
                        insumos_ali_json = ?, insumos_nao_ali_json = ?, precificacao_json = ?
                    WHERE id = ?
                """, (ft_produto.upper().strip(), ft_ref, ft_rend_crua, ft_rend_assada, ft_peso_unid, ft_qtd_pacote, ft_unid_prod, perda_pct/100.0, ins_ali_json_str, ins_nao_ali_json_str, precif_json_str, st.session_state.ft_id_carregada))
            conn.commit()
            st.success(f"Ficha Técnica '{ft_produto.upper()}' atualizada no banco de dados!")
        else:
            emp_v = emp_id_ativo if emp_id_ativo != 0 else None
            if is_postgres:
                cursor.execute("""
                    INSERT INTO fichas_tecnicas (
                        empresa_id, produto, referencia, rendimento_kg, rendimento_assada_kg,
                        peso_unidade_kg, qtd_por_pacote, unidades_produzidas, perda_pct,
                        insumos_ali_json, insumos_nao_ali_json, precificacao_json, data_criacao
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (emp_v, ft_produto.upper().strip(), ft_ref, ft_rend_crua, ft_rend_assada, ft_peso_unid, ft_qtd_pacote, ft_unid_prod, perda_pct/100.0, ins_ali_json_str, ins_nao_ali_json_str, precif_json_str, data_hoje))
            else:
                cursor.execute("""
                    INSERT INTO fichas_tecnicas (
                        empresa_id, produto, referencia, rendimento_kg, rendimento_assada_kg,
                        peso_unidade_kg, qtd_por_pacote, unidades_produzidas, perda_pct,
                        insumos_ali_json, insumos_nao_ali_json, precificacao_json, data_criacao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (emp_v, ft_produto.upper().strip(), ft_ref, ft_rend_crua, ft_rend_assada, ft_peso_unid, ft_qtd_pacote, ft_unid_prod, perda_pct/100.0, ins_ali_json_str, ins_nao_ali_json_str, precif_json_str, data_hoje))
            conn.commit()
            st.success(f"Ficha Técnica '{ft_produto.upper()}' cadastrada no banco de dados com sucesso!")
        st.rerun()

    if col_btn2.button("🗑️ Excluir Ficha Técnica Completa"):
        if st.session_state.ft_id_carregada is not None:
            cursor = conn.cursor()
            if is_postgres:
                cursor.execute("DELETE FROM fichas_tecnicas WHERE id = %s", (st.session_state.ft_id_carregada,))
            else:
                cursor.execute("DELETE FROM fichas_tecnicas WHERE id = ?", (st.session_state.ft_id_carregada,))
            conn.commit()
            st.session_state.ft_id_carregada = None
            st.success("Ficha Técnica excluída do banco de dados!")
            st.rerun()

    pdf_bytes_ft = gerar_pdf_relatorio_ficha_tecnica(
        st.session_state.empresa_nome if 'empresa_nome' in st.session_state else "Açougue",
        ft_produto, ft_ref, ft_rend_crua, ft_rend_assada, ft_peso_unid, ft_unid_prod, ft_qtd_pacote,
        st.session_state.ft_items_ali, st.session_state.ft_items_nao_ali, st.session_state.ft_precif, calc_res_pdf
    )

    col_btn3.download_button(
        label="📥 Baixar Relatório Completo da Ficha Técnica em PDF",
        data=pdf_bytes_ft,
        file_name=f"ficha_tecnica_{ft_produto.lower().replace(' ', '_')}_{datetime.date.today()}.pdf",
        mime="application/pdf",
        key="btn_pdf_ficha_tecnica"
    )

    conn.close()

# =========================================================================
# 6. MÓDULO NECESSIDADE DE CAPITAL DE GIRO (NCG COM GRAVAÇÃO E FILTRO POR DATAS)
# =========================================================================
def render_modulo_ncg():
    st.header("📈 Análise de Necessidade de Capital de Giro (NCG)")
    st.markdown("Calcule a NCG, simule cenários, grave análises no banco de dados e faça comparações entre datas.")

    emp_id_ativo = st.session_state.empresa_id
    conn = get_connection()
    is_postgres = "psycopg2" in str(type(conn))

    st.subheader("1. Dados Financeiros da Empresa (Entrada)")
    c1, c2, c3 = st.columns(3)
    fat = c1.number_input("Faturamento Bruto Mensal (R$)", min_value=0.0, value=157399.10, step=1000.0)
    cmv = c2.number_input("Custo da Mercadoria Vendida - CMV (R$)", min_value=0.0, value=98409.78, step=1000.0)
    receber = c3.number_input("Contas a Receber Acumuladas (R$)", min_value=0.0, value=1193.67, step=100.0)

    c4, c5, c6 = st.columns(3)
    estoque = c4.number_input("Estoque Atual (R$)", min_value=0.0, value=18700.00, step=1000.0)
    pagar = c5.number_input("Contas a Pagar / Fornecedores (R$)", min_value=0.0, value=50971.32, step=1000.0)
    caixa = c6.number_input("Reserva Financeira / Caixa (R$)", min_value=0.0, value=0.00, step=100.0)

    st.markdown("---")
    st.subheader("2. Prazos Médios Operacionais (em dias)")
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.markdown("**Cenário Atual**")
        pme_atual = st.number_input("Prazo Médio de Estoque - PME (Dias) [Atual]", min_value=0.0, value=8.5, step=0.5)
        pmr_atual = st.number_input("Prazo Médio de Recebimento - PMR (Dias) [Atual]", min_value=0.0, value=1.0, step=0.5)
        pmp_atual = st.number_input("Prazo Médio de Pagamento - PMP (Dias) [Atual]", min_value=0.0, value=14.0, step=0.5)

    with col_p2:
        st.markdown("**Cenário Proposto (Simulação)**")
        pme_prop = st.number_input("Prazo Médio de Estoque - PME (Dias) [Proposto]", min_value=0.0, value=7.0, step=0.5)
        pmr_prop = st.number_input("Prazo Médio de Recebimento - PMR (Dias) [Proposto]", min_value=0.0, value=7.0, step=0.5)
        pmp_prop = st.number_input("Prazo Médio de Pagamento - PMP (Dias) [Proposto]", min_value=0.0, value=18.0, step=0.5)

    # 3. CÁLCULOS AUTOMÁTICOS
    margem_bruta_rs = fat - cmv
    margem_bruta_pct = (fat - cmv) / fat if fat > 0 else 0.0
    cmv_diario = cmv / 30.0
    fat_diario = fat / 30.0

    ciclo_atual = pme_atual + pmr_atual - pmp_atual
    ciclo_prop = pme_prop + pmr_prop - pmp_prop

    ncg_atual = cmv_diario * ciclo_atual
    ncg_prop = cmv_diario * ciclo_prop

    # 4. ANÁLISE DE LIQUIDEZ E RISCO
    deficit_imed = receber - pagar + caixa
    entradas_atual = fat_diario * max(0.0, pmp_atual - pmr_atual) if pmr_atual <= pmp_atual else 0.0
    entradas_prop = fat_diario * max(0.0, pmp_prop - pmr_prop) if pmr_prop <= pmp_prop else 0.0

    saldo_ciclo_atual = entradas_atual + receber - pagar + caixa
    saldo_ciclo_prop = entradas_prop + receber - pagar + caixa
    economia_ncg = ncg_atual - ncg_prop

    st.markdown("---")
    st.subheader("3. Resultados da Análise")
    df_calcs = pd.DataFrame([
        {"Indicador": "Margem Bruta (R$)", "Cenário Atual": f"R$ {margem_bruta_rs:,.2f}", "Cenário Proposto": f"R$ {margem_bruta_rs:,.2f}"},
        {"Indicador": "CICLO FINANCEIRO (dias)", "Cenário Atual": f"{ciclo_atual:.1f} dias", "Cenário Proposto": f"{ciclo_prop:.1f} dias"},
        {"Indicador": "NCG - Necessidade de Capital de Giro (R$)", "Cenário Atual": f"R$ {ncg_atual:,.2f}", "Cenário Proposto": f"R$ {ncg_prop:,.2f}"}
    ])
    st.dataframe(df_calcs, use_container_width=True, hide_index=True)

    # GRAVAÇÃO EM BANCO DE DADOS
    st.markdown("---")
    st.subheader("💾 Salvar Análise de NCG")
    col_save1, col_save2 = st.columns([3, 1])
    titulo_ncg = col_save1.text_input("Título / Referência da Análise", value=f"Análise NCG {datetime.date.today().strftime('%m/%Y')}")
    
    if col_save2.button("💾 Gravar no Banco"):
        cursor = conn.cursor()
        data_hoje = str(datetime.date.today())
        
        dados_fin_j = json.dumps({'fat': fat, 'cmv': cmv, 'receber': receber, 'estoque': estoque, 'pagar': pagar, 'caixa': caixa})
        prazos_j = json.dumps({'pme_atual': pme_atual, 'pme_prop': pme_prop, 'pmr_atual': pmr_atual, 'pmr_prop': pmr_prop, 'pmp_atual': pmp_atual, 'pmp_prop': pmp_prop})
        calcs_j = json.dumps({'ciclo_atual': ciclo_atual, 'ciclo_prop': ciclo_prop, 'ncg_atual': ncg_atual, 'ncg_prop': ncg_prop, 'economia_ncg': economia_ncg})

        emp_v = emp_id_ativo if emp_id_ativo != 0 else None
        if is_postgres:
            cursor.execute("""
                INSERT INTO ncg_registros (empresa_id, titulo, data_registro, dados_financeiros_json, prazos_json, calculos_json)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (emp_v, titulo_ncg, data_hoje, dados_fin_j, prazos_j, calcs_j))
        else:
            cursor.execute("""
                INSERT INTO ncg_registros (empresa_id, titulo, data_registro, dados_financeiros_json, prazos_json, calculos_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (emp_v, titulo_ncg, data_hoje, dados_fin_j, prazos_j, calcs_j))
        conn.commit()
        st.success("Análise de NCG gravada com sucesso no banco de dados!")
        st.rerun()

    # FILTROS ENTRE DATAS E COMPARAÇÕES FUTURAS
    st.markdown("---")
    st.subheader("🔍 Filtro por Datas & Comparação de Históricos de NCG")

    col_f1, col_f2 = st.columns(2)
    dt_inicio = col_f1.date_input("Data Inicial", value=datetime.date.today() - datetime.timedelta(days=90))
    dt_fim = col_f2.date_input("Data Final", value=datetime.date.today())

    if emp_id_ativo == 0:
        query_ncg = "SELECT id, titulo, data_registro, calculos_json FROM ncg_registros WHERE data_registro BETWEEN %s AND %s ORDER BY data_registro DESC" if is_postgres else f"SELECT id, titulo, data_registro, calculos_json FROM ncg_registros WHERE data_registro BETWEEN '{dt_inicio}' AND '{dt_fim}' ORDER BY data_registro DESC"
        df_ncg_hist = pd.read_sql_query(query_ncg, conn, params=(str(dt_inicio), str(dt_fim)) if is_postgres else None)
    else:
        query_ncg = "SELECT id, titulo, data_registro, calculos_json FROM ncg_registros WHERE (empresa_id IS NULL OR empresa_id = %s) AND data_registro BETWEEN %s AND %s ORDER BY data_registro DESC" if is_postgres else f"SELECT id, titulo, data_registro, calculos_json FROM ncg_registros WHERE (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) AND data_registro BETWEEN '{dt_inicio}' AND '{dt_fim}' ORDER BY data_registro DESC"
        df_ncg_hist = pd.read_sql_query(query_ncg, conn, params=(emp_id_ativo, str(dt_inicio), str(dt_fim)) if is_postgres else None)

    if not df_ncg_hist.empty:
        st.dataframe(df_ncg_hist[['id', 'data_registro', 'titulo']], use_container_width=True)

        st.markdown("##### 📊 Selecionar Dois Registros para Comparação Side-by-Side")
        lista_opcoes = [f"#{r['id']} - {r['titulo']} ({r['data_registro']})" for _, r in df_ncg_hist.iterrows()]
        
        c_comp1, c_comp2 = st.columns(2)
        sel_reg1 = c_comp1.selectbox("Registro 1 (Base)", lista_opcoes, index=0)
        sel_reg2 = c_comp2.selectbox("Registro 2 (Comparativo)", lista_opcoes, index=min(1, len(lista_opcoes)-1))

        if sel_reg1 and sel_reg2 and sel_reg1 != sel_reg2:
            id1 = int(sel_reg1.split(" - ")[0].replace("#", ""))
            id2 = int(sel_reg2.split(" - ")[0].replace("#", ""))

            r1 = df_ncg_hist[df_ncg_hist['id'] == id1].iloc[0]
            r2 = df_ncg_hist[df_ncg_hist['id'] == id2].iloc[0]

            c1_json = json.loads(r1['calculos_json'])
            c2_json = json.loads(r2['calculos_json'])

            df_comparativo = pd.DataFrame([
                {"Métrica": "Ciclo Financeiro Atual (dias)", f"Reg #{id1}": f"{c1_json.get('ciclo_atual',0):.1f}", f"Reg #{id2}": f"{c2_json.get('ciclo_atual',0):.1f}"},
                {"Métrica": "NCG Atual (R$)", f"Reg #{id1}": f"R$ {c1_json.get('ncg_atual',0):,.2f}", f"Reg #{id2}": f"R$ {c2_json.get('ncg_atual',0):,.2f}"},
                {"Métrica": "NCG Proposto (R$)", f"Reg #{id1}": f"R$ {c1_json.get('ncg_prop',0):,.2f}", f"Reg #{id2}": f"R$ {c2_json.get('ncg_prop',0):,.2f}"}
            ])
            st.dataframe(df_comparativo, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de NCG encontrado no período selecionado.")

    # DOWNLOAD DO RELATÓRIO PDF
    st.markdown("---")
    dados_fin_dict = {'fat': fat, 'cmv': cmv, 'receber': receber, 'estoque': estoque, 'pagar': pagar, 'caixa': caixa}
    prazos_dict = {'pme_atual': pme_atual, 'pme_prop': pme_prop, 'pmr_atual': pmr_atual, 'pmr_prop': pmr_prop, 'pmp_atual': pmp_atual, 'pmp_prop': pmp_prop}
    calcs_dict = {'margem_bruta_rs': margem_bruta_rs, 'margem_bruta_pct': margem_bruta_pct, 'cmv_diario': cmv_diario, 'fat_diario': fat_diario, 'ciclo_atual': ciclo_atual, 'ciclo_prop': ciclo_prop, 'ncg_atual': ncg_atual, 'ncg_prop': ncg_prop}

    pdf_bytes_ncg = gerar_pdf_relatorio_ncg(
        st.session_state.empresa_nome if 'empresa_nome' in st.session_state else "Açougue",
        dados_fin_dict, prazos_dict, calcs_dict, {}, {}
    )

    st.download_button(
        label="📥 Baixar Relatório Completo de Capital de Giro (NCG) em PDF",
        data=pdf_bytes_ncg,
        file_name=f"relatorio_ncg_{datetime.date.today()}.pdf",
        mime="application/pdf",
        key="btn_pdf_ncg"
    )

    conn.close()

# =========================================================================
# 7. GERENCIAMENTO DE SESSÃO E LOGIN
# =========================================================================
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""
    st.session_state.e_admin = False

init_form_states()

if not st.session_state.logado:
    exibir_cabecalho(nome_empresa_usuaria=None)
    st.title("🔒 Portal de Acesso - Gestão de Açougues")
    
    with st.form("form_login"):
        st.subheader("Login de Acesso")
        campo_login = st.text_input("Usuário / Login")
        campo_senha = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Entrar no Sistema")
        
        if btn_entrar:
            login_formatado = campo_login.strip().lower() 
            
            if login_formatado == "admin" and campo_senha == "renato123":
                st.session_state.logado = True
                st.session_state.empresa_id = 0
                st.session_state.empresa_nome = "Administrador Geral"
                st.session_state.e_admin = True
                st.success("Acesso administrativo concedido!")
                st.rerun()
            else:
                conn = get_connection()
                cursor = conn.cursor()
                is_postgres = "psycopg2" in str(type(conn))
                
                if is_postgres:
                    cursor.execute("SELECT id, nome, ativo FROM empresas WHERE LOWER(login) = %s AND senha = %s", (login_formatado, campo_senha))
                else:
                    cursor.execute("SELECT id, nome, ativo FROM empresas WHERE LOWER(login) = ? AND senha = ?", (login_formatado, campo_senha))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    empresa_id, empresa_nome, status_ativo = user
                    if status_ativo == 0:
                        st.error("🚫 O acesso da sua empresa está suspenso temporariamente.")
                    else:
                        st.session_state.logado = True
                        st.session_state.empresa_id = empresa_id
                        st.session_state.empresa_nome = empresa_nome
                        st.session_state.e_admin = False
                        st.success(f"Login realizado como: {empresa_nome}!")
                        st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

else:
    st.sidebar.markdown(f"**🏢 Empresa Usuária:**\n`{st.session_state.empresa_nome.upper()}`")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Sair do Sistema", key="btn_sair_sistema"):
        st.session_state.logado = False
        st.session_state.empresa_id = None
        st.session_state.empresa_nome = ""
        st.session_state.e_admin = False
        reset_form_states()
        st.rerun()

    menu = st.sidebar.radio("Selecione a Tela:", ["Ficha Técnica", "Capital de Giro (NCG)"], key="menu_principal")

    exibir_cabecalho(nome_empresa_usuaria=st.session_state.empresa_nome)

    if menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()
    elif menu == "Capital de Giro (NCG)":
        render_modulo_ncg()