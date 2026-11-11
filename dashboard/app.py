import os
import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

st.set_page_config(page_title="Mortalidade Materna e Desigualdade Racial", layout="wide")

ORDEM = ["Branca", "Preta", "Parda", "Amarela", "Indigena", "Ignorado"]


def get_uri():
    try:
        return st.secrets["DB_URI"]
    except Exception:
        return os.environ["DB_URI"]


@st.cache_data(ttl=600)
def carregar():
    conn = psycopg2.connect(get_uri())
    cur = conn.cursor()
    cur.execute("""
        SELECT n.ano, n.uf, n.raca_cor, COALESCE(o.obitos_maternos, 0),
               n.nascidos_vivos, n.partos_cesareos, n.prenatal_insuficiente
        FROM nascidos_vivos_agg n
        LEFT JOIN obitos_maternos_agg o USING (ano, uf, raca_cor)
    """)
    df = pd.DataFrame(cur.fetchall(), columns=[
        "ano", "uf", "raca_cor", "obitos", "nascidos", "cesareos", "prenatal_insuf"])
    conn.close()
    return df


def agrega(df, by):
    g = df.groupby(by, as_index=False)[["obitos", "nascidos", "cesareos", "prenatal_insuf"]].sum()
    g["razao"] = (g["obitos"] * 100000 / g["nascidos"]).round(2)
    g["pct_cesarea"] = (g["cesareos"] * 100 / g["nascidos"]).round(2)
    g["pct_prenatal"] = (g["prenatal_insuf"] * 100 / g["nascidos"]).round(2)
    return g


df = carregar()

st.title("Mortalidade materna e desigualdade racial no Brasil")
st.caption("Fonte: SIM e SINASC (Ministério da Saúde). 2022 é preliminar no SIM. "
           "Violência obstétrica não é medida diretamente: cesárea e pré-natal insuficiente são indicadores indiretos.")

st.sidebar.header("Filtros")
ufs = st.sidebar.multiselect("UF", sorted(df["uf"].unique()), default=sorted(df["uf"].unique()))
anos = st.sidebar.slider("Período", int(df["ano"].min()), int(df["ano"].max()),
                         (int(df["ano"].min()), int(df["ano"].max())))
racas = st.sidebar.multiselect("Raça/cor da mãe", [r for r in ORDEM if r != "Ignorado"], default=[r for r in ORDEM if r != "Ignorado"])

f = df[df["uf"].isin(ufs) & df["ano"].between(*anos) & df["raca_cor"].isin(racas)]
if f.empty:
    st.warning("Nenhum dado para os filtros escolhidos.")
    st.stop()

tot = agrega(f.assign(g="t"), "g").iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Óbitos maternos", f"{int(tot['obitos']):,}".replace(",", "."))
c2.metric("Nascidos vivos", f"{int(tot['nascidos']):,}".replace(",", "."))
c3.metric("Razão geral (por 100 mil NV)", f"{tot['razao']:.1f}")
base = df[df["uf"].isin(ufs) & df["ano"].between(*anos)]; ign = base[base["raca_cor"] == "Ignorado"]["nascidos"].sum() * 100 / base["nascidos"].sum()
c4.metric("Raça/cor ignorada (%)", f"{ign:.1f}")

por_raca = agrega(f, "raca_cor")
por_raca["raca_cor"] = pd.Categorical(por_raca["raca_cor"], ORDEM, ordered=True)
por_raca = por_raca.sort_values("raca_cor")

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Razão de mortalidade materna por raça/cor")
    st.plotly_chart(px.bar(por_raca[por_raca["raca_cor"] != "Ignorado"], x="raca_cor", y="razao", text="obitos",
                           labels={"razao": "Óbitos por 100 mil NV", "raca_cor": "Raça/cor"}),
                    width="stretch")
    st.caption("O número sobre cada barra é o total de óbitos. Com poucos óbitos, a razão oscila muito. A categoria Ignorado não aparece aqui porque sua razão é instável.")
with col2:
    st.subheader("2. Evolução anual da razão")
    evo = agrega(f, ["ano", "raca_cor"])
    st.plotly_chart(px.line(evo[evo["raca_cor"] != "Ignorado"], x="ano", y="razao", color="raca_cor", markers=True,
                            category_orders={"raca_cor": ORDEM},
                            labels={"razao": "Óbitos por 100 mil NV", "ano": "Ano"}),
                    width="stretch")

col3, col4 = st.columns(2)
with col3:
    st.subheader("3. Partos cesáreos (%) por raça/cor")
    st.plotly_chart(px.bar(por_raca, x="raca_cor", y="pct_cesarea",
                           labels={"pct_cesarea": "% de cesáreas", "raca_cor": "Raça/cor"}),
                    width="stretch")
with col4:
    st.subheader("4. Pré-natal insuficiente (%) por raça/cor")
    st.plotly_chart(px.bar(por_raca, x="raca_cor", y="pct_prenatal",
                           labels={"pct_prenatal": "% com menos de 7 consultas", "raca_cor": "Raça/cor"}),
                    width="stretch")
    st.caption("Considera menos de 7 consultas (faixas 1 a 3 do SINASC).")

st.subheader("Dados por UF")
st.dataframe(agrega(f, ["uf", "raca_cor"]), width="stretch")


