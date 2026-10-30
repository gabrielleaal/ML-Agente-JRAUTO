---
name: criar-hub-anuncios
description: Criar (cadastrar) um anúncio novo no Mercado Livre pelo HUB Citel (hub.citelsoftware.com.br) da JR Auto Peças, usando o navegador do app, do título ao frete real. Cobre título vindo da planilha, tipo Premium/Clássico pelo preço base, categoria, garantia, comissão, regra dos R$ 69 para Taxa ML e Frete Grátis, campos por categoria, condição New, entrega me2, fotos do Syntra, salvar e reconsultar o frete. Use sempre que pedirem para anunciar, criar anúncio, cadastrar ou subir um produto/SKU no Mercado Livre pelo Hub, ex. "anuncia o SKU 37004", "cria o anúncio desse produto no Hub", "sobe esse produto no ML", "faz o anúncio da peça X", mesmo que a pessoa não cite as regras. Para só ver ou mudar o preço de anúncios que já existem, use a skill hub-precos-ml.
---

# Criar anúncio novo no Hub Citel

O Hub (https://hub.citelsoftware.com.br) cria o anúncio no Mercado Livre a partir do cadastro do produto no ERP (Autcom). Esta skill leva um SKU de "produto sem anúncio" até "anúncio publicado", pelo navegador embutido do app (`mcp__Claude_Browser__*`). Foi montada com o usuário no SKU 37004 (radiador Visconde), que virou o anúncio MLB7906544758.

Cada regra abaixo foi ditada pelo usuário. Quando surgir um caso que elas não cobrem, pare e pergunte; depois registre a resposta aqui. Não invente regra e não trate algo dito para um produto como regra geral sem confirmar.

## Antes de começar

1. **Login:** abra o Hub com `preview_start` passando a `url`. Se aparecer a tela de login (Loja, Usuário, Senha), peça para a pessoa entrar; nunca digite senha. O login fica salvo no navegador do app. Se o painel do navegador estiver oculto, peça Ctrl+Shift+B.
2. **Título:** o SKU precisa estar na planilha de títulos, `C:\Users\Usuario\Documents\Claude Project\Planilhas Títulos\a.csv` (gerada pela skill `titulos-anuncios-ml`; o `a.csv.txt` é a mesma planilha em UTF-8). Busque pelo código com `Grep`, sem ler o arquivo todo (é grande). Se o SKU não estiver lá, pare e avise: o nome do ERP traz códigos de referência e não serve de título.
3. **Fotos (sempre ANTES de abrir o formulário do anúncio):** abra `/Produtos/Alterar/<SKU>` (aba Mídias) e conte os slots. Sem nenhuma foto o Mercado Livre recusa o cadastro ("Item pictures are mandatory", 400 requiresPictures). O anúncio precisa de **10 fotos**: se houver menos de 10 (inclusive só 1), siga `references/fotos.md` e suba as 10 do kit do Syntra; o upload **substitui** a foto antiga, e não soma. Se já houver 10, pule. Não baixe as fotos no PC. Antes de anexar, redimensione cada foto para **1200x1200 JPEG** no canvas (WebP vira JPEG também): assim o Hub não mostra o diálogo "imagem fora do padrão" e não há OK para clicar (testado no 38858). Só depois abra `/CanalMercadoLivre/code/<SKU>`, para não precisar voltar.
   - Se `/Produtos/Alterar/<SKU>` redirecionar para `/Produtos/Consultar`, o produto ainda não foi enviado ao Hub pelo Autcom: avise o usuário.
   - O **número de peça** (`#PART_NUMBER`) vem do campo "Sku Fabricante" (`#MakerCode`) da aba Produto Básico de `/Produtos/Alterar/<SKU>`, e não do nome nem da descrição (no 38858, Mahle, é CR1466 e os códigos de referência RV2246, RMM8598001, 94717416 vão em OEM).
4. **Rascunho:** abra `/CanalMercadoLivre/code/<SKU>`. Produto sem anúncio mostra um cartão sem Id MLB e o bloco "Novo Anúncio". Se já houver Id MLB, o produto já tem anúncio: avise o usuário e não crie outro.

Nada é criado no Mercado Livre até clicar em Salvar. O formulário só existe na tela: sair da página o apaga. Para qualquer tarefa paralela (fotos, consultas), use outra aba (`preview_start` com `url`) e deixe a do anúncio quieta.

## Passo a passo (nesta ordem)

Os ids são dos campos do Hub. Preencha por clique ou JS e confira o valor lido de volta antes de seguir. A página mostra "Aguarde, Carregando..." em vários momentos e às vezes recarrega: espere sumir e releia os campos.

### 1. Nome da Família = título do anúncio
- `#FamilyName` vem com o nome do ERP. Clique, `ctrl+a` e digite o título da planilha (máximo 60 caracteres).
- "Variações do Anúncio" não é usado: ignore.

### 2. Descrição
- Não preencher nada. O usuário já sobe a descrição pelo Autcom e o Hub a traz do produto.

### 3. Tipo de anúncio (`#AdvertisementType`)
- Preço base (custo da Tabela Custo, `#maskMoney`) **maior que R$ 200 = Premium**. Abaixo disso = **Clássico**. (Valores do select: 1 Grátis, 0 Clássico, 2 Premium.)

### 4. Precificação (a parte mais importante), nesta ordem
1. **Categoria primeiro.** Em "Definição de categoria do Mercado Livre" o Hub mostra cartões sugeridos (`.ml-card-category-suggest`). Clique no sugerido: isso preenche `#CategoryMl` (radiador: MLB193399, "Radiadores de Água"). Regra do usuário: usar a categoria sugerida; se ela parecer errada para o produto, pergunte antes.
2. **Garantia:** `#warranty` já vem 3, mas `#warrantyUnit` vem "dia(s)". Troque para **mês(es)** (valor 1), ficando 3 meses. O select é estilizado: defina o `value` e dispare `change`.
3. **Margem padrão de 12%.** No campo de margem (`#margin`) deixe sempre **12** (12%), em todo anúncio, qualquer que seja o valor que vier de fábrica. O campo tem máscara como o do preço: clique, `ctrl+a`, `Backspace`, digite `12`, `Tab`, e confira por JS que o valor lido é 12 (`document.getElementById('margin').value`). Faça isto **antes** de consultar comissão e frete, porque o Hub calcula o preço de venda a partir da margem; se mexer na margem depois, consulte a comissão (e o frete, se for o caso) de novo. Não altere a margem para "acertar" o preço: o preço é consequência dos 12%.
4. **Consultar Comissão ML** (`#btnCommission`). Abre um pop-up de confirmação ("certifique-se que categoria, tipo e preço estão corretos"): clique Consultar. O Hub preenche a comissão (17% no Premium de radiador) e recalcula o preço.
5. **Regra dos R$ 69**, sobre o preço de venda que o Hub calcula:
   - **Abaixo de R$ 69:** marcar "Taxa ML" (`#rateMl`). **Nunca** consultar "Frete ML" e **nunca** marcar "Frete Grátis".
   - **A partir de R$ 69:** "Taxa ML" desmarcada; consultar "Frete ML" (`#btnFrete`; pop-up de confirmação, clique Consultar) e marcar "Frete Grátis" (`#FreeShipping`).
   - **Se o preço cruzar R$ 69 depois da consulta da comissão:** consultar o frete, marcar Frete Grátis e desmarcar Taxa ML.
   - **"Retirar Pessoalmente" (`#withdrawPersonally`) nunca fica ativado.**
   - "Entrega Flex" (`#FlexShipping`) vem marcada: deixe como veio.
   - O preço é calculado pelo Hub (margem, impostos, comissão, frete): não digite preço à mão.
   - O ramo "abaixo de R$ 69" foi validado e aprovado pelo usuário em 30/10/2026 (26276: Clássico, base R$ 42,07, Taxa ML marcada, sem Frete Grátis, preço R$ 74,19, anúncio MLB5487627353 ativo, sem frete grátis no ML). Pode seguir sem perguntar.

### 5. Condição e entrega, antes dos campos por categoria
- Condição do item (`#condicao-item`): sempre **New** (valor 0).
- Tipos de entrega (`#select-entregas`): sempre **me2** (valor 1; custom é 2).
- Mudar a entrega **apaga os "Campos por categoria"** (preço, categoria e garantia ficam). Por isso isto vem antes de preencher os campos da categoria. Espere o carregamento acabar.

### 6. Campos por categoria
Os campos mudam com a categoria. Liste os que estão visíveis antes de preencher:

```js
[...document.querySelectorAll('.card-collapse input[type=text], .card-collapse select')]
  .filter(e => e.offsetParent).map(e => [e.id, e.tagName, e.value])
```

"Atributos secundários" aparecem ao marcar `#attributesDmt-ck`. Regras do usuário:
- **Modelo** (`#MODEL`) = o título do anúncio.
- **Número de peça** (`#PART_NUMBER`, obrigatório) = o código de fábrica (Sku do Fabricante do produto, ex. RV2735).
- **Altura, largura e espessura** (`#HEIGHT`, `#WIDTH`, `#THICKNESS`, unidade cm) = **as medidas que já estão no Hub**, nos campos do produto `#maskHeight`, `#maskWidth` e `#maskLength` (Profundidade vira Espessura). É só copiar, sem converter; não use as medidas da descrição nem da planilha.
- **Tipo de veículo** (`#VEHICLE_TYPE`, obrigatório): na maioria das vezes Carro/Caminhonete; só muda quando a categoria for de Linha Pesada.
- **Demais informações que a categoria pedir** (inclui tampa, com cebolão, ar condicionado...): pesquise na descrição do produto. Ex.: "não acompanha tampa... nem cebolão" => Inclui tampa = Não, Com cebolão = Não. Selects Sim/Não: Não = 242084, Sim = 242085 (confira na categoria).
- **Código OEM** (`#OEM`): os códigos similares/de referência da descrição, menos o código do fabricante que já é o Número de peça, separados por vírgula (ex.: `NT7138116, 717056, 8V518005`).
- **Detran, Anatel, INMETRO e similares:** sempre "Não aplica".
- **Qualquer campo sem informação na descrição:** marque "Não aplica" (checkbox `#attribute-value-na-<ID DO CAMPO>`, use `.click()`).
- No fim, confira que nenhum campo visível ficou vazio sem "Não aplica".
- **Veículos compatíveis:** pular (o recurso só libera depois que o anúncio existe).

Para preencher por JS use o setter nativo do `value` e dispare `input`, `keyup` e `change`; em selects, `value` + `change` (+ `jQuery(el).trigger('change')`):

```js
const setT=(id,v)=>{const e=document.getElementById(id); e.focus();
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,v);
  ['input','keyup','change'].forEach(t=>e.dispatchEvent(new Event(t,{bubbles:true}))); e.blur();};
const setS=(id,v)=>{const e=document.getElementById(id); e.value=v;
  e.dispatchEvent(new Event('input',{bubbles:true})); e.dispatchEvent(new Event('change',{bubbles:true}));
  if(window.jQuery) jQuery(e).trigger('change');};
```

### 7. Conferir e salvar
Antes de salvar, releia tudo e compare com as regras (título, tipo, categoria, garantia, margem 12%, comissão, frete/Taxa ML, entrega, campos por categoria). Se o usuário pediu para salvar no fim do preenchimento, salve; se não, mostre o resumo e espere o "sim".

- Clique em **Salvar** (`#btn-save`, fim da página). Use as coordenadas do screenshot (referência 800x705), não as do JS (viewport 977x862).
- Se o Mercado Livre recusar, aparece um aviso vermelho que some em segundos: leia logo após o clique. O formulário continua preenchido; corrija a causa sem sair da página (se for foto, use outra aba).
- Sucesso: a página recarrega e o cartão mostra Id MLB, tipo, data e preço, e "Saúde do Anúncio" aparece. Leia `#IdMl` e `#link-anuncio`.

### 8. Reconsultar o frete real
- Em anúncio novo o frete consultado é uma **estimativa** (o pop-up avisa). Depois de salvar, clique de novo em "Consultar Frete ML". Em anúncio já criado não há pop-up: aparece "Buscando o valor do frete...". O primeiro clique pode não disparar; se não aparecer o aviso, clique de novo.
- Compare frete e preço. Igual: nada a salvar (foi o caso do 37004, R$ 49,35). Diferente: o preço muda; o frete real prevalece, então salve o preço novo (clique Salvar, confira por leitura que gravou) e informe o antes/depois no relatório; não precisa pedir "sim".

## Armadilhas

- **Mudar o Tipo de Entrega apaga os Campos por categoria:** entrega e condição vêm antes (passo 5).
- **Sair da página do anúncio apaga o formulário:** use outra aba para fotos e consultas.
- **Máscara do campo de preço:** não edite preço aqui. Se precisar mexer em preço de anúncio existente, use a skill `hub-precos-ml`.
- **Anúncio Full (Fulfillment):** o Hub não altera preço desses.
- **Salvar nunca se repete sem conferir (lição do lote de 25):** se ao salvar aparecer o aviso/toast "502 Bad Gateway" ou a página não recarregar, o anúncio PODE ter sido criado mesmo assim. Espere ~30 s e leia `/CanalMercadoLivre/code/<SKU>` (regex `MLB\d{6,}`, ignorando `MLB193399`, que é a categoria). Só clique Salvar de novo se não houver nenhum Id. No 66443 a segunda tentativa duplicou o anúncio. O diálogo "Falha ao consultar frete (502) Tem certeza que deseja prosseguir?": cancele e tente de novo mais tarde; não confirme por conta própria.
- **Coordenadas mudam:** a janela do app muda de tamanho (977 px e 487 px de largura já apareceram). Calcule o ponto do clique pelo `getBoundingClientRect()` do botão e leia o "coordinate frame" de um screenshot pequeno para converter; chame `tabs_select` antes de clicar (sem isso o clique pode falhar com "tab not on screen"). Clique que erra não dá aviso: o formulário simplesmente não salva.
- **Garantia:** confira `#warranty` = 3 em todo anúncio (um produto veio com 0 do Hub).
- **Campo digitado vai para quem tem foco:** após digitar o título espere ~2,5 s as sugestões de categoria antes de focar a margem; senão o "12" cai no título.
- **Frete real diferente da estimativa:** o frete real SEMPRE prevalece (regra do usuário, 29/10/2026). Se for menor ou maior que o estimado, salve o preço novo sem pedir confirmação e só informe no relatório (antes/depois). Em 3 de 25 anúncios o frete real foi menor que o estimado.
- **Fotos:** `#main<N>` muda de índice conforme a página; marque a capa clicando no 1º checkbox do 1º `.product-image-group`. O slot vazio de 1500x1500 é o espaço de "adicionar foto", não uma foto. Se aparecer "Algumas imagens não foram salvas", recarregue, confira e refaça o upload completo.
- **Diálogos de confirmação** (comissão, frete, imagens fora do padrão): leia o texto antes de confirmar. Nunca marque "Não exibir novamente", que é configuração persistente.

## O que reportar no fim

Id MLB e link, tipo, preço final, margem, comissão, frete (estimado e real), categoria, quantas fotos subiram, e tudo o que foi marcado "Não aplica" ou decidido por você sem regra do usuário. Se o usuário ditar uma regra nova, acrescente-a a esta skill.
