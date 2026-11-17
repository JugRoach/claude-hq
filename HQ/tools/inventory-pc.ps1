# READ-ONLY PC inventory for the life-organization plan. Moves, renames and deletes nothing; opens no file contents.
# For each root: lists its direct children with size, file count, newest file change (the best "last used" signal;
# Windows doesn't keep reliable last-access times). System, program and game roots are listed only (no sizing).
# C:\SIG: counts and sizes only, never names below the top level, never contents.
# Output: CSV at -Out (local only; see .gitignore HQ/work/life-org-data/).
param([string]$Out = "C:\Claude's Workspace\HQ\work\life-org-data\pc-inventory.csv")

New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
$listOnly = @('C:\Windows','C:\Program Files','C:\Program Files (x86)','C:\ProgramData','C:\Recovery','C:\System Volume Information',
              'C:\$Recycle.Bin','C:\Config.Msi','C:\Documents and Settings','C:\PerfLogs','C:\OneDriveTemp','C:\inetpub','C:\AMD',
              'C:\Users\mattt\AppData','C:\Users\mattt\Application Data','C:\Users\mattt\Local Settings',
              'C:\Nolvus')   # game install: listed, not measured

function Get-Measure($path) {
  $files = Get-ChildItem -LiteralPath $path -Recurse -File -Force -ErrorAction SilentlyContinue
  $sum = ($files | Measure-Object Length -Sum).Sum
  $newest = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
  [pscustomobject]@{ Files = @($files).Count; MB = [math]::Round(($sum / 1MB), 1); Newest = $newest }
}

$rows = New-Object System.Collections.ArrayList
function Add-Row($root, $item, $note) {
  $isDir = $item.PSIsContainer
  $listed = $listOnly -contains $item.FullName
  if ($isDir -and -not $listed) { $m = Get-Measure $item.FullName } elseif (-not $isDir) { $m = [pscustomobject]@{ Files = 1; MB = [math]::Round($item.Length / 1MB, 1); Newest = $item.LastWriteTime } } else { $m = [pscustomobject]@{ Files = ''; MB = ''; Newest = $item.LastWriteTime } }
  [void]$rows.Add([pscustomobject]@{ Root = $root; Name = $item.Name; Kind = $(if ($isDir) { 'folder' } else { 'file' }); Files = $m.Files; MB = $m.MB;
    Newest = $(if ($m.Newest) { $m.Newest.ToString('yyyy-MM-dd') } else { '' }); Note = $(if ($listed) { 'list only (system/program)' } else { $note }) })
}

# 1. other drives
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match '^[A-Z]:\\$' }
foreach ($dv in $drives) { [void]$rows.Add([pscustomobject]@{ Root = 'DRIVES'; Name = $dv.Root; Kind = 'drive'; Files = ''; MB = [math]::Round(($dv.Used / 1MB), 0); Newest = ''; Note = ('free {0:N0} GB' -f ($dv.Free / 1GB)) }) }

# 2. C:\ top level (and other drives' top level)
foreach ($dv in $drives) {
  Get-ChildItem -LiteralPath $dv.Root -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $n = if ($_.FullName -eq 'C:\SIG') { 'SIG: counts only, content never read' } elseif ($_.FullName -eq 'C:\Users') { 'see user folders' } else { '' }
    if ($_.FullName -in 'C:\Users') { [void]$rows.Add([pscustomobject]@{ Root = $dv.Root; Name = $_.Name; Kind = 'folder'; Files = ''; MB = ''; Newest = ''; Note = $n }) } else { Add-Row $dv.Root $_ $n }
  }
}

# 3. user profile top level, and inside each user library (local and OneDrive copies)
$userHome = 'C:\Users\mattt'
Get-ChildItem -LiteralPath $userHome -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -notin 'AppData','Application Data','Local Settings','NTUSER.DAT' -and $_.Name -notlike 'ntuser*' } | ForEach-Object { Add-Row $userHome $_ '' }
$libs = @("$userHome\Desktop","$userHome\Documents","$userHome\Downloads","$userHome\Pictures","$userHome\Videos","$userHome\Music","$userHome\OneDrive","$userHome\OneDrive\Desktop","$userHome\OneDrive\Documents","$userHome\OneDrive\Pictures","$userHome\Saved Games","$userHome\Coppice")
foreach ($lib in $libs) { if (Test-Path -LiteralPath $lib) { Get-ChildItem -LiteralPath $lib -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'desktop.ini' } | ForEach-Object { Add-Row $lib $_ '' } } }

$rows | Export-Csv -LiteralPath $Out -NoTypeInformation -Encoding UTF8
"rows: $($rows.Count) -> $Out"
