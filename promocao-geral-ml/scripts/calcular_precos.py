#!/usr/bin/env python3
"""Calcula o preço de entrada na promoção Geral: desconto de no máximo 6%
(limite de 7% se a promoção exigir mais). Evita erro de centavo fazendo as
contas em Decimal e arredondando PARA CIMA, para o desconto nunca passar do teto.

Uso:
    python3 calcular_precos.py [--excluir ARQ_IDS ...] < candidatos.csv

Entrada (stdin), uma linha por anúncio:
    ID,preco_original,min_discounted_price,max_discounted_price

--excluir ARQ_IDS  arquivo com IDs MLB (um por linha, ou texto livre: qualquer
                   MLB<números> encontrado vira exclusão). Pode repetir a opção.

Saída, separada por TAB:
    ID  ENTRAR   preco  desconto%  6% | ate 7%
    ID  PULAR    -      -          motivo
    ID  EXCLUIDO -      -          lista de exclusão
"""
import re
import sys
from decimal import Decimal, ROUND_CEILING

CENT = Decimal("0.01")


def carregar_exclusoes(caminhos):
    ids = set()
    for caminho in caminhos:
        with open(caminho, encoding="utf-8") as f:
            ids.update(re.findall(r"MLB\d+", f.read().upper()))
    return ids


def calcular(original, minimo, maximo):
    o, mn, mx = Decimal(original), Decimal(minimo), Decimal(maximo)
    p6 = (o * Decimal("0.94")).quantize(CENT, rounding=ROUND_CEILING)
    p7 = (o * Decimal("0.93")).quantize(CENT, rounding=ROUND_CEILING)
    if p6 < mn:
        return None, "6% fica abaixo do mínimo da faixa permitida"
    if p6 <= mx:
        return p6, "6%"
    if mx >= p7:
        return mx, "ate 7%"
    return None, "exigia mais de 7%"


def main():
    args = sys.argv[1:]
    arquivos = []
    while args:
        if args[0] == "--excluir" and len(args) > 1:
            arquivos.append(args[1])
            args = args[2:]
        else:
            sys.exit(__doc__)
    excluidos = carregar_exclusoes(arquivos)

    for linha in sys.stdin:
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        item, original, minimo, maximo = [c.strip() for c in linha.split(",")]
        item = item.upper()
        if item in excluidos:
            print(f"{item}\tEXCLUIDO\t-\t-\tlista de exclusão")
            continue
        preco, motivo = calcular(original, minimo, maximo)
        if preco is None:
            print(f"{item}\tPULAR\t-\t-\t{motivo}")
        else:
            desconto = (Decimal(original) - preco) / Decimal(original) * 100
            print(f"{item}\tENTRAR\t{preco}\t{desconto:.2f}%\t{motivo}")


if __name__ == "__main__":
    main()
