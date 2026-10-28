# Campeões nas promoções de dias iguais

Rotina sob demanda (não é agendada): "coloque os campeões nas promoções 11.11 / 10.10 / ...". Escolhe os 50 anúncios de melhor desempenho e coloca nas promoções da própria plataforma cujo nome é um dia igual ao mês (1.1, 2.2, ... 12.12). As regras de desconto são as mesmas da promoção Geral: no máximo 6% (limite 7% se a promoção exigir; acima disso o anúncio fica de fora), nunca água desmineralizada nem Radiador do Palio, nunca anúncios inelegíveis.

O Lucas dispensou o critério de margem: se o anúncio entra com até 7% de desconto, ele pode entrar. Não consulte `ml_custos` nesta rotina.

## Critérios do campeão (todos precisam passar)

1. **Vendas:** pelo menos 3 unidades em 60 dias. O ranking é por faturamento (unidades dos 60 dias x preço atual).
2. **Sem queda:** as vendas dos últimos 30 dias não podem ser mais de 30% menores que as dos 30 dias anteriores.
3. **Estoque:** 5 unidades ou mais.
4. **Experiência de compra:** anúncio ativo, nota de `ml_qualidade` de 70 ou mais, e fora da lista de inelegíveis.
5. **Cabe na regra de desconto:** é candidato à promoção e o desconto exigido é de no máximo 6% (ou 7%).

Os 50 primeiros por faturamento que passam em tudo formam o top 50. Anúncios que já estão na promoção e passam nos critérios de vendas, queda e estoque ocupam uma vaga (contam como "já estava"), para uma segunda rodada na mesma promoção não colocar mais 50.

As promoções da plataforma costumam exigir descontos maiores que as da loja (no 11.11 de 2026, 3 de 5 anúncios olhados exigiam mais de 7%). Esses campeões ficam de fora e vão para o relatório. Não é erro.

## Passo a passo

### 1. Escolher as promoções
`ml_conta` dá o ID da conta (em 22/10/2026 era 213514959). Depois:

`ml_api_get /seller-promotions/users/<id_da_conta>?app_version=v2`

Entram só as promoções cujo `name` começa com `D.D` ou `DD.DD` com os dois números iguais (ex. "11.11 da Black", "10.10", "2.2") e `status` `started` ou `pending`, com `finish_date` no futuro. Ignore todas as outras (Geral, cupons, relâmpago, "Impulsione suas vendas"...). Se não houver nenhuma, avise e pare. Se houver mais de uma, faça o processo inteiro para cada uma (o ranking dos passos 2 e 3 vale para todas).

### 2. Ler as vendas dos últimos 60 dias
`ml_vendas` com `status=paid`, `limit=51`, `desde` = hoje menos 60 dias (formato `2026-08-23T00:00:00.000-03:00`) e `ate` = hoje às 23:59:59 (fixo, o mesmo em todas as páginas, para os pedidos novos não deslocarem as páginas entre uma chamada e outra). Avance `offset` de 51 em 51 até passar de `total`.

**Leia em paralelo.** Faça a primeira página sozinha para saber o `total` e calcular quantas páginas há (`ceil(total / 51)`). Depois peça as demais em grupos de 6 a 12 chamadas no mesmo turno. Em teste (22/10/2026), 6 páginas em paralelo levaram cerca de 11 s contra cerca de 28 s uma a uma (≈2,6x mais rápido). O gasto de tokens é o mesmo nos dois jeitos (cerca de 12 a 15 mil por página), então o paralelo só ganha tempo.

**Anote cada grupo logo que ele chegar**, antes de pedir o próximo, acrescentando as linhas ao `vendas.csv` com `cat >> vendas.csv <<'EOF'`. Assim o contexto não acumula páginas ainda não anotadas.

Linha curta, uma por item vendido: `AAAA-MM-DD,MLBxxxxxxxxx,quantidade`. A data são os 10 primeiros caracteres de `data`, o ID é o que está entre parênteses e a quantidade é o "2x" no começo de cada item (sem "x", 1). Pedidos com vários itens geram várias linhas. Não copie nada do comprador (nome, apelido, ID), nem títulos, nem preços.

Pule a linha já na hora de anotar se o título tiver "Desmineralizada", ou "Radiador" e "Palio" juntos (a regra por título de `excluidos-permanentes.md`).

### 3. Aplicar os critérios 1 e 2
Monte `exclusoes.txt` com `references/excluidos-permanentes.md` e a memória `/areas/ml-promocao-inelegiveis.md` (ou `references/inelegiveis-2026-10-21.md` se a memória não responder). Rode:

`python3 scripts/campeoes.py vendas --hoje AAAA-MM-DD --vendas vendas.csv --excluir exclusoes.txt --janela 60`

Fique com as linhas `OK`.

### 4. Dados do anúncio e da promoção
- Preço, estoque e status: `ml_api_get /items?ids=<até 20 IDs>&attributes=id,title,price,available_quantity,status` para os `OK`. Descarte os que não estão `active`.
- Faixa de preço da promoção, lendo a lista inteira (sem filtro de status, para ver também os que já estão dentro): `ml_api_get /seller-promotions/promotions/<promotion_id>/items?promotion_type=<type>&app_version=v2&limit=50`, passando `&search_after=<paging.searchAfter>` para as páginas seguintes, até `ceil(paging.total / 50)` páginas. Cada item traz `status` (`started` = já está; `candidate` = pode entrar), `original_price`, `min_discounted_price` e `max_discounted_price`.

Anúncio `OK` que não aparece na lista da promoção não é candidato a ela: ficou de fora. Só vale conferir os que estiverem entre os 80 maiores faturamentos: `ml_promocoes` neles. Se `candidatas` vier vazia (sem nenhuma promoção), é inelegível: acrescente à memória (veja SKILL.md, seção de inelegíveis). Se tiver outras candidatas, só não participa desta promoção: relate, sem acrescentar à memória, porque a restrição pode ser só desta promoção.

### 5. Avaliar
Monte `dados.csv` (formato no cabeçalho do script) e rode:

`python3 scripts/campeoes.py avaliar --dados dados.csv --excluir exclusoes.txt --top 70`

Use `--top 70` nesta primeira passada, para sobrar margem para os que a nota de qualidade vai tirar.

### 6. Nota de qualidade
Para os `ENTRAR` e `JA_ESTA` na ordem do ranking, chame `ml_qualidade` e, quando a nota for menor que 70, anote o ID em `baixa_qualidade.txt`. Pare quando já tiver conferido 50 anúncios com nota boa. Rode o passo 5 de novo, acrescentando `--excluir baixa_qualidade.txt` e `--top 50`. Esse é o resultado final.

### 7. Entrar nas promoções
Para cada `ENTRAR`: `ml_promocao_entrar` com `item_id`, `tipo` (o `type` da promoção, ex. `DEAL`), `promotion_id` e `preco`. Não envie `preco_top`. Se a plataforma recusar por exigir esse campo, registre o erro e pare de enviar para esse anúncio. Faça em grupos de uns 30 em paralelo.

- Recusa por já estar em outra promoção (por exemplo a Geral), por sobreposição de datas ou por regra da própria plataforma: registre como "bloqueado por sobreposição" e siga. Nunca tire o anúncio da outra promoção.
- Confira `desconto_pct` e `confirmado` na resposta. Acima de 7%, avise como alerta; não desfaça sozinho.
- Nunca use `confirmar_desconto_alto`.

## Relatório
Em português, curto:

- Promoções usadas (nome e prazo).
- Quantos campeões entraram (6% e até 7%), quantos já estavam, quantos ficaram de fora e por quê (desconto exigido acima de 7%, estoque, nota de qualidade, sobreposição, erro), com ID e título dos principais.
- Inelegíveis novos acrescentados à memória.
