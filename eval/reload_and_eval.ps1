# Перезапускает n8n (так очищается база в памяти), загружает руководство заново
# и прогоняет проверочные вопросы.
# Запуск: powershell -File eval\reload_and_eval.ps1 [-Ids 1,2,11,12]
param([int[]]$Ids = @())

$root = Split-Path $PSScriptRoot -Parent
docker restart n8n-rag | Out-Null
do { Start-Sleep 3; try { $ok = (Invoke-WebRequest http://localhost:5678/healthz -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } catch { $ok = $false } } until ($ok)
Start-Sleep 10                                    # даём включиться вебхукам

Invoke-RestMethod -Uri http://localhost:5678/webhook/giis-ingest -Method Post -Body '{}' -ContentType 'application/json' | Out-Null
Start-Sleep 10
# ждём, пока загрузка закончится: последний запуск перестанет быть running
docker cp "$root\eval\exec_status.js" n8n-rag:/tmp/exec_status.js | Out-Null
do { Start-Sleep 15; $s = docker exec n8n-rag node /tmp/exec_status.js | Select-Object -First 1 } while ($s -match ' running ')
"ingest: $s"

$env:PYTHONIOENCODING = 'utf-8'
$env:EVAL_IDS = ($Ids -join ',')
& python "$root\eval\run_eval.py"
