---
name: ml-compat-pendentes
description: Adiciona as compatibilidades de veículos dos anúncios do Mercado Livre da JR Auto Peças que estão no filtro "Pendentes para corrigir" da aba "Gestão de anúncios" (anúncios inativos para revisar por "Não indica os veículos compatíveis"), pelo conector JR Mercado Livre, usando as aplicações da descrição do anúncio. Mexe SOMENTE em compatibilidade, nunca em título, preço, estoque, ficha, descrição ou fotos. Use sempre que pedirem para corrigir os pendentes do ML, reativar anúncios inativos por falta de compatibilidade, adicionar compatibilidade nos anúncios pendentes ou "zerar" o filtro Pendentes para corrigir, mesmo que a pessoa não cite o nome do filtro.
---

# Compatibilidades dos "Pendentes para corrigir" (Mercado Livre)

Autopeça sem tabela de compatibilidade fica **Inativa para revisar** no ML. Esta skill pega só os anúncios desse filtro e preenche a tabela de veículos a partir da seção "Aplicação" da descrição de cada anúncio. Nada além de compatibilidade é alterado: o Hub é dono de preço e estoque, e o resto do conteúdo segue a skill `ml-anuncios`.

## 1. Achar a lista certa (o filtro, não a etiqueta da API)

O filtro "Pendentes para corrigir" é um cartão da aba **Gestão de anúncios** (`https://vendedores.mercadolivre.com.br/anuncios`). Ele traz poucos anúncios (7 na primeira vez). Não confunda com:
- a etiqueta de API `incomplete_compatibilities` (42 anúncios com compatibilidade zerada, contendo os 7, mas também anúncios ativos);
- o cartão "Informe os veículos compatíveis" (39).
O pedido é só para o cartão "Pendentes para corrigir"; o resto fica fora, a menos que a pessoa peça.

Como ler a lista, no navegador do app (`mcp__Claude_Browser__*`):
1. Navegue para `https://www.mercadolivre.com.br/anuncios/lista`. Se aparecer login, peça para a pessoa entrar no painel do navegador (Ctrl+Shift+B abre o painel). Nunca digite senha.
2. Clique no cartão "Pendentes para corrigir". A URL passa a ter `task=GROUPED_UNDER_REVIEW_WAITING_FOR_PATCH`.
3. Confirme o motivo de cada linha ("Inativo para revisar · Não indica os veículos compatíveis"). Se algum motivo for outro (política, fotos, dimensão), esse anúncio não é desta skill: avise e pule.
4. Extraia os IDs com JS (a página tem linhas duplicadas, então deduplique):
```js
const t=document.body.innerText, out=[], re=/([^\n]+)\n\1\n#(\d{9,})\nSKU ([^\n]+)/g; let m;
while((m=re.exec(t))) out.push({mlb:'MLB'+m[2], titulo:m[1], sku:m[3]});
const seen={}; out.filter(o=>!seen[o.mlb]&&(seen[o.mlb]=1))
```
Confira se o total bate com o número do cartão.

## 2. Ler cada anúncio

`ml_anuncio` (um por vez ou em paralelo). Use a seção **Aplicação** da descrição como fonte dos veículos e leia também título e ficha (Marca, Número de peça, Código OEM, "com/sem ar", "automático") para filtrar versões. Confirme que `compatibilidades.total` é 0.

## 3. Montar os IDs de veículos

Para cada veículo da Aplicação, `ml_compat_veiculos` com `marca`, `modelo`, `anos` (ex.: `2017-2019`) e `filtro` de motor/versão quando houver, sempre com `item_id`. O retorno dá o `id` de catálogo e `no_anuncio`.

Regras para escolher as versões:
- Câmbio "automático" na descrição → só versões com "Aut." no nome. "Flex" na descrição → versões "Flex" (gasolina e diesel têm radiadores diferentes, ex.: Compass 2.0 Flex vs. 2.0 diesel).
- Motor citado (1.0, 1.8, 2.0 16V) → filtre por ele. Versões turbo/híbridas novas que a descrição não cita ficam de fora (ex.: Compass Hurricane).
- Ano fechado ("2017 a 2019") → use exatamente esse intervalo. Ano aberto ("1995 em diante") → só aceite quando o catálogo do veículo termina sozinho na geração certa (ex.: Ka 1.0 vai de 2015 a 2021, Monza acaba em 1994). Quando o catálogo se estende por gerações diferentes (Gol 1995 em diante, S10 sem ano), **não adicione**: peça a decisão da pessoa. Compatibilidade errada vira devolução.
- Quando a descrição não fecha o ano (ou o ano é "em diante"), pesquise o código da peça na web com `WebSearch` em modo **extended**. Só adicione se duas fontes concordarem. O que funcionou: buscar o código seco + marca + modelo (ex.: `RV2504 radiador Visconde Gol`, `RV9224 radiador Visconde S10`); o código numérico da Visconde (RV2504 = 12504, RV9224 = 19224) e os equivalentes da ficha (Notus NT..., Valeo 6AB..., Delphi RA/P..., Magneti Marelli RMM...) rendem catálogos de distribuidores (rumoautopecas, pitstop, apsdistribuidora, newcarpecas) com a faixa de anos. Buscas longas em modo standard não acharam nada.
- Use a faixa de anos que as fontes confirmam, não a da descrição, e cruze com outros anúncios da própria loja: o RV2504 aparece como Gol 1.6/1.8/2.0 de 1995 a 2008, e o Gol 1.0 da loja usa outro código (RV2509/Mahle CR2141). Quando a descrição cita um motor que as fontes não confirmam, deixe esse motor de fora e avise.
- Variações que não são o carro de passeio (ambulância, blindado) ficam de fora.
- Se a descrição contradiz o título ou os códigos da ficha, pule o anúncio e relate.
- O catálogo pode não ter o motor citado (ex.: Pajero IO 2.0 não existe no catálogo). Adicione o que existe e relate o que faltou.

## 4. Adicionar

`ml_compat_adicionar` com `item_id`, `veiculos` (até 600) e uma `nota` curta ("Aplicação da descrição: ..."). O pedido da pessoa de corrigir os pendentes autoriza adicionar nesses anúncios; não é preciso novo lote de aprovação. Confira `criadas` e `erros`. A ferramenta guarda histórico, então dá para desfazer com `ml_historico_anuncio` / `ml_compat_remover`.

## 5. Conferir

`ml_auditar_anuncios` com os IDs: `compatibilidades` deve bater com o que foi criado e a pendência "Indique com quais veículos..." deve sumir. Depois reabra o cartão no painel: o número de pendentes cai conforme o ML reprocessa (pode demorar; se o anúncio continuar "Inativo para revisar", diga isso, não force).

## 6. Relatar

Tabela por anúncio: MLB · título · veículos adicionados (por modelo) · ficou de fora e por quê. Em seguida, uma lista curta de decisões pendentes (anúncios pulados). Não altere nada além de compatibilidade, mesmo que veja outros problemas (preço, ficha, título): só mencione.

## Nunca

- Mexer em preço, estoque, título, ficha, descrição, fotos, frete ou promoção.
- Adicionar veículo sem estar na descrição do anúncio (ou sem a pessoa decidir).
- Digitar senha ou criar conta no painel do ML.
