param(
  [ValidateSet("APP","ARTICLE")][string]$PackageKind="APP",
  [string]$Directory="."
)
if ($PackageKind -eq "APP") { $Stem="CangaMetaG_App_Final.zip"; $Count=29 }
else { $Stem="CangaMetaG_Article_Final.zip"; $Count=47 }
$Suffix = "of-{0:D3}" -f $Count
$Parts = Get-ChildItem -LiteralPath $Directory -Filter "$Stem.part*-$Suffix" | Sort-Object Name
if ($Parts.Count -ne $Count) { throw "Expected $Count parts; found $($Parts.Count)" }
$Output = Join-Path $Directory $Stem
$Out = [System.IO.File]::Create($Output)
try {
  foreach ($Part in $Parts) {
    $In = [System.IO.File]::OpenRead($Part.FullName)
    try { $In.CopyTo($Out) } finally { $In.Dispose() }
  }
} finally { $Out.Dispose() }
$ExpectedLine = Get-Content (Join-Path $Directory "$Stem.sha256") | Select-Object -First 1
$Expected = ($ExpectedLine -split '\s+')[0].ToLowerInvariant()
$Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Output).Hash.ToLowerInvariant()
if ($Actual -ne $Expected) { throw "SHA-256 mismatch: expected $Expected; got $Actual" }
Write-Host "SHA-256 validated: $Actual"
Write-Host "Test the archive with: tar -tf `"$Output`" or 7z t `"$Output`""
