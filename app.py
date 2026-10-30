import yfinance as yf
import pandas as pd
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
    "WEGE3.SA",
    "ITUB4.SA",
    "TOTS3.SA",
    "BPAC11.SA",
    "BBSE3.SA",
    "CXSE3.SA",
    "PSSA3.SA",
    "ABEV3.SA",
    "B3SA3.SA",
    "RADL3.SA",
    "VIVA3.SA",
    "CURY3.SA",
    "TIMS3.SA",
    "MULT3.SA",
    "ITSA4.SA",
    "SBSP3.SA",
    "LREN3.SA",
    "VALE3.SA",
    "GGBR4.SA",
    "EZTC3.SA",
    "BBDC4.SA",
    "GOAU4.SA",
    "SANB4.SA",
    "MDIA3.SA",
    "GRND3.SA",
    "CMIN3.SA",
    "BBAS3.SA"
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
# CÁLCULO IFR 14 SEMANAL
# =========================

def calcular_rsi_wilder(fechamentos, janela=14):
    """
    Calcula o RSI pelo método de Wilder, com média inicial simples
    dos primeiros 14 ganhos/perdas. Essa inicialização é mais próxima
    da usada pelo RSI padrão do TradingView do que o EWM padrão da
    biblioteca ta.
    """
    close = pd.to_numeric(fechamentos, errors="coerce").dropna().astype(float)
    delta = close.diff()

    ganhos = delta.clip(lower=0)
    perdas = -delta.clip(upper=0)

    rsi = pd.Series(float("nan"), index=close.index, dtype=float)
    if len(close) <= janela:
        return rsi

    # Wilder: inicializa com a média simples dos primeiros 14 movimentos
    media_ganhos = ganhos.iloc[1:janela + 1].mean()
    media_perdas = perdas.iloc[1:janela + 1].mean()

    def valor_rsi(g, p):
        if p == 0:
            return 100.0 if g > 0 else 50.0
        rs = g / p
        return 100.0 - (100.0 / (1.0 + rs))

    rsi.iloc[janela] = valor_rsi(media_ganhos, media_perdas)

    for i in range(janela + 1, len(close)):
        media_ganhos = ((media_ganhos * (janela - 1)) + ganhos.iloc[i]) / janela
        media_perdas = ((media_perdas * (janela - 1)) + perdas.iloc[i]) / janela
        rsi.iloc[i] = valor_rsi(media_ganhos, media_perdas)

    return rsi

def calcular_ifr(ticker):
    try:
        # Baixa o histórico semanal mais longo possível para aquecer o RSI
        # e depois mede mínimo/máximo apenas dentro dos últimos cinco anos.
        # auto_adjust=False usa o fechamento "Close", sem ajuste por dividendos.
        df = yf.download(
            ticker,
            period="max",
            interval="1wk",
            auto_adjust=False,
            progress=False,
            actions=False
        )

        if df.empty:
            return None, None, None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if "Close" not in df.columns:
            return None, None, None

        df = df[["Close"]].dropna()
        df["rsi"] = calcular_rsi_wilder(df["Close"], janela=14)
        df = df.dropna(subset=["rsi"])

        if df.empty:
            return None, None, None

        data_limite = pd.Timestamp.now().normalize() - pd.DateOffset(years=5)
        janela_5_anos = df.loc[df.index >= data_limite]

        if janela_5_anos.empty:
            return None, None, None

        atual = df["rsi"].iloc[-1]
        minimo = janela_5_anos["rsi"].min()
        maximo = janela_5_anos["rsi"].max()

        return round(float(atual), 2), round(float(minimo), 2), round(float(maximo), 2)

    except Exception as erro:
        print(f"Erro ao calcular IFR de {ticker}: {erro}")
        return None, None, None

# =========================
# TERMÔMETRO
# =========================

def classificar_termometro(atual, minimo, maximo):
    if any(valor is None for valor in [atual, minimo, maximo]):
        return None

    intervalo = maximo - minimo
    if intervalo <= 0:
        return "normal"

    passo = intervalo / 7

    if atual <= minimo + passo:
        return "compra insana"
    elif atual <= minimo + 2 * passo:
        return "compra boa"
    elif atual <= minimo + 5 * passo:
        return "normal"
    elif atual <= minimo + 6 * passo:
        return "venda boa"
    else:
        return "venda insana"

# =========================
# GERAR TABELA
# =========================

def gerar_tabela(lista, tipo="acao"):
    dados = []

    for posicao, ativo in enumerate(lista, start=1):
        ifr, minimo, maximo = calcular_ifr(ativo)
        nome = ativo.replace(".SA", "").replace("-USD", "")

        if tipo == "btc":
            link_tv = "https://www.tradingview.com/chart/?symbol=BTCUSD"
        else:
            link_tv = f"https://www.tradingview.com/chart/?symbol=BMFBOVESPA:{nome}"

        termometro = classificar_termometro(ifr, minimo, maximo)

        linha = {
            "Nº": posicao,
            "Ativo": f'<a href="{link_tv}" target="_blank">{nome}</a>',
            "IFR 14": ifr,
            "Termômetro": termometro,
            "Min 5 anos": minimo
        }

        if tipo == "acao":
            link_fund = f"https://www.analisedeacoes.com/acoes/{nome.lower()}/"
            linha["📊"] = f'<a href="{link_fund}" target="_blank">📊</a>'

        dados.append(linha)

    df = pd.DataFrame(dados)
    df = df.dropna(subset=["IFR 14", "Min 5 anos", "Termômetro"])
    df = df.sort_values(by="IFR 14", ascending=True)

    # Mostra duas casas decimais para facilitar a comparação com o TradingView.
    df["IFR 14"] = df["IFR 14"].map(lambda x: f"{x:.2f}")
    df["Min 5 anos"] = df["Min 5 anos"].map(lambda x: f"{x:.2f}")

    return df

# =========================
# CORES
# =========================

def color_ifr(val):
    val = float(val)
    if val < 30:
        return "color: green"
    elif val < 40:
        return "color: lightgreen"
    elif val < 60:
        return "color: white"
    else:
        return "color: red"

def color_termometro(val):
    if val in ["compra insana", "compra boa"]:
        return "color: green; font-weight: bold"
    elif val in ["venda insana", "venda boa"]:
        return "color: red; font-weight: bold"
    else:
        return "color: white"

# =========================
# INTERFACE
# =========================

st.title("📊 Monitor de Mercado")

# AÇÕES
st.subheader("Ações")
df_acoes = gerar_tabela(acoes, tipo="acao")
styled_acoes = df_acoes.style.map(color_ifr, subset=["IFR 14"]) \
                              .map(color_termometro, subset=["Termômetro"])
st.markdown(styled_acoes.hide(axis="index").to_html(escape=False), unsafe_allow_html=True)

# FIIs
st.subheader("FIIs")
df_fiis = gerar_tabela(fiis, tipo="fii")
styled_fiis = df_fiis.style.map(color_ifr, subset=["IFR 14"]) \
                            .map(color_termometro, subset=["Termômetro"])
st.markdown(styled_fiis.hide(axis="index").to_html(escape=False), unsafe_allow_html=True)

# BTC
st.subheader("Bitcoin")
df_btc = gerar_tabela(btc, tipo="btc")
styled_btc = df_btc.style.map(color_ifr, subset=["IFR 14"]) \
                          .map(color_termometro, subset=["Termômetro"])
st.markdown(styled_btc.hide(axis="index").to_html(escape=False), unsafe_allow_html=True)
