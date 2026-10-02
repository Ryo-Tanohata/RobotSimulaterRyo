# Wait for an already running experiment 2 (sim/bipedal/run_exp2.sh in WSL) to finish,
# then commit + push the results and, only with -Shutdown, shut Windows down.
#   powershell -ExecutionPolicy Bypass -File tools\mjx\wait_exp2_then_shutdown.ps1 [-Shutdown]
# Shuts down ONLY with -Shutdown (only when the user explicitly asks). Cancel within 2 minutes with:  shutdown /a
param([switch]$Shutdown)

$ErrorActionPreference = "Continue"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo
[Environment]::CurrentDirectory = $repo
$log = Join-Path $repo "sim\bipedal\runs\exp2.driver.log"
function Log($m) { Add-Content -Path $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" -Encoding UTF8 }

Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[Win32.Power]::SetThreadExecutionState([uint32]"0x80000001") | Out-Null  # keep awake while waiting

Log "waiting for experiment 2 (run_study.sh) to finish"
while ($true) {
  $o = wsl -d Ubuntu -- pgrep -f run_study.sh
  if (-not $o) { break }
  Start-Sleep 60
}
Log "experiment 2 finished"

git add docs/bipedal_study2.md docs/media/bipedal_study2.png 2>$null
git add docs/media/bipedal_study2_*.mp4 2>$null
foreach ($d in Get-ChildItem "sim\bipedal\runs" -Directory -Filter "e2_*_seed*") {
  $ck = Get-ChildItem (Join-Path $d.FullName "checkpoints") -Directory -ErrorAction SilentlyContinue | Sort-Object { [long]$_.Name } | Select-Object -Last 1
  if ($ck) { git add -f $ck.FullName }
  foreach ($f in "log.csv", "config.json", "eval.json") { $p = Join-Path $d.FullName $f; if (Test-Path $p) { git add -f $p } }
}
git add -f sim/bipedal/runs/study2.log sim/bipedal/runs/exp2.driver.log 2>$null
$msg = Join-Path $env:TEMP "commit_exp2.txt"
$text = "実験 2 の結果: 体に合わせたお手本・速さ・足首のばねで、3 つの体 x 4 足・2 足 x 3 回`n`n- docs/bipedal_study2.md と docs/media/bipedal_study2.png (eval.py --summary が自動で作成)`n- 種 1 の動画 docs/media/bipedal_study2_*.mp4`n- 学習のあと自動でプッシュ (考察はまだ。bipedal_experiment2.md の 3〜5 章はこれから書く)`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
[IO.File]::WriteAllText($msg, $text, (New-Object Text.UTF8Encoding $false))
git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -q -F $msg
for ($i = 0; $i -lt 3; $i++) {
  git pull -q --rebase --autostash origin claude/physics-engine-robot-simulator-xmyxdn
  git push -q origin claude/physics-engine-robot-simulator-xmyxdn
  if ($LASTEXITCODE -eq 0) { Log "push ok"; break }
  Log "push failed, retry"; Start-Sleep 30
}
if (-not $Shutdown) { Log "done (no shutdown; pass -Shutdown only when the user asks)"; exit }
Log "shutdown in 120 s (user asked on 2026-10-03)"
wsl --shutdown
shutdown.exe /s /t 120 /c "Experiment 2 finished and pushed. Shutting down in 2 minutes (cancel: shutdown /a)."
