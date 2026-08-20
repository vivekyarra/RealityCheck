param(
  [Parameter(Mandatory = $true)][string]$ProjectId,
  [Parameter(Mandatory = $true)][string]$ServiceUrl,
  [Parameter(Mandatory = $true)][string]$TasksSecret,
  [string]$Region = "asia-south1",
  [string]$Service = "realitycheck"
)

$ErrorActionPreference = "Stop"
function Invoke-Gcloud {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
  & gcloud @Arguments
  if ($LASTEXITCODE -ne 0) { throw "gcloud failed: $($Arguments -join ' ')" }
}

Invoke-Gcloud config set project $ProjectId
$secretName = "realitycheck-tasks-secret"
$serviceAccount = "realitycheck-runtime@$ProjectId.iam.gserviceaccount.com"
gcloud secrets describe $secretName 2>$null
if ($LASTEXITCODE -ne 0) {
  Invoke-Gcloud secrets create $secretName --replication-policy="automatic"
}
$secretFile = New-TemporaryFile
try {
  Set-Content -LiteralPath $secretFile.FullName -Value $TasksSecret -NoNewline
  Invoke-Gcloud secrets versions add $secretName --data-file=$secretFile.FullName
} finally {
  Remove-Item -LiteralPath $secretFile.FullName -Force
}
Invoke-Gcloud secrets add-iam-policy-binding $secretName --member="serviceAccount:$serviceAccount" --role="roles/secretmanager.secretAccessor" --quiet --format=none
Invoke-Gcloud run services update $Service --region $Region --update-secrets="TASKS_SHARED_SECRET=$secretName`:latest" --quiet

gcloud pubsub topics describe realitycheck-watch 2>$null
if ($LASTEXITCODE -ne 0) { Invoke-Gcloud pubsub topics create realitycheck-watch }

gcloud scheduler jobs describe realitycheck-watch-tick --location $Region 2>$null
if ($LASTEXITCODE -eq 0) {
  Invoke-Gcloud scheduler jobs update http realitycheck-watch-tick --location $Region --schedule="*/15 * * * *" --uri="$ServiceUrl/api/tasks/tick" --http-method=POST --headers="X-Tasks-Secret=$TasksSecret"
} else {
  Invoke-Gcloud scheduler jobs create http realitycheck-watch-tick --location $Region --schedule="*/15 * * * *" --uri="$ServiceUrl/api/tasks/tick" --http-method=POST --headers="X-Tasks-Secret=$TasksSecret"
}
Write-Output "Cloud Scheduler configured for asynchronous obligation checks."
