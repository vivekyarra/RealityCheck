# Google Cloud deployment and proof

## Services used

- Cloud Run
- Cloud Firestore in Native mode
- Vertex AI Gemini 3.5 Flash
- Pub/Sub
- Cloud Scheduler
- Cloud Build / Artifact Registry

## Deploy

```powershell
gcloud auth login
gcloud auth application-default login
.\infra\deploy.ps1 -ProjectId YOUR_PROJECT_ID -Region asia-south1
```

The script prints `DEPLOYED_URL`. Verify:

```powershell
$url = "https://YOUR_SERVICE.run.app"
Invoke-RestMethod "$url/api/health"
Invoke-WebRequest "$url" -UseBasicParsing
```

## Configure asynchronous checks

The scheduler script writes the task credential to Secret Manager, grants only the runtime identity access, mounts it into Cloud Run, and configures the matching scheduler header:

```powershell
.\infra\scheduler.ps1 -ProjectId YOUR_PROJECT_ID -ServiceUrl $url -TasksSecret "LONG_RANDOM_SECRET"
```

## Evidence to capture for the demo video

1. Cloud Run service page showing the `realitycheck` revision and `.run.app` URL.
2. The health endpoint showing `store: firestore`, `model: gemini-3.5-flash`, and `ai_configured: true`.
3. Firestore Data page showing `realitycheck_cases/case_fibermax_demo`.
4. Cloud Logging query filtered to the service and one `http_request` event.
5. Cloud Scheduler job showing a successful `/api/tasks/tick` invocation.

Do not show API keys, access tokens, environment secret values, customer evidence, or billing identifiers in the recording.
