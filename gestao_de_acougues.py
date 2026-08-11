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

    cols_check = [
        ("referencia", "TEXT DEFAULT 'Produto Processado'"),
        ("insumos_ali_json", "TEXT"),
        ("insumos_nao_ali_json", "TEXT"),
        ("precificacao_json", "TEXT")
    ]
    for col_n, col_t in cols_check:
        try:
            cursor.execute(f"ALTER TABLE fichas_tecnicas ADD COLUMN {col_n} {col_t}")
            conn.commit()
        except Exception:
            conn.rollback()

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
# 5. MOTOR DE CÁLCULO DA DESOSSA & RELATÓRIO PDF DESOSSA
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

    pdf.set_font("Arial", style="B", size=7.5)
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

    pdf.ln(4)

    pdf.set_font("Arial", style="B", size=5.5)
    pdf.set_fill_color(226, 232, 240)
    
    cols_display = [
        'CORTE', 'QUAL.', 'PESO', 'P. CUSTO/KG', 'P. CUSTO', 
        'P. VENDA/KG', 'VALOR VENDAS', 'LUCRO BRUTO', '% CORTES', 
        'TAXAS DE CARTÃO', 'IMPOSTOS', 'EMBALAGENS', 'COMISSÃO', 'C. EFET/KG', 'CUSTO EFET. TOT'
    ]
    
    larguras = [32, 12, 14, 18, 17, 18, 21, 18, 15, 17, 16, 17, 15, 18, 21]
    
    for i, col_title in enumerate(cols_display):
        pdf.cell(larguras[i], 6, col_title, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", size=5.5)
    for _, r in df_res.iterrows():
        if pdf.get_y() > 185:
            pdf.add_page()
            pdf.set_font("Arial", style="B", size=5.5)
            pdf.set_fill_color(226, 232, 240)
            for i, col_title in enumerate(cols_display):
                pdf.cell(larguras[i], 6, col_title, 1, 0, 'C', True)
            pdf.ln()
            pdf.set_font("Arial", size=5.5)

        pdf.cell(larguras[0], 4.5, str(r['nome_corte'])[:22], 1, 0, 'L')
        pdf.cell(larguras[1], 4.5, str(r['qualidade']), 1, 0, 'C')
        pdf.cell(larguras[2], 4.5, f"{r['peso']:.3f}", 1, 0, 'R')
        pdf.cell(larguras[3], 4.5, f"{r['PREÇO CUSTO/KG']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[4], 4.5, f"{r['PREÇO/CUSTO']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[5], 4.5, f"{r['PREÇO VENDA/KG']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[6], 4.5, f"{r['VALOR TOTAL DE VENDAS']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[7], 4.5, f"{r['LUCRO BRUTO']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[8], 4.5, f"{r['PERCENTUAL/CORTES']*100:.1f}%", 1, 0, 'R')
        pdf.cell(larguras[9], 4.5, f"{r['TAXAS DE CARTÃO']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[10], 4.5, f"{r['IMPOSTOS']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[11], 4.5, f"{r['EMBALAGENS']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[12], 4.5, f"{r['COMISSÃO']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[13], 4.5, f"{r['CUSTO EFETIVO/KG']:.2f}", 1, 0, 'R')
        pdf.cell(larguras[14], 4.5, f"{r['CUSTO EFETIVO TOTAL']:.2f}", 1, 1, 'R')
        
    return pdf.output(dest='S').encode('latin1')

# =========================================================================
# 6. GERADOR DE RELATÓRIO PDF DO MÓDULO FINANCEIRO
# =========================================================================
def gerar_pdf_relatorio_financeiro(pv, i_mensal, n_parcelas, sistema, df_amort, total_pago, total_juros, nome_empresa, calculo_alvo):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)
    
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(10, 8, 190, 12, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", style="B", size=10)
    pdf.set_xy(10, 10)
    pdf.cell(190, 8, "RENATO FRIGOTUDO & ASSOCIADOS - RELATÓRIO FINANCEIRO & AMORTIZAÇÃO", ln=1, align="C")
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Arial", style="B", size=9)
    pdf.set_xy(10, 22)
    data_str = datetime.date.today().strftime("%d/%m/%Y")
    pdf.cell(190, 5, f"Empresa: {nome_empresa.upper()} | Data de Emissão: {data_str} | Sistema: {sistema}", ln=1, align="C")
    pdf.ln(3)

    pdf.set_font("Arial", style="B", size=9)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(190, 6, "QUADRO RESUMO DA OPERAÇÃO DE FINANCIAMENTO", 1, 1, 'C', True)

    pdf.set_font("Arial", size=8)
    quadro = [
        ("Objetivo do Cálculo:", calculo_alvo),
        ("Valor Financiado (PV):", f"R$ {pv:,.2f}"),
        ("Taxa de Juros Mensal Equivalente:", f"{i_mensal * 100:.4f}% a.m."),
        ("Prazo Total (Parcelas Mensais):", f"{n_parcelas} meses"),
        ("Total de Juros Pagos:", f"R$ {total_juros:,.2f}"),
        ("Custo Total do Contrato:", f"R$ {total_pago:,.2f}"),
        ("Primeira Prestação:", f"R$ {df_amort['Prestação'].iloc[0]:,.2f}"),
        ("Última Prestação:", f"R$ {df_amort['Prestação'].iloc[-1]:,.2f}")
    ]

    for label, val in quadro:
        pdf.cell(95, 5, label, 1, 0, 'L')
        pdf.cell(95, 5, val, 1, 1, 'R')

    pdf.ln(5)

    pdf.set_font("Arial", style="B", size=8)
    pdf.set_fill_color(226, 232, 240)
    
    cols = ['Mês', 'Prestação', 'Juros', 'Amortização', 'Saldo Devedor']
    larguras = [20, 42.5, 42.5, 42.5, 42.5]
    
    for i, col_title in enumerate(cols):
        pdf.cell(larguras[i], 6, col_title, 1, 0, 'C', True)
    pdf.ln()

    pdf.set_font("Arial", size=7.5)
    for _, row in df_amort.iterrows():
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_font("Arial", style="B", size=8)
            pdf.set_fill_color(226, 232, 240)
            for i, col_title in enumerate(cols):
                pdf.cell(larguras[i], 6, col_title, 1, 0, 'C', True)
            pdf.ln()
            pdf.set_font("Arial", size=7.5)

        pdf.cell(larguras[0], 4.5, str(int(row['Mês'])), 1, 0, 'C')
        pdf.cell(larguras[1], 4.5, f"R$ {row['Prestação']:,.2f}", 1, 0, 'R')
        pdf.cell(larguras[2], 4.5, f"R$ {row['Juros']:,.2f}", 1, 0, 'R')
        pdf.cell(larguras[3], 4.5, f"R$ {row['Amortização']:,.2f}", 1, 0, 'R')
        pdf.cell(larguras[4], 4.5, f"R$ {row['Saldo Devedor']:,.2f}", 1, 1, 'R')

    return pdf.output(dest='S').encode('latin1')

# =========================================================================
# 7. GERADOR DE RELATÓRIO PDF DO MÓDULO FICHA TÉCNICA
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
        ("Custo da Unidade / Pacote", f"R$ {calc_res['custo_unidade']:,.4f} / R$ {calc_res['custo_pacote']:,.2f}")
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
        ("Custo de Aquisição (CER)", f"{calc_res['cer_pct']:.2f}%", f"R$ {calc_res['cer']:,.4f}", f"R$ {calc_res['cer']:,.4f}"),
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

# =========================================================================
# 8. GERADOR DE RELATÓRIO PDF DO MÓDULO NECESSIDADE DE CAPITAL DE GIRO (NCG)
# =========================================================================
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
# 9. MÓDULOS DE SUPORTE (FINANCEIRO, FICHA TÉCNICA E NCG REESTRUTURADO)
# =========================================================================
def render_modulo_financeiro():
    st.header("🧮 Módulo de Cálculo Financeiro & Amortização Bidirecional")
    st.markdown("Calcule qualquer parâmetro do empréstimo (Prestação, Valor Financiado, Prazo ou Taxa) e gere a tabela de amortização com taxas equivalentes.")
    
    calculo_opcao = st.radio(
        "🎯 O que você deseja calcular?",
        ["Prestação (PMT)", "Valor Financiado (PV)", "Prazo (n)", "Taxa de Juros (i)"],
        horizontal=True
    )

    sistema = st.selectbox("Sistema de Amortização", ["Tabela Price (Prestações Iguais)", "Tabela SAC (Amortização Constante)"])
    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        if calculo_opcao != "Valor Financiado (PV)":
            pv_input = st.number_input("Valor Financiado / Empréstimo - PV (R$)", min_value=0.0, value=100000.0, step=1000.0)
        else:
            pv_input = None

        if calculo_opcao != "Prestação (PMT)":
            pmt_input = st.number_input("Valor da Prestação - PMR / PMT (R$)", min_value=0.0, value=9168.0, step=100.0)
        else:
            pmt_input = None

    with col_b:
        if calculo_opcao != "Taxa de Juros (i)":
            c_i1, c_i2 = st.columns([2, 1])
            taxa_val = c_i1.number_input("Taxa de Juros", min_value=0.0, value=1.5, step=0.1)
            taxa_unid = c_i2.selectbox("Periodicidade", ["% a.m.", "% a.a.", "% a.d."])
        else:
            taxa_val, taxa_unid = None, "% a.m."

        if calculo_opcao != "Prazo (n)":
            c_n1, c_n2 = st.columns([2, 1])
            prazo_val = c_n1.number_input("Prazo Total", min_value=1, value=12, step=1)
            prazo_unid = c_n2.selectbox("Unidade do Tempo", ["Meses", "Anos", "Dias"])
        else:
            prazo_val, prazo_unid = None, "Meses"

    def converter_para_taxa_mensal(val, unid):
        i_r = val / 100.0
        if unid == "% a.m.":
            return i_r
        elif unid == "% a.a.":
            return ((1.0 + i_r) ** (1.0 / 12.0)) - 1.0
        else:
            return ((1.0 + i_r) ** 30.0) - 1.0

    def converter_para_meses(val, unid):
        if unid == "Meses":
            return float(val)
        elif unid == "Anos":
            return float(val * 12)
        else:
            return float(val) / 30.0

    pv_calc, pmt_calc, i_m_calc, n_calc = 0.0, 0.0, 0.0, 0

    try:
        if calculo_opcao == "Prestação (PMT)":
            pv_calc = pv_input
            i_m_calc = converter_para_taxa_mensal(taxa_val, taxa_unid)
            n_calc = int(round(converter_para_meses(prazo_val, prazo_unid)))
            
            if "Price" in sistema:
                pmt_calc = pv_calc * (i_m_calc * (1 + i_m_calc)**n_calc) / ((1 + i_m_calc)**n_calc - 1) if i_m_calc > 0 else pv_calc / n_calc
            else:
                pmt_calc = (pv_calc / n_calc) + (pv_calc * i_m_calc)

        elif calculo_opcao == "Valor Financiado (PV)":
            pmt_calc = pmt_input
            i_m_calc = converter_para_taxa_mensal(taxa_val, taxa_unid)
            n_calc = int(round(converter_para_meses(prazo_val, prazo_unid)))
            
            if "Price" in sistema:
                pv_calc = pmt_calc * (((1 + i_m_calc)**n_calc - 1) / (i_m_calc * (1 + i_m_calc)**n_calc)) if i_m_calc > 0 else pmt_calc * n_calc
            else:
                pv_calc = (pmt_calc * n_calc) / (1 + i_m_calc * (n_calc + 1) / 2.0)

        elif calculo_opcao == "Prazo (n)":
            pv_calc = pv_input
            pmt_calc = pmt_input
            i_m_calc = converter_para_taxa_mensal(taxa_val, taxa_unid)
            
            if pmt_calc <= pv_calc * i_m_calc:
                st.error("A prestação informada é menor ou igual aos juros da primeira parcela. O empréstimo seria perpétuo!")
                return
            
            n_exact = math.log(pmt_calc / (pmt_calc - i_m_calc * pv_calc)) / math.log(1 + i_m_calc)
            n_calc = max(1, int(round(n_exact)))

        elif calculo_opcao == "Taxa de Juros (i)":
            pv_calc = pv_input
            pmt_calc = pmt_input
            n_calc = int(round(converter_para_meses(prazo_val, prazo_unid)))
            
            rate = 0.01
            for _ in range(100):
                f = pv_calc * (rate * (1 + rate)**n_calc) / ((1 + rate)**n_calc - 1) - pmt_calc
                df = pv_calc * ((1 + rate)**n_calc * ((1 + rate)**n_calc - rate * n_calc - 1)) / (((1 + rate)**n_calc - 1)**2)
                if abs(df) < 1e-7:
                    break
                rate_next = rate - f / df
                if abs(rate_next - rate) < 1e-6:
                    break
                rate = rate_next
            i_m_calc = max(0.0, rate)

        st.markdown("---")
        st.subheader("📌 Quadro Resumo dos Resultados")
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Valor Financiado (PV)", f"R$ {pv_calc:,.2f}")
        q2.metric("Prestação Base (PMT)", f"R$ {pmt_calc:,.2f}")
        q3.metric("Taxa Mensal Equivalente", f"{i_m_calc * 100:.4f}% a.m.")
        q4.metric("Prazo (Parcelas)", f"{n_calc} meses")

        dados = []
        saldo_devedor = pv_calc
        
        if "Price" in sistema:
            pmt_fixo = pv_calc * (i_m_calc * (1 + i_m_calc)**n_calc) / ((1 + i_m_calc)**n_calc - 1) if i_m_calc > 0 else pv_calc / n_calc
            for mes in range(1, n_calc + 1):
                juros = saldo_devedor * i_m_calc
                amortizacao = pmt_fixo - juros
                saldo_devedor -= amortizacao
                dados.append({"Mês": mes, "Prestação": pmt_fixo, "Juros": juros, "Amortização": amortizacao, "Saldo Devedor": max(0.0, saldo_devedor)})
        else:
            amortizacao = pv_calc / n_calc
            for mes in range(1, n_calc + 1):
                juros = saldo_devedor * i_m_calc
                pmt_var = amortizacao + juros
                saldo_devedor -= amortizacao
                dados.append({"Mês": mes, "Prestação": pmt_var, "Juros": juros, "Amortização": amortizacao, "Saldo Devedor": max(0.0, saldo_devedor)})

        df_amort = pd.DataFrame(dados)
        total_pago = df_amort["Prestação"].sum()
        total_juros = df_amort["Juros"].sum()

        st.markdown("##### 📈 Tabela Completa de Amortização")
        st.dataframe(df_amort.style.format({
            "Prestação": "R$ {:.2f}", "Juros": "R$ {:.2f}", "Amortização": "R$ {:.2f}", "Saldo Devedor": "R$ {:.2f}"
        }), use_container_width=True)

        pdf_bytes_fin = gerar_pdf_relatorio_financeiro(
            pv_calc, i_m_calc, n_calc, sistema, df_amort, total_pago, total_juros, 
            st.session_state.empresa_nome if 'empresa_nome' in st.session_state else "Açougue", calculo_opcao
        )
        
        st.download_button(
            label="📥 Baixar Relatório Financeiro Completo em PDF",
            data=pdf_bytes_fin,
            file_name=f"relatorio_financeiro_{datetime.date.today()}.pdf",
            mime="application/pdf",
            key="btn_pdf_financeiro"
        )

    except Exception as err:
        st.error(f"Erro ao calcular parâmetros do empréstimo: {err}")

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
            st.session_state.ft_rend_assada = 14.226
            st.session_state.ft_peso_unid = 0.118
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
            st.session_state.ft_rend_assada = float(row_ft['rendimento_assada_kg'])
            st.session_state.ft_peso_unid = float(row_ft['peso_unidade_kg'])
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

    if "ft_produto" not in st.session_state:
        st.session_state.ft_produto = "COSTELA ASSADA"
        st.session_state.ft_ref = "Produto Processado"
        st.session_state.ft_rend_assada = 14.226
        st.session_state.ft_peso_unid = 0.118
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
        ft_rend_assada = col_f3.number_input("Rendimento Depois de Assada kg", min_value=0.001, value=st.session_state.ft_rend_assada, step=0.1, format="%.3f")

        col_f4, col_f5 = st.columns(2)
        ft_peso_unid = col_f4.number_input("Peso da Unidade KG", min_value=0.001, value=st.session_state.ft_peso_unid, step=0.005, format="%.3f")
        ft_qtd_pacote = col_f5.number_input("Quantidade no Pacote", min_value=1.0, value=st.session_state.ft_qtd_pacote, step=1.0)

        # CÁLCULO DE UNIDADES PRODUZIDAS IDÊNTICO À PLANILHA EXCEL (=ROUNDDOWN(Rendimento_Assada / Peso_Unidade, 0))
        ft_unid_prod = math.floor(ft_rend_assada / ft_peso_unid) if ft_peso_unid > 0 else 0.0

        st.markdown("---")
        st.subheader("1. Insumos Alimentícios (Edição Interativa)")
        st.caption("✏️ Você pode editar qualquer célula diretamente na tabela abaixo. Altere quantidades, preços ou rendimentos em tempo real.")

        # MONTAGEM DA DATAFRAME INTERATIVA DE INSUMOS ALIMENTÍCIOS
        df_ali_raw = pd.DataFrame(st.session_state.ft_items_ali)
        if df_ali_raw.empty:
            df_ali_raw = pd.DataFrame(columns=["cod", "produto", "qtd_bruta", "unidade", "preco_bruto", "rendimento"])

        # RENOMEAR COLUNAS PARA APRESENTAÇÃO AMIGÁVEL
        df_ali_edit_input = df_ali_raw.rename(columns={
            "cod": "Cód",
            "produto": "Produto",
            "qtd_bruta": "Quantidade Bruta",
            "unidade": "Unidade",
            "preco_bruto": "Preço Bruto",
            "rendimento": "Rendimento (Fator)"
        })

        edited_ali_df = st.data_editor(
            df_ali_edit_input,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_insumos_alimenticios",
            column_config={
                "Quantidade Bruta": st.column_config.NumberColumn(format="%.3f"),
                "Preço Bruto": st.column_config.NumberColumn(format="R$ %.2f"),
                "Rendimento (Fator)": st.column_config.NumberColumn(format="%.2f")
            }
        )

        # ATUALIZAÇÃO DO SESSION STATE DE INSUMOS ALIMENTÍCIOS COM BASE NA TABELA EDITADA
        updated_ali_items = []
        for _, r_ali in edited_ali_df.iterrows():
            if str(r_ali.get("Produto", "")).strip() != "":
                qb = float(r_ali.get("Quantidade Bruta", 0.0))
                pb = float(r_ali.get("Preço Bruto", 0.0))
                rf = float(r_ali.get("Rendimento (Fator)", 1.0))
                updated_ali_items.append({
                    "cod": str(r_ali.get("Cód", "")),
                    "produto": str(r_ali.get("Produto", "")).upper().strip(),
                    "qtd_bruta": qb,
                    "unidade": str(r_ali.get("Unidade", "KG")).upper().strip(),
                    "preco_bruto": pb,
                    "rendimento": rf
                })
        st.session_state.ft_items_ali = updated_ali_items

        # EXIBIÇÃO DOS RESULTADOS CALCULADOS DOS INSUMOS ALIMENTÍCIOS (EXCEL IDÊNTICO)
        rows_ali_calc = []
        for idx, item in enumerate(st.session_state.ft_items_ali):
            ql = item['qtd_bruta'] * item['rendimento']
            pl = item['preco_bruto'] * ql
            rows_ali_calc.append({
                "Cód": item.get('cod', f"{idx+1:03d}"),
                "Produto": item['produto'],
                "Qtd Bruta": item['qtd_bruta'],
                "Unid": item['unidade'],
                "Preço Bruto (R$)": item['preco_bruto'],
                "Rendimento": item['rendimento'],
                "Qtd Líquida": ql,
                "Preço Líquido (R$)": pl
            })
        
        if rows_ali_calc:
            df_ali_view = pd.DataFrame(rows_ali_calc)
            st.markdown("**Cálculos Apurados dos Insumos Alimentícios:**")
            st.dataframe(df_ali_view.style.format({
                "Qtd Bruta": "{:.3f}", "Preço Bruto (R$)": "R$ {:.2f}", "Rendimento": "{:.2f}",
                "Qtd Líquida": "{:.3f}", "Preço Líquido (R$)": "R$ {:.2f}"
            }), use_container_width=True)

        # CÁLCULO DO RENDIMENTO CRUA (KG) COMO SOMA DAS QUANTIDADES LÍQUIDAS DOS INSUMOS ALIMENTÍCIOS (=SUM(H24:H47) NO EXCEL)
        ft_rend_crua = sum(item['qtd_bruta'] * item['rendimento'] for item in st.session_state.ft_items_ali)
        perda_pct = (1.0 - (ft_rend_assada / ft_rend_crua)) * 100.0 if ft_rend_crua > 0 else 0.0

        st.markdown("---")
        st.subheader("2. Insumos Não Alimentícios (Gás, Embalagens, etc. - Edição Interativa)")
        st.caption("✏️ Edite os insumos não alimentícios diretamente na tabela abaixo.")

        df_nao_ali_raw = pd.DataFrame(st.session_state.ft_items_nao_ali)
        if df_nao_ali_raw.empty:
            df_nao_ali_raw = pd.DataFrame(columns=["cod", "produto", "qtd_bruta", "unidade", "preco_bruto", "rendimento"])

        df_nao_ali_edit_input = df_nao_ali_raw.rename(columns={
            "cod": "Cód",
            "produto": "Produto",
            "qtd_bruta": "Quantidade Bruta",
            "unidade": "Unidade",
            "preco_bruto": "Preço Bruto",
            "rendimento": "Rendimento (Fator)"
        })

        edited_nao_ali_df = st.data_editor(
            df_nao_ali_edit_input,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_insumos_nao_alimenticios",
            column_config={
                "Quantidade Bruta": st.column_config.NumberColumn(format="%.3f"),
                "Preço Bruto": st.column_config.NumberColumn(format="R$ %.2f"),
                "Rendimento (Fator)": st.column_config.NumberColumn(format="%.2f")
            }
        )

        updated_nao_ali_items = []
        for _, r_nao in edited_nao_ali_df.iterrows():
            if str(r_nao.get("Produto", "")).strip() != "":
                qb = float(r_nao.get("Quantidade Bruta", 0.0))
                pb = float(r_nao.get("Preço Bruto", 0.0))
                rf = float(r_nao.get("Rendimento (Fator)", 1.0))
                updated_nao_ali_items.append({
                    "cod": str(r_nao.get("Cód", "")),
                    "produto": str(r_nao.get("Produto", "")).upper().strip(),
                    "qtd_bruta": qb,
                    "unidade": str(r_nao.get("Unidade", "UNID")).upper().strip(),
                    "preco_bruto": pb,
                    "rendimento": rf
                })
        st.session_state.ft_items_nao_ali = updated_nao_ali_items

        rows_nao_ali_calc = []
        for idx, item in enumerate(st.session_state.ft_items_nao_ali):
            ql = item['qtd_bruta'] * item['rendimento']
            pl = item['preco_bruto'] * ql
            rows_nao_ali_calc.append({
                "Cód": item.get('cod', f"{idx+101:03d}"),
                "Produto": item['produto'],
                "Qtd Bruta": item['qtd_bruta'],
                "Unid": item['unidade'],
                "Preço Bruto (R$)": item['preco_bruto'],
                "Rendimento": item['rendimento'],
                "Qtd Líquida": ql,
                "Preço Líquido (R$)": pl
            })

        if rows_nao_ali_calc:
            df_nao_ali_view = pd.DataFrame(rows_nao_ali_calc)
            st.markdown("**Cálculos Apurados dos Insumos Não Alimentícios:**")
            st.dataframe(df_nao_ali_view.style.format({
                "Qtd Bruta": "{:.3f}", "Preço Bruto (R$)": "R$ {:.2f}", "Rendimento": "{:.2f}",
                "Qtd Líquida": "{:.3f}", "Preço Líquido (R$)": "R$ {:.2f}"
            }), use_container_width=True)

        # CÁLCULOS IDÊNTICOS À PLANILHA EXCEL "COSTELA ASSADA"
        tot_ali_custo = sum(item['preco_bruto'] * (item['qtd_bruta'] * item['rendimento']) for item in st.session_state.ft_items_ali)
        tot_ali_qtd = ft_rend_crua
        tot_nao_ali_custo = sum(item['preco_bruto'] * (item['qtd_bruta'] * item['rendimento']) for item in st.session_state.ft_items_nao_ali)

        custo_total = tot_ali_custo + tot_nao_ali_custo
        custo_kg_crua = custo_total / ft_rend_crua if ft_rend_crua > 0 else 0.0
        custo_kg_assada = custo_total / ft_rend_assada if ft_rend_assada > 0 else 0.0
        custo_unidade = custo_total / ft_unid_prod if ft_unid_prod > 0 else 0.0
        custo_pacote = custo_unidade * ft_qtd_pacote

        st.markdown("---")
        st.subheader("📊 Tabela de Custos")
        
        info_perda_col, info_unid_col = st.columns(2)
        info_perda_col.info(f"📊 **Rendimento Crua:** `{ft_rend_crua:.3f} kg` | **Rendimento Assada:** `{ft_rend_assada:.3f} kg` | **Perda %:** `{perda_pct:.4f}%`")
        info_unid_col.info(f"📦 **Unidades Produzidas:** `{int(ft_unid_prod)}` (calculado de {ft_rend_assada:.3f}/{ft_peso_unid:.3f}) | **Qtd por Pacote:** `{int(ft_qtd_pacote)}`")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Custo Total", f"R$ {custo_total:,.2f}")
        m2.metric("Custo/Kg Crua", f"R$ {custo_kg_crua:,.2f}")
        m3.metric("Custo/kg Total Depois de Assada", f"R$ {custo_kg_assada:,.2f}")
        m4.metric("Custo da Unidade", f"R$ {custo_unidade:,.4f}")
        m5.metric("Custo do Pacote", f"R$ {custo_pacote:,.2f}")

    with tab_prec:
        st.subheader("💲 Formação do Preço de Venda por KG")
        
        precif_dict = st.session_state.ft_precif
        opcao_salva_cer = precif_dict.get("opcao_cer", "Custo/kg Total Depois de Assada")

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

    margem_bruta_rs = fat - cmv
    margem_bruta_pct = (fat - cmv) / fat if fat > 0 else 0.0
    cmv_diario = cmv / 30.0
    fat_diario = fat / 30.0

    ciclo_atual = pme_atual + pmr_atual - pmp_atual
    ciclo_prop = pme_prop + pmr_prop - pmp_prop

    ncg_atual = cmv_diario * ciclo_atual
    ncg_prop = cmv_diario * ciclo_prop

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
# 10. GERENCIAMENTO DE SESSÃO E LOGIN
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

    if st.session_state.e_admin:
        st.sidebar.markdown("### 🛠️ Menu Administrativo")
        menu = st.sidebar.radio("Selecione a Tela:", ["Gerenciar Empresas", "Cadastrar Empresa", "Gerenciar Cadastro de Cortes", "Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"], key="menu_admin")
    else:
        st.sidebar.markdown("### 🥩 Menu de Operações")
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Gerenciar Cadastro de Cortes", "Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"], key="menu_operacional")

    exibir_cabecalho(nome_empresa_usuaria=st.session_state.empresa_nome)

    # =========================================================================
    # 11. EXECUÇÃO DOS MÓDULOS DE TELA
    # =========================================================================
    if menu == "Cadastrar Empresa":
        st.header("🏢 Cadastrar Nova Empresa / Açougue")
        with st.form("form_cadastrar_empresa"):
            novo_nome = st.text_input("Nome da Empresa")
            novo_login = st.text_input("Usuário / Login de Acesso")
            nova_senha = st.text_input("Senha", type="password")
            btn_salvar = st.form_submit_button("Salvar Cadastro")
            
            if btn_salvar:
                if not novo_nome or not novo_login or not nova_senha:
                    st.error("Preencha todos os campos obrigatoriamente.")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    is_postgres = "psycopg2" in str(type(conn))
                    try:
                        login_clean = novo_login.strip().lower()
                        if is_postgres:
                            cursor.execute("INSERT INTO empresas (nome, login, senha, ativo) VALUES (%s, %s, %s, 1)", (novo_nome.strip(), login_clean, nova_senha))
                        else:
                            cursor.execute("INSERT INTO empresas (nome, login, senha, ativo) VALUES (?, ?, ?, 1)", (novo_nome.strip(), login_clean, nova_senha))
                        conn.commit()
                        st.success(f"Empresa '{novo_nome}' cadastrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar empresa (Login pode já existir): {e}")
                    finally:
                        conn.close()

    elif menu == "Gerenciar Empresas":
        st.header("🏢 Gerenciamento de Empresas Cadastradas")
        conn = get_connection()
        is_postgres = "psycopg2" in str(type(conn))
        df_empresas = pd.read_sql_query("SELECT id, nome, login, senha, ativo FROM empresas ORDER BY nome ASC", conn)
        conn.close()
        
        if df_empresas.empty:
            st.info("Nenhuma empresa cadastrada no sistema.")
        else:
            for _, emp in df_empresas.iterrows():
                e_id = emp['id']
                e_nome = emp['nome']
                e_login = emp['login']
                e_senha = emp['senha']
                e_ativo = emp['ativo']
                
                status_str = "🟢 Ativa" if e_ativo == 1 else "🔴 Bloqueada"
                
                with st.expander(f"🏢 {e_nome.upper()} ({status_str}) - Login: {e_login}"):
                    with st.form(f"form_edit_emp_{e_id}"):
                        edit_nome = st.text_input("Nome da Empresa", value=e_nome, key=f"edit_nome_{e_id}")
                        edit_login = st.text_input("Login", value=e_login, key=f"edit_login_{e_id}")
                        edit_senha = st.text_input("Senha", value=e_senha, type="password", key=f"edit_senha_{e_id}")
                        
                        col_b1, col_b2, col_b3 = st.columns(3)
                        btn_salvar_edit = col_b1.form_submit_button("💾 Salvar Alterações")
                        
                        btn_label_block = "🔒 Bloquear Empresa" if e_ativo == 1 else "🔓 Desbloquear Empresa"
                        btn_bloquear = col_b2.form_submit_button(btn_label_block)
                        
                        btn_excluir = col_b3.form_submit_button("🗑️ Excluir Empresa")
                        
                        if btn_salvar_edit:
                            conn = get_connection()
                            cursor = conn.cursor()
                            if is_postgres:
                                cursor.execute("UPDATE empresas SET nome = %s, login = %s, senha = %s WHERE id = %s", (edit_nome.strip(), edit_login.strip().lower(), edit_senha, e_id))
                            else:
                                cursor.execute("UPDATE empresas SET nome = ?, login = ?, senha = ? WHERE id = ?", (edit_nome.strip(), edit_login.strip().lower(), edit_senha, e_id))
                            conn.commit()
                            conn.close()
                            st.success("Dados atualizados com sucesso!")
                            st.rerun()
                            
                        if btn_bloquear:
                            novo_status = 0 if e_ativo == 1 else 1
                            conn = get_connection()
                            cursor = conn.cursor()
                            if is_postgres:
                                cursor.execute("UPDATE empresas SET ativo = %s WHERE id = %s", (novo_status, e_id))
                            else:
                                cursor.execute("UPDATE empresas SET ativo = ? WHERE id = ?", (novo_status, e_id))
                            conn.commit()
                            conn.close()
                            st.success(f"Status da empresa alterado!")
                            st.rerun()

                        if btn_excluir:
                            conn = get_connection()
                            cursor = conn.cursor()
                            if is_postgres:
                                cursor.execute("DELETE FROM empresas WHERE id = %s", (e_id,))
                            else:
                                cursor.execute("DELETE FROM empresas WHERE id = ?", (e_id,))
                            conn.commit()
                            conn.close()
                            st.success("Empresa excluída com sucesso!")
                            st.rerun()

    elif menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Gerenciar Tipos de Desossa & Cortes Padrão")
        emp_id_ativo = st.session_state.empresa_id
        
        st.subheader("1. Tipos de Desossa (Ex: Quarto Traseiro, Vaca Casada)")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            with st.form("form_add_tipo_desossa"):
                novo_tipo = st.text_input("Novo Tipo de Desossa")
                if st.form_submit_button("➕ Cadastrar Tipo") and novo_tipo:
                    conn = get_connection()
                    cursor = conn.cursor()
                    is_postgres = "psycopg2" in str(type(conn))
                    try:
                        emp_v = emp_id_ativo if emp_id_ativo != 0 else None
                        if is_postgres:
                            cursor.execute("INSERT INTO tipos_desossa (nome, empresa_id) VALUES (%s, %s)", (novo_tipo.upper().strip(), emp_v))
                        else:
                            cursor.execute("INSERT INTO tipos_desossa (nome, empresa_id) VALUES (?, ?)", (novo_tipo.upper().strip(), emp_v))
                        conn.commit()
                        st.success(f"Tipo '{novo_tipo.upper()}' cadastrado!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")
                    finally:
                        conn.close()
                        st.rerun()

        with col_t2:
            conn = get_connection()
            is_postgres = "psycopg2" in str(type(conn))
            if emp_id_ativo == 0:
                df_tipos_db = pd.read_sql_query("SELECT id, nome FROM tipos_desossa ORDER BY nome ASC", conn)
            else:
                if is_postgres:
                    df_tipos_db = pd.read_sql_query("SELECT id, nome FROM tipos_desossa WHERE empresa_id IS NULL OR empresa_id = %s ORDER BY nome ASC", conn, params=(emp_id_ativo,))
                else:
                    df_tipos_db = pd.read_sql_query(f"SELECT id, nome FROM tipos_desossa WHERE empresa_id IS NULL OR empresa_id = {emp_id_ativo} ORDER BY nome ASC", conn)
            conn.close()

            if not df_tipos_db.empty:
                st.markdown("**Tipos Existentes (Edição / Exclusão):**")
                for _, r_t in df_tipos_db.iterrows():
                    tid = r_t['id']
                    tnome = r_t['nome']
                    c_n1, c_n2, c_n3 = st.columns([3, 1, 1])
                    edit_t_val = c_n1.text_input("Nome", value=tnome, key=f"input_t_{tid}", label_visibility="collapsed")
                    if c_n2.button("💾", key=f"save_t_{tid}", help="Salvar Alteração"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        if is_postgres:
                            cursor.execute("UPDATE tipos_desossa SET nome = %s WHERE id = %s", (edit_t_val.upper().strip(), tid))
                            cursor.execute("UPDATE cortes_padrao SET tipo_desossa = %s WHERE tipo_desossa = %s", (edit_t_val.upper().strip(), tnome))
                        else:
                            cursor.execute("UPDATE tipos_desossa SET nome = ? WHERE id = ?", (edit_t_val.upper().strip(), tid))
                            cursor.execute("UPDATE cortes_padrao SET tipo_desossa = ? WHERE tipo_desossa = ?", (edit_t_val.upper().strip(), tnome))
                        conn.commit()
                        conn.close()
                        st.success("Tipo atualizado!")
                        st.rerun()
                    if c_n3.button("🗑️", key=f"del_t_{tid}", help="Excluir Tipo"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        if is_postgres:
                            cursor.execute("DELETE FROM tipos_desossa WHERE id = %s", (tid,))
                            cursor.execute("DELETE FROM cortes_padrao WHERE tipo_desossa = %s", (tnome,))
                        else:
                            cursor.execute("DELETE FROM tipos_desossa WHERE id = ?", (tid,))
                            cursor.execute("DELETE FROM cortes_padrao WHERE tipo_desossa = ?", (tnome,))
                        conn.commit()
                        conn.close()
                        st.success("Tipo e cortes associados removidos!")
                        st.rerun()

        st.markdown("---")
        
        st.subheader("2. Cortes Padrão Associados")
        tipos_disponiveis = get_tipos_desossa(emp_id_ativo)
        
        if tipos_disponiveis:
            tipo_sel = st.selectbox("Selecione o Tipo de Desossa para ver e gerenciar os cortes", tipos_disponiveis, key="tipo_sel_config_cortes")
            
            with st.form("form_adicionar_corte_padrao"):
                st.markdown(f"**Adicionar Novo Corte Padrão para:** `{tipo_sel}`")
                novo_corte_nome = st.text_input("Nome do Corte")
                if st.form_submit_button("Cadastrar Corte Padrão") and novo_corte_nome:
                    conn = get_connection()
                    cursor = conn.cursor()
                    is_postgres = "psycopg2" in str(type(conn))
                    try:
                        emp_v = emp_id_ativo if emp_id_ativo != 0 else None
                        if is_postgres:
                            cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (%s, %s, %s)", (tipo_sel, novo_corte_nome.upper().strip(), emp_v))
                        else:
                            cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (tipo_sel, novo_corte_nome.upper().strip(), emp_v))
                        conn.commit()
                        st.success(f"Corte '{novo_corte_nome.upper()}' cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar corte: {e}")
                    finally:
                        conn.close()
                        st.rerun()

            conn = get_connection()
            is_postgres = "psycopg2" in str(type(conn))
            if emp_id_ativo == 0:
                if is_postgres:
                    df_padroes = pd.read_sql_query("SELECT id, tipo_desossa, nome_corte FROM cortes_padrao WHERE tipo_desossa = %s ORDER BY nome_corte ASC", conn, params=(tipo_sel,))
                else:
                    df_padroes = pd.read_sql_query(f"SELECT id, tipo_desossa, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' ORDER BY nome_corte ASC", conn)
            else:
                if is_postgres:
                    df_padroes = pd.read_sql_query("SELECT id, tipo_desossa, nome_corte FROM cortes_padrao WHERE tipo_desossa = %s AND (empresa_id = %s OR empresa_id IS NULL) ORDER BY nome_corte ASC", conn, params=(tipo_sel, emp_id_ativo))
                else:
                    df_padroes = pd.read_sql_query(f"SELECT id, tipo_desossa, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND (empresa_id = {emp_id_ativo} OR empresa_id IS NULL) ORDER BY nome_corte ASC", conn)
            conn.close()

            st.markdown(f"**Cortes Cadastrados para `{tipo_sel}`:**")
            if not df_padroes.empty:
                for _, cp in df_padroes.iterrows():
                    c_id = cp['id']
                    c_nome = cp['nome_corte']
                    
                    col_cn1, col_cn2, col_cn3 = st.columns([4, 1, 1])
                    val_c_edit = col_cn1.text_input("Corte", value=c_nome, key=f"edit_cp_val_{c_id}", label_visibility="collapsed")
                    
                    if col_cn2.button("💾", key=f"salv_cp_{c_id}", help="Salvar Alteração"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        if is_postgres:
                            cursor.execute("UPDATE cortes_padrao SET nome_corte = %s WHERE id = %s", (val_c_edit.upper().strip(), c_id))
                        else:
                            cursor.execute("UPDATE cortes_padrao SET nome_corte = ? WHERE id = ?", (val_c_edit.upper().strip(), c_id))
                        conn.commit()
                        conn.close()
                        st.success("Corte atualizado!")
                        st.rerun()

                    if col_cn3.button("🗑️", key=f"del_cp_{c_id}", help="Excluir Corte"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        if is_postgres:
                            cursor.execute("DELETE FROM cortes_padrao WHERE id = %s", (c_id,))
                        else:
                            cursor.execute("DELETE FROM cortes_padrao WHERE id = ?", (c_id,))
                        conn.commit()
                        conn.close()
                        st.success("Corte removido!")
                        st.rerun()
            else:
                st.info("Nenhum corte padrão cadastrado para este tipo de desossa.")

    elif menu == "Cálculo Financeiro":
        render_modulo_financeiro()
    elif menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()
    elif menu == "Capital de Giro (NCG)":
        render_modulo_ncg()
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
                            st.markdown("##### 🐂 Apuração dos Parâmetros & Indicadores da Simulação")
                            
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
                                        f"{ind['prata_margem_pct']*100:.2f}%", f"{ind['prata_margem_pct']*100:.2f}%", f"R$ {ind['prata_pm_compra']:.2f}", f"R$ {ind['prata_pm_venda']:.2f}"
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
                                label="📥 Baixar Relatório Completo em PDF",
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