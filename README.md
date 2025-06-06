# Old School Weather Report
## Kubernetes
Prepeare Environment in windows:

```
docker context use default
minikube start
kubectl config set-context --current --namespace=weather-report
```

Open UI: `minikube service weather-report-service -n weather-report`

## TODO:
- MongoDB
- Scraper container
- UI Backend
- UI

## Fehler
Image not found when starting deployment:

- In the deployment `imagePullPolicy: IfNotPresent`
- Building the docker image in the minikube `& minikube -p minikube docker-env --shell powershell | Invoke-Expression`
- Last resort: `minikube image load weather-report-ui:latest`
