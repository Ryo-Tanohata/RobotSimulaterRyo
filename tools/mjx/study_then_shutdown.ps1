# Run the 2-leg / 4-leg comparison study (train all conditions x seeds, evaluate, chart, videos),
# then commit + push the results and shut Windows down.
#   powershell -ExecutionPolicy Bypass -File tools\mjx\study_then_shutdown.ps1 [-Steps 60000000] [-Seeds 3] [-NoShutdown]
# Cancel the shutdown within 2 minutes with:  shutdown /a
param([long]$Steps = 60000000, [int]$Seeds = 3, [switch]$NoShutdown)

$ErrorActionPreference = "Continue"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo
[Environment]::CurrentDirectory = $repo
$log = Join-Path $repo "sim\bipedal\runs\study.driver.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
function Log($m) { Add-Content -Path $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" -Encoding UTF8 }

Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[Win32.Power]::SetThreadExecutionState([uint32]"0x80000001") | Out-Null  # keep awake while running

Log "study start (steps=$Steps seeds=$Seeds)"
$wslScript = "/mnt/c" + ($repo.Substring(2) -replace '\\', '/') + "/sim/bipedal/run_study.sh"
wsl -d Ubuntu -e bash $wslScript $Steps $Seeds *>> (Join-Path $repo "sim\bipedal\runs\study.log")
Log "study finished"

Log "commit and push"
git add sim/bipedal docs/bipedal_study.md docs/media/bipedal_study.png 2>$null
git add docs/media/bipedal_study_*.mp4 2>$null
foreach ($d in Get-ChildItem "sim\bipedal\runs" -Directory -Filter "*_seed*") {
  $ck = Get-ChildItem (Join-Path $d.FullName "checkpoints") -Directory -ErrorAction SilentlyContinue | Sort-Object { [long]$_.Name } | Select-Object -Last 1
  if ($ck) { git add -f $ck.FullName }
  foreach ($f in "log.csv", "config.json", "eval.json") { $p = Join-Path $d.FullName $f; if (Test-Path $p) { git add -f $p } }
}
git add -f sim/bipedal/runs/study.log sim/bipedal/runs/study.driver.log 2>$null
$msg = Join-Path $env:TEMP "commit_study.txt"
$text = "2 足・4 足の比較: 学習量をそろえ各条件 3 回、支える力のコストも評価`n`n- 4 条件 (チンパンジー型 4 足・2 足、ルーシー型 2 足、人型 2 足) x 乱数の種 $Seeds、各 $Steps ステップ`n- docs/bipedal_study.md と docs/media/bipedal_study.png (自動で作成)`n- 学習のあと自動でプッシュし、パソコンをシャットダウン`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
[IO.File]::WriteAllText($msg, $text, (New-Object Text.UTF8Encoding $false))
git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -q -F $msg
for ($i = 0; $i -lt 3; $i++) {
  git push -q origin claude/physics-engine-robot-simulator-xmyxdn
  if ($LASTEXITCODE -eq 0) { Log "push ok"; break }
  Log "push failed, retry"; Start-Sleep 30
}
if ($NoShutdown) { Log "done (no shutdown)"; exit }
Log "shutdown in 120 s"
wsl --shutdown
shutdown.exe /s /t 120 /c "Study finished and pushed. Shutting down in 2 minutes (cancel: shutdown /a)."
