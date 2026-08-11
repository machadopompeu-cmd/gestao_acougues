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
# FUNÇÃO AUXILIAR PARA CONVERSÃO SEGURA DE NÚMEROS
# =========================================================================
def safe_float(val, default=0.0):
    """Converte valores com segurança para float, tratando None, NaN, strings com R$ e %."""
    if val is None or pd.isna(val):
        return default
    try:
        if isinstance(val, str):
            val = val.replace('R$', '').replace('%', '').replace(' ', '').replace(',', '.').strip()
            if val == "":
                return default
        return float(val)
    except (ValueError, TypeError):
        return default

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
    div.stButton > button, div.stDownloadButton > button {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #1E3A8A !important;
        padding: 8px 18px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #1D4ED8 !important;
        color: #FFFFFF !important;
        border-color: #1D4ED8 !important;
    }
    form button, div.stFormSubmitButton > button {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #1E3A8A !important;
        font-weight: 700 !important;
    }
    form button:hover, div.stFormSubmitButton > button:hover {
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
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] div.stButton > button,
    section[data-testid="stSidebar"] div.stDownloadButton > button, section[data-testid="stSidebar"] a {
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
# 2. CONEXÃO E INICIALIZAÇÃO DO BANCO DE DADOS
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
        cursor.execute("CREATE TABLE IF NOT EXISTS empresas (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, login TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, ativo INTEGER DEFAULT 1)")
        cursor.execute("CREATE TABLE IF NOT EXISTS tipos_desossa (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, empresa_id INTEGER DEFAULT NULL, UNIQUE(nome, empresa_id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS cortes_padrao (id SERIAL PRIMARY KEY, tipo_desossa TEXT NOT NULL, nome_corte TEXT NOT NULL, empresa_id INTEGER DEFAULT NULL, UNIQUE(tipo_desossa, nome_corte, empresa_id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS acoes (id SERIAL PRIMARY KEY, empresa_id INTEGER, data_acao TEXT, tipo_animal TEXT, peso_bruto REAL, preco_animal_kg REAL, ossos_muxiba REAL, quebra_nao_identificada REAL, exsudato_escorrimento REAL, p_cartao REAL DEFAULT 0.0, p_impostos REAL DEFAULT 0.0, p_embalagens REAL DEFAULT 0.0, p_comissao REAL DEFAULT 0.0)")
        cursor.execute("CREATE TABLE IF NOT EXISTS fichas_tecnicas (id SERIAL PRIMARY KEY, empresa_id INTEGER, produto TEXT NOT NULL, referencia TEXT DEFAULT 'Produto Processado', rendimento_kg REAL DEFAULT 0.0, rendimento_assada_kg REAL DEFAULT 0.0, peso_unidade_kg REAL DEFAULT 0.0, qtd_por_pacote REAL DEFAULT 1.0, unidades_produzidas REAL DEFAULT 1.0, perda_pct REAL DEFAULT 0.0, insumos_ali_json TEXT, insumos_nao_ali_json TEXT, precificacao_json TEXT, data_criacao TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS ncg_registros (id SERIAL PRIMARY KEY, empresa_id INTEGER, titulo TEXT, data_registro TEXT, dados_financeiros_json TEXT, prazos_json TEXT, calculos_json TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS cortes (id SERIAL PRIMARY KEY, acao_id INTEGER, nome_corte TEXT, qualidade TEXT, peso REAL, preco_venda REAL)")
    else:
        cursor.execute("CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, login TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, ativo INTEGER DEFAULT 1)")
        cursor.execute("CREATE TABLE IF NOT EXISTS tipos_desossa (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, empresa_id INTEGER DEFAULT NULL, UNIQUE(nome, empresa_id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS cortes_padrao (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_desossa TEXT NOT NULL, nome_corte TEXT NOT NULL, empresa_id INTEGER DEFAULT NULL, UNIQUE(tipo_desossa, nome_corte, empresa_id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS acoes (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, data_acao TEXT, tipo_animal TEXT, peso_bruto REAL, preco_animal_kg REAL, ossos_muxiba REAL, quebra_nao_identificada REAL, exsudato_escorrimento REAL, p_cartao REAL DEFAULT 0.0, p_impostos REAL DEFAULT 0.0, p_embalagens REAL DEFAULT 0.0, p_comissao REAL DEFAULT 0.0)")
        cursor.execute("CREATE TABLE IF NOT EXISTS fichas_tecnicas (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, produto TEXT NOT NULL, referencia TEXT DEFAULT 'Produto Processado', rendimento_kg REAL DEFAULT 0.0, rendimento_assada_kg REAL DEFAULT 0.0, peso_unidade_kg REAL DEFAULT 0.0, qtd_por_pacote REAL DEFAULT 1.0, unidades_produzidas REAL DEFAULT 1.0, perda_pct REAL DEFAULT 0.0, insumos_ali_json TEXT, insumos_nao_ali_json TEXT, precificacao_json TEXT, data_criacao TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS ncg_registros (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, titulo TEXT, data_registro TEXT, dados_financeiros_json TEXT, prazos_json TEXT, calculos_json TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS cortes (id INTEGER PRIMARY KEY AUTOINCREMENT, acao_id INTEGER, nome_corte TEXT, qualidade TEXT, peso REAL, preco_venda REAL)")

    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=60)
def carregar_fichas_tecnicas_db(emp_id_ativo, termo_busca=""):
    conn = get_connection()
    is_postgres = "psycopg2" in str(type(conn))
    termo = termo_busca.lower().strip()
    
    if emp_id_ativo == 0:
        if termo:
            query_ft = "SELECT * FROM fichas_tecnicas WHERE LOWER(produto) LIKE %s ORDER BY produto ASC" if is_postgres else f"SELECT * FROM fichas_tecnicas WHERE LOWER(produto) LIKE '%{termo}%' ORDER BY produto ASC"
            df = pd.read_sql_query(query_ft, conn, params=(f"%{termo}%",) if is_postgres else None)
        else:
            df = pd.read_sql_query("SELECT * FROM fichas_tecnicas ORDER BY produto ASC", conn)
    else:
        if termo:
            query_ft = "SELECT * FROM fichas_tecnicas WHERE (empresa_id IS NULL OR empresa_id = %s) AND LOWER(produto) LIKE %s ORDER BY produto ASC" if is_postgres else f"SELECT * FROM fichas_tecnicas WHERE (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) AND LOWER(produto) LIKE '%{termo}%' ORDER BY produto ASC"
            df = pd.read_sql_query(query_ft, conn, params=(emp_id_ativo, f"%{termo}%") if is_postgres else None)
        else:
            query_ft = "SELECT * FROM fichas_tecnicas WHERE (empresa_id IS NULL OR empresa_id = %s) ORDER BY produto ASC" if is_postgres else f"SELECT * FROM fichas_tecnicas WHERE (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) ORDER BY produto ASC"
            df = pd.read_sql_query(query_ft, conn, params=(emp_id_ativo,) if is_postgres else None)
            
    conn.close()
    return df

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
# 3. CABEÇALHO DA INTERFACE
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
        subtitulo_empresa = nome_empresa_usuaria.upper() if nome_empresa_usuaria else "PORTAL DE ACESSO"
        st.markdown(
            f"""
            <div style="padding-top: 5px;">
                <h1 style="margin: 0; color: #1E3A8A; font-family: Arial, sans-serif; font-size: 28px; font-weight: 800;">
                    RENATO FRIGOTUDO & ASSOCIADOS
                </h1>
                <h3 style="margin: 4px 0 0 0; color: #0F172A; font-family: Arial, sans-serif; font-size: 18px; font-weight: 700;">
                    🏢 Empresa Usuária: {subtitulo_empresa}
                </h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px; border-top: 3px solid #1E3A8A;'>", unsafe_allow_html=True)

# =========================================================================
# 4. MÓDULO FICHA TÉCNICA (TOTALMENTE OTIMIZADO PARA DIGITAÇÃO PRÉ-GRAVAÇÃO)
# =========================================================================
def reset_ft_session():
    st.session_state.ft_id_carregada = None
    st.session_state.ft_items_ali = []
    st.session_state.ft_items_nao_ali = []
    st.session_state.ft_produto = "NOVO PRODUTO"
    st.session_state.ft_ref = "Produto Processado"
    st.session_state.ft_rend_crua = 21.900
    st.session_state.ft_rend_assada = 14.226
    st.session_state.ft_peso_unid = 0.118
    st.session_state.ft_qtd_pacote = 4.0
    st.session_state.ft_precif = {
        "imposto_pct": 5.0, "tx_cartao_pct": 5.0, "comissao_pct": 3.51,
        "outros_custos_var_pct": 1.0, "desp_fixas_pct": 2.0, "margem_lucro_pct": 31.6724,
        "desconto_simulado_pct": 0.0, "opcao_cer": "Custo/kg Total Depois de Assada"
    }

def render_modulo_ficha_tecnica():
    st.header("📋 Ficha Técnica & Precificação")
    emp_id_ativo = st.session_state.empresa_id

    st.subheader("🔍 Selecionar ou Buscar Ficha Técnica")
    col_s1, col_s2 = st.columns([3, 1])
    termo_busca = col_s1.text_input("Buscar por Nome do Produto", value="", key="input_termo_busca_ft")
    df_ft_db = carregar_fichas_tecnicas_db(emp_id_ativo, termo_busca)

    opcoes_fichas = ["➕ Criar Nova Ficha Técnica"]
    if not df_ft_db.empty:
        opcoes_fichas += [f"#{r['id']} - {r['produto']}" for _, r in df_ft_db.iterrows()]

    ficha_selecionada = col_s2.selectbox("Fichas Salvas", opcoes_fichas)

    if "ft_items_ali" not in st.session_state:
        reset_ft_session()

    if st.button("📥 Carregar Ficha Selecionada"):
        if ficha_selecionada == "➕ Criar Nova Ficha Técnica":
            reset_ft_session()
            st.success("Nova Ficha Técnica pronta para digitação!")
            st.rerun()
        else:
            ft_id = int(ficha_selecionada.split(" - ")[0].replace("#", ""))
            row_ft = df_ft_db[df_ft_db['id'] == ft_id].iloc[0]
            st.session_state.ft_id_carregada = ft_id
            st.session_state.ft_produto = str(row_ft['produto'])
            st.session_state.ft_ref = str(row_ft.get('referencia', 'Produto Processado'))
            st.session_state.ft_rend_crua = safe_float(row_ft.get('rendimento_kg'), 21.900)
            st.session_state.ft_rend_assada = safe_float(row_ft['rendimento_assada_kg'], 14.226)
            st.session_state.ft_peso_unid = safe_float(row_ft['peso_unidade_kg'], 0.118)
            st.session_state.ft_qtd_pacote = safe_float(row_ft['qtd_por_pacote'], 4.0)

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
            st.success(f"Ficha #{ft_id} ({row_ft['produto']}) carregada na memória!")
            st.rerun()

    st.markdown("---")
    
    # ISOLAMENTO DE DIGITAÇÃO DOS PARÂMETROS
    with st.form("form_dados_ficha_tecnica"):
        st.subheader("1. Digitação dos Parâmetros Gerais e Precificação")
        c1, c2 = st.columns(2)
        prod = c1.text_input("Nome do Produto", value=st.session_state.ft_produto)
        ref = c2.text_input("Referência", value=st.session_state.ft_ref)

        c3, c4, c5, c6 = st.columns(4)
        rcrua = c3.number_input("Rendimento Cru (kg)", min_value=0.001, value=safe_float(st.session_state.ft_rend_crua, 21.9), format="%.3f")
        rassada = c4.number_input("Rendimento Assado (kg)", min_value=0.001, value=safe_float(st.session_state.ft_rend_assada, 14.226), format="%.3f")
        punid = c5.number_input("Peso Unidade (kg)", min_value=0.001, value=safe_float(st.session_state.ft_peso_unid, 0.118), format="%.3f")
        qpacote = c6.number_input("Qtd no Pacote", min_value=1.0, value=safe_float(st.session_state.ft_qtd_pacote, 4.0))

        st.markdown("**Alíquotas de Precificação (%)**")
        prec_dict = st.session_state.ft_precif
        cp1, cp2, cp3, cp4, cp5, cp6 = st.columns(6)
        p_imp = cp1.number_input("Imposto %", value=safe_float(prec_dict.get("imposto_pct"), 5.0))
        p_cart = cp2.number_input("Cartão %", value=safe_float(prec_dict.get("tx_cartao_pct"), 5.0))
        p_com = cp3.number_input("Comissão %", value=safe_float(prec_dict.get("comissao_pct"), 3.51))
        p_outros = cp4.number_input("Outros Custos %", value=safe_float(prec_dict.get("outros_custos_var_pct"), 1.0))
        p_fixas = cp5.number_input("Desp. Fixas %", value=safe_float(prec_dict.get("desp_fixas_pct"), 2.0))
        p_lucro = cp6.number_input("Lucro %", value=safe_float(prec_dict.get("margem_lucro_pct"), 31.67))

        btn_confirmar_form = st.form_submit_button("⚡ Confirmar Alterações dos Parâmetros (Em Memória)")
        if btn_confirmar_form:
            st.session_state.ft_produto = prod
            st.session_state.ft_ref = ref
            st.session_state.ft_rend_crua = rcrua
            st.session_state.ft_rend_assada = rassada
            st.session_state.ft_peso_unid = punid
            st.session_state.ft_qtd_pacote = qpacote
            st.session_state.ft_precif = {
                "imposto_pct": p_imp, "tx_cartao_pct": p_cart, "comissao_pct": p_com,
                "outros_custos_var_pct": p_outros, "desp_fixas_pct": p_fixas, "margem_lucro_pct": p_lucro,
                "desconto_simulado_pct": 0.0, "opcao_cer": "Custo/kg Total Depois de Assada"
            }
            st.success("Parâmetros atualizados na memória temporária!")

    st.markdown("---")
    st.subheader("2. Edição de Insumos Alimentícios")
    df_ali_input = pd.DataFrame(st.session_state.ft_items_ali)
    if df_ali_input.empty:
        df_ali_input = pd.DataFrame([{"cod": "001", "produto": "COSTELA", "qtd_bruta": 21.0, "unidade": "KG", "preco_bruto": 24.90, "rendimento_pct": 100.0}])

    edited_ali_df = st.data_editor(df_ali_input, num_rows="dynamic", use_container_width=True, key="editor_batch_ali")

    st.subheader("3. Edição de Insumos Não Alimentícios")
    df_nao_ali_input = pd.DataFrame(st.session_state.ft_items_nao_ali)
    if df_nao_ali_input.empty:
        df_nao_ali_input = pd.DataFrame([{"cod": "101", "produto": "GAS", "qtd_bruta": 0.25, "unidade": "UNID", "preco_bruto": 130.00, "rendimento_pct": 100.0}])

    edited_nao_ali_df = st.data_editor(df_nao_ali_input, num_rows="dynamic", use_container_width=True, key="editor_batch_nao_ali")

    st.markdown("---")
    # BOTÃO FINAL DE GRAVAÇÃO NO BANCO DE DADOS
    if st.button("💾 GRAVAR FICHA TÉCNICA COMPLETA NO BANCO DE DADOS"):
        conn = get_connection()
        cursor = conn.cursor()
        is_postgres = "psycopg2" in str(type(conn))

        items_ali_list = edited_ali_df.to_dict("records")
        items_nao_ali_list = edited_nao_ali_df.to_dict("records")
        
        ins_ali_json_str = json.dumps(items_ali_list)
        ins_nao_ali_json_str = json.dumps(items_nao_ali_list)
        precif_json_str = json.dumps(st.session_state.ft_precif)
        data_hoje = str(datetime.date.today())

        unid_prod = math.floor(st.session_state.ft_rend_assada / st.session_state.ft_peso_unid) if st.session_state.ft_peso_unid > 0 else 0.0
        perda_pct = (1.0 - (st.session_state.ft_rend_assada / st.session_state.ft_rend_crua)) if st.session_state.ft_rend_crua > 0 else 0.0

        if st.session_state.ft_id_carregada is not None:
            if is_postgres:
                cursor.execute("""
                    UPDATE fichas_tecnicas SET
                        produto = %s, referencia = %s, rendimento_kg = %s, rendimento_assada_kg = %s,
                        peso_unidade_kg = %s, qtd_por_pacote = %s, unidades_produzidas = %s, perda_pct = %s,
                        insumos_ali_json = %s, insumos_nao_ali_json = %s, precificacao_json = %s
                    WHERE id = %s
                """, (st.session_state.ft_produto.upper(), st.session_state.ft_ref, st.session_state.ft_rend_crua, st.session_state.ft_rend_assada, st.session_state.ft_peso_unid, st.session_state.ft_qtd_pacote, unid_prod, perda_pct, ins_ali_json_str, ins_nao_ali_json_str, precif_json_str, st.session_state.ft_id_carregada))
            else:
                cursor.execute("""
                    UPDATE fichas_tecnicas SET
                        produto = ?, referencia = ?, rendimento_kg = ?, rendimento_assada_kg = ?,
                        peso_unidade_kg = ?, qtd_por_pacote = ?, unidades_produzidas = ?, perda_pct = ?,
                        insumos_ali_json = ?, insumos_nao_ali_json = ?, precificacao_json = ?
                    WHERE id = ?
                """, (st.session_state.ft_produto.upper(), st.session_state.ft_ref, st.session_state.ft_rend_crua, st.session_state.ft_rend_assada, st.session_state.ft_peso_unid, st.session_state.ft_qtd_pacote, unid_prod, perda_pct, ins_ali_json_str, ins_nao_ali_json_str, precif_json_str, st.session_state.ft_id_carregada))
        else:
            emp_v = emp_id_ativo if emp_id_ativo != 0 else None
            if is_postgres:
                cursor.execute("""
                    INSERT INTO fichas_tecnicas (
                        empresa_id, produto, referencia, rendimento_kg, rendimento_assada_kg,
                        peso_unidade_kg, qtd_por_pacote, unidades_produzidas, perda_pct,
                        insumos_ali_json, insumos_nao_ali_json, precificacao_json, data_criacao
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (emp_v, st.session_state.ft_produto.upper(), st.session_state.ft_ref, st.session_state.ft_rend_crua, st.session_state.ft_rend_assada, st.session_state.ft_peso_unid, st.session_state.ft_qtd_pacote, unid_prod, perda_pct, ins_ali_json_str, ins_nao_ali_json_str, precif_json_str, data_hoje))
            else:
                cursor.execute("""
                    INSERT INTO fichas_tecnicas (
                        empresa_id, produto, referencia, rendimento_kg, rendimento_assada_kg,
                        peso_unidade_kg, qtd_por_pacote, unidades_produzidas, perda_pct,
                        insumos_ali_json, insumos_nao_ali_json, precificacao_json, data_criacao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (emp_v, st.session_state.ft_produto.upper(), st.session_state.ft_ref, st.session_state.ft_rend_crua, st.session_state.ft_rend_assada, st.session_state.ft_peso_unid, st.session_state.ft_qtd_pacote, unid_prod, perda_pct, ins_ali_json_str, ins_nao_ali_json_str, precif_json_str, data_hoje))

        conn.commit()
        conn.close()
        st.cache_data.clear()
        st.success("🎉 Ficha Técnica e todos os insumos digitados foram gravados no banco de dados!")

# =========================================================================
# 5. MÓDULO NOVA DESOSSA (DIGITAÇÃO EM LOTE)
# =========================================================================
def render_modulo_nova_desossa():
    st.header("🥩 Lançar Nova Ação de Desossa (Digitação Completa pré-gravação)")
    emp_id_ativo = st.session_state.empresa_id
    tipos_empresa = get_tipos_desossa(emp_id_ativo)

    if not tipos_empresa:
        st.warning("Cadastre os seus 'Tipos de Desossa' primeiro.")
        return

    # Form de parâmetros do animal
    with st.form("form_parametros_desossa"):
        col1, col2, col3 = st.columns(3)
        data_input = col1.date_input("Data da Ação", datetime.date.today())
        tipo_animal = col2.selectbox("Tipo de Desossa", tipos_empresa)
        peso_bruto = col3.number_input("Peso Bruto (KG)", min_value=0.0, format="%.3f")

        col4, col5, col6 = st.columns(3)
        preco_animal_kg = col4.number_input("Preço Animal (R$/KG)", min_value=0.0)
        ossos_muxiba = col5.number_input("Ossos/Muxiba (KG)", min_value=0.0, format="%.3f")
        quebra = col6.number_input("Quebra Não Ident. (KG)", min_value=0.0, format="%.3f")

        btn_confirmar_carcaca = st.form_submit_button(" Confirmar Parâmetros da Carcaça (Em Memória)")
        if btn_confirmar_carcaca:
            st.session_state.desossa_temp = {
                "data": str(data_input), "tipo": tipo_animal, "peso_bruto": peso_bruto,
                "preco_animal_kg": preco_animal_kg, "ossos_muxiba": ossos_muxiba, "quebra": quebra
            }
            st.success("Dados da carcaça mantidos na memória!")

    st.markdown("---")
    st.subheader("Cortes da Desossa (Edição Direta na Tabela)")

    if "df_cortes_lote" not in st.session_state:
        st.session_state.df_cortes_lote = pd.DataFrame([
            {"nome_corte": "PICANHA", "qualidade": "OURO", "peso": 2.500, "preco_venda": 69.90},
            {"nome_corte": "ALCATRA", "qualidade": "OURO", "peso": 6.100, "preco_venda": 42.90}
        ])

    df_cortes_editados = st.data_editor(st.session_state.df_cortes_lote, num_rows="dynamic", use_container_width=True, key="editor_cortes_batch")

    st.markdown("---")
    if st.button("💾 FINALIZAR E GRAVAR DESOSSA COMPLETA NO BANCO DE DADOS"):
        info_carcaca = st.session_state.get("desossa_temp")
        if not info_carcaca:
            st.error("Preencha e confirme os parâmetros do animal primeiro!")
            return

        conn = get_connection()
        cursor = conn.cursor()
        is_postgres = "psycopg2" in str(type(conn))

        if is_postgres:
            cursor.execute("""
                INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (emp_id_ativo, info_carcaca["data"], info_carcaca["tipo"], info_carcaca["peso_bruto"], info_carcaca["preco_animal_kg"], info_carcaca["ossos_muxiba"], info_carcaca["quebra"]))
            acao_id = cursor.fetchone()[0]
        else:
            cursor.execute("""
                INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (emp_id_ativo, info_carcaca["data"], info_carcaca["tipo"], info_carcaca["peso_bruto"], info_carcaca["preco_animal_kg"], info_carcaca["ossos_muxiba"], info_carcaca["quebra"]))
            acao_id = cursor.lastrowid

        lista_cortes = []
        for _, r in df_cortes_editados.iterrows():
            if str(r.get("nome_corte", "")).strip() != "":
                lista_cortes.append((acao_id, str(r["nome_corte"]).upper(), str(r["qualidade"]).upper(), safe_float(r["peso"]), safe_float(r["preco_venda"])))

        if is_postgres:
            cursor.executemany("INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda) VALUES (%s, %s, %s, %s, %s)", lista_cortes)
        else:
            cursor.executemany("INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda) VALUES (?, ?, ?, ?, ?)", lista_cortes)

        conn.commit()
        conn.close()
        st.session_state.df_cortes_lote = pd.DataFrame(columns=["nome_corte", "qualidade", "peso", "preco_venda"])
        st.success(f"🎉 Desossa #{acao_id} e {len(lista_cortes)} cortes gravados com sucesso!")

# =========================================================================
# 6. MÓDULO CAPITAL DE GIRO (NCG - OTIMIZADO)
# =========================================================================
def render_modulo_ncg():
    st.header("📈 Capital de Giro (NCG) - Digitação e Gravação Em Lote")
    emp_id_ativo = st.session_state.empresa_id

    with st.form("form_ncg_completo"):
        st.subheader("1. Entradas Financeiras")
        c1, c2, c3 = st.columns(3)
        fat = c1.number_input("Faturamento Mensal (R$)", value=157399.10)
        cmv = c2.number_input("CMV Mensal (R$)", value=98409.78)
        receber = c3.number_input("Contas a Receber (R$)", value=1193.67)

        c4, c5, c6 = st.columns(3)
        estoque = c4.number_input("Estoque (R$)", value=18700.0)
        pagar = c5.number_input("Contas a Pagar (R$)", value=50971.32)
        caixa = c6.number_input("Caixa (R$)", value=0.0)

        st.subheader("2. Prazos Médios (Dias)")
        cp1, cp2, cp3 = st.columns(3)
        pme = cp1.number_input("Prazo Estoque (PME)", value=8.5)
        pmr = cp2.number_input("Prazo Recebimento (PMR)", value=1.0)
        pmp = cp3.number_input("Prazo Pagamento (PMP)", value=14.0)

        titulo_ncg = st.text_input("Título da Análise", value=f"Análise {datetime.date.today().strftime('%m/%Y')}")

        btn_gravar_ncg = st.form_submit_button("💾 CALCULAR E GRAVAR ANÁLISE NO BANCO")

        if btn_gravar_ncg:
            ciclo = pme + pmr - pmp
            cmv_diario = cmv / 30.0
            ncg_val = cmv_diario * ciclo

            dados_fin_j = json.dumps({'fat': fat, 'cmv': cmv, 'receber': receber, 'estoque': estoque, 'pagar': pagar, 'caixa': caixa})
            prazos_j = json.dumps({'pme_atual': pme, 'pme_prop': pme, 'pmr_atual': pmr, 'pmr_prop': pmr, 'pmp_atual': pmp, 'pmp_prop': pmp})
            calcs_j = json.dumps({'ciclo_atual': ciclo, 'ncg_atual': ncg_val})

            conn = get_connection()
            cursor = conn.cursor()
            is_postgres = "psycopg2" in str(type(conn))

            emp_v = emp_id_ativo if emp_id_ativo != 0 else None
            if is_postgres:
                cursor.execute("INSERT INTO ncg_registros (empresa_id, titulo, data_registro, dados_financeiros_json, prazos_json, calculos_json) VALUES (%s, %s, %s, %s, %s, %s)",
                               (emp_v, titulo_ncg, str(datetime.date.today()), dados_fin_j, prazos_j, calcs_j))
            else:
                cursor.execute("INSERT INTO ncg_registros (empresa_id, titulo, data_registro, dados_financeiros_json, prazos_json, calculos_json) VALUES (?, ?, ?, ?, ?, ?)",
                               (emp_v, titulo_ncg, str(datetime.date.today()), dados_fin_j, prazos_j, calcs_j))

            conn.commit()
            conn.close()
            st.success(f"Análise '{titulo_ncg}' gravada com sucesso! NCG Calculada: R$ {ncg_val:,.2f}")

# =========================================================================
# 7. MÓDULO CÁLCULO FINANCEIRO
# =========================================================================
def render_modulo_financeiro():
    st.header("🧮 Cálculo Financeiro e Amortização")

    with st.form("form_financeiro"):
        c1, c2 = st.columns(2)
        pv = c1.number_input("Valor Financiado (R$)", value=100000.0)
        prazo = c2.number_input("Prazo (Meses)", value=12)

        c3, c4 = st.columns(2)
        taxa = c3.number_input("Taxa de Juros Mensal (%)", value=1.5)
        sistema = c4.selectbox("Sistema", ["Tabela Price (Prestações Iguais)", "Tabela SAC (Amortização Constante)"])

        btn_calcular = st.form_submit_button("⚡ Gerar Tabela de Amortização")

        if btn_calcular:
            i_m = taxa / 100.0
            dados = []
            saldo = pv

            if "Price" in sistema:
                pmt = pv * (i_m * (1 + i_m)**prazo) / ((1 + i_m)**prazo - 1)
                for mes in range(1, prazo + 1):
                    juros = saldo * i_m
                    amort = pmt - juros
                    saldo -= amort
                    dados.append({"Mês": mes, "Prestação": pmt, "Juros": juros, "Amortização": amort, "Saldo Devedor": max(0.0, saldo)})
            else:
                amort = pv / prazo
                for mes in range(1, prazo + 1):
                    juros = saldo * i_m
                    pmt = amort + juros
                    saldo -= amort
                    dados.append({"Mês": mes, "Prestação": pmt, "Juros": juros, "Amortização": amort, "Saldo Devedor": max(0.0, saldo)})

            df_amort = pd.DataFrame(dados)
            st.dataframe(df_amort.style.format({"Prestação": "R$ {:.2f}", "Juros": "R$ {:.2f}", "Amortização": "R$ {:.2f}", "Saldo Devedor": "R$ {:.2f}"}), use_container_width=True)

# =========================================================================
# 8. TELA DE LOGIN E NAVEGAÇÃO PRINCIPAL
# =========================================================================
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""

if not st.session_state.logado:
    exibir_cabecalho()
    st.title("🔒 Portal de Acesso")

    with st.form("form_login"):
        campo_login = st.text_input("Usuário / Login")
        campo_senha = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Entrar")

        if btn_entrar:
            login_clean = campo_login.strip().lower()
            if login_clean == "admin" and campo_senha == "renato123":
                st.session_state.logado = True
                st.session_state.empresa_id = 0
                st.session_state.empresa_nome = "Administrador Geral"
                st.rerun()
            else:
                conn = get_connection()
                cursor = conn.cursor()
                is_postgres = "psycopg2" in str(type(conn))
                if is_postgres:
                    cursor.execute("SELECT id, nome FROM empresas WHERE LOWER(login) = %s AND senha = %s AND ativo = 1", (login_clean, campo_senha))
                else:
                    cursor.execute("SELECT id, nome FROM empresas WHERE LOWER(login) = ? AND senha = ? AND ativo = 1", (login_clean, campo_senha))
                user = cursor.fetchone()
                conn.close()

                if user:
                    st.session_state.logado = True
                    st.session_state.empresa_id = user[0]
                    st.session_state.empresa_nome = user[1]
                    st.rerun()
                else:
                    st.error("Login inválido!")
else:
    st.sidebar.markdown(f"**🏢 Empresa:** `{st.session_state.empresa_nome.upper()}`")
    if st.sidebar.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()

    menu = st.sidebar.radio("Navegação", ["Nova Desossa", "Ficha Técnica", "Capital de Giro (NCG)", "Cálculo Financeiro"])
    exibir_cabecalho(st.session_state.empresa_nome)

    if menu == "Nova Desossa":
        render_modulo_nova_desossa()
    elif menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()
    elif menu == "Capital de Giro (NCG)":
        render_modulo_ncg()
    elif menu == "Cálculo Financeiro":
        render_modulo_financeiro()