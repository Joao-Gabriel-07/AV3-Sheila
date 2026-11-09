CREATE TABLE IF NOT EXISTS obitos_maternos_agg (
    ano SMALLINT NOT NULL,
    uf CHAR(2) NOT NULL,
    raca_cor VARCHAR(20) NOT NULL,
    obitos_maternos INTEGER NOT NULL,
    PRIMARY KEY (ano, uf, raca_cor)
);

CREATE TABLE IF NOT EXISTS nascidos_vivos_agg (
    ano SMALLINT NOT NULL,
    uf CHAR(2) NOT NULL,
    raca_cor VARCHAR(20) NOT NULL,
    nascidos_vivos INTEGER NOT NULL,
    partos_cesareos INTEGER NOT NULL,
    prenatal_insuficiente INTEGER NOT NULL,
    PRIMARY KEY (ano, uf, raca_cor)
);

CREATE OR REPLACE VIEW indicadores AS
SELECT
    n.ano, n.uf, n.raca_cor,
    COALESCE(o.obitos_maternos, 0) AS obitos_maternos,
    n.nascidos_vivos,
    ROUND(COALESCE(o.obitos_maternos, 0) * 100000.0 / NULLIF(n.nascidos_vivos, 0), 2) AS razao_mortalidade,
    ROUND(n.partos_cesareos * 100.0 / NULLIF(n.nascidos_vivos, 0), 2) AS pct_cesarea,
    ROUND(n.prenatal_insuficiente * 100.0 / NULLIF(n.nascidos_vivos, 0), 2) AS pct_prenatal_insuficiente
FROM nascidos_vivos_agg n
LEFT JOIN obitos_maternos_agg o USING (ano, uf, raca_cor);
