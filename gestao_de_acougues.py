import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
import numpy as np
from scipy.optimize import brentq
from fpdf import FPDF

# =========================================================================
# 1. CONFIGURAÇÃO VISUAL E ESTILIZAÇÃO DA INTERFACE (UI/UX)
# =========================================================================
# Define o título da página no navegador e ativa o modo largo (wide)
st.set_page_config(page_title="Gestão de Açougues - Renato Frigotudo & Associados", layout="wide")

# Injeção de CSS personalizado para padronizar cores, botões e campos de entrada
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
# 2. CONEXÃO E INICIALIZAÇÃO DA BASE DE DADOS HÍBRIDA
# =========================================================================
def get_connection():
    """
    Verifica se a aplicação está a rodar na nuvem com Supabase (DB_URL)
    ou se deve conectar ao SQLite local.
    """
    if "DB_URL" in st.secrets:
        import psycopg2
        url = st.secrets["DB_URL"]
        if "?" in url:
            url = url.split("?")[0]
        return psycopg2.connect(url)
    else:
        return sqlite3.connect("desossa_db.db")

def init_db():
    """Cria as tabelas necessárias no banco de dados caso ainda não existam."""
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
            CREATE TABLE IF NOT EXISTS insumos_ficha (
                id SERIAL PRIMARY KEY,
                ficha_id INTEGER,
                codigo TEXT,
                produto_insumo TEXT NOT NULL,
                qtd_bruta REAL DEFAULT 0.0,
                unidade TEXT,
                preco_bruto REAL DEFAULT 0.0,
                rendimento REAL DEFAULT 100.0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumos_nao_alimenticios_ficha (
                id SERIAL PRIMARY KEY,
                ficha_id INTEGER,
                codigo TEXT,
                produto_insumo TEXT NOT NULL,
                qtd_bruta REAL DEFAULT 0.0,
                unidade TEXT,
                preco_bruto REAL DEFAULT 0.0,
                rendimento REAL DEFAULT 100.0
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
            CREATE TABLE IF NOT EXISTS insumos_ficha (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ficha_id INTEGER,
                codigo TEXT,
                produto_insumo TEXT NOT NULL,
                qtd_bruta REAL DEFAULT 0.0,
                unidade TEXT,
                preco_bruto REAL DEFAULT 0.0,
                rendimento REAL DEFAULT 100.0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumos_nao_alimenticios_ficha (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ficha_id INTEGER,
                codigo TEXT,
                produto_insumo TEXT NOT NULL,
                qtd_bruta REAL DEFAULT 0.0,
                unidade TEXT,
                preco_bruto REAL DEFAULT 0.0,
                rendimento REAL DEFAULT 100.0
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
    
    # Inserção de dados padrão de desossa na primeira inicialização
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

# Executa a inicialização do banco de dados
init_db()

def get_tipos_desossa(empresa_id):
    """Busca no banco os tipos de desossa cadastrados para a empresa ativa."""
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
# 3. GERENCIAMENTO DE ESTADO DA SESSÃO
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
# 4. ELEMENTOS DE CABEÇALHO E VISUAIS
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
# 5. MÓDULOS DE CÁLCULO
# =========================================================================

def render_modulo_financeiro():
    """Módulo de Simulação de Financiamentos (Tabela Price e SAC)."""
    st.header("🧮 Módulo de Cálculo Financeiro & Amortização")
    st.write("Simule financiamentos e veja o cronograma de pagamentos.")
    
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
            if i > 0:
                pmt = pv * (i * (1 + i)**n) / ((1 + i)**n - 1)
            else:
                pmt = pv / n
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
    """Módulo para Cadastro e Consulta de Fichas Técnicas."""
    st.header("📋 Módulo de Ficha Técnica & Precificação")
    emp_id_ativo = st.session_state.empresa_id
    
    with st.form("form_nova_ficha"):
        st.subheader("Cadastrar Nova Ficha Técnica")
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
    """Módulo de Análise e Cálculo de Necessidade de Capital de Giro."""
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
# 6. AUTENTICAÇÃO E SESSÃO DO UTILIZADOR
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
    # Barra lateral de navegação quando o utilizador está autenticado
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
    # 7. EXECUÇÃO DAS PÁGINAS SELECIONADAS NO MENU
    # =========================================================================
    if menu == "Cálculo Financeiro":
        render_modulo_financeiro()
    elif menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()
    elif menu == "Capital de Giro (NCG)":
        render_modulo_ncg()
    elif menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Configurar e Gerenciar Tipos de Desossa e Cortes")
        emp_id_ativo = st.session_state.empresa_id
        tipos_disponiveis = get_tipos_desossa(emp_id_ativo)
        if tipos_disponiveis:
            tipo_sel = st.selectbox("Selecione o Tipo de Desossa", tipos_disponiveis, key="tipo_sel_cortes")
            conn = get_connection()
            is_postgres = "psycopg2" in str(type(conn))
            if st.session_state.e_admin:
                df_padroes = pd.read_sql_query(f"SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND empresa_id IS NULL ORDER BY nome_corte ASC", conn)
            else:
                if is_postgres:
                    df_padroes = pd.read_sql_query("SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = %s AND empresa_id = %s ORDER BY nome_corte ASC", conn, params=(tipo_sel, emp_id_ativo))
                else:
                    df_padroes = pd.read_sql_query("SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = ? AND empresa_id = ? ORDER BY nome_corte ASC", conn, params=(tipo_sel, emp_id_ativo))
            conn.close()
            st.dataframe(df_padroes, use_container_width=True)
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
                    
                    if st.form_submit_button("➕ Adicionar Corte") and nome_corte != "":
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
                        st.write(f"• **{c['nome_corte']}** ({c['qualidade']}) - {c['peso']:.3f} KG - R$ {c['preco_venda']:.2f}/KG")

                if st.button("💾 Salvar Ação no Banco de Dados em Nuvem", key=f"btn_salvar_db_{v_form}"):
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
                        st.success("🎉 Lote salvo com sucesso na nuvem!")
                        reset_form_states()
                        st.rerun()

        elif menu == "Histórico & Edição":
            st.header("📂 Histórico & Edição de Desossas")
            conn = get_connection()
            is_postgres = "psycopg2" in str(type(conn))
            if is_postgres:
                df_acoes = pd.read_sql_query("SELECT * FROM acoes WHERE empresa_id = %s ORDER BY data_acao DESC", conn, params=(emp_id_ativo,))
            else:
                df_acoes = pd.read_sql_query(f"SELECT * FROM acoes WHERE empresa_id = {emp_id_ativo} ORDER BY data_acao DESC", conn)
            conn.close()
            
            if df_acoes.empty:
                st.warning("Nenhuma desossa cadastrada.")
            else:
                st.dataframe(df_acoes, use_container_width=True)