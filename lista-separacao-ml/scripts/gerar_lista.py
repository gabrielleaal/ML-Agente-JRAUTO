#!/usr/bin/env python3
"""Gera o PDF da lista de separação a partir das vendas do Mercado Livre.

Uso:
    python3 gerar_lista.py vendas.json saida.pdf [--produtos produtos.csv] [--data 21/10/2026]

vendas.json: lista de vendas, cada uma com pelo menos "sku" e "quantidade".
Campos opcionais: "pedido" (nº da venda) e "titulo" (título do anúncio).
    [{"pedido": "2000001234", "sku": "64265", "quantidade": 1, "titulo": "Radiador Palio..."}]

O script soma as quantidades do mesmo código, cruza com a planilha de produtos
(CÓDIGO;DESCRIÇÃO DO PRODUTO;LOC.FÍSICA;...) e ordena pela localização física,
para o separador andar pelo estoque numa ordem só.
"""
import argparse, csv, json, os, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AQUI = os.path.dirname(os.path.abspath(__file__))
PRODUTOS_PADRAO = os.path.join(AQUI, "..", "assets", "produtos.csv")


def ler_produtos(caminho):
    for enc in ("utf-8-sig", "cp1252"):
        try:
            with open(caminho, encoding=enc, newline="") as f:
                linhas = list(csv.reader(f, delimiter=";"))
            break
        except UnicodeDecodeError:
            continue
    cab = [c.strip().upper() for c in linhas[0]]

    def col(*nomes):
        for i, c in enumerate(cab):
            if any(c.startswith(n) for n in nomes):
                return i
        sys.exit(f"Coluna {nomes[0]} não encontrada na planilha: {cab}")

    i_cod, i_desc, i_loc = col("CÓDIGO", "CODIGO"), col("DESCRI"), col("LOC")
    produtos = {}
    for l in linhas[1:]:
        if len(l) <= max(i_cod, i_desc, i_loc) or not l[i_cod].strip():
            continue
        produtos[normalizar_codigo(l[i_cod])] = (l[i_desc].strip(), l[i_loc].strip())
    return produtos


def normalizar_codigo(c):
    c = str(c).strip()
    return c.lstrip("0") or c if c.isdigit() else c.upper()


def resumir(desc, limite=60):
    """Tira os códigos de referência do fim da descrição (RV2540, DS1804, 93221445...)."""
    desc = desc.replace("==", " ")
    saida = []
    for tok in desc.split():
        limpo = tok.strip("()")
        digitos = sum(ch.isdigit() for ch in limpo)
        if saida and len(limpo) >= 5 and digitos >= 3 and "/" not in limpo and "." not in limpo:
            break  # a partir daqui são referências cruzadas
        saida.append(tok)
    texto = " ".join(saida)
    if texto.count("(") > texto.count(")"):
        texto = texto[: texto.rfind("(")].strip()
    if len(texto) > limite:
        texto = texto[:limite].rsplit(" ", 1)[0] + "…"
    return texto


def refs(desc, limite=60):
    resumo = resumir(desc, 9999).rstrip("…")
    desc = desc.replace("==", " ")
    r = desc[len(resumo):].strip() if desc.startswith(resumo) else ""
    return r

def chave_local(loc):
    if not loc:
        return (1, "")
    partes = re.split(r"(\d+)", loc.upper())
    return (0, [int(p) if p.isdigit() else p for p in partes])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vendas")
    ap.add_argument("saida")
    ap.add_argument("--produtos", default=PRODUTOS_PADRAO)
    ap.add_argument("--data", default=datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y"))
    a = ap.parse_args()

    produtos = ler_produtos(a.produtos)
    vendas = json.load(open(a.vendas, encoding="utf-8"))

    itens, faltando = {}, {}
    for v in vendas:
        cod = normalizar_codigo(v.get("sku", ""))
        qtd = int(v.get("quantidade", 1) or 1)
        destino = itens if cod in produtos else faltando
        reg = destino.setdefault(cod, {"qtd": 0, "pedidos": [], "titulo": v.get("titulo", "")})
        reg["qtd"] += qtd
        if v.get("pedido"):
            reg["pedidos"].append(str(v["pedido"]))

    linhas = []
    for cod, r in itens.items():
        desc, loc = produtos[cod]
        linhas.append((loc, cod, resumir(desc) + (f"<br/><b>Ref: {refs(desc)}</b>" if refs(desc) else "<br/><i>(sem código de referência)</i>"), r["qtd"]))
    linhas.sort(key=lambda x: (chave_local(x[0]), x[1]))

    # ---- PDF ----
    st = ParagraphStyle("c", fontName="Helvetica", fontSize=9.5, leading=11.5)
    stb = ParagraphStyle("b", parent=st, fontName="Helvetica-Bold")
    doc = SimpleDocTemplate(a.saida, pagesize=A4, leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            title=f"Lista de separação {a.data}")
    total_un = sum(l[3] for l in linhas)
    story = [
        Paragraph(f"<b>LISTA DE SEPARAÇÃO – MERCADO LIVRE</b>", ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=15, leading=18)),
        Paragraph(f"Envios de {a.data} · {len(vendas)} venda(s) · {len(linhas)} produto(s) · {total_un} unidade(s)", st),
        Spacer(1, 5 * mm),
    ]
    dados = [["OK", "LOCALIZAÇÃO", "CÓDIGO", "DESCRIÇÃO", "QTD"]]
    for loc, cod, desc, qtd in linhas:
        dados.append(["", Paragraph(f"<b>{loc}</b>" if loc else "<i>sem local</i>", st), Paragraph(f"<b>{cod}</b>", st),
                      Paragraph(desc, st), Paragraph(f"<b>{qtd}</b>", stb)])
    t = Table(dados, colWidths=[9 * mm, 30 * mm, 20 * mm, 112 * mm, 15 * mm], repeatRows=1)
    estilo = [
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#888888")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
        ("TOPPADDING", (0, 1), (-1, -1), 5), ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]
    for i in range(2, len(dados), 2):
        estilo.append(("BACKGROUND", (1, i), (-1, i), colors.HexColor("#F2F2F2")))
    t.setStyle(TableStyle(estilo))
    story.append(t)

    if faltando:
        story += [Spacer(1, 6 * mm),
                  Paragraph("<b>ATENÇÃO – SKU não encontrado na planilha (separar manualmente)</b>", stb),
                  Spacer(1, 2 * mm)]
        d2 = [["OK", "SKU", "ANÚNCIO / PEDIDO", "QTD"]]
        for cod, r in faltando.items():
            info = r["titulo"] or ""
            if r["pedidos"]:
                info += f" (venda {', '.join(r['pedidos'])})"
            d2.append(["", Paragraph(cod or "<i>sem SKU</i>", st), Paragraph(info.strip(), st), Paragraph(f"<b>{r['qtd']}</b>", stb)])
        t2 = Table(d2, colWidths=[9 * mm, 30 * mm, 132 * mm, 15 * mm])
        t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#888888")),
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFE08A")),
                                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (3, 0), (3, -1), "CENTER")]))
        story.append(t2)

    story += [Spacer(1, 8 * mm), Paragraph("Separado por: ______________________   Conferido por: ______________________", st)]
    doc.build(story)
    print(json.dumps({"produtos": len(linhas), "unidades": total_un, "nao_encontrados": list(faltando)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
