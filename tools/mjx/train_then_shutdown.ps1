# Train on the GPU (WSL2) for a fixed time, render a video, commit + push the results, then shut down Windows.
#   powershell -ExecutionPolicy Bypass -File tools\mjx\train_then_shutdown.ps1 -Name s1_long -Minutes 60
# Checkpoints are saved during training, so stopping at the time limit keeps everything up to the last save.
# Shuts down ONLY with -Shutdown (only when the user explicitly asks). Cancel within 2 minutes with:  shutdown /a
param([string]$Name = "s1_long", [int]$Minutes = 60, [double]$S = 1.0, [switch]$Shutdown, [switch]$NoGit)

$ErrorActionPreference = "Continue"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo
$log = Join-Path $repo "sim\bipedal\runs\$Name.driver.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
function Log($m) { $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"; Add-Content -Path $log -Value $line -Encoding UTF8 }

# Keep Windows awake while this script runs (no settings are changed; released when the script exits)
Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[Win32.Power]::SetThreadExecutionState([uint32]"0x80000001") | Out-Null  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

$wslRepo = "/mnt/c" + ($repo.Substring(2) -replace '\\', '/')
$secs = $Minutes * 60
Log "start training $Name for $Minutes min (s=$S)"
wsl -d Ubuntu -- bash -lc "cd '$wslRepo/sim/bipedal' && timeout -s INT $secs ~/mjx/venv/bin/python train.py $Name --s $S --steps 400000000 --evals 100 > runs/$Name.train.log 2>&1; tail -3 runs/$Name/log.csv"
Log "training finished"

Log "render video"
wsl -d Ubuntu -- bash -lc "cd '$wslRepo/sim/bipedal' && MUJOCO_GL=egl timeout 600 ~/mjx/venv/bin/python render.py $Name ../../docs/media/bipedal_$Name.mp4 --s $S --seconds 10 2>&1 | grep -v -E 'Module|Warning|warn|egl' | tail -4 >> runs/$Name.driver.log"

if ($NoGit) { Log "done (no git, no shutdown)"; exit }
Log "commit and push"
$ck = Get-ChildItem "sim\bipedal\runs\$Name\checkpoints" -Directory -ErrorAction SilentlyContinue | Sort-Object { [long]$_.Name } | Select-Object -Last 1
git add "sim/bipedal/render.py" "tools/mjx/train_then_shutdown.ps1" 2>$null
git add -f "sim/bipedal/runs/$Name/log.csv" "sim/bipedal/runs/$Name.driver.log" 2>$null
if ($ck) { git add -f $ck.FullName; git rm -q --cached --ignore-unmatch (Join-Path $ck.FullName "commit_success.txt") }  # it holds the PC path (user name): keep it out
if (Test-Path "docs\media\bipedal_$Name.mp4") { git add "docs/media/bipedal_$Name.mp4" }
$msg = Join-Path $env:TEMP "commit_$Name.txt"
$text = "2 足歩行: GPU で $Minutes 分の学習 ($Name, s=$S) の結果`n`n- 最後に保存した脳、学習の記録 (log.csv)、動画`n- 学習のあと自動でプッシュし、パソコンをシャットダウン`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
[IO.File]::WriteAllText($msg, $text, (New-Object Text.UTF8Encoding $false))
git -c user.name=Ryo-Tanohata -c user.email=39688846+Ryo-Tanohata@users.noreply.github.com commit -q -F $msg
for ($i = 0; $i -lt 3; $i++) {
  git push -q origin claude/physics-engine-robot-simulator-xmyxdn
  if ($LASTEXITCODE -eq 0) { Log "push ok"; break }
  Log "push failed, retry"; Start-Sleep 30
}

if (-not $Shutdown) { Log "done (no shutdown; pass -Shutdown only when the user asks)"; exit }
Log "shutdown in 120 s"
wsl --shutdown
shutdown.exe /s /t 120 /c "Training finished and pushed. Shutting down in 2 minutes (cancel: shutdown /a)."
