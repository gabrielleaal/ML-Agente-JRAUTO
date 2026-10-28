---
name: promocao-geral-ml
description: Rotina mensal da JR Auto Peças no Mercado Livre - todo dia 30, coloca os anúncios ativos da loja na promoção "Geral" do MÊS SEGUINTE (ex. no dia 30 de outubro, "Geral Novembro"), com desconto de no máximo 6% (limite 7% se a promoção exigir mais). Deixa sempre de fora a água desmineralizada (61801) e o Radiador do Palio (64265), com todas as variações, e ignora os anúncios inelegíveis (que o Mercado Livre recusa), guardando os novos na memória. Também escolhe os 50 anúncios campeões de venda e os coloca nas promoções de dias iguais da plataforma (1.1, 10.10, 11.11, 12.12...), com as mesmas regras. Use sempre que pedirem os campeões, a promoção 11.11 ou 10.10, ou para colocar os produtos / a loja toda na promoção Geral do próximo mês, rodar a promoção do dia 30, ou quando a tarefa agendada mensal do dia 30 rodar, mesmo que a pessoa não cite a regra de 6%.
---

# Promoções no Mercado Livre (JR Auto Peças)

Esta skill tem duas rotinas, com as mesmas regras de desconto e de exclusão:

1. **Promoção Geral do mês seguinte** (abaixo): todos os anúncios ativos, todo dia 30.
2. **Campeões nas promoções de dias iguais** (seção no fim): os 50 anúncios de melhor desempenho nas promoções da plataforma 10.10, 11.11 etc., sob demanda. Detalhes em `references/campeoes.md`.

## Rotina 1: Promoção Geral do mês seguinte

Os produtos da loja ficam sempre em promoção. Todo dia 30 de cada mês, colocar os anúncios ativos na promoção do **mês seguinte**, chamada **"Geral <mês seguinte>"** (no dia 30 de outubro entra em "Geral Novembro"; em 30 de novembro, "Geral Dezembro"; em 30 de dezembro, "Geral Janeiro"). O Lucas deixa essa promoção criada antes. Assim, quando o mês virar, os produtos já estão na promoção nova.

A pessoa só quer entrar na promoção, sem mexer em mais nada. O desconto tem teto, alguns produtos nunca entram e alguns anúncios o Mercado Livre não aceita.

Ferramentas: `ml_buscar_anuncios`, `ml_promocoes`, `ml_promocao_entrar`, `ml_api_get` (só leitura) e `ml_anuncio` do servidor Mercado Livre da JR (carregue com ToolSearch se não estiverem disponíveis), mais as ferramentas de memória. O SKU de cada anúncio é o código do produto no Autcom.

## Regras que não podem ser quebradas

1. **Desconto máximo de 6%.** Se a promoção não permitir entrar com 6%, o limite absoluto é **7%**. Se passar de 7%, o anúncio fica de fora.
2. **Nunca entram** (nem a pedido, nem por engano de busca): a **água desmineralizada** (código 61801) e o **Radiador do Palio** (código 64265), com todas as variações de marca, tamanho e anúncios duplicados. A lista completa de IDs e a regra por título estão em `references/excluidos-permanentes.md`. Leia esse arquivo em toda rodada.
3. **Anúncios inelegíveis ficam fora, sem nova tentativa** (ver a seção seguinte).
4. Só a promoção "Geral" do mês seguinte. Nunca entrar em outras (11.11, Impulsione suas vendas, cupons, Lightning etc.), mesmo que o Mercado Livre sugira, e nunca na "Geral" do mês atual.
5. Nunca usar `confirmar_desconto_alto`. Nunca tirar anúncio de promoção, nem mudar preço fora da promoção.

Por que essas regras: o desconto vem da margem da loja e esses produtos não comportam promoção. A busca só pelo SKU não basta, porque existem anúncios sem SKU cadastrado (já aconteceu com uma água e um radiador), por isso a busca por título também é obrigatória. Na dúvida, deixar de fora e avisar no relatório vale mais do que entrar.

## Anúncios inelegíveis

Anúncios ativos que ficam sem promoção costumam ter problema na experiência de compra, e o Mercado Livre os recusa. O Lucas pediu para lembrar deles e ignorá-los direto nas próximas rodadas.

- **No início da rodada**, leia a memória `/areas/ml-promocao-inelegiveis.md` (`memory_read`) e junte esses IDs à lista de exclusão. Se a memória não estiver disponível, use `references/inelegiveis-2026-10-21.md` como cópia de segurança e avise no relatório.
- **Durante a rodada**, se `ml_promocao_entrar` recusar com "não é candidato a SELLER_CAMPAIGN ... Candidatas: []", o anúncio é inelegível. Anote o ID, não tente de novo e não mexa no preço.
- **No fim da rodada**, acrescente todos os IDs novos à memória com uma única escrita (`memory_read` para pegar a versão, depois `memory_append`), no formato:
  `- [stated] inelegíveis identificados em DD/MM/AAAA (N anúncios recusados na "Geral <mês>"): MLB..., MLB...`
  Se não houver IDs novos, não escreva nada. Se a escrita falhar, liste os IDs no relatório para o Lucas guardar.

Erro diferente desse (limite de requisições, falha de rede etc.) não torna o anúncio inelegível: registre como erro e siga.

## Passo a passo

### 1. Descobrir o nome da promoção
Pegar a data atual (use a ferramenta de hora) e calcular o mês seguinte (dezembro vira janeiro). Montar `Geral <mês seguinte por extenso em português, com inicial maiúscula>`. Comparar ignorando maiúsculas e acentos ("Marco" = "Março").

### 2. Montar a lista de exclusão
Gravar em um arquivo temporário (ex. `exclusoes.txt`) todos os IDs de:
- `ml_buscar_anuncios` com `sku=64265` e com `sku=61801`;
- `ml_buscar_anuncios` com `texto=Desmineralizada` e com `texto=Radiador Palio` (`limit=100`). Qualquer anúncio ativo cujo título tenha "Desmineralizada", ou "Radiador" e "Palio" juntos, entra na lista, mesmo sem SKU;
- `references/excluidos-permanentes.md`;
- a memória de inelegíveis (seção acima).

Se alguma busca falhar, pare e avise em vez de seguir sem a lista.

### 3. Descobrir o promotion_id
Rode `ml_promocoes` em um anúncio ativo que não esteja na lista de exclusão e procure, em `candidatas`, a promoção chamada "Geral <mês seguinte>". Guarde o `promotion_id` (ex. `C-MLB...`) e o `tipo` (normalmente `SELLER_CAMPAIGN`). Se não achar em 3 anúncios diferentes, pare e avise que a promoção ainda não foi criada.

### 4. Listar os candidatos em lote
Consultar anúncio por anúncio seria lento (a loja tem mais de 800 anúncios). Use `ml_api_get`:

`/seller-promotions/promotions/<promotion_id>/items?promotion_type=SELLER_CAMPAIGN&app_version=v2&limit=50&status=candidate`

Para a página seguinte, repita com `&search_after=<paging.searchAfter da resposta>`. Atenção: o filtro `status=candidate` é aplicado depois de montar cada página de 50, então algumas páginas voltam com `results: null` e há mais páginas. Continue até percorrer `ceil(paging.total / 50)` páginas.

Cada resultado traz `id`, `original_price`, `min_discounted_price` e `max_discounted_price`. Anúncios que já estão na promoção (`status: started`) não aparecem com esse filtro: contam como "já estavam".

### 5. Calcular os preços
Para cada página, monte linhas `ID,original_price,min_discounted_price,max_discounted_price` e rode:

`python3 scripts/calcular_precos.py --excluir exclusoes.txt < candidatos.csv`

O script arredonda para cima em centavos, então o desconto nunca passa de 6% por causa de centavo. A lógica é: se o preço de 6% está dentro da faixa permitida, entra com ele; se a promoção exige mais desconto, entra com o preço máximo da faixa, desde que o desconto fique em até 7%; senão, pula ("exigia mais de 7%"). Linhas `EXCLUIDO` e `PULAR` não entram.

### 6. Entrar na promoção
Para cada linha `ENTRAR`, chame `ml_promocao_entrar` com `item_id`, `tipo`, `promotion_id` e `preco`. Pode fazer em grupos de uns 30 anúncios em paralelo. Confira `desconto_pct` e `confirmado` na resposta. Se vier desconto acima de 7%, avise no relatório como alerta e não tente desfazer sozinho. Recusa "não é candidato" é inelegível (seção acima). Outros erros: registre e siga, sem repetir a chamada.

## Relatório final
Resumo curto, em português:

- Nome da promoção usada e data.
- Quantos entraram com 6%, quantos com mais de 6% até 7%, quantos já estavam, quantos ficaram de fora.
- Anúncios ignorados por já estarem na lista de inelegíveis, e inelegíveis novos (com os IDs acrescentados à memória).
- Lista dos que ficaram de fora por exigirem mais de 7% ou por erro, com ID e título.
- Confirmação de que a água desmineralizada e o Radiador do Palio foram pulados.

Em execução agendada, não há ninguém para responder perguntas: tome a decisão mais conservadora e relate.

## Quando rodar
Dia 30 de cada mês. Fevereiro não tem dia 30: em fevereiro a rotina roda no **último dia do mês** (28 ou 29), entrando em "Geral Março".

## Rotina 2: Campeões nas promoções de dias iguais

Quando pedirem os campeões, ou para entrar na 10.10, 11.11 e semelhantes, leia `references/campeoes.md` e siga o passo a passo. Resumo do que muda em relação à Geral:

- **Quais promoções:** só as da plataforma cujo nome é um dia igual ao mês (1.1, 2.2 ... 12.12) e que estejam abertas ou por abrir. Nenhuma outra, e nunca a Geral por esta rotina.
- **Quais anúncios:** os 50 melhores por faturamento nos últimos 60 dias que passam em todos os critérios: vendas (3 unidades ou mais em 60 dias), sem queda, estoque de 5 ou mais, nota de qualidade de 70 ou mais, ativo e fora das listas de exclusão e de inelegíveis.
- **Desconto:** as regras 1 a 5 da seção "Regras que não podem ser quebradas" valem iguais. Promoções da plataforma costumam exigir mais de 7%: esses anúncios ficam de fora e entram no relatório.
- **Sem critério de margem:** o Lucas dispensou. Se o anúncio entra com até 7% de desconto, ele pode entrar. Não consulte `ml_custos`.
- **Inelegíveis:** só vão para a memória os que não têm nenhuma promoção candidata (`candidatas` vazia). Recusa só desta promoção vai para o relatório.
- **Execução:** só sob pedido. Não agende sozinha.
