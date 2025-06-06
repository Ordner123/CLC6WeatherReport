& minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker build -t weather-report-ui:latest .