import re

VERDE = "#0f766e"
AMBRA = "#fcd34d"

STILE = """<style>
    body { margin: 0; background: #eef2f6; color: #1e293b; font-family: "Segoe UI", Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.55; }
    .report { max-width: 980px; margin: 24px auto; padding: 32px; background: #fff; border-radius: 16px; box-shadow: 0 2px 12px rgba(15, 23, 42, .08); }
    .testo h1 { margin: 0; padding: 26px 28px; font-size: 26px; color: #fff; background: linear-gradient(120deg, #0f766e, #134e4a); border-radius: 14px; }
    .testo h2 { margin: 38px 0 12px; font-size: 20px; color: #0f172a; }
    .testo h2:before { content: ""; display: inline-block; width: 10px; height: 10px; margin-right: 10px; background: #0f766e; border-radius: 50%; }
    .testo > p { margin: 0 0 12px; padding: 10px 16px; color: #134e4a; background: #f0fdfa; border-radius: 10px; }
    .testo > h1 + p { margin-top: 16px; padding: 18px 22px; font-size: 16.5px; line-height: 1.6; color: #1e293b; background: #fff; border: 1px solid #d9e2ec; box-shadow: 0 1px 4px rgba(15, 23, 42, .06); }
    .testo > table { width: 100%; margin: 14px 0; border-collapse: separate; border-spacing: 0; }
    .testo > table th { padding: 10px 8px; text-align: right; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: #fff; background: #0f766e; }
    .testo > table th:first-child { border-top-left-radius: 8px; }
    .testo > table th:last-child { border-top-right-radius: 8px; }
    .testo > table td { padding: 9px 8px; text-align: right; font-size: 13px; border-bottom: 1px solid #e8eef3; }
    .testo > table tr:nth-child(even) td { background: #f8fafc; }
    .testo > table th:first-child, .testo > table td:first-child { text-align: left; word-break: break-word; }
    .testo ul { padding-left: 20px; }
    .testo li { margin-bottom: 10px; }
    @page { size: A4; margin: 12mm; }
    @media print {
        body { background: #fff; }
        .report { max-width: none; margin: 0; padding: 0; box-shadow: none; border-radius: 0; }
        * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        h2 { break-after: avoid; }
        tr, .grafico, .kpi { break-inside: avoid; }
        .testo > p { break-inside: avoid; break-after: avoid; }
    }
</style>"""


def _inserisci(html: str, segnaposto: str, contenuto: str) -> str:
    """Sostituisce il segnaposto (anche se l'LLM lo ha messo dentro un <p>)."""
    return re.sub(rf"(<p>\s*)?{re.escape(segnaposto)}(\s*</p>)?", lambda m: contenuto, html)


def _kpi_html(dati: dict) -> str:
    canali = {c["canale"]: c for c in dati["canali"]}
    web = dati["ricerca_web"]
    schede = [
        ("Clic totali", dati["clic_totali"], dati["clic_totali_variazione"]),
        ("Clic da Discover", canali["Discover"]["clic"], canali["Discover"]["variazione"]),
        ("CTR Discover", canali["Discover"]["ctr"], canali["Discover"]["ctr_variazione"]),
        ("Clic da ricerca web", web["clic"], web["clic_variazione"]),
        ("CTR ricerca web", web["ctr"], web["ctr_variazione"]),
    ]
    celle = ""
    for titolo, valore, var in schede:
        colori = "background:#fee2e2; color:#b91c1c;" if var.startswith("-") else "background:#dcfce7; color:#15803d;"
        celle += (
            "<td style='width:20%; padding:12px 12px; vertical-align:top; background:#f0fdfa; border:5px solid #fff; border-radius:12px;'>"
            f"<div style='font-size:12px; color:#475569;'>{titolo}</div>"
            f"<div style='margin:2px 0 6px; font-size:26px; font-weight:700; color:{VERDE};'>{valore}</div>"
            f"<span style='padding:2px 8px; font-size:12px; font-weight:600; border-radius:10px; {colori}'>{var}</span>"
            "<div style='margin-top:4px; font-size:11px; color:#64748b;'>vs settimana prec.</div></td>"
        )
    return f"<div class='kpi' style='margin:22px 0;'><table style='width:100%; border-collapse:separate; border-spacing:0;'><tr>{celle}</tr></table></div>"


def _grafico_html(titolo: str, serie: dict, giorni_settimana: list, legenda: tuple) -> str:
    """Per ogni giorno due barre vicine: la settimana precedente (ambra) e quella analizzata (verde)."""
    massimo = max(serie["prima"] + serie["ora"]) or 1
    colonne = ""
    for prima, ora, giorno in zip(serie["prima"], serie["ora"], giorni_settimana):
        barre = "".join(
            f"<td title='{giorno}: {v} clic' style='width:50%; height:120px; padding:0 1px; vertical-align:bottom;'>"
            f"<div style='height:{round(v / massimo * 120)}px; background:{colore}; border-radius:3px 3px 0 0;'></div></td>"
            for v, colore in ((prima, AMBRA), (ora, VERDE))
        )
        colonne += (
            "<td style='padding:0 5px; vertical-align:bottom;'>"
            f"<table style='width:100%; table-layout:fixed; border-collapse:collapse;'><tr>{barre}</tr></table></td>"
        )
    etichette = "".join(
        f"<td style='padding:4px 0 0; font-size:10px; color:#64748b; text-align:center;'>{g}</td>" for g in giorni_settimana
    )
    quadratino = "display:inline-block; width:10px; height:10px; margin-right:4px; border-radius:2px; background:"
    var_colore = "#b91c1c" if serie["variazione"].startswith("-") else "#15803d"
    return (
        "<div class='grafico' style='display:inline-block; box-sizing:border-box; width:47%; margin:8px 1% 16px; padding:12px 14px; "
        "vertical-align:top; background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;'>"
        f"<div style='font-size:13px; font-weight:600;'>{titolo}</div>"
        f"<div style='font-size:12px; margin:4px 0 6px; color:#475569;'>Totale {serie['totale_ora']} clic contro {serie['totale_prima']} "
        f"(<strong style='color:{var_colore};'>{serie['variazione']}</strong>)</div>"
        f"<div style='font-size:11px; color:#64748b; margin:0 0 8px;'>"
        f"<span style='{quadratino}{AMBRA};'></span>{legenda[0]} &nbsp; "
        f"<span style='{quadratino}{VERDE};'></span>{legenda[1]}</div>"
        f"<table style='width:100%; table-layout:fixed; border-collapse:collapse; border-bottom:1px solid #cbd5e1;'>"
        f"<tr>{colonne}</tr></table>"
        f"<table style='width:100%; table-layout:fixed; border-collapse:collapse;'><tr>{etichette}</tr></table>"
        "</div>"
    )


def crea_report(llm_html: str, risultato: dict) -> str:
    """Report finito: testo e tabelle scritti dall'LLM, indicatori e grafici calcolati dal codice."""
    html = llm_html.replace("```html", "").replace("```", "")

    grafici = risultato["grafici"]
    legenda = (risultato["periodo_precedente"], risultato["periodo"])
    html = _inserisci(html, "[[GRAFICO_DISCOVER]]",
                      _grafico_html("Clic da Discover al giorno", grafici["discover"], grafici["giorni_settimana"], legenda))
    html = _inserisci(html, "[[GRAFICO_WEB]]",
                      _grafico_html("Clic da ricerca web al giorno", grafici["web"], grafici["giorni_settimana"], legenda))

    # Gli indicatori vanno dopo la sintesi, prima della prima sezione
    kpi = _kpi_html(risultato["dati"])
    html = html.replace("<h2", kpi + "<h2", 1) if "<h2" in html else html + kpi

    return (
        f"<html><head><meta charset='utf-8'>{STILE}</head>"
        f"<body><div class='report'><div class='testo'>{html}</div></div></body></html>"
    )