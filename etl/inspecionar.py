import pysus

obitos = pysus.ftp.sim(state="BA", year=2021)
nasc = pysus.ftp.sinasc(state="BA", year=2021)

for nome, r in [("SIM", obitos), ("SINASC", nasc)]:
    print(nome, type(r))
    if isinstance(r, list):
        print("itens:", len(r), [type(x).__name__ for x in r])
        for x in r:
            if hasattr(x, "shape"):
                print(x.shape, list(x.columns)[:15])
    elif hasattr(r, "shape"):
        print(r.shape, list(r.columns)[:15])
