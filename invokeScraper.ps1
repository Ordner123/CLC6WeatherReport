param (
    [string]$Namespace = "weather-report",
    [string]$CronJobName = "weather-scraper"
)

# Generate unique job name
$timestamp = Get-Date -UFormat %s
$jobName = "$CronJobName-manual-$timestamp"

Write-Host "🚀 Creating job: $jobName from cronjob/$CronJobName"

# Create Job from CronJob
kubectl create job --from=cronjob/$CronJobName $jobName -n $Namespace

# Wait for Pod to start
Write-Host "⏳ Waiting for Pod to be created..."

do {
    Start-Sleep -Seconds 1
    $podName = kubectl get pods -n $Namespace --selector=job-name=$jobName -o jsonpath='{.items[0].metadata.name}' 2>$null
} while (-not $podName)

Write-Host "📦 Pod created: $podName"

# Wait for Pod to be ready or complete
do {
    $status = kubectl get pod $podName -n $Namespace -o jsonpath='{.status.phase}'
    Start-Sleep -Seconds 1
} while ($status -eq "Pending" -or $status -eq "ContainerCreating")

# Show logs
Write-Host "📜 Fetching logs from: $podName"
kubectl logs $podName -n $Namespace

# Optional cleanup (uncomment to enable)
# Write-Host "🧹 Deleting Job and Pod..."
# kubectl delete job $jobName -n $Namespace
