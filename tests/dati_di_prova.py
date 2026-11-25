"""
Dati di prova nel formato degli export giornalieri di Search Console.
30 giorni (dal 28 settembre al 27 ottobre 2026): 4 settimane complete e 2 giorni della successiva.
Fenomeni noti che il report deve far emergere:
  - Discover cala per 4 settimane
  - la ricerca web cresce, trainata dalla pagina "bonus casa"
  - una pagina e una query compaiono solo nell'ultima settimana (novità)
  - due query hanno molte impressioni e posizione tra 8 e 15 (opportunità)
"""
from datetime import date, timedelta

import pandas as pd

INIZIO = date(2026, 9, 28)                              # lunedì
GIORNI = 30                                             # fino a martedì 27 ottobre
PESO_GIORNO = [1.0, 1.1, 1.0, 0.95, 0.9, 0.7, 0.65]     # da lunedì a domenica
ULTIMA_SETTIMANA = date(2026, 10, 19)
SITO = "https://www.sito-di-prova.it"

# canale, pagina o query, clic al giorno, fattore delle 4 settimane, CTR, posizione, primo giorno
PAGINE = [
    ("discover", SITO + "/arredamento/stufa.php", 900, [1.0, 0.85, 0.65, 0.45], 0.04, 1.0, None),
    ("discover", SITO + "/arredamento/pellet.php", 500, [1.0, 0.90, 0.70, 0.50], 0.04, 1.0, None),
    ("discover", SITO + "/news/nuova-pagina.php", 120, [1.0, 1.0, 1.0, 1.0], 0.04, 1.0, ULTIMA_SETTIMANA),
    ("web", SITO + "/news/bonus-casa.php", 120, [1.0, 1.3, 1.7, 2.2], 0.015, 2.5, None),
    ("web", SITO + "/arredamento/divani.php", 60, [1.0, 1.0, 1.05, 1.1], 0.015, 6.0, None),
    ("image", SITO + "/design/lampade.php", 15, [1.0, 1.0, 1.0, 1.0], 0.004, 30.0, None),
    ("googleNews", SITO + "/news/bonus-casa.php", 20, [1.0, 1.0, 1.2, 1.5], 0.05, 1.0, None),
    ("video", SITO + "/design/lampade.php", 3, [1.0, 1.0, 1.0, 1.0], 0.04, 15.0, None),
]

QUERY = [
    ("web", "bonus casa 2027", 80, [1.0, 1.3, 1.7, 2.2], 0.08, 2.5, None),
    ("web", "accensione riscaldamento", 40, [1.0, 0.8, 0.6, 0.4], 0.05, 4.0, None),
    ("web", "stufa a legna prezzi", 35, [1.0, 1.0, 1.0, 1.0], 0.05, 5.0, None),
    ("web", "divano letto ikea", 5, [1.0, 1.0, 1.0, 1.0], 0.002, 11.0, None),
    ("web", "cucine mondo convenienza", 6, [1.0, 1.0, 1.0, 1.0], 0.003, 10.5, None),
    ("web", "query nuova ottobre", 25, [1.0, 1.0, 1.0, 1.0], 0.05, 4.0, ULTIMA_SETTIMANA),
]


def _genera(voci, colonna):
    """Una riga al giorno per ogni voce. Nessun valore casuale: il risultato è sempre lo stesso."""
    righe = []
    for canale, nome, clic, fattori, ctr, posizione, primo in voci:
        for i in range(GIORNI):
            giorno = INIZIO + timedelta(days=i)
            if primo and giorno < primo:
                continue
            c = round(clic * fattori[min(i // 7, 3)] * PESO_GIORNO[giorno.weekday()])
            righe.append({"search_type": canale, "date": giorno, colonna: nome,
                          "clicks": c, "impressions": round(c / ctr), "ctr": ctr, "position": posizione})
    return pd.DataFrame(righe)


def dati_pagine():
    return _genera(PAGINE, "page")


def dati_query():
    return _genera(QUERY, "query")


def come_csv(df):
    return df.to_csv(index=False)