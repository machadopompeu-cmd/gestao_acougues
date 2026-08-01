import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
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
        color: #FFFFFF !important;
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
    div[data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        padding: 12px !important;
        border-radius: 10px !important;
        border: 1px solid #3B82F6 !important;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #0F172A !important;
        border: 2px dashed #3B82F6 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stFileUploader"] small, div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] div, div[data-testid="stFileUploader"] p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    div[data-testid="stFileUploader"] button {
        background-color: #3B82F6 !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================================
# 2. CONEXÃO INTELIGENTE AO BANCO DE DADOS (SUPABASE / NUVEM OU LOCAL)
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
                rendimento_kg REAL DEFAULT 0.0,
                rendimento_assada_kg REAL DEFAULT 0.0,
                peso_unidade_kg REAL DEFAULT 0.0,
                qtd_por_pacote REAL DEFAULT 4.0,
                unidades_produzidas REAL DEFAULT 1.0,
                perda_pct REAL DEFAULT 0.0,
                data_criacao TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_ncg (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER,
                nome_simulacao TEXT,
                data_simulacao TEXT,
                fat_mensal REAL,
                cmv_mensal REAL,
                contas_receber REAL,
                estoque_atual REAL,
                contas_pagar REAL,
                reserva_financeira REAL,
                pme_atual REAL,
                pme_prop REAL,
                pmr_atual REAL,
                pmr_prop REAL,
                pmp_atual REAL,
                pmp_prop REAL,
                ncg_atual REAL,
                ncg_prop REAL,
                economia_ncg REAL
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
                rendimento_kg REAL DEFAULT 0.0,
                rendimento_assada_kg REAL DEFAULT 0.0,
                peso_unidade_kg REAL DEFAULT 0.0,
                qtd_por_pacote REAL DEFAULT 4.0,
                unidades_produzidas REAL DEFAULT 1.0,
                perda_pct REAL DEFAULT 0.0,
                data_criacao TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_ncg (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER,
                nome_simulacao TEXT,
                data_simulacao TEXT,
                fat_mensal REAL,
                cmv_mensal REAL,
                contas_receber REAL,
                estoque_atual REAL,
                contas_pagar REAL,
                reserva_financeira REAL,
                pme_atual REAL,
                pme_prop REAL,
                pmr_atual REAL,
                pmr_prop REAL,
                pmp_atual REAL,
                pmp_prop REAL,
                ncg_atual REAL,
                ncg_prop REAL,
                economia_ncg REAL
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
    
    cursor.execute("SELECT COUNT(*) FROM tipos_desossa")
    if cursor.fetchone()[0] == 0:
        tipos_iniciais = [
            ("QUARTO TRASEIRO", None), ("QUARTO DIANTEIRO", None), 
            ("VACA CASADA", None), ("BOI CASADO", None), ("SUINO", None)
        ]
        for nome_t, emp_t in tipos_iniciais:
            if is_postgres:
                cursor.execute("INSERT INTO tipos_desossa (nome, empresa_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (nome_t, emp_t))
            else:
                cursor.execute("INSERT OR IGNORE INTO tipos_desossa (nome, empresa_id) VALUES (?, ?)", (nome_t, emp_t))
    
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
# 3. CONTROLE DE ESTADOS DO FORMULÁRIO
# =========================================================================
def init_form_states():
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "cortes_temp" not in st.session_state:
        st.session_state.cortes_temp = []

def reset_form_states():
    st.session_state.form_version += 1
    st.session_state.cortes_temp = []

# =========================================================================
# 4. ELEMENTOS VISUAIS DE CABEÇALHO
# =========================================================================
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
# 5. MOTOR DE CÁLCULO DA DESOSSA (SIMULAÇÃO 21 07) & RELATÓRIO PDF
# =========================================================================
def processar_calculos_desossa(acao, df_cortes):
    peso_bruto = float(acao['peso_bruto'])
    preco_animal_kg = float(acao['preco_animal_kg'])
    custo_total_animal = peso_bruto * preco_animal_kg
    
    ossos = float(acao['ossos_muxiba'])
    quebra = float(acao['quebra_nao_identificada'])
    exsudato = float(acao['exsudato_escorrimento'])
    total_quebra = ossos + quebra + exsudato
    peso_final = max(0.0, peso_bruto - total_quebra)
    
    p_cartao = float(acao.get('p_cartao', 0.0)) / 100.0
    p_impostos = float(acao.get('p_impostos', 0.0)) / 100.0
    p_embalagens = float(acao.get('p_embalagens', 0.0)) / 100.0
    p_comissao = float(acao.get('p_comissao', 0.0)) / 100.0
    soma_percentuais_var = p_cartao + p_impostos + p_embalagens + p_comissao
    
    coef_global = peso_final / peso_bruto if peso_bruto > 0 else 0.0
    
    if df_cortes.empty:
        return pd.DataFrame(), {}

    df = df_cortes.copy()
    
    if 'peso' in df.columns:
        df['peso'] = df['peso'].astype(str).str.replace(',', '.', regex=True)
        df['peso'] = pd.to_numeric(df['peso'], errors='coerce').fillna(0.0)
    else:
        df['peso'] = 0.0
        
    col_preco_encontrada = None
    for c_p in ['preco_venda', 'preco_de_venda', 'preço_de_venda']:
        if c_p in df.columns:
            col_preco_encontrada = c_p
            break
            
    if col_preco_encontrada:
        df['preco_venda'] = df[col_preco_encontrada].astype(str).str.replace('R$', '', regex=False).str.replace(' ', '', regex=False).str.replace(',', '.', regex=True)
        df['preco_venda'] = pd.to_numeric(df['preco_venda'], errors='coerce').fillna(0.0)
    else:
        df['preco_venda'] = 0.0
        
    if 'qualidade' not in df.columns:
        df['qualidade'] = 'OURO'
    else:
        df['qualidade'] = df['qualidade'].astype(str).str.upper().str.strip()
        
    col_nome_encontrada = None
    for c_n in ['nome_corte', 'nom_corte']:
        if c_n in df.columns:
            col_nome_encontrada = c_n
            break
            
    if col_nome_encontrada:
        df['nome_corte'] = df[col_nome_encontrada].astype(str).str.upper().str.strip()
    else:
        df['nome_corte'] = 'CORTE'
    
    peso_ouro = df[df['qualidade'] == 'OURO']['peso'].sum()
    peso_prata = df[df['qualidade'] == 'PRATA']['peso'].sum()
    
    val_venda_ouro = (df[df['qualidade'] == 'OURO']['peso'] * df[df['qualidade'] == 'OURO']['preco_venda']).sum()
    val_venda_prata = (df[df['qualidade'] == 'PRATA']['peso'] * df[df['qualidade'] == 'PRATA']['preco_venda']).sum()
    total_vendas_geral = val_venda_ouro + val_venda_prata
    
    custo_total_efetivo = custo_total_animal / (1.0 - soma_percentuais_var) if (1.0 - soma_percentuais_var) > 0 else custo_total_animal
    
    custo_ouro = custo_total_efetivo * 0.56 if total_vendas_geral == 0 else custo_total_efetivo * (val_venda_ouro / total_vendas_geral)
    custo_prata = custo_total_efetivo * 0.44 if total_vendas_geral == 0 else custo_total_efetivo * (val_venda_prata / total_vendas_geral)
    
    precos_custo_kg = []
    precos_custo_total = []
    valor_vendas = []
    lucro_bruto = []
    perc_cortes = []
    t_cartao_val = []
    t_imp_val = []
    t_emb_val = []
    t_com_val = []
    custo_efetivo_kg_list = []
    custo_efetivo_tot_list = []
    
    for _, row in df.iterrows():
        p = row['peso']
        pv = row['preco_venda']
        qual = str(row['qualidade']).upper()
        
        vv = p * pv
        valor_vendas.append(vv)
        
        pc_tot = (custo_ouro * (p / peso_ouro)) if (qual == 'OURO' and peso_ouro > 0) else ((custo_prata * (p / peso_prata)) if (qual == 'PRATA' and peso_prata > 0) else 0.0)
        pc_kg = pc_tot / p if p > 0 else 0.0
        precos_custo_kg.append(pc_kg)
        precos_custo_total.append(pc_tot)
        
        lb = vv - pc_tot
        lucro_bruto.append(lb)
        
        pcort = (vv / total_vendas_geral) if total_vendas_geral > 0 else 0.0
        perc_cortes.append(pcort)
        
        t_cartao_val.append(vv * p_cartao)
        t_imp_val.append(vv * p_impostos)
        t_emb_val.append(vv * p_embalagens)
        t_com_val.append(vv * p_comissao)
        
        ce_tot = pc_tot / (1.0 - soma_percentuais_var) if (1.0 - soma_percentuais_var) > 0 else pc_tot
        ce_kg = ce_tot / p if p > 0 else 0.0
        custo_efetivo_kg_list.append(ce_kg)
        custo_efetivo_tot_list.append(ce_tot)

    df['PREÇO CUSTO/KG'] = precos_custo_kg
    df['PREÇO/CUSTO'] = precos_custo_total
    df['PREÇO VENDA/KG'] = df['preco_venda']
    df['VALOR TOTAL DE VENDAS'] = valor_vendas
    df['LUCRO BRUTO'] = lucro_bruto
    df['PERCENTUAL/CORTES'] = perc_cortes
    df['TAXAS DE CARTÃO'] = t_cartao_val
    df['IMPOSTOS'] = t_imp_val
    df['EMBALAGENS'] = t_emb_val
    df['COMISSÃO'] = t_com_val
    df['CUSTO EFETIVO/KG'] = custo_efetivo_kg_list
    df['CUSTO EFETIVO TOTAL'] = custo_efetivo_tot_list
    
    total_peso_cortes = df['peso'].sum()
    margem_contrib_rs = total_vendas_geral - custo_total_efetivo
    margem_contrib_pct = (margem_contrib_rs / total_vendas_geral) if total_vendas_geral > 0 else 0.0
    markup = (total_vendas_geral / custo_total_efetivo - 1.0) if custo_total_efetivo > 0 else 0.0
    
    preco_medio_compra_sem = custo_total_animal / total_peso_cortes if total_peso_cortes > 0 else 0.0
    preco_medio_compra_com = custo_total_efetivo / total_peso_cortes if total_peso_cortes > 0 else 0.0
    preco_medio_venda = total_vendas_geral / total_peso_cortes if total_peso_cortes > 0 else 0.0

    margem_contrib_ouro_rs = val_venda_ouro - custo_ouro
    margem_contrib_prata_rs = val_venda_prata - custo_prata

    preco_medio_compra_ouro = custo_ouro / peso_ouro if peso_ouro > 0 else 0.0
    preco_medio_compra_prata = custo_prata / peso_prata if peso_prata > 0 else 0.0

    preco_medio_venda_ouro = val_venda_ouro / peso_ouro if peso_ouro > 0 else 0.0
    preco_medio_venda_prata = val_venda_prata / peso_prata if peso_prata > 0 else 0.0

    indicadores = {
        "peso_bruto": peso_bruto,
        "ossos": ossos,
        "quebra": quebra,
        "exsudato": exsudato,
        "peso_final": peso_final,
        
        "ouro_preco_compra": custo_ouro,
        "prata_preco_compra": custo_prata,
        "total_preco_compra": custo_total_efetivo,
        
        "ouro_preco_venda": val_venda_ouro,
        "prata_preco_venda": val_venda_prata,
        "total_preco_venda": total_vendas_geral,
        
        "ouro_peso": peso_ouro,
        "prata_peso": peso_prata,
        "total_peso": total_peso_cortes,
        
        "ouro_coef": coef_global,
        "prata_coef": coef_global,
        "total_coef": coef_global,
        
        "ouro_custo_efetivo": custo_ouro,
        "prata_custo_efetivo": custo_prata,
        "total_custo_efetivo": custo_total_efetivo,
        
        "ouro_margem_rs": margem_contrib_ouro_rs,
        "prata_margem_rs": margem_contrib_prata_rs,
        "total_margem_rs": margem_contrib_rs,
        
        "ouro_margem_pct": margem_contrib_pct,
        "prata_margem_pct": margem_contrib_pct,
        "total_margem_pct": margem_contrib_pct,
        
        "ouro_markup": markup,
        "prata_markup": markup,
        "total_markup": markup,
        
        "ouro_pm_compra": preco_medio_compra_ouro,
        "prata_pm_compra": preco_medio_compra_prata,
        "total_pm_compra": preco_medio_compra_sem,
        
        "ouro_pm_venda": preco_medio_venda_ouro,
        "prata_pm_venda": preco_medio_venda_prata,
        "total_pm_venda": preco_medio_venda
    }

    return df, indicadores

def gerar_pdf_relatorio_desossa(acao, df_res, ind, nome_empresa):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(10, 8, 277, 12, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", style="B", size=10)
    pdf.set_xy(10, 10)
    pdf.cell(277, 8, f"RENATO FRIGOTUDO & ASSOCIADOS - SIMULAÇÃO DE APURACAO DE DESOSSA", ln=1, align="C")
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Arial", style="B", size=8.5)
    pdf.set_xy(10, 22)
    pdf.cell(277, 5, f"Empresa: {nome_empresa.upper()} | Data: {acao['data_acao']} | Tipo: {acao['tipo_animal']}", ln=1, align="C")
    pdf.ln(2)

    pdf.set_font("Arial", style="B", size=8)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(90, 5, "APURAÇÃO DOS PARÂMETROS DO ANIMAL", 1, 0, 'C', True)
    pdf.cell(5, 5, "", 0, 0)
    pdf.cell(182, 5, "INDICADORES DA SIMULAÇÃO (OURO / PRATA / TOTAL)", 1, 1, 'C', True)

    pdf.set_font("Arial", size=7.5)
    ap_linhas = [
        ("PESO BRUTO/KG", f"{ind['peso_bruto']:.3f}"),
        ("OSSOS/MUXIBA", f"{ind['ossos']:.3f}"),
        ("QUEBRA NÃO IDENTIF.", f"{ind['quebra']:.3f}"),
        ("ESCORRIMENTO", f"{ind['exsudato']:.3f}"),
        ("Peso Final", f"{ind['peso_final']:.3f}"),
        ("TOTAL DE QUEBRA", f"{(ind['ossos']+ind['quebra']+ind['exsudato']):.3f}")
    ]

    ind_tabela = [
        ("PREÇO TOTAL/Compra Sem Custos", f"R$ {ind['ouro_preco_compra']:,.2f}", f"R$ {ind['prata_preco_compra']:,.2f}", f"R$ {ind['total_preco_compra']:,.2f}"),
        ("PREÇO TOTAL/Venda", f"R$ {ind['ouro_preco_venda']:,.2f}", f"R$ {ind['prata_preco_venda']:,.2f}", f"R$ {ind['total_preco_venda']:,.2f}"),
        ("Peso Desossado", f"{ind['ouro_peso']:.3f}", f"{ind['prata_peso']:.3f}", f"{ind['total_peso']:.3f}"),
        ("COEFICIENTE", f"{ind['ouro_coef']:.5f}", f"{ind['prata_coef']:.5f}", f"{ind['total_coef']:.5f}"),
        ("Custo Efetivo Total", f"R$ {ind['ouro_custo_efetivo']:,.2f}", f"R$ {ind['prata_custo_efetivo']:,.2f}", f"R$ {ind['total_custo_efetivo']:,.2f}"),
        ("Margem de Contribuição R$", f"R$ {ind['ouro_margem_rs']:,.2f}", f"R$ {ind['prata_margem_rs']:,.2f}", f"R$ {ind['total_margem_rs']:,.2f}"),
        ("Margem de Contribuição %", f"{ind['ouro_margem_pct']*100:.2f}%", f"{ind['prata_margem_pct']*100:.2f}%", f"{ind['total_margem_pct']*100:.2f}%"),
        ("Markup", f"{ind['ouro_markup']*100:.2f}%", f"{ind['prata_markup']*100:.2f}%", f"{ind['total_markup']*100:.2f}%"),
        ("Preço médio Compra/KG", f"R$ {ind['ouro_pm_compra']:.2f}", f"R$ {ind['prata_pm_compra']:.2f}", f"R$ {ind['total_pm_compra']:.2f}"),
        ("Preço médio Venda/KG", f"R$ {ind['ouro_pm_venda']:.2f}", f"R$ {ind['prata_pm_venda']:.2f}", f"R$ {ind['total_pm_venda']:.2f}")
    ]

    max_linhas = max(len(ap_linhas), len(ind_tabela))
    for idx in range(max_linhas):
        if idx < len(ap_linhas):
            pdf.cell(50, 4.5, ap_linhas[idx][0], 1, 0, 'L')
            pdf.cell(40, 4.5, ap_linhas[idx][1], 1, 0, 'R')
        else:
            pdf.cell(90, 4.5, "", 1, 0)
            
        pdf.cell(5, 4.5, "", 0, 0)
        
        if idx < len(ind_tabela):
            pdf.cell(74, 4.5, ind_tabela[idx][0], 1, 0, 'L')
            pdf.cell(36, 4.5, ind_tabela[idx][1], 1, 0, 'R')
            pdf.cell(36, 4.5, ind_tabela[idx][2], 1, 0, 'R')
            pdf.cell(36, 4.5, ind_tabela[idx][3], 1, 1, 'R')
        else:
            pdf.cell(182, 4.5, "", 1, 1)

    pdf.ln(3)

    pdf.set_font("Arial", style="B", size=7.5)
    cols = ['nome_corte', 'qualidade', 'peso', 'PREÇO CUSTO/KG', 'PREÇO/CUSTO', 'PREÇO VENDA/KG', 'VALOR TOTAL DE VENDAS', 'LUCRO BRUTO', 'PERCENTUAL/CORTES', 'CUSTO EFETIVO TOTAL']
    larguras = [35, 18, 18, 22, 22, 22, 28, 24, 22, 38]
    
    for i, col_name in enumerate(cols):
        pdf.cell(larguras[i], 6, col_name.replace("_", " ").upper(), 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", size=7)
    for _, r in df_res.iterrows():
        pdf.cell(larguras[0], 5, str(r['nome_corte']), 1, 0, 'L')
        pdf.cell(larguras[1], 5, str(r['qualidade']), 1, 0, 'C')
        pdf.cell(larguras[2], 5, f"{r['peso']:.3f}", 1, 0, 'R')
        pdf.cell(larguras[3], 5, f"{r['PREÇO CUSTO/KG']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[4], 5, f"{r['PREÇO/CUSTO']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[5], 5, f"{r['PREÇO VENDA/KG']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[6], 5, f"{r['VALOR TOTAL DE VENDAS']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[7], 5, f"{r['LUCRO BRUTO']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[8], 5, f"{r['PERCENTUAL/CORTES']*100:.1f}%", 1, 0, 'R')
        pdf.cell(larguras[9], 5, f"{r['CUSTO EFETIVO TOTAL']:.2f}", 1, 1, 'R')
        
    return pdf.output(dest='S').encode('latin1')

# =========================================================================
# 6. MÓDULOS DE SUPORTE (FINANCEIRO, FICHA TÉCNICA E NCG)
# =========================================================================
def render_modulo_financeiro():
    st.header("🧮 Módulo de Cálculo Financeiro & Amortização")
    col1, col2, col3 = st.columns(3)
    with col1:
        pv = st.number_input("Valor Financiado / Empréstimo (R$)", min_value=0.0, value=100000.0, step=1000.0)
    with col2:
        i = st.number_input("Taxa de Juros Mensal (%)", min_value=0.0, value=1.5, step=0.1) / 100.0
    with col3:
        n = st.number_input("Prazo (Meses)", min_value=1, value=12, step=1)

    sistema = st.radio("Sistema de Amortização", ["Tabela Price (Prestações Iguais)", "Tabela SAC (Amortização Constante)"], horizontal=True)

    if st.button("Gerar Tabela de Amortização"):
        dados = []
        saldo_devedor = pv
        if "Price" in sistema:
            pmt = pv * (i * (1 + i)**n) / ((1 + i)**n - 1) if i > 0 else pv / n
            for mes in range(1, n + 1):
                juros = saldo_devedor * i
                amortizacao = pmt - juros
                saldo_devedor -= amortizacao
                dados.append({"Mês": mes, "Prestação": pmt, "Juros": juros, "Amortização": amortizacao, "Saldo Devedor": max(0.0, saldo_devedor)})
        else:
            amortizacao = pv / n
            for mes in range(1, n + 1):
                juros = saldo_devedor * i
                pmt = amortizacao + juros
                saldo_devedor -= amortizacao
                dados.append({"Mês": mes, "Prestação": pmt, "Juros": juros, "Amortização": amortizacao, "Saldo Devedor": max(0.0, saldo_devedor)})

        df_Amort = pd.DataFrame(dados)
        st.dataframe(df_Amort.style.format({
            "Prestação": "R$ {:.2f}", "Juros": "R$ {:.2f}", "Amortização": "R$ {:.2f}", "Saldo Devedor": "R$ {:.2f}"
        }), use_container_width=True)

def render_modulo_ficha_tecnica():
    st.header("📋 Módulo de Ficha Técnica & Precificação")
    emp_id_ativo = st.session_state.empresa_id
    
    with st.form("form_nova_ficha"):
        produto_nome = st.text_input("Nome do Produto Preparado / Embutido")
        rendimento_kg = st.number_input("Rendimento Total Produzido (KG)", min_value=0.0, value=10.0, step=0.1)
        peso_unid = st.number_input("Peso por Unidade / Porção (KG)", min_value=0.0, value=0.5, step=0.05)
        
        if st.form_submit_button("Salvar Ficha Técnica") and produto_nome:
            conn = get_connection()
            cursor = conn.cursor()
            is_postgres = "psycopg2" in str(type(conn))
            data_hoje = str(datetime.date.today())
            if is_postgres:
                cursor.execute("INSERT INTO fichas_tecnicas (empresa_id, produto, rendimento_kg, peso_unidade_kg, data_criacao) VALUES (%s, %s, %s, %s, %s)", (emp_id_ativo, produto_nome, rendimento_kg, peso_unid, data_hoje))
            else:
                cursor.execute("INSERT INTO fichas_tecnicas (empresa_id, produto, rendimento_kg, peso_unidade_kg, data_criacao) VALUES (?, ?, ?, ?, ?)", (emp_id_ativo, produto_nome, rendimento_kg, peso_unid, data_hoje))
            conn.commit()
            conn.close()
            st.success(f"Ficha técnica para '{produto_nome}' salva com sucesso!")
            st.rerun()

    conn = get_connection()
    is_postgres = "psycopg2" in str(type(conn))
    if is_postgres:
        df_fichas = pd.read_sql_query("SELECT * FROM fichas_tecnicas WHERE empresa_id = %s OR empresa_id IS NULL ORDER BY id DESC", conn, params=(emp_id_ativo,))
    else:
        df_fichas = pd.read_sql_query("SELECT * FROM fichas_tecnicas WHERE empresa_id = ? OR empresa_id IS NULL ORDER BY id DESC", conn, params=(emp_id_ativo,))
    conn.close()
    
    if not df_fichas.empty:
        st.subheader("Fichas Cadastradas")
        st.dataframe(df_fichas, use_container_width=True)

def render_modulo_ncg():
    st.header("📈 Análise de Necessidade de Capital de Giro (NCG)")
    col1, col2 = st.columns(2)
    with col1:
        fat = st.number_input("Faturamento Mensal (R$)", min_value=0.0, value=100000.0, step=5000.0)
        cmv = st.number_input("CMV Mensal (R$)", min_value=0.0, value=70000.0, step=5000.0)
        pmr = st.number_input("Prazo Médio de Recebimento - PMR (Dias)", min_value=0.0, value=30.0, step=1.0)
    with col2:
        pme = st.number_input("Prazo Médio de Estoque - PME (Dias)", min_value=0.0, value=20.0, step=1.0)
        pmp = st.number_input("Prazo Médio de Pagamento - PMP (Dias)", min_value=0.0, value=30.0, step=1.0)

    if st.button("Calcular Necessidade de Capital de Giro"):
        ac = (fat / 30.0) * pmr + (cmv / 30.0) * pme
        pc = (cmv / 30.0) * pmp
        ncg = ac - pc
        st.metric("Necessidade de Capital de Giro (NCG Calculada)", f"R$ {ncg:,.2f}")
        st.info(f"Ativo Cíclico: R$ {ac:,.2f} | Passivo Cíclico: R$ {pc:,.2f}")

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
    st.sidebar.markdown("### ☁️ Banco de Dados em Nuvem")
    st.sidebar.success("🟢 Conectado ao Supabase (Dados seguros e persistentes).")
                
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Sair do Sistema", key="btn_sair_sistema"):
        st.session_state.logado = False
        st.session_state.empresa_id = None
        st.session_state.empresa_nome = ""
        st.session_state.e_admin = False
        reset_form_states()
        st.rerun()

    if st.session_state.e_admin:
        st.sidebar.markdown("### 🛠️ Menu Administrativo")
        menu = st.sidebar.radio("Selecione a Tela:", ["Gerenciar Empresas", "Cadastrar Empresa", "Gerenciar Cadastro de Cortes", "Importar Cortes (CSV)", "Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"], key="menu_admin")
    else:
        st.sidebar.markdown("### 🥩 Menu de Operações")
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Gerenciar Cadastro de Cortes", "Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"], key="menu_operacional")

    exibir_cabecalho(nome_empresa_usuaria=st.session_state.empresa_nome)

    # =========================================================================
    # 8. EXECUÇÃO DOS MÓDULOS DE TELA
    # =========================================================================
    if menu == "Cálculo Financeiro":
        render_modulo_financeiro()
    elif menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()
    elif menu == "Capital de Giro (NCG)":
        render_modulo_ncg()
    elif menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Configurar e Gerenciar Tipos de Desossa e Cortes Padrão")
        emp_id_ativo = st.session_state.empresa_id
        tipos_disponiveis = get_tipos_desossa(emp_id_ativo)
        
        if tipos_disponiveis:
            tipo_sel = st.selectbox("Selecione o Tipo de Desossa", tipos_disponiveis, key="tipo_sel_config_cortes")
            
            with st.form("form_adicionar_corte_padrao"):
                st.subheader(f"Adicionar Novo Corte Padrão para: {tipo_sel}")
                novo_corte_nome = st.text_input("Nome do Corte Padrão")
                if st.form_submit_button("Cadastrar Corte Padrão") and novo_corte_nome:
                    conn = get_connection()
                    cursor = conn.cursor()
                    is_postgres = "psycopg2" in str(type(conn))
                    try:
                        if is_postgres:
                            cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (%s, %s, %s)", (tipo_sel, novo_corte_nome.upper().strip(), emp_id_ativo if emp_id_ativo != 0 else None))
                        else:
                            cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (tipo_sel, novo_corte_nome.upper().strip(), emp_id_ativo if emp_id_ativo != 0 else None))
                        conn.commit()
                        st.success(f"Corte '{novo_corte_nome.upper()}' cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar corte (pode já existir): {e}")
                    conn.close()
                    st.rerun()

            conn = get_connection()
            is_postgres = "psycopg2" in str(type(conn))
            if is_postgres:
                df_padroes = pd.read_sql_query("SELECT id, tipo_desossa, nome_corte FROM cortes_padrao WHERE tipo_desossa = %s AND (empresa_id = %s OR empresa_id IS NULL) ORDER BY nome_corte ASC", conn, params=(tipo_sel, emp_id_ativo))
            else:
                df_padroes = pd.read_sql_query(f"SELECT id, tipo_desossa, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND (empresa_id = {emp_id_ativo} OR empresa_id IS NULL) ORDER BY nome_corte ASC", conn)
            conn.close()

            st.subheader(f"Cortes Cadastrados para '{tipo_sel}'")
            if not df_padroes.empty:
                for _, cp in df_padroes.iterrows():
                    c_id = cp['id']
                    c_nome = cp['nome_corte']
                    col_n, col_d = st.columns([5, 1])
                    col_n.write(f"• **{c_nome}**")
                    if col_d.button("🗑️ Excluir", key=f"del_cp_{c_id}"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        if is_postgres:
                            cursor.execute("DELETE FROM cortes_padrao WHERE id = %s", (c_id,))
                        else:
                            cursor.execute("DELETE FROM cortes_padrao WHERE id = ?", (c_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Corte '{c_nome}' removido!")
                        st.rerun()
            else:
                st.info("Nenhum corte padrão cadastrado para este tipo de desossa.")
    else:
        emp_id_ativo = st.session_state.empresa_id
        v_form = st.session_state.form_version
        
        if menu == "Nova Desossa":
            st.header("📋 Lançar Nova Ação de Desossa")
            tipos_empresa = get_tipos_desossa(emp_id_ativo)
            
            if not tipos_empresa:
                st.warning("Cadastre os seus 'Tipos de Desossa' no menu correspondente primeiro.")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    data_input = st.date_input("Data da Ação", datetime.date.today(), key=f"date_picker_{v_form}")
                    tipo_animal = st.selectbox("Tipo de Desossa", tipos_empresa, key=f"tipo_animal_select_{v_form}")
                    peso_bruto = st.number_input("Peso Bruto (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_peso_bruto_{v_form}")
                    preco_animal_kg = st.number_input("Preço do Animal (R$/KG)", min_value=0.0, step=0.01, key=f"input_preco_animal_{v_form}")
                with col2:
                    ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_ossos_{v_form}")
                    quebra_nao_identificada = st.number_input("Quebra Não Identificada (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_quebra_{v_form}")
                    exsudato_escorrimento = st.number_input("Exsudato / Escorrimento (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_exsudato_{v_form}")
                with col3:
                    p_cartao = st.number_input("Taxas de Cartão (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_cartao_{v_form}")
                    p_impostos = st.number_input("Impostos (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_impostos_{v_form}")
                    p_embalagens = st.number_input("Embalagens (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_embalagens_{v_form}")
                    p_comissao = st.number_input("Comissão (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_comissao_{v_form}")

                st.markdown("---")
                st.markdown("#### 📥 Opção de Adicionar Cortes: Manualmente ou por Upload de Ficheiro (CSV / XLSX)")
                
                uploaded_cortes_file = st.file_uploader("Carregar Ficheiro de Cortes (CSV ou XLSX)", type=["csv", "xlsx"], key=f"uploader_cortes_lote_{v_form}")
                if uploaded_cortes_file is not None:
                    try:
                        if uploaded_cortes_file.name.endswith('.csv'):
                            df_up = pd.read_csv(uploaded_cortes_file, encoding='latin-1', sep=None, engine='python')
                        else:
                            df_up = pd.read_excel(uploaded_cortes_file)
                        
                        col_map = {c: str(c).strip().lower().replace(" ", "_") for c in df_up.columns}
                        df_up.rename(columns=col_map, inplace=True)
                        
                        if 'nom_corte' in df_up.columns and 'nome_corte' not in df_up.columns:
                            df_up.rename(columns={'nom_corte': 'nome_corte'}, inplace=True)
                        
                        col_preco_encontrada = None
                        for cp_cand in ['preco_venda', 'preco_de_venda', 'preço_de_venda']:
                            if cp_cand in df_up.columns:
                                col_preco_encontrada = cp_cand
                                break
                        
                        if col_preco_encontrada and col_preco_encontrada != 'preco_venda':
                            df_up.rename(columns={col_preco_encontrada: 'preco_venda'}, inplace=True)
                        
                        colunas_necessarias = ['nome_corte', 'qualidade', 'peso', 'preco_venda']
                        if all(k in df_up.columns for k in colunas_necessarias):
                            if st.button("⚡ Importar Cortes do Ficheiro para o Lote", key=f"btn_import_file_{v_form}"):
                                st.session_state.cortes_temp = []
                                for _, r in df_up.iterrows():
                                    p_str = str(r['peso']).replace(',', '.')
                                    pv_str = str(r['preco_venda']).replace('R$', '').replace(' ', '').replace(',', '.')
                                    
                                    try:
                                        p_val = float(p_str)
                                    except:
                                        p_val = 0.0
                                        
                                    try:
                                        pv_val = float(pv_str)
                                    except:
                                        pv_val = 0.0
                                        
                                    st.session_state.cortes_temp.append({
                                        "nome_corte": str(r['nome_corte']).upper().strip(),
                                        "qualidade": str(r['qualidade']).upper().strip(),
                                        "peso": p_val,
                                        "preco_venda": pv_val
                                    })
                                st.success("🎉 Cortes importados com sucesso do ficheiro!")
                                st.rerun()
                        else:
                            st.error(f"❌ O ficheiro enviado não contém as colunas exigidas. Colunas detetadas: {list(df_up.columns)}")
                    except Exception as e_up:
                        st.error(f"Erro ao ler o ficheiro: {e_up}")

                conn = get_connection()
                is_postgres = "psycopg2" in str(type(conn))
                if is_postgres:
                    df_rec_cortes = pd.read_sql_query("SELECT nome_corte FROM cortes_padrao WHERE tipo_desossa = %s AND (empresa_id IS NULL OR empresa_id = %s) ORDER BY nome_corte ASC", conn, params=(tipo_animal, emp_id_ativo))
                else:
                    df_rec_cortes = pd.read_sql_query(f"SELECT nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_animal}' AND (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) ORDER BY nome_corte ASC", conn)
                conn.close()
                
                lista_cortes_disponiveis = df_rec_cortes["nome_corte"].tolist() if not df_rec_cortes.empty else []
                
                with st.form(f"adicionar_corte_{v_form}"):
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    if lista_cortes_disponiveis:
                        nome_corte = col_c1.selectbox("Corte Cadastrado", lista_cortes_disponiveis, key=f"sel_corte_cad_{v_form}")
                    else:
                        nome_corte = col_c1.text_input("Nome do Corte Manual", key=f"input_corte_nome_manual_{v_form}")
                        
                    qualidade = col_c2.selectbox("Qualidade", ["OURO", "PRATA"], key=f"sel_qual_corte_{v_form}")
                    peso_corte = col_c3.number_input("Peso do Corte (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_corte_peso_{v_form}")
                    preco_venda = col_c4.number_input("Preço de Venda (R$/KG)", min_value=0.0, step=0.01, key=f"input_corte_preco_{v_form}")
                    
                    if st.form_submit_button("➕ Adicionar Corte Manual") and nome_corte != "":
                        st.session_state.cortes_temp.append({
                            "nome_corte": nome_corte.upper(),
                            "qualidade": qualidade,
                            "peso": peso_corte,
                            "preco_venda": preco_venda
                        })
                        st.success("Corte adicionado!")
                        st.rerun()

                if st.session_state.cortes_temp:
                    st.markdown("##### 📋 Cortes Adicionados ao Lote:")
                    for idx, c in enumerate(st.session_state.cortes_temp):
                        col_info_txt, col_del_btn = st.columns([5, 1])
                        col_info_txt.write(f"• **{c['nome_corte']}** ({c['qualidade']}) - {c['peso']:.3f} KG - R$ {c['preco_venda']:.2f}/KG")
                        if col_del_btn.button("🗑️ Remover", key=f"del_temp_{idx}"):
                            st.session_state.cortes_temp.pop(idx)
                            st.rerun()

                if st.button("💾 Salvar Ação Completa no Banco de Dados", key=f"btn_salvar_db_{v_form}"):
                    if not st.session_state.cortes_temp:
                        st.error("Adicione pelo menos um corte!")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        is_postgres = "psycopg2" in str(type(conn))
                        
                        if is_postgres:
                            cursor.execute("""
                                INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                            """, (emp_id_ativo, str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao))
                            acao_id = cursor.fetchone()[0]
                        else:
                            cursor.execute("""
                                INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (emp_id_ativo, str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao))
                            acao_id = cursor.lastrowid
                        
                        for c in st.session_state.cortes_temp:
                            if is_postgres:
                                cursor.execute("INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda) VALUES (%s, %s, %s, %s, %s)", (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                            else:
                                cursor.execute("INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda) VALUES (?, ?, ?, ?, ?)", (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                        
                        conn.commit()
                        conn.close()
                        st.success("🎉 Desossa salva com sucesso!")
                        reset_form_states()
                        st.rerun()

        elif menu == "Histórico & Edição":
            st.header("📂 Histórico, Filtro por Datas & Gestão de Desossas")
            conn = get_connection()
            is_postgres = "psycopg2" in str(type(conn))
            
            col_f1, col_f2 = st.columns(2)
            data_inicio_filtro = col_f1.date_input("Data Início", datetime.date.today() - datetime.timedelta(days=30))
            data_fim_filtro = col_f2.date_input("Data Fim", datetime.date.today())
            
            if is_postgres:
                df_acoes = pd.read_sql_query("SELECT * FROM acoes WHERE empresa_id = %s AND data_acao BETWEEN %s AND %s ORDER BY data_acao DESC", conn, params=(emp_id_ativo, str(data_inicio_filtro), str(data_fim_filtro)))
            else:
                df_acoes = pd.read_sql_query(f"SELECT * FROM acoes WHERE empresa_id = {emp_id_ativo} AND data_acao BETWEEN '{data_inicio_filtro}' AND '{data_fim_filtro}' ORDER BY data_acao DESC", conn)
            
            if df_acoes.empty:
                st.warning("Nenhuma desossa encontrada no intervalo de datas selecionado.")
                conn.close()
            else:
                for _, acao in df_acoes.iterrows():
                    acao_id = acao['id']
                    with st.expander(f"🥩 Lote #{acao_id} - Data: {acao['data_acao']} | Tipo: {acao['tipo_animal']} | Peso Bruto: {acao['peso_bruto']} KG"):
                        if is_postgres:
                            df_c = pd.read_sql_query("SELECT * FROM cortes WHERE acao_id = %s", conn, params=(acao_id,))
                        else:
                            df_c = pd.read_sql_query(f"SELECT * FROM cortes WHERE acao_id = {acao_id}", conn)
                        
                        df_res, ind = processar_calculos_desossa(acao, df_c)
                        
                        if not df_res.empty:
                            st.markdown("##### 🐂 Apuração dos Parâmetros & Indicadores da Simulação (Aba Simulação 21 07)")
                            
                            col_p, col_i = st.columns([1, 2])
                            with col_p:
                                st.markdown("**Apuração Bovina**")
                                df_apuracao = pd.DataFrame({
                                    "Parâmetro": ["PESO BRUTO/KG", "OSSOS/MUXIBA", "QUEBRA NÃO IDENTIF.", "ESCORRIMENTO", "Peso Final", "TOTAL DE QUEBRA"],
                                    "Valor": [f"{ind['peso_bruto']:.3f}", f"{ind['ossos']:.3f}", f"{ind['quebra']:.3f}", f"{ind['exsudato']:.3f}", f"{ind['peso_final']:.3f}", f"{(ind['ossos']+ind['quebra']+ind['exsudato']):.3f}"]
                                })
                                st.dataframe(df_apuracao, use_container_width=True, hide_index=True)

                            with col_i:
                                st.markdown("**INDICADORES (Classificação das Carnes)**")
                                df_ind_tab = pd.DataFrame({
                                    "INDICADORES": [
                                        "PREÇO TOTAL/Compra Sem Custos", "PREÇO TOTAL/Venda", "Peso Desossado", 
                                        "COEFICIENTE", "Custo Efetivo Total", "Margem de Contribuição R$", 
                                        "Margem de Contribuição %", "Markup", "Preço médio Compra/KG", "Preço médio Venda/KG"
                                    ],
                                    "OURO": [
                                        f"R$ {ind['ouro_preco_compra']:,.2f}", f"R$ {ind['ouro_preco_venda']:,.2f}", f"{ind['ouro_peso']:.3f}",
                                        f"{ind['ouro_coef']:.5f}", f"R$ {ind['ouro_custo_efetivo']:,.2f}", f"R$ {ind['ouro_margem_rs']:,.2f}",
                                        f"{ind['ouro_margem_pct']*100:.2f}%", f"{ind['ouro_markup']*100:.2f}%", f"R$ {ind['ouro_pm_compra']:.2f}", f"R$ {ind['ouro_pm_venda']:.2f}"
                                    ],
                                    "PRATA": [
                                        f"R$ {ind['prata_preco_compra']:,.2f}", f"R$ {ind['prata_preco_venda']:,.2f}", f"{ind['prata_peso']:.3f}",
                                        f"{ind['prata_coef']:.5f}", f"R$ {ind['prata_custo_efetivo']:,.2f}", f"R$ {ind['prata_margem_rs']:,.2f}",
                                        f"{ind['prata_margem_pct']*100:.2f}%", f"{ind['prata_markup']*100:.2f}%", f"R$ {ind['prata_pm_compra']:.2f}", f"R$ {ind['prata_pm_venda']:.2f}"
                                    ],
                                    "Total": [
                                        f"R$ {ind['total_preco_compra']:,.2f}", f"R$ {ind['total_preco_venda']:,.2f}", f"{ind['total_peso']:.3f}",
                                        f"{ind['total_coef']:.5f}", f"R$ {ind['total_custo_efetivo']:,.2f}", f"R$ {ind['total_margem_rs']:,.2f}",
                                        f"{ind['total_margem_pct']*100:.2f}%", f"{ind['total_markup']*100:.2f}%", f"R$ {ind['total_pm_compra']:.2f}", f"R$ {ind['total_pm_venda']:.2f}"
                                    ]
                                })
                                st.dataframe(df_ind_tab, use_container_width=True, hide_index=True)

                            st.markdown("##### 🥩 Cortes Apurados")
                            st.dataframe(df_res.style.format({
                                "peso": "{:.3f} KG",
                                "PREÇO CUSTO/KG": "R$ {:.2f}",
                                "PREÇO/CUSTO": "R$ {:.2f}",
                                "PREÇO VENDA/KG": "R$ {:.2f}",
                                "VALOR TOTAL DE VENDAS": "R$ {:.2f}",
                                "LUCRO BRUTO": "R$ {:.2f}",
                                "PERCENTUAL/CORTES": "{:.2%}",
                                "CUSTO EFETIVO TOTAL": "R$ {:.2f}"
                            }), use_container_width=True)
                            
                            pdf_bytes = gerar_pdf_relatorio_desossa(acao, df_res, ind, st.session_state.empresa_nome if 'empresa_nome' in st.session_state else "Açougue")
                            st.download_button(
                                label="📥 Baixar Relatório Completo em PDF (Replica aba Simulação 21 07)",
                                data=pdf_bytes,
                                file_name=f"desossa_lote_{acao_id}_{acao['data_acao']}.pdf",
                                mime="application/pdf",
                                key=f"pdf_lote_{acao_id}"
                            )
                        
                        col_acao1, col_acao2 = st.columns(2)
                        if col_acao1.button(f"🗑️ Excluir Lote Inteiro #{acao_id}", key=f"del_lote_{acao_id}"):
                            cursor = conn.cursor()
                            if is_postgres:
                                cursor.execute("DELETE FROM cortes WHERE acao_id = %s", (acao_id,))
                                cursor.execute("DELETE FROM acoes WHERE id = %s", (acao_id,))
                            else:
                                cursor.execute("DELETE FROM cortes WHERE acao_id = ?", (acao_id,))
                                cursor.execute("DELETE FROM acoes WHERE id = ?", (acao_id,))
                            conn.commit()
                            st.success(f"Lote #{acao_id} excluído com sucesso!")
                            st.rerun()
                conn.close()