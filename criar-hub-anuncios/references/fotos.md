# Fotos do anúncio: do Syntra para o Hub

Use quando o produto não tem foto no Hub (aba Mídias vazia). O Mercado Livre recusa o anúncio sem foto. Leia inteiro antes de começar.

## 1. Achar e conferir o kit no Syntra

- O conector do Syntra tem `listar_kits` (kits recentes, com id) e `ver_kit` (situação e fotos). Procure o kit pelo título do anúncio ou pelo SKU.
- Pode haver **mais de um kit do mesmo produto**: pergunte ao usuário qual usar (no 37004 ele escolheu o mais novo).
- Se não houver kit, a criação é com a skill `titulos-anuncios-ml` (`criar_kit_de_fotos`, custa cerca de US$ 0,01 por foto) e depende da foto base da peça: não crie sem o usuário pedir.
- Confira com `ver_kit` com `mostrar_fotos=true`: a peça deve ser a mesma em todas (formato, furos, conectores), e as de "ângulo de trás" e "instalada no carro" costumam vir com aviso de ângulo. Diga ao usuário se alguma parecer errada. As posições 9 e 10 são as artes fixas da loja.

## 2. Baixar para o computador (PULAR em lote)

Regra do usuário (29/10/2026): **não baixar as fotos no PC**. O passo 3 busca direto no Syntra pela própria página do Hub, então o download só serve para guardar cópia local. Só faça este passo se o usuário pedir a cópia. Baixar arquivo exige o OK do usuário (diga origem, nomes e tamanho). Use `scripts/baixar_fotos.py` da skill `titulos-anuncios-ml` (`C:\Users\Usuario\.claude\skills\titulos-anuncios-ml\scripts\baixar_fotos.py`):

1. Rode `ver_kit` logo antes: os links das fotos valem cerca de 1 hora.
2. Grave `lista.txt` com a ferramenta Write, uma linha por foto, `SKU|posição|url`, com as 10 fotos (posição do kit: capa = 1, artes da loja = 9 e 10).
3. **O caminho do scratchpad passa de 260 caracteres e o Python não abre.** Copie a lista para uma pasta curta, por exemplo `C:\Users\Usuario\Documents\Claude Project\Planilhas Títulos\tmp\lista-<SKU>.txt` (PowerShell: `Copy-Item -LiteralPath '\\?\<caminho longo>' -Destination ...`).
4. `py scripts/baixar_fotos.py <lista>` a partir da pasta da skill. Salva em `C:\Users\Usuario\Documents\Claude Project\Fotos Syntra\<SKU>\` com o nome `<SKU>-<posição+1>` (37004-2.jpg ... 37004-11.webp; as 2 artes da loja saem em WebP).
5. Apague a lista temporária: ela contém tokens de acesso.

## 3. Subir no Hub

O navegador do app **não abre o seletor de arquivos do Windows**. O que funciona é a própria página do Hub buscar as fotos no Syntra (o CORS é liberado) e anexá-las ao campo de upload:

1. Abra **uma aba nova** em `https://hub.citelsoftware.com.br/Produtos/Alterar/<SKU>` com `preview_start`. A aba do anúncio fica intacta.
2. O campo é `#file-1` (aceita só `image/jpeg`, vários arquivos, `onchange` do Hub cria um slot por foto). As artes da loja vêm em WebP e precisam virar JPEG. Rode na aba nova, com as 10 URLs na ordem do kit (use as URLs frescas do `ver_kit`):

```js
const urls = [/* 10 URLs assinadas, posição 1 a 10 */];
const SKU = '37004';
window.__fotos = [];
for (let i = 0; i < urls.length; i++) {
  const r = await fetch(urls[i]);
  if (!r.ok) throw new Error('falhou ' + (i+1) + ' ' + r.status);
  let b = await r.blob();
  if (b.type !== 'image/jpeg') {            // WebP -> JPEG por canvas
    const bm = await createImageBitmap(b);
    const c = document.createElement('canvas'); c.width = bm.width; c.height = bm.height;
    const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0,0,c.width,c.height); x.drawImage(bm,0,0);
    b = await new Promise(res => c.toBlob(res, 'image/jpeg', 0.92));
  }
  window.__fotos.push(new File([b], SKU + '-' + (i+2) + '.jpg', {type: 'image/jpeg'}));
}
```

3. Anexe ao campo e dispare o evento do Hub:

```js
const dt = new DataTransfer(); window.__fotos.forEach(f => dt.items.add(f));
const inp = document.getElementById('file-1'); inp.files = dt.files;
inp.dispatchEvent(new Event('change', {bubbles: true}));
```

4. O Hub abre **um diálogo por imagem** ("imagem fora do padrão esperado", 1600 px contra 1200 px, ajuste automático). Clique OK em cada um (botão OK perto de (333,646) no screenshot 800x705), **sem marcar "Não exibir novamente"**. Tire um screenshot entre os cliques para garantir que é o diálogo certo. Ao final devem existir 10 slots com foto.
5. Marque a posição 1 (capa) como "Imagem Principal": `document.getElementById('main1').click()`. Confira que só ela está marcada.
6. Clique em **Salvar** das mídias (`#btn-save-media`, perto de (603,646) depois de rolar até o fim).
7. Pode aparecer "Algumas imagens não foram salvas" apontando uma foto. **Recarregue a página e confira**: no 37004 as 10 estavam salvas (1200x1200) mesmo assim. Confira com:

```js
[...document.querySelectorAll('.product-image-group img.product-image-img')]
  .map((i,n)=>[n+1, i.naturalWidth, i.naturalHeight, i.complete])
```

Se alguma realmente faltar, refaça só ela (anexe só esse arquivo) e salve de novo.
8. Feche a aba nova e volte à aba do anúncio, que continua preenchida, para salvar o anúncio.
