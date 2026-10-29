import yfinance as yf
import pandas as pd
import ta
import streamlit as st

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
h1, h2, h3 {
    text-align: center;
}
table {
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LISTAS
# =========================

acoes = [
    "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "SANB4.SA", "BPAC11.SA", "B3SA3.SA", "PSSA3.SA",
    "VALE3.SA", "GOAU4.SA", "GGBR4.SA", "CMIN3.SA",
    "ABEV3.SA", "LREN3.SA", "VIVA3.SA", "GRND3.SA",
    "EZTC3.SA", "CURY3.SA",
    "TOTS3.SA", "ODPV3.SA", "ITSA4.SA", "WEGE3.SA",
    "BBSE3.SA", "CXSE3.SA", "MDIA3.SA", "SBSP3.SA"
]

fiis = [
    "KNCR11.SA",
    "BTLG11.SA",
    "HGRU11.SA",
    "HGLG11.SA",
    "ALZR11.SA",
    "BRCO11.SA",
    "KNRI11.SA",
    "MXRF11.SA",
    "XPML11.SA",
    "VISC11.SA"
]

btc = ["BTC-USD"]

# =========================
# FUNÇÃO IFR
# =========================

def calcular_ifr(ticker):
    try:
        df = yf.download(ticker, period="5y", interval="1wk", auto_adjust=True, progress=False)

        if df.empty or len(df) < 20:
            return None, None, None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()

        atual = df['rsi'].iloc[-1]
        minimo = df['rsi'].min()
        maximo = df['rsi'].max()

        return round(atual, 1), round(minimo, 1), round(maximo, 1)

    except:
        return None, None, None

# =========================
# TERMÔMETRO
# =========================

def classificar_termometro(atual, minimo, maximo):
    if None in [atual, minimo, maximo]:
        return None

    intervalo = maximo - minimo
    passo = intervalo / 7

    if atual <= minimo + passo:
        return "compra insana"
    elif atual <= minimo + 2*passo:
        return "compra boa"
    elif atual <= minimo + 3*passo:
        return "normal"
    elif atual <= minimo + 4*passo:
        return "normal"
    elif atual <= minimo + 5*passo:
        return "normal"
    elif atual <= minimo + 6*passo:
        return "venda boa"
    else:
        return "venda insana"

# =========================
# GERAR TABELA
# =========================

def gerar_tabela(lista, tipo="acao"):
    dados = []

    for ativo in lista:
        ifr, minimo, maximo = calcular_ifr(ativo)

        nome = ativo.replace(".SA", "").replace("-USD", "")

        if tipo == "btc":
            link_tv = "https://www.tradingview.com/chart/?symbol=BTCUSD"
        else:
            link_tv = f"https://www.tradingview.com/chart/?symbol=BMFBOVESPA:{nome}"

        termometro = classificar_termometro(ifr, minimo, maximo)

        if tipo == "acao":
            link_fund = f"https://www.analisedeacoes.com/acoes/{nome.lower()}/"

            dados.append({
                "Ativo": f'<a href="{link_tv}" target="_blank">{nome}</a>',
                "IFR 14": ifr,
                "Termômetro": termometro,
                "Min 5 anos": minimo,
                "📊": f'<a href="{link_fund}" target="_blank">📊</a>'
            })

        else:
            dados.append({
                "Ativo": f'<a href="{link_tv}" target="_blank">{nome}</a>',
                "IFR 14": ifr,
                "Termômetro": termometro,
                "Min 5 anos": minimo
            })

    df = pd.DataFrame(dados)
    df = df.dropna()
    df = df.sort_values(by="IFR 14")

    # FORMATAÇÃO
    df["IFR 14"] = df["IFR 14"].map(lambda x: f"{x:.1f}")
    df["Min 5 anos"] = df["Min 5 anos"].map(lambda x: f"{x:.1f}")

    return df

# =========================
# CORES
# =========================

def color_ifr(val):
    val = float(val)
    if val < 30:
        return 'color: green'
    elif val < 40:
        return 'color: lightgreen'
    elif val < 60:
        return 'color: white'
    else:
        return 'color: red'

def color_termometro(val):
    if val in ["compra insana", "compra boa"]:
        return 'color: green; font-weight: bold'
    elif val in ["venda insana", "venda boa"]:
        return 'color: red; font-weight: bold'
    else:
        return 'color: white'

# =========================
# INTERFACE
# =========================

st.title("📊 Monitor de Mercado")

# AÇÕES
st.subheader("Ações")
df_acoes = gerar_tabela(acoes, tipo="acao")
styled_acoes = df_acoes.style.map(color_ifr, subset=["IFR 14"]) \
                              .map(color_termometro, subset=["Termômetro"])
st.markdown(styled_acoes.to_html(escape=False), unsafe_allow_html=True)

# FIIs
st.subheader("FIIs")
df_fiis = gerar_tabela(fiis, tipo="fii")
styled_fiis = df_fiis.style.map(color_ifr, subset=["IFR 14"]) \
                            .map(color_termometro, subset=["Termômetro"])
st.markdown(styled_fiis.to_html(escape=False), unsafe_allow_html=True)

# BTC
st.subheader("Bitcoin")
df_btc = gerar_tabela(btc, tipo="btc")
styled_btc = df_btc.style.map(color_ifr, subset=["IFR 14"]) \
                          .map(color_termometro, subset=["Termômetro"])
st.markdown(styled_btc.to_html(escape=False), unsafe_allow_html=True)
