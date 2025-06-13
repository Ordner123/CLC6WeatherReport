& minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker build -t dortner/clc6-weather-report-scraper:latest -f scraper/Dockerfile .
docker push dortner/clc6-weather-report-scraper:latest
