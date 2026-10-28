"""Monta a planilha de títulos e descrições para o Hub.

Uso: py montar_planilha.py ENTRADA.csv dados.json SAIDA.csv

Lê o CSV original dos produtos e o dados.json (preenchido pelo Claude),
monta a descrição no modelo fixo da loja, valida as regras e grava o CSV
de saída (UTF-8 com BOM, separador ";").
"""
import csv
import json
import os
import re
import sys
import unicodedata

LIMITE_TITULO = 60
MIN_SOBRE = 300  # caracteres do bloco "Sobre o produto"
PROIBIDAS = ["promoção", "promocao", "frete grátis", "frete gratis", "oferta"]
SIMBOLOS = "!*%$#"
NOMES_CODIGO = {"codigo", "cod", "sku"}
FONTES = {"fabricante", "loja/catálogo", "planilha", "web", "estimado"}
MEDIDAS = [("largura", "Largura", "cm"), ("altura", "Altura", "cm"),
           ("profundidade", "Profundidade", "cm"), ("peso", "Peso", "g")]
RODAPE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "textos", "rodape.txt")

# A planilha sai enxuta (pedido do usuário): do CSV de entrada só ficam
# Código, Marca, Localização física e Estoque; depois vêm Título, Descrição e as
# medidas da embalagem. Os alertas não vão para a planilha: são impressos no terminal.
COLUNAS_EMBALAGEM = ["Embalagem Largura (cm)", "Embalagem Altura (cm)",
                     "Embalagem Profundidade (cm)", "Embalagem Peso (g)"]
COLUNAS_EXTRA = ["Título", "Descrição"] + COLUNAS_EMBALAGEM


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def ler_csv(caminho):
    for enc in ("utf-8-sig", "cp1252", "latin-1"):  # latin-1 nunca falha
        try:
            with open(caminho, encoding=enc, newline="") as f:
                texto = f.read()
            break
        except UnicodeDecodeError:
            continue
    primeira = texto.splitlines()[0] if texto else ""
    sep = ";" if primeira.count(";") >= primeira.count(",") else ","
    leitor = csv.DictReader(texto.splitlines(keepends=True), delimiter=sep)
    linhas = list(leitor)
    return list(leitor.fieldnames or []), linhas


def achar_coluna_codigo(cabecalho):
    for nome in cabecalho:
        if _sem_acento(nome).strip().lower() in NOMES_CODIGO:
            return nome
    raise ValueError("Nenhuma coluna de código (Código, Cod ou SKU) no CSV: %s" % cabecalho)


def colunas_mantidas(cabecalho):
    """Código, Marca, Localização física e Estoque, nessa ordem (as que existirem)."""
    def norm(nome):
        return re.sub(r"[^a-z]", "", _sem_acento(nome).lower())
    cols = [achar_coluna_codigo(cabecalho)]
    marca = [c for c in cabecalho if norm(c) == "marca"]
    local = [c for c in cabecalho if norm(c).startswith("loc")]
    # quantidade em estoque (QTD.ESTQ, Estoque...), nunca valor ou localização do estoque
    estoque = [c for c in cabecalho if ("estq" in norm(c) or "estoque" in norm(c))
               and not norm(c).startswith(("vlr", "valor", "loc"))]
    return cols + marca[:1] + local[:1] + estoque[:1]


def num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    v = str(v).strip().replace(",", ".")
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _br(n):
    """12.5 -> '12,5'; 3.0 -> '3'."""
    if n is None:
        return ""
    return ("%g" % round(n, 2)).replace(".", ",")


def validar_titulo(titulo, original):
    titulo = (titulo or "").strip()
    if not titulo:
        return ["Título vazio"]
    alertas = []
    if len(titulo) > LIMITE_TITULO:
        alertas.append("Título com %d caracteres (máx. %d)" % (len(titulo), LIMITE_TITULO))
    baixo = titulo.lower()
    for p in PROIBIDAS:
        if p in baixo:
            alertas.append("Palavra proibida no título: %s" % p)
    if not original and re.search(r"\boriginal\b", baixo):
        alertas.append("Palavra proibida no título: original (peça não é original)")
    achados = sorted({c for c in titulo if c in SIMBOLOS})
    if achados:
        alertas.append("Símbolo no título: %s" % " ".join(achados))
    return alertas


def formatar_medidas(m, fonte):
    prefixo = "aprox. " if fonte == "estimado" else ""
    partes = []
    for chave, rotulo, unidade in MEDIDAS:
        n = num((m or {}).get(chave))
        if n is not None:
            partes.append("%s: %s%s %s" % (rotulo, prefixo, _br(n), unidade))
    return " | ".join(partes)


def _lista(titulo, itens):
    itens = [i for i in (itens or []) if str(i).strip()]
    return "%s\n%s" % (titulo, "\n".join("• %s" % i for i in itens)) if itens else ""


def montar_descricao(d, rodape):
    blocos = [d.get("nome", "").strip()]
    sobre = [p.strip() for p in (d.get("sobre") or []) if p.strip()]
    if sobre:
        blocos.append("Sobre o produto\n" + "\n\n".join(sobre))
    espec = ["• %s" % e for e in d.get("especificacoes", [])]
    medidas = formatar_medidas(d.get("peca"), d.get("fonte_medidas_peca"))
    if medidas:
        espec.append("• Medidas da peça: %s" % medidas)
    if espec:
        blocos.append("Especificações\n" + "\n".join(espec))
    if d.get("codigos_ref"):
        blocos.append("Códigos de referência\n" + "\n".join("• %s" % c for c in d["codigos_ref"]))
    aplic = d.get("aplicacao") or []
    corpo = "\n".join("• %s" % a for a in aplic) if aplic else "Consulte a compatibilidade na área de Perguntas."
    blocos.append("Aplicação\n" + corpo)
    blocos.append(_lista("O que vem na embalagem", d.get("conteudo_embalagem")))
    blocos.append(_lista("Quando trocar", d.get("sinais_troca")))
    blocos.append(_lista("Dicas de instalação e manutenção", d.get("dicas")))
    blocos.append(rodape.strip())
    return "\n\n".join(b for b in blocos if b)


def _alertas_produto(d):
    alertas = validar_titulo(d.get("titulo"), bool(d.get("original")))
    sobre = "".join(p.strip() for p in (d.get("sobre") or []))
    if not sobre:
        alertas.append("Descrição sem 'Sobre o produto'")
    elif len(sobre) < MIN_SOBRE:
        alertas.append("'Sobre o produto' curto (%d caracteres, mín. %d)" % (len(sobre), MIN_SOBRE))
    if not [i for i in (d.get("conteudo_embalagem") or []) if str(i).strip()]:
        alertas.append("Descrição sem 'O que vem na embalagem'")
    if not d.get("aplicacao"):
        alertas.append("Sem aplicação: conferir")
    elif d.get("fonte_aplicacao") not in FONTES:
        alertas.append("Fonte da aplicação inválida: %r" % d.get("fonte_aplicacao"))
    elif d.get("fonte_aplicacao") == "web":
        alertas.append("Aplicação da web: conferir")
    for qual in ("peca", "embalagem"):
        fonte = d.get("fonte_medidas_%s" % qual)
        if any(num((d.get(qual) or {}).get(k)) is not None for k, _, _ in MEDIDAS) and fonte not in FONTES:
            alertas.append("Fonte das medidas (%s) inválida: %r" % (qual, fonte))
    alertas.extend(d.get("alertas") or [])
    return alertas


def gerar_saida(entrada, dados, saida):
    """Grava a planilha e devolve {código: [alertas]} dos produtos com alerta."""
    cabecalho, linhas = ler_csv(entrada)
    col = achar_coluna_codigo(cabecalho)
    with open(dados, encoding="utf-8-sig") as f:
        por_codigo = {str(k).strip(): v for k, v in json.load(f).items()}
    with open(RODAPE, encoding="utf-8") as f:
        rodape = f.read()

    alertas = {}
    with open(saida, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas_mantidas(cabecalho) + COLUNAS_EXTRA, delimiter=";",
                           quoting=csv.QUOTE_MINIMAL, extrasaction="ignore")
        w.writeheader()
        for linha in linhas:
            cod = (linha.get(col) or "").strip()
            d = por_codigo.get(cod)
            if d is None:
                alertas[cod] = ["Não processado"]
                w.writerow(linha)
                continue
            emb = d.get("embalagem") or {}
            w.writerow(dict(linha, **{
                "Título": (d.get("titulo") or "").strip(),
                "Descrição": montar_descricao(d, rodape),
            }, **{col_emb: _br(num(emb.get(chave)))
                  for col_emb, (chave, _, _) in zip(COLUNAS_EMBALAGEM, MEDIDAS)}))
            a = _alertas_produto(d)
            if a:
                alertas[cod] = a
    return alertas


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    alertas = gerar_saida(argv[1], argv[2], argv[3])
    total = len(ler_csv(argv[1])[1])
    print("%d produtos, %d com alerta -> %s" % (total, len(alertas), argv[3]))
    for cod, a in alertas.items():
        print("  %s: %s" % (cod, "; ".join(a)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
