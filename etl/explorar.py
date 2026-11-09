import glob, os
import pandas as pd

pd.set_option("display.max_columns", None)
base = os.path.expanduser("~/pysus")

def achar(nome):
    r = glob.glob(os.path.join(base, "**", nome), recursive=True)
    return r[0]

obitos = pd.read_parquet(achar("DOBA2021.parquet"))
nasc = pd.read_parquet(achar("DNBA2021.parquet"))
obitos.columns = [c.upper() for c in obitos.columns]
nasc.columns = [c.upper() for c in nasc.columns]

print("SIM linhas:", len(obitos))
print("SINASC linhas:", len(nasc))

for c in ["DTOBITO", "CAUSABAS", "OBITOGRAV", "OBITOPUERP", "RACACOR", "CODMUNRES"]:
    print("SIM", c, c in obitos.columns)
for c in ["DTNASC", "RACACORMAE", "PARTO", "CONSULTAS", "CODMUNRES"]:
    print("SINASC", c, c in nasc.columns)

for nome, df, col in [("RACACOR (SIM)", obitos, "RACACOR"),
                      ("RACACORMAE (SINASC)", nasc, "RACACORMAE"),
                      ("PARTO", nasc, "PARTO"),
                      ("CONSULTAS", nasc, "CONSULTAS")]:
    if col in df.columns:
        print("\n" + nome)
        print(df[col].value_counts(dropna=False))

if "CAUSABAS" in obitos.columns:
    print("\nObitos com causa basica do capitulo O:",
          obitos["CAUSABAS"].astype(str).str.startswith("O").sum())
