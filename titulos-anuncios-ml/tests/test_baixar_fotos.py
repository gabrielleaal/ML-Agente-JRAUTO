import os
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "scripts"))

from baixar_fotos import ler_lista, nome_arquivo  # noqa: E402


class TestNome(unittest.TestCase):
    def test_capa_vira_2(self):
        url = "https://x.supabase.co/storage/v1/object/sign/generated/a/b/1-2.jpg?token=abc.def"
        self.assertEqual(nome_arquivo("27904", 1, url), "27904-2.jpg")

    def test_arte_da_loja_webp(self):
        url = "https://x.supabase.co/storage/v1/object/sign/store/store-1-17.webp?token=z"
        self.assertEqual(nome_arquivo("27904", 10, url), "27904-11.webp")


class TestLista(unittest.TestCase):
    def test_ler_lista(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "l.txt")
            with open(p, "w", encoding="utf-8") as f:
                f.write("27904|1|https://a/1-1.jpg?token=x|y\n\n26388|2|https://a/2-1.jpg\n")
            itens = ler_lista(p)
            self.assertEqual(itens[0], ("27904", 1, "https://a/1-1.jpg?token=x|y"))
            self.assertEqual(itens[1][0], "26388")


if __name__ == "__main__":
    unittest.main()
