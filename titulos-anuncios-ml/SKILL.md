---
name: titulos-anuncios-ml
description: Cria título e descrição de anúncios NOVOS do Mercado Livre da JR Auto Peças a partir de um CSV de produtos (inclusive relatórios do Autcom, como a Curva ABC), no padrão da loja, pesquisando a compatibilidade de veículos (aplicação) e as medidas da peça e da embalagem, e devolve uma planilha CSV pronta para subir no Hub. Também gera no Syntra Images o kit de fotos de anúncio de cada produto e confere. Use sempre que mandarem um CSV de produtos para cadastrar, pedirem títulos ou descrições de anúncios, "criar anúncios novos", "planilha para o Hub" ou cadastro de produtos no ML.
---

# Títulos e descrições de anúncios novos (JR Auto Peças)

Você recebe um CSV de produtos novos e entrega uma planilha com **título, descrição, aplicação e medidas** de cada um, mais um **kit de fotos de anúncio** de cada produto, gerado no Syntra Images (conector com as ferramentas `criar_kit_de_fotos`, `ver_kit` e `refazer_fotos`). As fotos ficam no app do Syntra: **não baixe os kits para o computador** (pedido do usuário). A subida no ML é feita pelo Hub da loja: **não publique nem edite anúncios no Mercado Livre**.

O trabalho de julgamento é seu (ler, pesquisar, escrever o título). A montagem da descrição e as validações são do script `scripts/montar_planilha.py`, que garante o mesmo padrão em todo lote. Não escreva a descrição à mão.

## Passo 1 — Ler o CSV
- Leia o CSV e identifique as colunas: código (obrigatória: `Código`, `Cod` ou `SKU`), descrição, marca, código do fabricante/OEM, aplicação, medidas.
- Relatórios do Autcom (ex.: Curva ABC) vêm com linhas de filtros antes da tabela e em cp1252: **não recorte**, o script acha o cabeçalho sozinho. Na descrição do Autcom costumam vir a aplicação resumida (ex.: `AGILE/CELTA/CORSA 10/`) e os códigos equivalentes (ex.: `PD82 N377 HQ3001`): use como ponto de partida, nunca como confirmação.
- Se alguma coluna for ambígua, mostre ao usuário como você entendeu antes de seguir.
- Mais de 50 produtos: avise e processe em partes de 50, entregando cada parte.
- Mais de 10 produtos: faça a pesquisa em subagentes (seção abaixo).

## Lotes com mais de 10 produtos: pesquisa em subagentes
A pesquisa (Passos 2 a 4) é o que mais demora. Em lote grande, divida entre subagentes que rodam ao mesmo tempo. Testado em 28/10/2026: 15 produtos em 3 subagentes de 5 levaram 8 min 20 s, contra cerca de 18 min em sequência, e nenhum título ou descrição foi recusado pelo script. Até 10 produtos, faça tudo você mesmo: abrir subagentes não compensa.

1. **Divida** o CSV em partes de **5 produtos** e rode **no máximo 5 subagentes ao mesmo tempo** (lote de 50 = 2 rodadas de 5). Cada subagente custa cerca de 130 a 170 mil tokens.
2. **Cada subagente** (tipo `general-purpose`, em segundo plano) faz só os Passos 2, 3, 3b e 4 das suas 5 peças e grava `dados-parte-<N>.json` em `C:\Users\Usuario\Documents\Claude Project\Planilhas Títulos\tmp\`. Não use o scratchpad: o caminho dele passa de 260 caracteres e o Python não abre.
3. **O prompt de cada subagente** precisa trazer: o caminho desta SKILL.md para ler inteira; os 5 produtos com código, descrição do Autcom e marca; o significado dos prefixos dos códigos equivalentes (ex.: N = Cobreq, PD = Fras-le, HQ/HQJ = Bendix, RCPT = TRW, SYL = Syl, ECO = Ecopads, NKF = Nakata); como carregar o conector JR Mercado Livre com ToolSearch (`select:` com `ml_buscar_anuncios`, `ml_anuncio`, `ml_api_get` do servidor `mcp__f8303fc9-b23e-4d67-8568-81dc73e375c9__`) e `select:WebSearch,WebFetch`; o caminho exato do JSON de saída; e o que **não** fazer: não chamar o Syntra, não baixar fotos, não rodar `montar_planilha.py`, não publicar nem editar no ML, não fazer login, não mexer na skill. Peça que confira o JSON com py (abre, título até 60, "sobre" com 300 ou mais) e responda em até 200 palavras, uma linha por código: anúncio da loja usado, fonte da aplicação, foto base, `tem_fio`, alertas.
4. **Você (agente principal)** junta os JSON num só `dados.json`, apaga **só** os `dados-parte-*.json` da pasta `tmp` (nunca outros arquivos de `Planilhas Títulos`), revisa os títulos para manter o mesmo padrão entre as partes, e segue daqui em diante sozinho: Passo 5 (planilha), conferência das fotos base, Passo 6 (Syntra) e Passo 7.
5. **Fotos e busca no ML pelo navegador:** o WebFetch dá 403 nas fotos e na busca do ML, então tudo isso passa pelo navegador embutido. Mande no prompt as regras da busca no navegador (Passo 2): aba própria, esperar a página carregar, versão `2X-F` da foto, conferir com screenshot, parar no captcha, nada de compra, conta ou dados pessoais. Teste de 29/10/2026: 1 subagente, 3 produtos sem anúncio da loja, 3 min 48 s, sem captcha, 2 fotos boas e 1 produto sem foto limpa (todas com caixa, selo ou marca d'água). Vários subagentes no navegador ao mesmo tempo **ainda não foram testados**: comece com no máximo 2 e, se algum voltar com captcha, peça ao usuário para completar e reenvie só os produtos que faltaram. Antes do Syntra, **abra você mesmo cada `foto_url`** escolhida e confira; foto com carro, texto, caixa ou outras peças não serve.
6. **Confira `tem_fio`**: avisador de desgaste metálico (lâmina que chia) **não é fio**. `tem_fio: true` só para sensor elétrico com cabo e conector.

## Passo 2 — Pesquisar cada produto
Identifique a peça pelo **código do fabricante** (ex.: CT488, DS1809, W610/10, RA32540). Se o CSV não tiver, tire da descrição ou procure pela marca + descrição.

**Primeiro, o anúncio da própria loja.** Muitos produtos já têm anúncio da JR no ML (outra variação, outro título). Procure pelo conector JR Mercado Livre:
1. `ml_buscar_anuncios` com `sku` = código do produto (se não achar, com `texto` = código do fabricante).
2. Achou: `ml_anuncio` traz a ficha técnica (medidas e peso da embalagem, "Código OEM", "Inclui sensores de desgaste", posição, quantidade), a descrição (com códigos de referência por marca e aplicação com anos) e as compatibilidades. `ml_api_get` com `/items/<ID>?attributes=pictures` traz as fotos (`secure_url`).
3. Esses dados são da loja: use para embalagem (fonte `planilha`), códigos e aplicação, e **a primeira foto como foto base** do Syntra. Ainda confira a aplicação no fabricante quando der, e anote em `alertas` o id do anúncio usado.
4. A API pública de busca (`/sites/MLB/search`) dá 403: não use.

**Depois, a busca do ML no navegador embutido** (para produto **sem anúncio da loja** ou com foto ruim). A conta do usuário fica conectada no navegador do Claude (ferramentas `mcp__Claude_Browser__*`).
1. Abra uma **aba própria** com `tabs_create`, use o `tabId` dela em tudo e feche no final (`tabs_close`). Não mexa nas outras abas.
2. Busque `https://lista.mercadolivre.com.br/pastilha-freio-cobreq-n1286` (troque pelo tipo da peça, marca e código sem hífen). Se a leitura vier vazia, a página ainda está carregando: espere 1 a 2 s e leia de novo.
3. Abra anúncios com o **mesmo código** no título e pegue a foto pela galeria (`javascript_tool` nas tags `img` ou no `og:image`). Prefira a versão grande `D_NQ_NP_2X_...-F.webp` (cerca de 1200 px); a `-O` tem só uns 500 px.
4. Abra a imagem na sua aba e confira com screenshot (regras da foto base, abaixo). No máximo 3 anúncios por produto. A primeira foto da galeria costuma ter a caixa: veja as outras.
5. Aproveite para comparar a aplicação e os códigos equivalentes, mas os anúncios de terceiros são fonte `web`: confirme no fabricante quando der.
6. **Captcha ou "Por segurança, complete esta etapa": pare na hora.** Não tente resolver nem contornar. Peça ao usuário para completar a verificação no navegador do Claude e continue depois. Sem login (tela "acesse sua conta"), peça ao usuário para entrar; você nunca digita senha.
7. Proibido: comprar, carrinho, favoritar, perguntar a vendedor, abrir páginas da conta (compras, dados, endereço), sair da conta, mudar configurações. Não repita nome, endereço ou outros dados pessoais que aparecem nas páginas.

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

**Foto da peça (base para o Syntra):**
1. Ordem das fontes: **primeira foto do anúncio da própria loja** (acima); depois **anúncios de outros vendedores no ML pelo navegador** (acima); depois o site do fabricante; depois catálogo ou loja grande, sempre pelo código do fabricante. Use o **link direto da imagem** (.jpg, .jpeg, .png ou .webp, até 10 MB).
2. A foto precisa mostrar **a mesma peça** (mesmo código), inteira, nítida, de preferência em fundo branco, **sem marca d'água**, sem texto e sem outras peças junto. Banner de lançamento (com texto, desenho técnico, carro ao fundo) não serve. Foto de peça parecida não serve: o Syntra copia o que vê. Abra a imagem no navegador embutido para conferir antes de usar.
3. Se achar uma segunda boa foto da mesma peça em outro ângulo, guarde também (vira `referencia_url`).
4. Anote em `tem_fio` se a peça tem sensor elétrico com fio, cabo ou conector (ficha "Inclui sensores de desgaste", ou o que a foto mostra). A ficha do ML às vezes marca "sensor: Sim" para o avisador metálico (lâmina que chia), que **não** é fio: confie na foto. O Syntra **inventa cabo de sensor** em peças que não têm, se ninguém avisar.
5. Se não achar foto confiável, deixe `foto_url: null` e ponha em `alertas` "Sem foto base: kit de fotos não gerado".

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
    "foto_url": "https://.../ct488.jpg",
    "referencia_url": null,
    "tem_fio": false,
    "alertas": []
  }
}
```
- `nome`: nome completo da peça, que vira a primeira linha da descrição.
- `especificacoes`: dados técnicos (dentes, vias, comprimento do cabo, material...). Não repita as medidas aqui: o script já põe a linha "Medidas da peça".
- `foto_url` / `referencia_url` / `tem_fio`: foto base da peça e se ela tem sensor, fio ou conector (Passo 2). O script da planilha ignora esses campos; eles servem para o Passo 6.
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

## Passo 6 — Gerar os kits de fotos no Syntra
Depois que a planilha estiver montada (títulos já validados), gere um kit para cada produto que tem `foto_url`.

1. **Criar:** chame `criar_kit_de_fotos` para cada produto, um atrás do outro (cada chamada responde na hora com o id do kit):
   - `produto`: o **SKU** do produto (a chave do `dados.json`, ex. `27904`), por pedido do usuário, e não o título do anúncio;
   - `foto_url`: a `foto_url` do produto; `referencia_url`, se houver;
   - `carro`: o primeiro modelo do título (o mais vendido) com o ano inicial da aplicação dele, ex. `{"modelo": "Palio", "ano": "2010"}`. Sem aplicação, não mande `carro` (capa só com a peça);
   - `total` 10 e `fotos_da_loja` no padrão (capa, 7 fotos e as 2 artes da loja);
   - `tipos`: **sempre as 7 cenas livres abaixo, nesta ordem** (pedido do usuário: nada de "peça instalada no carro", e no lugar dela a bancada de oficina). Os tipos prontos do Syntra não aceitam instrução e inventaram cabo de sensor em peça sem sensor; as cenas livres resolvem isso. Troque `<PEÇA>` pelo que aparece na foto base (ex.: "o jogo de 4 pastilhas de freio dianteiras", "a correia dentada") e `<FIO>` por:
     - peça sem fio (`tem_fio: false`): "A peça NÃO tem sensor, fio, cabo nem conector: não desenhe nenhum."
     - peça com fio (`tem_fio: true`): "A peça tem <o sensor/chicote/conector> exatamente como na foto de referência."
     ```json
     [
       {"nome": "Frente, fundo branco", "descricao": "Foto de estúdio em fundo branco liso: <PEÇA> vista de frente, idêntica à foto de referência, sem inventar clipes, furos ou detalhes. <FIO>"},
       {"nome": "Lateral, fundo branco", "descricao": "Foto de estúdio em fundo branco liso: <PEÇA> vista de lado, mostrando a espessura, idêntica à foto de referência. <FIO>"},
       {"nome": "Detalhe de perto, fundo branco", "descricao": "Close em fundo branco liso de <PEÇA>, mostrando o acabamento e os detalhes, fiel à foto de referência. <FIO>"},
       {"nome": "Mecânico segurando a peça", "descricao": "Mão de mecânico segurando <PEÇA>, com oficina mecânica levemente desfocada ao fundo. Manter a peça idêntica à foto de referência. <FIO>"},
       {"nome": "Peça ao lado da embalagem", "descricao": "Fundo branco: <PEÇA> ao lado da embalagem da marca, como na foto de referência. <FIO>"},
       {"nome": "Ângulo de trás, fundo branco", "descricao": "Fundo branco liso: <PEÇA> vista por trás, com o mesmo contorno da foto de referência, sem inventar detalhes. <FIO>"},
       {"nome": "Peça na bancada da oficina", "descricao": "Foto tirada com celular de <PEÇA> sobre uma bancada de metal de uma oficina mecânica, com ferramentas e o fundo de oficina levemente desfocado, luz natural de galpão. Manter a peça idêntica à foto de referência. <FIO>"}
     ]
     ```
   A **capa** é feita pelo Syntra e não aceita instrução: confira com atenção e, se vier errada, refaça a posição 1.
   Guarde o id de cada kit junto do código do produto. Se der erro de limite diário ou "recusou a chave configurada no servidor", pare de criar, siga com os kits já criados e avise quais produtos ficaram sem kit (o segundo erro é da configuração do Syntra: quem cuida do app precisa ver a chave ou o limite).
2. **Esperar:** cada kit leva cerca de 1 minuto. Crie todos primeiro e só depois comece a conferir, começando pelo primeiro criado.
3. **Conferir:** abra cada kit com `ver_kit` e compare cada foto gerada com a foto base: formato, cor, conectores, furos, quantidade de dentes ou vias, inscrições. Ainda pendente: espere e veja de novo. Falhou: refaça.
4. **Refazer:** chame `refazer_fotos` com as `posicoes` das fotos em que a peça saiu diferente (a capa é a 1). Refaça **no máximo 1 vez** por kit. Se continuar diferente, não insista: anote as posições para o usuário revisar no app do Syntra.
5. Custo: cerca de US$ 0,01 por foto gerada ou refeita (um kit padrão dá cerca de US$ 0,08). Lotes acima de 20 produtos: avise o custo estimado antes de criar.

## Passo 7 — Entregar
Entregue o CSV de saída e um resumo curto:
- quantos produtos estão prontos e quantos têm alerta;
- os principais motivos dos alertas (ex.: "4 sem aplicação, 12 com medidas estimadas da embalagem");
- **fotos:** quantos kits ficaram prontos no Syntra (SKU e link do kit no app), quais produtos ficaram sem kit (sem foto base, limite diário, erro do Syntra) e quais kits têm fotos para revisar (SKU, link do kit no app e posições);
- lembrete: medidas da **embalagem** estimadas afetam frete e Full, então vale pesar os itens de maior giro.

## O que a planilha traz
Só estas colunas (pedido do usuário): Código, Marca, Localização física e Quantidade em estoque (as únicas mantidas do CSV de entrada, quando existirem), Título, Descrição e as medidas da embalagem (Largura, Altura, Profundidade em cm e Peso em g). Aplicação e medidas da peça aparecem dentro da descrição; não crie outras colunas. O CSV sai com separador `;` e UTF-8, e abre direto no Excel.
