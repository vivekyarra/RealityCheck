param(
  [Parameter(Mandatory = $true)][string]$ProjectId,
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
Invoke-Gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com aiplatform.googleapis.com pubsub.googleapis.com cloudscheduler.googleapis.com secretmanager.googleapis.com

$serviceAccount = "realitycheck-runtime@$ProjectId.iam.gserviceaccount.com"
$existing = Invoke-Gcloud iam service-accounts list --filter="email=$serviceAccount" --format="value(email)"
if (-not $existing) {
  Invoke-Gcloud iam service-accounts create realitycheck-runtime --display-name="RealityCheck Cloud Run runtime"
}

Invoke-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$serviceAccount" --role="roles/datastore.user" --quiet --format=none
Invoke-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$serviceAccount" --role="roles/aiplatform.user" --quiet --format=none
Invoke-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$serviceAccount" --role="roles/pubsub.publisher" --quiet --format=none

$databases = Invoke-Gcloud firestore databases list --format="value(name)"
if (-not $databases) {
  Invoke-Gcloud firestore databases create --location=$Region --type=firestore-native --quiet
}

Invoke-Gcloud run deploy $Service `
  --source . `
  --region $Region `
  --allow-unauthenticated `
  --service-account $serviceAccount `
  --set-env-vars "APP_ENV=production,REALITYCHECK_STORE=firestore,GOOGLE_CLOUD_PROJECT=$ProjectId,GOOGLE_CLOUD_LOCATION=global,GEMINI_MODEL=gemini-3.5-flash,GOOGLE_GENAI_USE_VERTEXAI=TRUE,PROVIDER_MODE=sandbox" `
  --min-instances 0 `
  --max-instances 3 `
  --memory 1Gi `
  --cpu 1 `
  --quiet

$url = Invoke-Gcloud run services describe $Service --region $Region --format="value(status.url)"
if (-not $url) { throw "Cloud Run returned no service URL." }
Write-Output "DEPLOYED_URL=$url"
Write-Output "Verify: Invoke-RestMethod '$url/api/health'"
