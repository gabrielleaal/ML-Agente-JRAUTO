---
name: etiquetas-ml-mdk022
description: Baixa as etiquetas de envio do Mercado Livre da JR Auto Peças que estão "prontas para imprimir" (pelo conector JR Mercado Livre, ferramenta ml_etiquetas) e imprime cada uma na impressora térmica de etiquetas MDK-022 do PC, em 102 x 152 mm, sem borda e sem cortar. Use sempre que pedirem para imprimir etiquetas do ML, etiquetas de envio, etiquetas do dia, "imprime as etiquetas", "manda as etiquetas pra impressora", reimprimir a etiqueta de uma venda/envio, ou quando a tarefa agendada das 8h30 (seg-sex) rodar. Também cobre os problemas conhecidos da MDK-022 (unidade D:, papel, margem, corte em cima).
---

# Etiquetas do ML na MDK-022

Rotina da JR Auto Peças: pegar as etiquetas de envio do Mercado Livre que estão prontas e imprimir na térmica MDK-022, uma etiqueta por adesivo.

Tudo roda no PC Windows do usuário: o conector do ML entrega um link do PDF, e o script `C:\MDK-D\imprimir-etiquetas-ml.ps1` baixa, recorta e imprime.

## Por que é feito assim (o que já deu errado)

- **O driver da MDK-022 grava arquivos temporários em `D:\`** (`D:\Mirrror.data`, `D:\Page_180.bmp`...). O PC só tem C:, então existe uma unidade D: virtual apontando para `C:\MDK-D`, criada a cada boot pela tarefa do Windows **"MDK-022 Unidade D"** (roda como SYSTEM: `subst D: C:\MDK-D`). Sem D:, todo documento falha com "arquivo não encontrado" (erro 2) ou "dispositivo não está pronto" (erro 21). Não apague a pasta `C:\MDK-D` nem a tarefa.
- **A MDK-022 é impressora de etiqueta (linguagem TSPL)**, não de cupom: comandos ESC/POS são ignorados.
- **O PDF do ML vem em A4 deitado**, com até 3 etiquetas lado a lado. O script separa cada etiqueta pela faixa em branco entre elas, recorta e converte para preto e branco puro (código de barras nítido).
- **Tamanho:** papel 4x6" do driver (RawKind 257 = 102 x 152 mm). Em 100 x 150 mm o topo ficava cortado. A etiqueta é esticada para ocupar a largura toda (o usuário não quer borda).
- **Corte em cima:** a MDK-022 começa a imprimir ~2,5 mm antes do topo do adesivo. O script desce a imagem 2,5 mm (`-DescerMm 2.5`, padrão) e encolhe a altura na mesma medida. Esse ajuste foi aprovado pelo usuário em 06/11/2026.
- **Baixar a etiqueta no ML marca o envio como IMPRESSO** (sai de "pronto para imprimir" e vai para "pronto para coleta"). O usuário disse que isso é ok (o envio continua agendado). Reimprimir envio já impresso não muda nada. Por isso: confira a impressora **antes** de baixar.

## Passo a passo

### 1. Conferir o PC e a impressora (antes de baixar qualquer coisa)

```powershell
"D: existe: $(Test-Path D:\)"
Test-Path C:\MDK-D\imprimir-etiquetas-ml.ps1
Get-Printer -Name 'MDK-022' | Select-Object Name, PrinterStatus, WorkOffline
Get-PrintJob -PrinterName 'MDK-022' | Select-Object Id, DocumentName, JobStatus
```

- Se **D: não existir**: pare e avise. Não baixe nada (senão os envios ficam marcados como impressos sem etiqueta). A correção é reiniciar o PC ou rodar a tarefa "MDK-022 Unidade D" no Agendador de Tarefas (precisa de administrador).
- Se **o script não existir** em `C:\MDK-D`: copie `scripts/imprimir-etiquetas-ml.ps1` desta skill para `C:\MDK-D\`.
- Se a impressora estiver offline ou houver trabalhos travados com erro: avise e não baixe.

### 2. Ver quais etiquetas estão prontas

Chame `ml_etiquetas` com `so_listar: true`. Isso não marca nada. Se `total_envios` for 0, diga que não há etiquetas pendentes e encerre.

### 3. Baixar e imprimir

Chame `ml_etiquetas` com `entrega: "link"` e `formato: "pdf"`, passando os mesmos `shipment_ids` da listagem (ou sem ids, para pegar todas as prontas, até 50). **Não use `zpl2`**: a MDK-022 é TSPL e o ZPL vem zipado.

Prefira o link à entrega `arquivo` (base64): o link é baixado direto pelo PowerShell e não passa o PDF inteiro pela conversa. O link vale 1 hora.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\MDK-D\imprimir-etiquetas-ml.ps1 -Url "<link devolvido>"
```

O script salva o PDF em `C:\MDK-D\etiquetas\etiquetas-AAAAMMDD-HHMMSS.pdf` (fica guardado para reimprimir) e mostra "Etiquetas encontradas: N" e "Enviado para MDK-022: N etiqueta(s)".

Confira que N bate com `total_envios`. Uma folha pode ter até 3 etiquetas, então o número de páginas não é o número de etiquetas. Se não bater, rode com `-SoPreview` (gera PNGs em `C:\MDK-D\etiquetas\preview\`), olhe as imagens e explique.

### 4. Conferir e relatar

Espere ~10 s e confira a fila e os erros:

```powershell
Get-PrintJob -PrinterName 'MDK-022' | Select-Object Id, DocumentName, JobStatus
Get-WinEvent -LogName 'Microsoft-Windows-PrintService/Admin' -MaxEvents 5 |
  Where-Object { $_.TimeCreated -gt (Get-Date).AddMinutes(-2) } | Format-List TimeCreated, Message
```

Relate em português simples:
- Quantas etiquetas foram impressas, com a lista: venda, produto e quantidade (vem em `envios[].itens` da resposta do `ml_etiquetas`).
- Onde o PDF ficou salvo.
- Qualquer erro. Se algo falhou depois do download, deixe claro que esses envios já constam como impressos no ML e que dá para reimprimir com `-Pdf "<arquivo salvo>"`.

## Reimprimir

- Etiqueta de uma venda/envio específico: `ml_etiquetas` com `shipment_ids: ["<envio>"]` e `entrega: "link"`, depois `-Url`. Para envio já impresso, isso não muda status.
- De um PDF já baixado: `-Pdf "C:\MDK-D\etiquetas\<arquivo>.pdf"`.

## Ajustes finos (só se o usuário reclamar)

| Sintoma | Ajuste |
|---|---|
| Corta em cima / sobra faixa embaixo | aumentar `-DescerMm` (ex.: 3.5) |
| Sobra faixa em cima | diminuir `-DescerMm` (ex.: 1.5) |
| Começa no meio de uma etiqueta, pula etiquetas | calibrar: com a impressora ligada, segurar FEED 2-3 s até a luz piscar |
| Impressão fraca | conferir se a bobina está com o lado térmico virado para a cabeça (risque com a unha: o lado térmico escurece) |

Se um ajuste ficar permanente, mude o padrão do parâmetro no script em `C:\MDK-D` (e na cópia em `scripts/` desta skill).

## Quando roda pela tarefa agendada (seg-sex, 8h30)

Ninguém está olhando a tela. Então:
- Faça os passos 1 a 4 sem pedir confirmação. O usuário já autorizou baixar e imprimir as etiquetas prontas.
- Se o passo 1 falhar, **não baixe nada**: relate o problema e pare.
- Termine com um resumo curto do que foi impresso ou do que impediu.
