"""Baixa as fotos dos kits do Syntra e renomeia no padrão do Hub.

Uso: py baixar_fotos.py LISTA.txt [PASTA]

LISTA.txt tem uma linha por foto, no formato SKU|posição|url
(a posição é a do kit no Syntra: a capa é a 1). As fotos vão para
PASTA/<SKU>/<SKU>-<posição + 1>.<ext>, ou seja, a capa vira <SKU>-2
(padrão do Hub, pedido do usuário). PASTA padrão:
C:\\Users\\Usuario\\Documents\\Claude Project\\Fotos Syntra
"""
import os
import sys
import urllib.parse
import urllib.request

PASTA_PADRAO = os.path.join(os.path.expanduser("~"), "Documents", "Claude Project", "Fotos Syntra")


def nome_arquivo(sku, posicao, url):
    """27904, 1, '.../1-2.jpg?token=...' -> '27904-2.jpg'"""
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"
    return "%s-%d%s" % (sku, int(posicao) + 1, ext)


def ler_lista(caminho):
    itens = []
    with open(caminho, encoding="utf-8-sig") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            sku, posicao, url = linha.split("|", 2)
            itens.append((sku.strip(), int(posicao), url.strip()))
    return itens


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    pasta = argv[2] if len(argv) > 2 else PASTA_PADRAO
    ok, falhas = 0, []
    for sku, posicao, url in ler_lista(argv[1]):
        destino = os.path.join(pasta, sku)
        os.makedirs(destino, exist_ok=True)
        arquivo = os.path.join(destino, nome_arquivo(sku, posicao, url))
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(arquivo, "wb") as f:
                f.write(r.read())
            ok += 1
        except Exception as e:  # link vencido (vale ~1 h), rede...
            falhas.append("%s posição %d: %s" % (sku, posicao, e))
    print("%d fotos baixadas, %d falhas -> %s" % (ok, len(falhas), pasta))
    for f in falhas:
        print("  " + f)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
