"""
Calcoli del report settimanale a partire dagli export giornalieri di Search Console
(uno per pagina e uno per query). Il risultato contiene:
  - "dati": numeri già formattati in italiano, che l'LLM deve solo leggere e spiegare
  - "grafici": serie numeriche per i grafici a barre
"""
import io
import os
from collections import Counter
from datetime import timedelta

import pandas as pd
import requests

NOMI_CANALI = {
    "discover": "Discover",
    "web": "Ricerca web",
    "image": "Immagini",
    "googleNews": "Google News",
    "video": "Video",
}
SENZA_POSIZIONE = ["discover", "googleNews"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
TOP = 5  # righe per ogni tabella
COLONNE = {"search_type", "date", "clicks", "impressions", "position"}


# ---------- Formato italiano ----------

def italiano(testo):
    """1,234.5 -> 1.234,5"""
    return testo.replace(",", "#").replace(".", ",").replace("#", ".")


def intero(x):
    return italiano(f"{round(x):,}")


def decimale(x, cifre=2):
    return italiano(f"{x:,.{cifre}f}")


def percentuale(x, cifre=1):
    return decimale(x, cifre) + "%"


def con_segno(testo, x):
    return ("+" if x >= 0 else "-") + testo.lstrip("-")


def variazione(ora, prima):
    if prima == 0:
        return "nuovo (prima 0)" if ora > 0 else "0,0%"
    v = (ora - prima) / prima * 100
    return con_segno(percentuale(v), v)


def differenza(ora, prima):
    return con_segno(intero(ora - prima), ora - prima)


def nome_periodo(inizio, fine):
    return f"{inizio.day}-{fine.day} {MESI[fine.month - 1]} {fine.year}"


def senza_dominio(indice):
    """https://www.sito.it/pagina.php -> /pagina.php"""
    return indice.str.replace(r"^https?://[^/]+", "", regex=True)


def nome_giorno(d):
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]}"


# ---------- Lettura e calcoli di base ----------

def leggi_csv(file):
    """Legge un export giornaliero di Search Console."""
    df = pd.read_csv(file)
    if not COLONNE.issubset(df.columns):
        raise ValueError("colonne mancanti")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def ultima_settimana(df):
    """Ultima settimana completa (lunedì-domenica) presente nei dati."""
    ultimo = df["date"].max()
    fine = ultimo - timedelta(days=(ultimo.weekday() + 1) % 7)
    return fine - timedelta(days=6), fine


def scarica_csv(nome_file):
    """Scarica un export dal server dei dati (in locale: la cartella static/gsc)."""
    base = os.getenv("GSC_DATA_URL", "http://127.0.0.1:8000/static/gsc")
    risposta = requests.get(f"{base}/{nome_file}", timeout=30)
    risposta.raise_for_status()
    return leggi_csv(io.StringIO(risposta.text))


def nel_periodo(df, inizio, fine):
    return df[(df["date"] >= inizio) & (df["date"] <= fine)]


def totali(df):
    """Clic, impressioni, CTR (%) e posizione media pesata sulle impressioni."""
    clic = df["clicks"].sum()
    impr = df["impressions"].sum()
    ctr = clic / impr * 100 if impr else 0
    pos = (df["position"] * df["impressions"]).sum() / impr if impr else 0
    return clic, impr, ctr, pos


def per_elemento(df, colonna):
    """Somma clic e impressioni per pagina o query, con CTR e posizione."""
    df = df.assign(pos_x_impr=df["position"] * df["impressions"])
    g = df.groupby(colonna)[["clicks", "impressions", "pos_x_impr"]].sum()
    g["ctr"] = g["clicks"] / g["impressions"] * 100
    g["posizione"] = g["pos_x_impr"] / g["impressions"]
    return g


def confronta(ora, prima, colonna):
    """Tabella con i valori di ora e del periodo prima, affiancati."""
    t = per_elemento(ora, colonna).join(per_elemento(prima, colonna), how="outer", rsuffix="_prec")
    t = t.fillna({"clicks": 0, "impressions": 0, "clicks_prec": 0, "impressions_prec": 0})
    t["delta"] = t["clicks"] - t["clicks_prec"]
    return t


# ---------- Sezioni del report ----------

def sezione_canali(ora, prima):
    tot_ora = ora["clicks"].sum()
    diff_totale = tot_ora - prima["clicks"].sum()
    righe = []
    for codice, nome in NOMI_CANALI.items():
        clic, impr, ctr, pos = totali(ora[ora["search_type"] == codice])
        clic_p, _, ctr_p, _ = totali(prima[prima["search_type"] == codice])
        riga = {
            "canale": nome,
            "clic": intero(clic),
            "clic_prec": intero(clic_p),
            "variazione": variazione(clic, clic_p),
            "differenza_clic": differenza(clic, clic_p),
            "peso_sulla_variazione_totale": percentuale((clic - clic_p) / diff_totale * 100) if diff_totale else "-",
            "quota_sui_clic_totali": percentuale(clic / tot_ora * 100),
            "impressioni": intero(impr),
            "ctr": percentuale(ctr, 2),
            "ctr_prec": percentuale(ctr_p, 2),
            "ctr_variazione": con_segno(decimale(ctr - ctr_p), ctr - ctr_p) + " pt",
        }
        if codice not in SENZA_POSIZIONE:
            riga["posizione"] = decimale(pos)
        righe.append(riga)
    return righe


def per_giorno(df, canale, inizio):
    """Clic e impressioni di ognuno dei 7 giorni a partire da `inizio`, per un canale."""
    somme = df[df["search_type"] == canale].groupby("date")[["clicks", "impressions"]].sum()
    return somme.reindex([inizio + timedelta(days=i) for i in range(7)], fill_value=0)


def sezione_giornaliera(ora, prima, inizio, inizio_prec, canale):
    """Dati per l'LLM e serie per il grafico dei clic al giorno di un canale."""
    g_ora = per_giorno(ora, canale, inizio)
    g_prima = per_giorno(prima, canale, inizio_prec)
    media = g_ora["clicks"].sum() / 7

    giorni = []
    for i in range(7):
        clic = g_ora["clicks"].iloc[i]
        scarto = (clic - media) / media * 100 if media else 0
        giorni.append({
            "giorno": nome_giorno(inizio + timedelta(days=i)),
            "clic": intero(clic),
            "impressioni": intero(g_ora["impressions"].iloc[i]),
            "clic_stesso_giorno_settimana_prec": intero(g_prima["clicks"].iloc[i]),
            "scostamento_dalla_media": con_segno(percentuale(scarto), scarto),
        })
    dati = {"media_clic_al_giorno": intero(media), "giorni": giorni}
    tot_ora, tot_prima = g_ora["clicks"].sum(), g_prima["clicks"].sum()
    grafico = {
        "prima": [int(x) for x in g_prima["clicks"]],
        "ora": [int(x) for x in g_ora["clicks"]],
        "totale_prima": intero(tot_prima),
        "totale_ora": intero(tot_ora),
        "variazione": variazione(tot_ora, tot_prima),
    }
    return dati, grafico


def sezione_pagine(ora, prima, canale):
    ora = ora[ora["search_type"] == canale]
    prima = prima[prima["search_type"] == canale]
    tot, tot_p = ora["clicks"].sum(), prima["clicks"].sum()
    t = confronta(ora, prima, "page")
    t.index = senza_dominio(t.index)

    def riga(nome, r):
        d = {
            "pagina": nome,
            "clic": intero(r["clicks"]),
            "clic_prec": intero(r["clicks_prec"]),
            "differenza_clic": con_segno(intero(r["delta"]), r["delta"]),
            "quota_sui_clic_del_canale": percentuale(r["clicks"] / tot * 100),
        }
        if canale not in SENZA_POSIZIONE and r["impressions"] > 0:
            d["impressioni"] = intero(r["impressions"])
            d["ctr"] = percentuale(r["ctr"], 2)
            d["posizione"] = decimale(r["posizione"])
        return d

    piu_cliccate = t.sort_values("clicks", ascending=False).head(TOP)
    in_crescita = t.sort_values("delta", ascending=False).head(TOP)
    in_calo = t.sort_values("delta").head(TOP)
    migliore = in_crescita.iloc[0]

    return {
        "quota_prime_3_pagine": percentuale(piu_cliccate["clicks"].head(3).sum() / tot * 100),
        "pagine_piu_cliccate": [riga(n, r) for n, r in piu_cliccate.iterrows()],
        "pagine_in_crescita": [riga(n, r) for n, r in in_crescita.iterrows()],
        "pagine_in_calo": [riga(n, r) for n, r in in_calo.iterrows()],
        "senza_la_pagina_piu_cresciuta": {
            "pagina": in_crescita.index[0],
            "clic_canale": intero(tot - migliore["clicks"]),
            "clic_canale_prec": intero(tot_p - migliore["clicks_prec"]),
            "variazione": variazione(tot - migliore["clicks"], tot_p - migliore["clicks_prec"]),
        },
    }


def sezione_ricerca_web(ora, prima):
    clic, impr, ctr, pos = totali(ora[ora["search_type"] == "web"])
    clic_p, impr_p, ctr_p, pos_p = totali(prima[prima["search_type"] == "web"])
    return {
        "clic": intero(clic), "clic_prec": intero(clic_p), "clic_variazione": variazione(clic, clic_p),
        "impressioni": intero(impr), "impressioni_prec": intero(impr_p),
        "impressioni_variazione": variazione(impr, impr_p),
        "ctr": percentuale(ctr, 2), "ctr_prec": percentuale(ctr_p, 2),
        "ctr_variazione": con_segno(decimale(ctr - ctr_p), ctr - ctr_p) + " pt",
        "posizione": decimale(pos), "posizione_prec": decimale(pos_p),
        "posizione_variazione": con_segno(decimale(pos - pos_p), pos - pos_p),
        "posizione_giudizio": "peggiora" if pos > pos_p else "migliora",
        **sezione_pagine(ora, prima, "web"),
    }


def parole_frequenti(query):
    """Parole che compaiono in almeno 2 query della lista."""
    conta = Counter(p for q in query for p in dict.fromkeys(q.split()) if len(p) > 2)
    return [parola for parola, n in conta.most_common(8) if n >= 2]


def sezione_query(ora, prima):
    ora = ora[ora["search_type"] == "web"]
    prima = prima[prima["search_type"] == "web"]
    t = confronta(ora, prima, "query")

    def riga(nome, r):
        return {
            "query": nome,
            "clic": intero(r["clicks"]),
            "clic_prec": intero(r["clicks_prec"]),
            "impressioni": intero(r["impressions"]),
            "impressioni_prec": intero(r["impressions_prec"]),
            "ctr": percentuale(r["ctr"], 2) if r["impressions"] else "0,00%",
            "posizione": decimale(r["posizione"]) if r["impressions"] else "-",
        }

    piu_cliccate = t.sort_values(["clicks", "impressions"], ascending=False)
    in_calo = t.sort_values("delta")
    opportunita = t[(t["impressions"] >= 300) & t["posizione"].between(8, 20)]
    opportunita = opportunita.sort_values("impressions", ascending=False)

    query = {
        "nota": "Il file query non contiene le query anonime: i clic delle query sono meno dei clic della ricerca web.",
        "query_piu_cliccate": [riga(n, r) for n, r in piu_cliccate.head(TOP).iterrows()],
        "clic_prime_query_insieme": intero(piu_cliccate["clicks"].head(TOP).sum()),
        "query_in_calo": [riga(n, r) for n, r in in_calo.head(TOP).iterrows()],
    }
    opp = {
        "criterio": "almeno 300 impressioni e posizione media tra 8 e 20",
        "query": [riga(n, r) for n, r in opportunita.head(TOP).iterrows()],
        "impressioni_insieme": intero(opportunita["impressions"].head(TOP).sum()),
        "clic_insieme": intero(opportunita["clicks"].head(TOP).sum()),
    }
    temi = {
        "parole_frequenti_nelle_query_principali": parole_frequenti(piu_cliccate.index[:30]),
        "parole_frequenti_nelle_query_in_calo": parole_frequenti(in_calo.index[:30]),
        "parole_frequenti_nelle_opportunita": parole_frequenti(opportunita.index[:30]),
    }
    return query, opp, temi


def sezione_novita(p_ora, p_prima, q_ora, q_prima):
    """Elementi che la settimana prima non avevano né clic né impressioni: probabilmente nuovi."""

    def nuovi(ora, prima, colonna):
        t = confronta(ora, prima, colonna)
        senza_storia = (t["clicks_prec"] == 0) & (t["impressions_prec"] == 0)
        return t[senza_storia & (t["clicks"] > 0)].sort_values("clicks", ascending=False)

    def riassunto(ora, nuovi_el, righe):
        tot = ora["clicks"].sum()
        return {
            "numero": len(nuovi_el),
            "clic_insieme": intero(nuovi_el["clicks"].sum()),
            "quota_sui_clic_del_canale": percentuale(nuovi_el["clicks"].sum() / tot * 100) if tot else "0,0%",
            "elenco": righe,
        }

    def pagine(canale):
        ora, prima = p_ora[p_ora["search_type"] == canale], p_prima[p_prima["search_type"] == canale]
        el = nuovi(ora, prima, "page")
        el.index = senza_dominio(el.index)
        righe = []
        for nome, r in el.head(TOP).iterrows():
            riga = {"pagina": nome, "clic": intero(r["clicks"])}
            if canale not in SENZA_POSIZIONE:
                riga.update(impressioni=intero(r["impressions"]), ctr=percentuale(r["ctr"], 2),
                            posizione=decimale(r["posizione"]))
            righe.append(riga)
        return riassunto(ora, el, righe)

    q_ora, q_prima = q_ora[q_ora["search_type"] == "web"], q_prima[q_prima["search_type"] == "web"]
    el = nuovi(q_ora, q_prima, "query")
    righe = [
        {"query": nome, "clic": intero(r["clicks"]), "impressioni": intero(r["impressions"]),
         "ctr": percentuale(r["ctr"], 2), "posizione": decimale(r["posizione"])}
        for nome, r in el.head(TOP).iterrows()
    ]
    return {
        "criterio": "pagine e query con clic questa settimana e nessun clic né impressione la settimana precedente (probabilmente nuove)",
        "pagine_discover": pagine("discover"),
        "pagine_ricerca_web": pagine("web"),
        "query": riassunto(q_ora, el, righe),
    }


def sezione_trend(pagine, inizio):
    """Clic delle ultime settimane complete (fino a 4) e confronto con la media delle precedenti."""
    inizi = [inizio]
    while len(inizi) < 4 and inizi[-1] - timedelta(days=7) >= pagine["date"].min():
        inizi.append(inizi[-1] - timedelta(days=7))
    inizi.reverse()  # dalla più vecchia alla più recente
    if len(inizi) < 3:
        return None  # servono almeno 2 settimane precedenti per avere una media

    settimane = [nome_periodo(i, i + timedelta(days=6)) for i in inizi]
    canali = [("Totale", None), ("Discover", "discover"), ("Ricerca web", "web")]
    righe = []
    for nome, codice in canali:
        clic = []
        for i in inizi:
            sett = nel_periodo(pagine, i, i + timedelta(days=6))
            clic.append((sett if codice is None else sett[sett["search_type"] == codice])["clicks"].sum())
        media = sum(clic[:-1]) / len(clic[:-1])
        righe.append({
            "canale": nome,
            "clic_per_settimana": [intero(c) for c in clic],
            "media_settimane_precedenti": intero(media),
            "variazione_rispetto_alla_media": variazione(clic[-1], media),
            "variazione_rispetto_alla_settimana_prima": variazione(clic[-1], clic[-2]),
        })
    return {"settimane_dalla_piu_vecchia": settimane, "canali": righe}


# ---------- Funzione principale ----------

def analizza_settimana(pagine, query):
    """Confronta l'ultima settimana completa dei dati con quella precedente."""
    inizio, fine = ultima_settimana(pagine)
    fine_prec = inizio - timedelta(days=1)
    inizio_prec = fine_prec - timedelta(days=6)

    p_ora, p_prima = nel_periodo(pagine, inizio, fine), nel_periodo(pagine, inizio_prec, fine_prec)
    q_ora, q_prima = nel_periodo(query, inizio, fine), nel_periodo(query, inizio_prec, fine_prec)
    if p_ora.empty or q_ora.empty:
        raise ValueError("I file non contengono una settimana completa (da lunedì a domenica).")

    clic, clic_p = p_ora["clicks"].sum(), p_prima["clicks"].sum()
    giorni_discover, grafico_discover = sezione_giornaliera(p_ora, p_prima, inizio, inizio_prec, "discover")
    giorni_web, grafico_web = sezione_giornaliera(p_ora, p_prima, inizio, inizio_prec, "web")
    sez_query, sez_opportunita, sez_temi = sezione_query(q_ora, q_prima)

    dati = {
        "clic_totali": intero(clic),
        "clic_totali_prec": intero(clic_p),
        "clic_totali_variazione": variazione(clic, clic_p),
        "clic_totali_differenza": differenza(clic, clic_p),
        "canali": sezione_canali(p_ora, p_prima),
        "trend": sezione_trend(pagine, inizio),
        "andamento_giornaliero_discover": giorni_discover,
        "andamento_giornaliero_web": giorni_web,
        "discover": sezione_pagine(p_ora, p_prima, "discover"),
        "ricerca_web": sezione_ricerca_web(p_ora, p_prima),
        "query": sez_query,
        "novita": sezione_novita(p_ora, p_prima, q_ora, q_prima),
        "opportunita": sez_opportunita,
        "temi": sez_temi,
    }
    # Etichetta di ogni coppia di barre: giorno della settimana e data della settimana analizzata
    giorni_settimana = [f"{GIORNI[i][:3].capitalize()} {(inizio + timedelta(days=i)).day}" for i in range(7)]

    return {
        "periodo": nome_periodo(inizio, fine),
        "periodo_precedente": nome_periodo(inizio_prec, fine_prec),
        "dati": dati,
        "grafici": {"discover": grafico_discover, "web": grafico_web, "giorni_settimana": giorni_settimana},
    }