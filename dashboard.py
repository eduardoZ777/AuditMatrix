import os
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure page metadata and wide layout
st.set_page_config(
    page_title="AuditMatrix - Error Analytics Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import app components inside functions or after page configuration
from app.config import settings
from app.repository import get_repository

# Custom premium styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Core fonts and background */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif;
        background-color: #0b0c10;
        color: #c5c6c7;
    }
    
    /* Header styling */
    [data-testid="stHeader"] {
        background-color: rgba(11, 12, 16, 0.8);
        backdrop-filter: blur(10px);
    }
    
    /* Text styling */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Custom Title Gradient */
    .title-gradient {
        background: linear-gradient(90deg, #66fcf1 0%, #45a29e 50%, #8a2be2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        text-shadow: 0 0 30px rgba(102, 252, 241, 0.1);
    }
    
    .subtitle-text {
        font-size: 1.1rem;
        color: #c5c6c7;
        margin-bottom: 2rem;
        opacity: 0.8;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(31, 40, 51, 0.45) 0%, rgba(11, 12, 16, 0.7) 100%);
        border: 1px solid rgba(102, 252, 241, 0.15);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        transition: all 0.3s ease-in-out;
    }
    
    .metric-card:hover {
        border-color: rgba(102, 252, 241, 0.4);
        box-shadow: 0 8px 32px 0 rgba(102, 252, 241, 0.1);
        transform: translateY(-2px);
    }
    
    .metric-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        color: #45a29e;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 4px;
    }
    
    .metric-subtitle {
        font-size: 0.8rem;
        color: #c5c6c7;
        opacity: 0.6;
    }
    
    /* Code blocks and logs */
    code, pre {
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Styled container blocks */
    .content-box {
        background-color: #1f2833;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #66fcf1;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Helper function to inject logs to sistema.log
def inject_sample_logs():
    os.makedirs("logs", exist_ok=True)
    sample_logs = [
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [ERROR] [ERPMain] [LoginController] - Password validation failed for user admin.",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Exception] [BillingService] [InvoiceGenerator] - Connection timeout connecting to Sefaz SE.",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [ERROR] [ERPMain] [DashboardView] - NullPointerException occurred while loading chart widgets.",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [ERROR] [InventoryApp] [StockManager] - IntegrityError: Duplicate entry for SKU-88493.",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Exception] [AuthService] [TokenValidator] - SignatureVerificationException: Signature is expired.",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [ERROR] [BillingService] [PaymentGateway] - HTTP 500: Gateway rejected payment transaction."
    ]
    
    # Write to sistema.log
    with open(settings.LOG_SOURCE_PATH, "a", encoding="utf-8") as f:
        for log in sample_logs:
            f.write(log + "\n")
            
    # Also write straight to repositories to instantly showcase UI if monitor isn't running
    repo = get_repository()
    from app.parser import ErrorParser
    parser = ErrorParser()
    for log in sample_logs:
        parsed = parser.parse_line(log)
        if parsed:
            repo.save(parsed)

# --- Title Header ---
st.markdown('<div class="title-gradient">AuditMatrix Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Monitoramento de Erros, Auditoria em Tempo Real & Métricas de Suporte</div>', unsafe_allow_html=True)

# --- Sidebar Controls ---
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/shield.png", width=90)
    st.markdown("### Configurações do Sistema")
    st.markdown(f"**Modo de Storage:** `{settings.AUDIT_STORAGE_MODE.upper()}`")
    st.markdown(f"**Log Origem:** `{os.path.basename(settings.LOG_SOURCE_PATH)}`")
    
    if settings.AUDIT_STORAGE_MODE.lower() in ("text", "both"):
        st.markdown(f"**Arquivo TXT:** `{os.path.basename(settings.AUDIT_TEXT_PATH)}`")
        
    st.markdown("---")
    
    st.markdown("### Ferramentas de Teste")
    st.write("Não tem logs gerados ainda? Clique abaixo para simular erros do ERP na hora.")
    if st.button("🚀 Injetar Erros de Exemplo", use_container_width=True):
        inject_sample_logs()
        st.success("Erros de teste gravados com sucesso!")
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    st.markdown("<small>AuditMatrix v0.1.0 • Desenvolvido por Antigravity</small>", unsafe_allow_html=True)

# --- Data Loading ---
repository = get_repository()
raw_entries = repository.get_all()

if not raw_entries:
    st.info("💡 **Nenhum log de erro foi auditado ainda.**")
    st.write(
        "Certifique-se de que o serviço `main.py` está rodando em segundo plano e monitorando "
        "o arquivo configurado. Ou clique em **Injetar Erros de Exemplo** no menu lateral "
        "para ver o painel funcionar imediatamente."
    )
    
    # Showcase empty dashboard state nicely
    st.stop()

# Convert Pydantic schemas to Pandas DataFrame
df = pd.DataFrame([entry.model_dump() for entry in raw_entries])
df["timestamp"] = pd.to_datetime(df["timestamp"])

# --- Key Metrics Cards ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total de Ocorrências</div>
        <div class="metric-value">{len(df)}</div>
        <div class="metric-subtitle">Erros auditados e limpos</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    distinct_programs = df["nome_programa"].nunique()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Programas Afetados</div>
        <div class="metric-value">{distinct_programs}</div>
        <div class="metric-subtitle">Aplicações com falhas ativas</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    distinct_modules = df["modulo_sistema"].nunique()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Telas/Módulos Impactados</div>
        <div class="metric-value">{distinct_modules}</div>
        <div class="metric-subtitle">Áreas do ERP com exceções</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    most_common_program = df["nome_programa"].mode()[0] if not df.empty else "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Principal Ofensor</div>
        <div class="metric-value" style="font-size: 1.6rem; line-height: 2.2rem; color: #ff5252;">{most_common_program}</div>
        <div class="metric-subtitle">Programa com mais falhas</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Charts Section ---
char_col1, char_col2 = st.columns(2)

with char_col1:
    st.markdown("### 📊 Erros por Programa")
    program_counts = df["nome_programa"].value_counts().reset_index()
    program_counts.columns = ["Programa", "Erros"]
    
    fig_prog = px.bar(
        program_counts,
        x="Erros",
        y="Programa",
        orientation="h",
        color="Erros",
        color_continuous_scale=["#1f2833", "#45a29e", "#66fcf1"],
        template="plotly_dark"
    )
    fig_prog.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_prog, use_container_width=True)

with char_col2:
    st.markdown("### 📈 Histórico de Incidentes")
    # Group errors by hour
    df_timeline = df.set_index("timestamp").resample("h").size().reset_index()
    df_timeline.columns = ["Horário", "Quantidade"]
    
    fig_time = px.line(
        df_timeline,
        x="Horário",
        y="Quantidade",
        template="plotly_dark",
        markers=True
    )
    fig_time.update_traces(
        line_color="#66fcf1",
        line_width=3,
        marker=dict(size=8, color="#8a2be2")
    )
    fig_time.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    )
    st.plotly_chart(fig_time, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Error Explorer Section ---
st.markdown("### 🔎 Auditoria de Exceções (Logs Consolidados)")

# Filter interface
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    search_query = st.text_input("Buscar na mensagem do erro", "")
with f_col2:
    prog_options = ["Todos"] + sorted(df["nome_programa"].unique().tolist())
    selected_prog = st.selectbox("Filtrar por Programa", prog_options)
with f_col3:
    mod_options = ["Todos"] + sorted(df["modulo_sistema"].unique().tolist())
    selected_mod = st.selectbox("Filtrar por Módulo/Tela", mod_options)

# Filter Dataframe
filtered_df = df.copy()
if search_query:
    filtered_df = filtered_df[filtered_df["mensagem_erro"].str.contains(search_query, case=False, na=False)]
if selected_prog != "Todos":
    filtered_df = filtered_df[filtered_df["nome_programa"] == selected_prog]
if selected_mod != "Todos":
    filtered_df = filtered_df[filtered_df["modulo_sistema"] == selected_mod]

# Sort by newest
filtered_df = filtered_df.sort_values(by="timestamp", ascending=False)

# Display formatted table
display_df = filtered_df.copy()
display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
display_df.columns = ["Data/Hora", "Level", "Programa", "Módulo/Tela", "Mensagem de Erro"]

st.dataframe(
    display_df,
    use_container_width=True,
    column_config={
        "Data/Hora": st.column_config.TextColumn("Data/Hora", width="medium"),
        "Level": st.column_config.TextColumn("Level", width="small"),
        "Programa": st.column_config.TextColumn("Programa", width="medium"),
        "Módulo/Tela": st.column_config.TextColumn("Módulo/Tela", width="medium"),
        "Mensagem de Erro": st.column_config.TextColumn("Mensagem de Erro", width="large"),
    },
    hide_index=True
)

st.markdown("<br>", unsafe_allow_html=True)

# --- Raw Audit File Output ---
if settings.AUDIT_STORAGE_MODE.lower() in ("text", "both"):
    with st.expander("📄 Visualizar Arquivo de Auditoria Local (auditoria.txt)"):
        st.markdown(
            "Este é o conteúdo exato gravado em tempo real no arquivo local do servidor:"
        )
        if os.path.exists(settings.AUDIT_TEXT_PATH):
            try:
                with open(settings.AUDIT_TEXT_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                st.code(content, language="text")
            except Exception as e:
                st.error(f"Erro ao ler arquivo de auditoria: {e}")
        else:
            st.warning("O arquivo de auditoria física ainda não foi gerado.")
