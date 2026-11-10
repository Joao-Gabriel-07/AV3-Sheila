import glob, os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import pysus

UFS = ["BA", "SP", "PA", "RS"]
YEARS = list(range(2015, 2023))

UF_COD = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
          "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
          "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
          "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
          "51": "MT", "52": "GO", "53": "DF"}
RACA = {"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indigena"}
BASE = os.path.expanduser("~/pysus")


def achar(nome):
    r = glob.glob(os.path.join(BASE, "**", nome), recursive=True)
    return r[0] if r else None


def ler(prefixo, uf, ano):
    nome = f"{prefixo}{uf}{ano}.parquet"
    if not achar(nome):
        fonte = pysus.sim if prefixo == "DO" else pysus.sinasc
        fonte(state=uf, year=ano)
    assert achar(nome), f"arquivo nao encontrado: {nome}"; df = pd.read_parquet(achar(nome))
    df.columns = [c.upper() for c in df.columns]
    return df


def prep(df, col_raca):
    df["UF"] = df["CODMUNRES"].astype(str).str[:2].map(UF_COD)
    df["RACA"] = df[col_raca].astype(str).str.strip().map(RACA).fillna("Ignorado")
    return df.dropna(subset=["UF"])


conn = psycopg2.connect(os.environ["DB_URI"])
cur = conn.cursor()

for uf in UFS:
    for ano in YEARS:
        ob = prep(ler("DO", uf, ano), "RACACOR")
        causa = ob["CAUSABAS"].astype(str).str[:3]
        ob = ob[causa.str.startswith("O") & ~causa.isin(["O96", "O97"])]
        agg_ob = ob.groupby(["UF", "RACA"]).size().reset_index(name="n")

        nv = prep(ler("DN", uf, ano), "RACACORMAE")
        nv["CES"] = (nv["PARTO"].astype(str).str.strip() == "2").astype(int)
        nv["PRE"] = nv["CONSULTAS"].astype(str).str.strip().isin(["1", "2", "3"]).astype(int)
        agg_nv = nv.groupby(["UF", "RACA"]).agg(
            n=("UF", "size"), ces=("CES", "sum"), pre=("PRE", "sum")).reset_index()

        for u in set(agg_ob["UF"]) | set(agg_nv["UF"]):
            cur.execute("DELETE FROM obitos_maternos_agg WHERE ano=%s AND uf=%s", (ano, u))
            cur.execute("DELETE FROM nascidos_vivos_agg WHERE ano=%s AND uf=%s", (ano, u))
        execute_values(cur,
            "INSERT INTO obitos_maternos_agg (ano, uf, raca_cor, obitos_maternos) VALUES %s",
            [(ano, r.UF, r.RACA, int(r.n)) for r in agg_ob.itertuples()])
        execute_values(cur,
            "INSERT INTO nascidos_vivos_agg (ano, uf, raca_cor, nascidos_vivos, partos_cesareos, prenatal_insuficiente) VALUES %s",
            [(ano, r.UF, r.RACA, int(r.n), int(r.ces), int(r.pre)) for r in agg_nv.itertuples()])
        conn.commit()
        print("carregado:", uf, ano)

cur.execute("SELECT * FROM indicadores ORDER BY ano, uf, raca_cor")
for linha in cur.fetchall():
    print(linha)
conn.close()
