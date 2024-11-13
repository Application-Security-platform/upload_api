## create a zip file of the app code
```
tar -czf app-code.tar.gz -C api_script .
```
## create a configmap with the tar file
```
kubectl create configmap app-code-configmap --from-file=app-code.tar.gz
```
## create a pvc for the app code
```
kubectl apply -f pvc.yaml
```

## create a deployment with the app code
```
kubectl apply -f deployment.yaml
```
## create a service for the app
```
kubectl apply -f service.yaml
```

## get the service url
```
kubectl get svc repo-handler-service
```

## Access the API url in the browser
```
http://<service-url>:8000/upload
 or
minikube service repo-handler-service
```
## Hit the API using curl
```
curl -X POST -F "repo_type=url" -F "repo_name=test" -F "user=test" -F "repo_url=https://github.com/test/test" http://<service-url>:8000/repository/
```
