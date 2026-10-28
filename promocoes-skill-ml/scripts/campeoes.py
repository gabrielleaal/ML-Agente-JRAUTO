#!/usr/bin/env python3
"""Seleção dos anúncios campeões para as promoções de dias iguais (10.10, 11.11...).

Dois comandos, usados em sequência (o passo a passo completo está em
references/campeoes.md):

1) vendas   - critérios 1 e 2: vendeu bem na janela (60 dias) e não está em queda.
   python3 campeoes.py vendas --hoje AAAA-MM-DD --vendas vendas.csv \
       [--excluir ARQ ...] [--janela 60] [--min-vendas 3] [--queda-max 0.30]

   vendas.csv, uma linha por item vendido (pedidos pagos):
       AAAA-MM-DD,MLB123456789,quantidade

   Saída (TAB): item  un_janela  un30  prev  OK|FORA  motivo   (mais vendidos primeiro)
   un30 = últimos 30 dias; prev = dias anteriores dentro da janela (janela-30 dias).
   Queda: un30 mais de 30% abaixo da média de 30 dias de prev.

2) avaliar  - estoque, regra de desconto (6%, até 7%), ranking e top N.
   python3 campeoes.py avaliar --dados dados.csv [--excluir ARQ ...] \
       [--estoque-min 5] [--top 50]

   dados.csv, uma linha por anúncio (sem cabeçalho; campos que não se aplicam
   ficam vazios):
       id,un_janela,preco_original,estoque,status,min,max
   status = ja_esta (já participa da promoção) ou candidato.
   min/max = min_discounted_price / max_discounted_price da promoção.

   Saída (TAB): item  ENTRAR|JA_ESTA|PULAR|EXCLUIDO|FORA_DO_TOP  preco  desconto%  faturamento  motivo
   Ordenada por faturamento (un_janela x preco_original), do maior para o menor.
   Os N primeiros que são ENTRAR ou JA_ESTA formam o top N; o resto vira FORA_DO_TOP.

Exclusões (--excluir): arquivos com IDs MLB (qualquer texto serve; todo MLB<n>
encontrado vira exclusão), por exemplo água/radiador, inelegíveis e os de nota baixa.
"""
import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calcular_precos import calcular, carregar_exclusoes  # noqa: E402


def ler_csv(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        for linha in csv.reader(f):
            if not linha or not linha[0].strip() or linha[0].lstrip().startswith("#"):
                continue
            yield [c.strip() for c in linha]


def dec(valor):
    if valor is None or valor == "":
        return None
    try:
        return Decimal(valor)
    except InvalidOperation:
        return None


def cmd_vendas(a):
    hoje = date.fromisoformat(a.hoje)
    excluidos = carregar_exclusoes(a.excluir or [])
    un90, un30, prev60 = defaultdict(int), defaultdict(int), defaultdict(int)
    for linha in ler_csv(a.vendas):
        dia, item, qtd = linha[0][:10], linha[1].upper(), int(linha[2])
        dias = (hoje - date.fromisoformat(dia)).days
        if dias < 0 or dias >= a.janela:
            continue
        un90[item] += qtd
        if dias < 30:
            un30[item] += qtd
        else:
            prev60[item] += qtd

    for item in sorted(un90, key=lambda i: -un90[i]):
        u90, u30, p60 = un90[item], un30[item], prev60[item]
        if item in excluidos:
            estado, motivo = "FORA", "lista de exclusão"
        elif u90 < a.min_vendas:
            estado, motivo = "FORA", f"menos de {a.min_vendas} vendas em {a.janela} dias"
        elif p60 > 0 and Decimal(u30) < (1 - Decimal(str(a.queda_max))) * Decimal(p60) * 30 / Decimal(a.janela - 30):
            estado, motivo = "FORA", "vendas em queda"
        else:
            estado, motivo = "OK", ""
        print(f"{item}\t{u90}\t{u30}\t{p60}\t{estado}\t{motivo}")


def cmd_avaliar(a):
    excluidos = carregar_exclusoes(a.excluir or [])
    linhas = []
    for c in ler_csv(a.dados):
        c += [""] * (7 - len(c))
        item = c[0].upper()
        un90 = int(c[1] or 0)
        original = dec(c[2])
        estoque = int(c[3] or 0)
        status = c[4].lower()
        faturamento = (Decimal(un90) * original) if original else Decimal(0)
        res = dict(item=item, fat=faturamento, preco="-", desc="-")

        if item in excluidos:
            res.update(estado="EXCLUIDO", motivo="lista de exclusão")
        elif estoque < a.estoque_min:
            res.update(estado="PULAR", motivo=f"estoque {estoque} abaixo de {a.estoque_min}")
        elif status == "ja_esta":
            res.update(estado="JA_ESTA", motivo="já participa da promoção")
        else:
            mn, mx = dec(c[5]), dec(c[6])
            if original is None or mn is None or mx is None:
                res.update(estado="PULAR", motivo="faixa de preço da promoção ausente")
            else:
                preco, motivo = calcular(str(original), str(mn), str(mx))
                if preco is None:
                    res.update(estado="PULAR", motivo=motivo)
                else:
                    desc = (original - preco) / original * 100
                    res.update(estado="ENTRAR", preco=str(preco), desc=f"{desc:.2f}%", motivo=motivo)
        linhas.append(res)

    linhas.sort(key=lambda r: -r["fat"])
    contados = 0
    for r in linhas:
        if r["estado"] in ("ENTRAR", "JA_ESTA"):
            contados += 1
            if contados > a.top:
                r.update(estado="FORA_DO_TOP", motivo=f"fora dos {a.top} primeiros")
        print(f"{r['item']}\t{r['estado']}\t{r['preco']}\t{r['desc']}\t{r['fat']:.2f}\t{r['motivo']}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("vendas")
    v.add_argument("--hoje", required=True)
    v.add_argument("--vendas", required=True)
    v.add_argument("--excluir", action="append")
    v.add_argument("--janela", type=int, default=60)
    v.add_argument("--min-vendas", type=int, default=3)
    v.add_argument("--queda-max", type=float, default=0.30)
    v.set_defaults(fn=cmd_vendas)

    e = sub.add_parser("avaliar")
    e.add_argument("--dados", required=True)
    e.add_argument("--excluir", action="append")
    e.add_argument("--estoque-min", type=int, default=5)
    e.add_argument("--top", type=int, default=50)
    e.set_defaults(fn=cmd_avaliar)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
