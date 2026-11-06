# Imprime etiquetas do Mercado Livre (PDF) na impressora termica MDK-022, papel 4x6 (102x152 mm), sem borda.
# Uso:
#   powershell -ExecutionPolicy Bypass -File C:\MDK-D\imprimir-etiquetas-ml.ps1 -Pdf "C:\caminho\etiquetas.pdf"
#   powershell -ExecutionPolicy Bypass -File C:\MDK-D\imprimir-etiquetas-ml.ps1 -Url "https://...pdf"
#   -SoPreview  : so gera PNGs em C:\MDK-D\etiquetas\preview (nao imprime)
# Requisito: a unidade D: virtual (tarefa "MDK-022 Unidade D") precisa existir, senao o driver falha.
param(
  [string]$Pdf,
  [string]$Url,
  [string]$Impressora = 'MDK-022',
  [int]$Dpi = 300,
  [switch]$SoPreview,
  [double]$Folga = 0,
  # Empurra a impressao para baixo (mm). A MDK-022 comeca a imprimir ~2,5 mm antes do topo da etiqueta.
  [double]$DescerMm = 2.5
)
$ErrorActionPreference = 'Stop'
$pasta = 'C:\MDK-D\etiquetas'
New-Item -ItemType Directory -Force $pasta | Out-Null

if ($Url) {
  $Pdf = Join-Path $pasta ("etiquetas-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".pdf")
  Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Pdf
}
if (-not $Pdf -or -not (Test-Path $Pdf)) { throw "PDF nao encontrado. Use -Pdf ou -Url." }
if (-not $SoPreview -and -not (Test-Path 'D:\')) { throw "Unidade D: nao existe. Rode a tarefa 'MDK-022 Unidade D' ou reinicie o PC." }

# --- Renderiza o PDF com a API nativa do Windows (Windows.Data.Pdf) ---
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
$asTaskAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
function Await($op, [Type]$t) { $task = $asTaskGeneric.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(); $task.Result }
function AwaitAction($op) { $task = $asTaskAction.Invoke($null, @($op)); $task.Wait() }

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path $Pdf).Path)) ([Windows.Storage.StorageFile])
$doc  = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])

Add-Type -AssemblyName System.Drawing
$imagens = New-Object System.Collections.Generic.List[System.Drawing.Bitmap]
for ($i = 0; $i -lt $doc.PageCount; $i++) {
  $page = $doc.GetPage($i)
  $sz = $page.Size   # em DIPs (1/96 pol)
  $opt = New-Object Windows.Data.Pdf.PdfPageRenderOptions
  $opt.DestinationWidth  = [uint32][Math]::Round($sz.Width  / 96 * $Dpi)
  $opt.DestinationHeight = [uint32][Math]::Round($sz.Height / 96 * $Dpi)
  $ms = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
  AwaitAction ($page.RenderToStreamAsync($ms, $opt))
  $net = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($ms.GetInputStreamAt(0))
  $bmp = New-Object System.Drawing.Bitmap $net
  Write-Host ("Pagina {0}: {1:N0} x {2:N0} mm" -f ($i+1), ($sz.Width/96*25.4), ($sz.Height/96*25.4))
  $imagens.Add($bmp)
  $page.Dispose()
}

# --- Recorta cada etiqueta da folha (o ML poe ate 3 por folha A4, lado a lado) e binariza ---
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System; using System.Drawing; using System.Drawing.Imaging; using System.Collections.Generic; using System.Runtime.InteropServices;
public static class Recorte {
  static byte[] Gray(Bitmap b, out int w, out int h) {
    w = b.Width; h = b.Height; var r = new Rectangle(0,0,w,h);
    var d = b.LockBits(r, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
    var buf = new byte[d.Stride*h]; Marshal.Copy(d.Scan0, buf, 0, buf.Length); b.UnlockBits(d);
    var g = new byte[w*h];
    for (int y=0;y<h;y++) for (int x=0;x<w;x++){ int i=y*d.Stride+x*4; int a=buf[i+3];
      int v=(buf[i]*114+buf[i+1]*587+buf[i+2]*299)/1000; v = (v*a + 255*(255-a))/255; g[y*w+x]=(byte)v; }
    return g;
  }
  public static List<Bitmap> Etiquetas(Bitmap b, int limiar, int gapMin, int larguraMin) {
    int w,h; var g = Gray(b, out w, out h); var res = new List<Bitmap>();
    var col = new bool[w];
    for (int x=0;x<w;x++){ for(int y=0;y<h;y++) if (g[y*w+x]<limiar){ col[x]=true; break; } }
    int xi=-1, branco=0;
    for (int x=0;x<=w;x++){
      bool c = x<w && col[x];
      if (c){ if (xi<0) xi=x; branco=0; }
      else if (xi>=0){ branco++; if (branco>=gapMin || x==w){ int xf=x-branco; if (xf-xi+1>=larguraMin) res.Add(Corta(g,w,h,xi,xf,limiar)); xi=-1; branco=0; } }
    }
    return res;
  }
  static Bitmap Corta(byte[] g,int w,int h,int x0,int x1,int limiar){
    int y0=h, y1=-1;
    for(int y=0;y<h;y++) for(int x=x0;x<=x1;x++) if(g[y*w+x]<limiar){ if(y<y0)y0=y; y1=y; break; }
    int cw=x1-x0+1, ch=y1-y0+1;
    var o = new Bitmap(cw, ch, PixelFormat.Format24bppRgb);
    var d = o.LockBits(new Rectangle(0,0,cw,ch), ImageLockMode.WriteOnly, PixelFormat.Format24bppRgb);
    var buf = new byte[d.Stride*ch];
    for(int y=0;y<ch;y++) for(int x=0;x<cw;x++){ byte v = g[(y0+y)*w+(x0+x)] < 160 ? (byte)0 : (byte)255; int i=y*d.Stride+x*3; buf[i]=v;buf[i+1]=v;buf[i+2]=v; }
    Marshal.Copy(buf,0,d.Scan0,buf.Length); o.UnlockBits(d); return o;
  }
}
'@
$folhas = $imagens
$imagens = New-Object System.Collections.Generic.List[System.Drawing.Bitmap]
foreach ($f in $folhas) {
  # gap de 3 mm em branco separa etiquetas; etiqueta tem pelo menos 40 mm de largura
  $gap = [int]($Dpi * 3 / 25.4); $min = [int]($Dpi * 40 / 25.4)
  foreach ($e in [Recorte]::Etiquetas($f, 200, $gap, $min)) { $imagens.Add($e) }
}
Write-Host ("Etiquetas encontradas: {0}" -f $imagens.Count)
if ($imagens.Count -eq 0) { throw "Nenhuma etiqueta encontrada no PDF." }

if ($SoPreview) {
  $pv = Join-Path $pasta 'preview'; New-Item -ItemType Directory -Force $pv | Out-Null
  for ($i = 0; $i -lt $imagens.Count; $i++) { $imagens[$i].Save((Join-Path $pv ("pagina{0}.png" -f ($i+1)))) }
  Write-Host "Preview salvo em $pv"; return
}

# --- Imprime cada pagina numa etiqueta 4x6, ajustando sem distorcer ---
$pd = New-Object System.Drawing.Printing.PrintDocument
$pd.PrinterSettings.PrinterName = $Impressora
if (-not $pd.PrinterSettings.IsValid) { throw "Impressora '$Impressora' nao encontrada." }
# Papel 4x6" (102 x 152 mm) - tamanho do driver (RawKind 257). Com 100x150 cortava em cima.
$papel = $pd.PrinterSettings.PaperSizes | Where-Object { $_.RawKind -eq 257 } | Select-Object -First 1
if (-not $papel) { $papel = New-Object System.Drawing.Printing.PaperSize('Etiqueta 4x6', 400, 600) }
$pd.DefaultPageSettings.PaperSize = $papel
$pd.DefaultPageSettings.Margins = New-Object System.Drawing.Printing.Margins(0,0,0,0)
$pd.OriginAtMargins = $false
$pd.DocumentName = 'Etiquetas ML - ' + [IO.Path]::GetFileName($Pdf)
$script:idx = 0
$pd.add_PrintPage({
  param($s, $e)
  $img = $imagens[$script:idx]
  $W = $e.PageBounds.Width; $H = $e.PageBounds.Height        # 1/100 pol
  $iw = $img.Width; $ih = $img.Height
  # gira se a pagina do PDF estiver deitada e a etiqueta em pe
  if (($iw -gt $ih) -and ($H -gt $W)) { $img.RotateFlip([System.Drawing.RotateFlipType]::Rotate90FlipNone); $iw = $img.Width; $ih = $img.Height }
  # Preenche a etiqueta 10x15 inteira (sem margem). $Folga = recuo de seguranca em mm no topo/base.
  $f = $Folga / 25.4 * 100
  $desc = $DescerMm / 25.4 * 100
  $dw = $W; $dh = $H - 2 * $f - $desc
  $x = - $e.PageSettings.HardMarginX
  $y = $f + $desc - $e.PageSettings.HardMarginY
  $e.Graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
  $e.Graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
  $e.Graphics.DrawImage($img, [single]$x, [single]$y, [single]$dw, [single]$dh)
  $script:idx++
  $e.HasMorePages = ($script:idx -lt $imagens.Count)
})
$pd.Print()
Write-Host ("Enviado para {0}: {1} etiqueta(s)." -f $Impressora, $imagens.Count)

