import csv
import os
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from montar_planilha import (  # noqa: E402
    _alertas_produto,
    achar_coluna_codigo,
    colunas_mantidas,
    formatar_medidas,
    gerar_saida,
    ler_csv,
    montar_descricao,
    num,
    validar_titulo,
)


class TestTitulo(unittest.TestCase):
    def test_titulo_ok(self):
        t = "Correia Dentada CT488 Uno Palio Mobi Siena 1.0 2010 A 2020"
        self.assertEqual(validar_titulo(t, False), [])

    def test_titulo_longo(self):
        t = "A" * 61
        self.assertIn("Título com 61 caracteres (máx. 60)", validar_titulo(t, False))

    def test_titulo_proibida(self):
        alertas = validar_titulo("Radiador Palio Frete Grátis", False)
        self.assertTrue(any("frete grátis" in a for a in alertas))
        self.assertTrue(any("original" in a for a in validar_titulo("Sensor Original Fiat", False)))
        self.assertEqual(validar_titulo("Sensor Original Fiat", True), [])

    def test_titulo_simbolo(self):
        self.assertTrue(validar_titulo("Radiador Palio!!", False))

    def test_titulo_vazio(self):
        self.assertIn("Título vazio", validar_titulo("", False))


class TestMedidas(unittest.TestCase):
    def test_medidas_estimadas(self):
        m = {"largura": 12.5, "altura": None, "profundidade": 3, "peso": 200}
        self.assertEqual(
            formatar_medidas(m, "estimado"),
            "Largura: aprox. 12,5 cm | Profundidade: aprox. 3 cm | Peso: aprox. 200 g",
        )

    def test_medidas_com_fonte(self):
        m = {"largura": "51,5", "altura": 37.8, "profundidade": 11, "peso": None}
        self.assertEqual(
            formatar_medidas(m, "fabricante"),
            "Largura: 51,5 cm | Altura: 37,8 cm | Profundidade: 11 cm",
        )

    def test_num(self):
        self.assertEqual(num("12,5"), 12.5)
        self.assertEqual(num("12.5"), 12.5)
        self.assertEqual(num(12), 12.0)
        self.assertIsNone(num(""))
        self.assertIsNone(num(None))


class TestDescricao(unittest.TestCase):
    def dados(self, **extra):
        d = {
            "nome": "Correia Dentada Contitech CT488",
            "especificacoes": ["129 dentes"],
            "codigos_ref": ["Contitech CT488"],
            "aplicacao": ["Fiat Palio 1.0 8V Flex 2011 em diante"],
            "peca": {"largura": 2.2, "altura": None, "profundidade": None, "peso": 120},
            "fonte_medidas_peca": "estimado",
        }
        d.update(extra)
        return d

    def test_descricao_ordem(self):
        desc = montar_descricao(self.dados(), "RODAPE")
        pos = [desc.index(s) for s in (
            "Correia Dentada Contitech CT488", "Especificações", "129 dentes",
            "Medidas da peça: Largura: aprox. 2,2 cm", "Códigos de referência",
            "Aplicação", "• Fiat Palio 1.0 8V Flex 2011 em diante", "RODAPE")]
        self.assertEqual(pos, sorted(pos))

    def test_descricao_sem_aplicacao(self):
        desc = montar_descricao(self.dados(aplicacao=[]), "RODAPE")
        self.assertIn("Consulte a compatibilidade na área de Perguntas.", desc)

    def test_descricao_completa_ordem(self):
        d = self.dados(
            sobre=["A correia dentada sincroniza o virabrequim e o comando.", "Segundo parágrafo."],
            conteudo_embalagem=["1 correia dentada"],
            sinais_troca=["Ruído na região da correia"],
            dicas=["Troque junto com o tensor"],
        )
        desc = montar_descricao(d, "RODAPE")
        pos = [desc.index(s) for s in (
            "Correia Dentada Contitech CT488",
            "Sobre o produto", "A correia dentada sincroniza", "Segundo parágrafo.",
            "Especificações", "Códigos de referência", "Aplicação",
            "O que vem na embalagem", "• 1 correia dentada",
            "Quando trocar", "• Ruído na região da correia",
            "Dicas de instalação e manutenção", "• Troque junto com o tensor",
            "RODAPE")]
        self.assertEqual(pos, sorted(pos))
        self.assertIn("A correia dentada sincroniza o virabrequim e o comando.\n\nSegundo parágrafo.", desc)

    def test_blocos_opcionais_omitidos(self):
        desc = montar_descricao(self.dados(), "RODAPE")
        for titulo in ("Sobre o produto", "O que vem na embalagem", "Quando trocar", "Dicas de"):
            self.assertNotIn(titulo, desc)

    def test_alerta_sobre_ausente_ou_curto(self):
        base = {"titulo": "Correia Dentada CT488 Uno Palio", "aplicacao": ["x"],
                "fonte_aplicacao": "fabricante", "conteudo_embalagem": ["1 peça"]}
        self.assertIn("Descrição sem 'Sobre o produto'", _alertas_produto(base))
        curto = dict(base, sobre=["Texto curto."])
        self.assertTrue(any("curto" in a for a in _alertas_produto(curto)))
        ok = dict(base, sobre=["x" * 400])
        self.assertEqual(_alertas_produto(ok), [])
        sem_emb = dict(ok, conteudo_embalagem=[])
        self.assertIn("Descrição sem 'O que vem na embalagem'", _alertas_produto(sem_emb))


class TestEntrada(unittest.TestCase):
    def test_ler_cp1252(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "e.csv")
            with open(p, "w", encoding="cp1252", newline="") as f:
                f.write("Código;Descrição\r\n1;Peça de borracha\r\n")
            cab, linhas = ler_csv(p)
            self.assertEqual(cab, ["Código", "Descrição"])
            self.assertEqual(linhas[0]["Descrição"], "Peça de borracha")
            self.assertEqual(achar_coluna_codigo(cab), "Código")

    def test_ler_byte_estranho(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "e.csv")
            with open(p, "wb") as f:
                f.write(b"Codigo;Descricao\r\n1;Pe\x81a\r\n")
            cab, linhas = ler_csv(p)
            self.assertEqual(linhas[0]["Codigo"], "1")

    def test_ler_virgula(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "e.csv")
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write("sku,nome\n10,Filtro\n")
            cab, linhas = ler_csv(p)
            self.assertEqual(achar_coluna_codigo(cab), "sku")
            self.assertEqual(linhas[0]["nome"], "Filtro")

    def test_ler_relatorio_autcom(self):
        # relatório Curva ABC do Autcom: filtros antes da tabela
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "e.csv")
            with open(p, "w", encoding="cp1252", newline="") as f:
                f.write("JR AUTO PECAS - MATRIZ\r\n\r\nMarca : 000012-COBREQ\r\n"
                        "Produto : TODOS\r\n\r\n"
                        "CÓDIGO;DESCRIÇÃO DO PRODUTO;LOC.FÍSICA;MARCA;QTD.ESTQ;VLR. ESTQ\r\n"
                        '"27904";"PASTILHA FR AGILE";"G 0229";"COBREQ";1,00;42,57\r\n')
            cab, linhas = ler_csv(p)
            self.assertEqual(achar_coluna_codigo(cab), "CÓDIGO")
            self.assertEqual(len(linhas), 1)
            self.assertEqual(linhas[0]["CÓDIGO"], "27904")
            self.assertEqual(colunas_mantidas(cab), ["CÓDIGO", "MARCA", "LOC.FÍSICA", "QTD.ESTQ"])

    def test_sem_coluna_codigo(self):
        with self.assertRaises(ValueError):
            achar_coluna_codigo(["nome", "preço"])


class TestSaida(unittest.TestCase):
    def test_saida_completa(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = os.path.join(tmp, "s.csv")
            alertas = gerar_saida(
                os.path.join(AQUI, "exemplo_entrada.csv"),
                os.path.join(AQUI, "exemplo_dados.json"),
                saida,
            )
            self.assertEqual(len(alertas), 2)
            self.assertNotIn("64265", alertas)
            self.assertIn("Sem aplicação: conferir", alertas["32803"])
            self.assertEqual(alertas["25395"], ["Não processado"])
            with open(saida, "rb") as f:
                self.assertTrue(f.read(3) == b"\xef\xbb\xbf")
            with open(saida, encoding="utf-8-sig", newline="") as f:
                leitor = csv.DictReader(f, delimiter=";")
                linhas = list(leitor)
            self.assertEqual(leitor.fieldnames, [
                "Codigo", "Marca", "Título", "Descrição", "Embalagem Largura (cm)",
                "Embalagem Altura (cm)", "Embalagem Profundidade (cm)", "Embalagem Peso (g)"])
            self.assertEqual(len(linhas), 3)
            por_cod = {l["Codigo"]: l for l in linhas}
            self.assertIn("\n", por_cod["64265"]["Descrição"])
            self.assertEqual(por_cod["25395"]["Título"], "")

    def test_colunas_mantidas(self):
        cab = ["CÓDIGO", "DESCRIÇÃO DO PRODUTO", "LOC.FÍSICA", "MARCA", "REFERÊNCIA", "QTD.ESTQ", "VLR. ESTQ"]
        self.assertEqual(colunas_mantidas(cab), ["CÓDIGO", "MARCA", "LOC.FÍSICA", "QTD.ESTQ"])
        self.assertEqual(colunas_mantidas(["SKU", "Localização Estoque", "Estoque"]),
                         ["SKU", "Localização Estoque", "Estoque"])
        self.assertEqual(colunas_mantidas(["Cod", "Localização física", "Marca"]),
                         ["Cod", "Marca", "Localização física"])


if __name__ == "__main__":
    unittest.main()
