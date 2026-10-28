---
name: "lista-separacao-ml"
description: Assistente de marketplace da JR Auto Peças. Puxa no Mercado Livre as vendas que precisam ser enviadas hoje (ou amanhã, se pedido), cruza o SKU de cada venda com o código do produto na planilha do Autcom e gera um PDF de lista de separação (código, descrição resumida, localização física e quantidade) para imprimir. Use sempre que pedirem a lista de separação, separação do dia, picking, vendas do ML para enviar hoje ou amanhã, ou quando a tarefa agendada das 8:10 rodar.
---

# Lista de separação diária – Mercado Livre

O objetivo é que quem separa as peças pegue uma folha impressa e ande pelo estoque numa ordem só, pegando cada produto vendido no ML que precisa sair no dia. Por isso a lista é ordenada pela localização física, soma a quantidade do mesmo código vendido em várias vendas, e destaca separadamente o que não deu para cruzar com a planilha.

## Arquivos da skill
- `assets/produtos.csv` – cadastro de produtos exportado do Autcom (colunas `CÓDIGO;DESCRIÇÃO DO PRODUTO;LOC.FÍSICA;...`). É a fonte da descrição e da localização.
- `scripts/gerar_lista.py` – recebe as vendas em JSON e gera o PDF pronto (o cruzamento com a planilha é todo feito por ele; não leia o CSV na mão).

## Passo 1 – Ler as vendas no Mercado Livre

Use o navegador do app Claude no computador da loja (built-in browser), onde a conta de vendedor já está logada. Leia antes a skill `built-in-browser`. Se o navegador não estiver disponível (computador desligado ou app fechado), não tente outro caminho: avise o usuário na conversa que não foi possível acessar o Mercado Livre e pare.

### 1.1 Abrir a lista certa (por URL, sem clicar)

- **Envios de hoje:** `https://vendedores.mercadolivre.com.br/vendas/omni/lista?filters=TAB_TODAY&subFilters=&search=&limit=50&offset=0&startPeriod=`
- **Próximos dias (para a lista de amanhã ou de outra data):** o mesmo link com `filters=TAB_NEXT_DAYS`.

Se a página mostrar a tela de login, verificação ou CAPTCHA, não tente resolver: avise o usuário e pare (peça para ele logar de novo no navegador do app).

O critério é a **data de envio/coleta**, não a data da venda. Não use filtros de "vendas de hoje", "concluídas" ou "faturamento".

### 1.2 Extrair as vendas com JavaScript (método principal)

Rode o trecho abaixo com `javascript_tool` na aba da lista. Ele devolve um JSON compacto com uma linha por venda, em vez de obrigar a ler a página inteira como texto:

```js
(()=>{const rows=[...document.querySelectorAll('.sc-list .sc-row')];
const out=rows.map(r=>{
 const t=r.innerText.replace(/\s+/g,' ');
 const L=r.innerText.split('\n').map(s=>s.trim()).filter(Boolean);
 const pedido=(t.match(/#(2000\d{12})/)||[])[1]||null;
 const skus=[...new Set([...t.matchAll(/SKU:\s*(\S+)/g)].map(m=>m[1]))];
 const q=(t.match(/(\d+)\s+unidades?/)||[])[1]||null;
 let status='ok';
 if(!pedido||/Não foi possível exibir/i.test(t))status='erro_leitura';
 else if(/cancelad/i.test(t))status='cancelada';
 else if(/Devolu|Reclama|mediaç|Acompanhar (o envio|devolução)/i.test(t))status='devolucao_reclamacao';
 const m=t.match(/coleta do dia (\d{1,2}) de (\w+)/i);
 const quando=m?`${m[1]} de ${m[2]}`:/coleta de amanhã|que passará amanhã/i.test(t)?'amanha':/coleta (de )?hoje|passará hoje/i.test(t)?'hoje':null;
 const i=L.findIndex(s=>/^\d+ unidades?$/.test(s));let j=i-1;
 if(j>=0&&/^(Cor|Cores|Tamanho|Voltagem|Lado|Posição):/i.test(L[j]))j--;
 const titulo=j>=0?L[j]:null;
 return {pedido,sku:skus.join(','),quantidade:q?+q:null,quando,status,titulo}});
return JSON.stringify(out)})()
```

Como interpretar o resultado:
- Na aba **TAB_TODAY**, entram as linhas com `status: "ok"` (todas são para despachar hoje).
- Na aba **TAB_NEXT_DAYS**, entram só as linhas com `status: "ok"` e `quando` igual ao dia pedido: `"amanha"` para a lista de amanhã (ou a data por extenso, ex. `"23 de outubro"`, para outro dia). Não inclua as que têm outra data.
- **Nunca** inclua `cancelada` (mesmo com etiqueta já impressa) nem `devolucao_reclamacao`.
- `erro_leitura` ("Não foi possível exibir as informações"): recarregue a página (navigate de novo na mesma URL) e rode o trecho outra vez; repita até 2 vezes. Se persistir, abra o detalhe da venda ou use o plano B abaixo.
- `sku` vazio ou com mais de um valor: abra o detalhe da venda (ou leia o texto da página) para conferir. Venda sem SKU no anúncio vai para o aviso final, para separar manualmente pelo título.
- Se a lista tiver mais de 50 vendas, mude `offset` (50, 100…) e rode de novo.
- Se o resultado vier vazio, a estrutura da página pode ter mudado: use o plano B.

### 1.3 Plano B (se o JavaScript falhar)

Leia a página com `get_page_text` e extraia à mão: número da venda, SKU, quantidade, título e a frase de coleta ("coleta de amanhã", "coleta do dia X"), aplicando as mesmas regras de exclusão. Na conta da JR o **SKU é o próprio código do Autcom** (ex. 64265). Venda com vários itens (carrinho) vira uma linha por item, com o mesmo número de venda.

### 1.4 Salvar as vendas válidas

Salve num arquivo, por exemplo `vendas.json` (só `pedido`, `sku`, `quantidade`, `titulo`; se o SKU vier com vírgula, uma linha por SKU):

```json
[
  {"pedido": "2000009876543210", "sku": "64265", "quantidade": 1, "titulo": "Radiador Palio Fire ..."}
]
```

Se não houver nenhuma venda válida para a data pedida, não gere PDF: só avise "Nenhuma venda do Mercado Livre para enviar hoje" (ou "amanhã"). Se só houver canceladas, diga quais.

## Passo 2 – Gerar o PDF

```bash
python3 <pasta-da-skill>/scripts/gerar_lista.py vendas.json lista_separacao_DD-MM-AAAA.pdf
```

**Descrição com código de referência (regra do usuário):** na coluna de descrição, abaixo da descrição resumida, o script imprime em negrito `Ref:` seguido dos códigos de referência/fábrica que ficam no fim da descrição da planilha (ex. `Ref: B04M128 I26596 MR377128`). Se o produto não tiver nenhum, imprime "(sem código de referência)" e você deve avisar o usuário na mensagem de entrega quais produtos ficaram sem.

**Produtos fora da planilha:** os códigos 24317 (J524b), 62175 (H 0053), 64979 (YA 050) e 62815 (H 515), 37888 (F 0030, Filtro de Óleo Mann HU8006Z) e 38041 (CESTO B 061, Filtro de Combustível Monza Mann WK47/1) foram acrescentados ao final do `assets/produtos.csv` com a localização informada pelo usuário. Quando o usuário informar a localização de outro produto que falta, acrescente uma linha no mesmo formato (`CÓDIGO;DESCRIÇÃO;LOC.FÍSICA;;PC;;;;;`) e avise que o CSV da skill precisa ser atualizado.

O script usa `assets/produtos.csv`, coloca a data de hoje no cabeçalho (horário de Brasília) e imprime um resumo em JSON com `nao_encontrados`. Ele soma as quantidades do mesmo código, resume a descrição, ordena pela localização física e lista à parte, em amarelo, os SKUs que não existem na planilha.

Observação: para a lista de **amanhã**, o cabeçalho do PDF ainda mostra a data de hoje. Nesse caso nomeie o arquivo com a data de amanhã e avise o usuário.

Abra a primeira página do PDF como imagem (`pdftoppm -png -r 70`) e confira rapidamente se a tabela saiu certa antes de entregar.

## Passo 3 – Entregar

1. Envie o PDF aqui na conversa com SendUserFile (`status: "proactive"` na execução agendada, para chegar a notificação). Guarde o `file_uuid`.
2. Salve também o PDF na pasta do computador da loja, com `mcp__remote-devices__device_commit_files` (carregue com ToolSearch se estiver adiado), em `C:\Users\Usuario\Documents\Claude Project\Lista de Separação\lista_separacao_DD-MM-AAAA.pdf`. Se a pasta não estiver conectada à sessão, peça acesso com `device_request_folder_access`; em execução agendada, sem ninguém para aprovar, apenas avise que não foi possível salvar na pasta e siga com o envio na conversa.
3. **Atualização da lista no mesmo dia** (usuário pede para refazer/corrigir): gere o PDF de novo com o mesmo nome de arquivo e **substitua** o arquivo da pasta (commit com `force: true`, no mesmo caminho). Não crie cópias com outros nomes.

Na mensagem, em uma ou duas linhas: para qual dia é a lista, quantas vendas, quantos produtos/unidades, que o arquivo foi salvo na pasta, e se houver SKU não encontrado ou venda sem SKU, quais são.

## Observações
- Se o usuário mandar uma planilha de produtos nova, use-a com `--produtos caminho.csv` (UTF-8 ou formato do Autcom, cp1252, separado por ponto e vírgula).
- Não altere nada no Mercado Livre (não marque como enviado, não imprima etiqueta, não responda mensagens): esta skill só lê as vendas.
