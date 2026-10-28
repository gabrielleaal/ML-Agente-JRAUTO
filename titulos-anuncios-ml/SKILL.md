---
name: titulos-anuncios-ml
description: Cria título e descrição de anúncios NOVOS do Mercado Livre da JR Auto Peças a partir de um CSV de produtos, no padrão da loja, pesquisando na web a compatibilidade de veículos (aplicação) e as medidas da peça e da embalagem, e devolve uma planilha CSV pronta para subir no Hub. Use sempre que mandarem um CSV de produtos para cadastrar, pedirem títulos ou descrições de anúncios, "criar anúncios novos", "planilha para o Hub" ou cadastro de produtos no ML.
---

# Títulos e descrições de anúncios novos (JR Auto Peças)

Você recebe um CSV de produtos novos e entrega uma planilha com **título, descrição, aplicação e medidas** de cada um. A subida no ML é feita pelo Hub da loja: **não publique nem edite anúncios no Mercado Livre**.

O trabalho de julgamento é seu (ler, pesquisar, escrever o título). A montagem da descrição e as validações são do script `scripts/montar_planilha.py`, que garante o mesmo padrão em todo lote. Não escreva a descrição à mão.

## Passo 1 — Ler o CSV
- Leia o CSV e identifique as colunas: código (obrigatória: `Código`, `Cod` ou `SKU`), descrição, marca, código do fabricante/OEM, aplicação, medidas.
- Se alguma coluna for ambígua, mostre ao usuário como você entendeu antes de seguir.
- Mais de 50 produtos: avise e processe em partes de 50, entregando cada parte.

## Passo 2 — Pesquisar cada produto
Identifique a peça pelo **código do fabricante** (ex.: CT488, DS1809, W610/10, RA32540). Se o CSV não tiver, tire da descrição ou procure pela marca + descrição.

**Aplicação (compatibilidade):**
1. Catálogo do fabricante pelo código da peça.
2. Se não achar, fontes de confiança: catálogos de distribuidores e lojas grandes de autopeças.
3. **Nunca estime.** Se as fontes discordarem ou não houver nenhuma, deixe `aplicacao: []`, e o script marca "Sem aplicação: conferir".
4. Formato de cada item: `Montadora Modelo Motor Válvulas Combustível Ano a Ano`, por exemplo `Fiat Palio 1.0 8V Flex 2009 em diante` ou `Fiat Siena 1.4 2001 a 2013`.
5. Guarde o link em `link_aplicacao` e a fonte em `fonte_aplicacao` (`fabricante`, `loja/catálogo`, `planilha` ou `web`).

**Medidas da peça e da embalagem** (largura, altura, profundidade em cm e peso em g):
1. Fabricante, depois loja ou catálogo.
2. Se não achar, **estime** a partir de peças iguais ou parecidas (mesmo tipo e tamanho) e marque `"estimado"`. A descrição sai com "aprox."
3. Use medidas do CSV quando existirem (fonte `planilha`).

Da web, use só dados técnicos. Nunca copie texto de outros sites.

## Passo 3 — Escrever o título
Padrão: **Peça + Código + Modelos + Motor + Anos**, com a marca da peça só se sobrar espaço.
- **Máximo de 60 caracteres.** Aproveite o espaço, mas não passe.
- Modelos mais vendidos e mais buscados primeiro (Palio, Uno, Gol, Onix, Strada etc.).
- Proibido: "promoção", "oferta", "frete grátis", "original" (só se a peça for original de montadora, com `"original": true`), símbolos `! * % $ #`.
- Primeira letra de cada palavra maiúscula, como nos anúncios da loja.

Títulos que vendem bem na loja, para usar como referência:
- `Radiador Água Palio Siena Idea 1.0 1.4 1.8 2001 A 2017` (o campeão: modelos, motor e anos)
- `Sensor De Rotação Uno Palio Doblo Punto Ds1809 2vias`
- `Filtro De Óleo W610/10 Palio Siena Lancer Uno Strada Pajero`
- `Correia Dentada Ct846 Contitech Gol Parati Fox 2000 A 2016`

## Passo 3b — Escrever o conteúdo da descrição
A descrição precisa ser **bem detalhada**, como nos anúncios da loja. O comprador e o mecânico devem entender o que a peça faz, se ela serve no carro e o que vem na caixa, sem precisar perguntar. O script monta os blocos nesta ordem:

1. **Nome** (`nome`)
2. **Sobre o produto** (`sobre`): de 2 a 4 parágrafos escritos por você, com **no mínimo 300 caracteres** no total:
   - o que a peça faz no carro e em qual sistema ela trabalha (arrefecimento, distribuição, injeção, freio...);
   - como ela funciona, em linguagem simples (por exemplo: "o sensor de rotação envia ao módulo de injeção o sinal que sincroniza o tempo de injeção e o avanço da ignição");
   - o que acontece quando ela falha (por exemplo: superaquecimento, motor que não pega, quebra de válvulas);
   - construção e qualidade: material, padrão de encaixe do original, marca.
3. **Especificações** (`especificacoes`, mais a linha automática "Medidas da peça")
4. **Códigos de referência** (`codigos_ref`): o código da marca, os **equivalentes de outras marcas** (Gates, Dayco, Goodyear, Cofap, Nakata, Bosch...) e os números originais da montadora. É o que o mecânico usa para conferir.
5. **Aplicação** (`aplicacao`)
6. **O que vem na embalagem** (`conteudo_embalagem`), obrigatório: quantidade e o que **não** acompanha. Por exemplo: "1 correia dentada (não acompanha tensor)" ou "1 radiador (não acompanha tampa nem cebolão)".
7. **Quando trocar** (`sinais_troca`): de 3 a 5 sintomas de defeito e o intervalo de troca recomendado, quando houver.
8. **Dicas de instalação e manutenção** (`dicas`): de 2 a 4 dicas práticas. Por exemplo: trocar a correia junto com o tensor e a bomba d'água, trocar o líquido de arrefecimento, apertar com o torque do fabricante, apagar os códigos de falha da injeção depois da troca.
9. Rodapé fixo da loja (Sobre a Empresa, Avisos, Lembrete), que o script põe sozinho.

Regras:
- Escreva **com suas palavras**. Nunca copie texto de outros sites.
- Só afirme o que é verdade para aquela peça. Na dúvida sobre um dado técnico, deixe de fora ou ponha em `alertas`.
- Sem promessas que a loja não pode garantir ("dura para sempre", "melhor do mercado"), sem preço, sem frete e sem contato externo (telefone, site, WhatsApp), que o ML proíbe.

## Passo 4 — Gravar o `dados.json`
Um objeto por código do produto (a chave é o código exatamente como está no CSV):
```json
{
  "32803": {
    "titulo": "Correia Dentada CT488 Uno Palio Mobi Siena 1.0 2010 A 2020",
    "nome": "Correia Dentada Contitech CT488",
    "sobre": ["A correia dentada sincroniza o giro do virabrequim com o do comando de válvulas...", "Fabricada em borracha HNBR..."],
    "conteudo_embalagem": ["1 correia dentada (não acompanha tensor)"],
    "sinais_troca": ["Ruído ou chiado na região da distribuição", "Trincas ou dentes gastos na inspeção"],
    "dicas": ["Troque junto com o tensor e verifique a bomba d'água"],
    "original": false,
    "especificacoes": ["129 dentes", "Material: borracha HNBR"],
    "codigos_ref": ["Contitech CT488", "Gates 40859X22", "Dayco 129P8S220H"],
    "aplicacao": ["Fiat Mobi 1.0 8V Flex 2016 em diante"],
    "fonte_aplicacao": "fabricante",
    "link_aplicacao": "https://...",
    "peca": {"largura": 2.2, "altura": 0.5, "profundidade": 92, "peso": 120},
    "embalagem": {"largura": 24, "altura": 3, "profundidade": 27, "peso": 206},
    "fonte_medidas_peca": "fabricante",
    "fonte_medidas_embalagem": "estimado",
    "link_medidas": "https://...",
    "alertas": []
  }
}
```
- `nome`: nome completo da peça, que vira a primeira linha da descrição.
- `especificacoes`: dados técnicos (dentes, vias, comprimento do cabo, material...). Não repita as medidas aqui: o script já põe a linha "Medidas da peça".
- `alertas`: tudo o que o usuário deve conferir, por exemplo marca do CSV diferente da encontrada, código com mais de uma versão ou aplicação parcial.
- Valor desconhecido: `null`.

Salve `dados.json` ao lado do CSV de entrada (ou no scratchpad).

## Passo 5 — Montar a planilha
```
py scripts/montar_planilha.py ENTRADA.csv dados.json SAIDA.csv
```
(o caminho de `scripts/` é relativo à pasta desta skill; em Linux/macOS use `python3`)

O script imprime `N produtos, M com alerta`. Se houver alerta de **título** (tamanho, palavra proibida, símbolo) ou de **descrição** ("Sobre o produto" ausente ou curto, embalagem ausente), corrija no JSON e rode de novo, no máximo 2 vezes. Os outros alertas saem só no terminal (não vão para a planilha): repasse-os ao usuário no resumo.

Nome da saída: `titulos-<nome do CSV de entrada>.csv`, sempre na pasta `C:\Users\Usuario\Documents\Claude Project\Planilhas Títulos` (pedido do usuário; não salve ao lado da entrada).

## Passo 6 — Entregar
Entregue o CSV de saída e um resumo curto:
- quantos produtos estão prontos e quantos têm alerta;
- os principais motivos dos alertas (ex.: "4 sem aplicação, 12 com medidas estimadas da embalagem");
- lembrete: medidas da **embalagem** estimadas afetam frete e Full, então vale pesar os itens de maior giro.

## O que a planilha traz
Só estas colunas (pedido do usuário): Código, Marca, Localização física e Quantidade em estoque (as únicas mantidas do CSV de entrada, quando existirem), Título, Descrição e as medidas da embalagem (Largura, Altura, Profundidade em cm e Peso em g). Aplicação e medidas da peça aparecem dentro da descrição; não crie outras colunas. O CSV sai com separador `;` e UTF-8, e abre direto no Excel.
