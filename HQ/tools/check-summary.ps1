# Quality gate for any "summary in the cloud, full file on the PC" pair (Taste Dossier, Budget, ...).
# Makes sure shrinking a full file to a summary never silently loses or leaks anything:
#   1. FRESH     - the summary's "SOURCE: ... | sha256 <16 hex> |" matches the full file now (else STALE: re-summarize)
#   2. COVERAGE  - every numbered section of the full file ("N. Title" lines) has a "## N." section in the summary
#   3. POINTERS  - every [a-b] line reference in the summary is inside the full file
#   4. KEEP-OUT  - no line of the summary contains a term from the keep-out list (one term per line, # comments)
#   5. COUNTS    - optional: "-CountPattern <regex>" counts matching lines in the full file; the summary must state
#                  that number next to "-CountLabel <text>" (e.g. 58 questions)
# Exit code 0 = PASS, 1 = FAIL. Read-only: it never edits either file.
#
#   & "C:\Claude's Workspace\HQ\tools\check-summary.ps1" -Full <full.txt> -Summary <summary.md> -KeepOut <keep-out.txt> `
#       -CountPattern '^\* [A-Z]\d+\.' -CountLabel 'questions'
param([Parameter(Mandatory)][string]$Full, [Parameter(Mandatory)][string]$Summary, [string]$KeepOut,
      [string]$CountPattern, [string]$CountLabel)

$fail = 0
function Report-Check($name, $ok, $detail) { "{0,-9} {1}  {2}" -f $name, $(if ($ok) { 'PASS' } else { 'FAIL' }), $detail; if (-not $ok) { $script:fail++ } }

$fullLines = Get-Content $Full -Encoding UTF8
$sum = Get-Content $Summary -Raw -Encoding UTF8
$sumLines = Get-Content $Summary -Encoding UTF8

# 1. fresh
$hash = (Get-FileHash $Full -Algorithm SHA256).Hash.Substring(0, 16).ToLower()
$m = [regex]::Match($sum, 'sha256\s+([0-9a-f]{16})')
Report-Check 'FRESH' ($m.Success -and $m.Groups[1].Value -eq $hash) "summary says $($m.Groups[1].Value), full file is $hash"

# 2. coverage
$secs = @($fullLines | Where-Object { $_ -match '^(\d{1,2})\.\s+\S' -and $_.Length -lt 90 } | ForEach-Object { [int]([regex]::Match($_, '^(\d{1,2})').Groups[1].Value) } | Sort-Object -Unique)
$missing = @($secs | Where-Object { $sum -notmatch "(?m)^##\s+$_\." })
Report-Check 'COVERAGE' ($missing.Count -eq 0) ("{0} sections in full file; missing in summary: {1}" -f $secs.Count, $(if ($missing) { $missing -join ', ' } else { 'none' }))

# 3. pointers
$bad = @([regex]::Matches($sum, '\[(\d+)[–-](\d+)\]') | Where-Object { [int]$_.Groups[1].Value -lt 1 -or [int]$_.Groups[2].Value -gt $fullLines.Count -or [int]$_.Groups[1].Value -gt [int]$_.Groups[2].Value } | ForEach-Object { $_.Value })
Report-Check 'POINTERS' ($bad.Count -eq 0) ("full file has {0} lines; bad refs: {1}" -f $fullLines.Count, $(if ($bad) { $bad -join ' ' } else { 'none' }))

# 4. keep-out
if ($KeepOut -and (Test-Path $KeepOut)) {
  $terms = @(Get-Content $KeepOut -Encoding UTF8 | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith('#') })
  $hits = @(foreach ($t in $terms) { $n = 0; foreach ($l in $sumLines) { $n++; if ($l -match [regex]::Escape($t)) { "line $n" } } })
  # never print the term itself: the list is private
  Report-Check 'KEEP-OUT' ($hits.Count -eq 0) ("{0} terms checked; hits: {1}" -f $terms.Count, $(if ($hits) { $hits -join ', ' } else { 'none' }))
} else { Report-Check 'KEEP-OUT' $false 'no keep-out list given' }

# 5. counts
if ($CountPattern) {
  $n = @($fullLines | Where-Object { $_ -match $CountPattern }).Count
  $stated = [regex]::Match($sum, "(\d+)\s+$([regex]::Escape($CountLabel))")
  Report-Check 'COUNTS' ($stated.Success -and [int]$stated.Groups[1].Value -eq $n) "full file has $n $CountLabel; summary states $($stated.Groups[1].Value)"
}

if ($fail) { "RESULT    FAIL ($fail check(s))"; exit 1 } else { "RESULT    PASS"; exit 0 }
