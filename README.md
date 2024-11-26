# Upload API Setup

## Prerequisites
- Kubernetes cluster running (minikube or similar)
- kubectl installed
- kustomize installed (comes with recent versions of kubectl)

## Setup Instructions

### 1. Initial Setup (First time only)
```bash
# Go to k8 directory
cd k8

# Apply deployment and service
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 2. Update Code Changes
```bash
# Run the update script (this will create/update configmap)
./update-configmap.sh
```

This script will:
- Copy necessary files from api_script
- Create/update the ConfigMap with latest code
- Apply changes using kustomize

### 3. Verify Deployment
```bash
# Check if pods are running
kubectl get pods -l app=repo-handler

# Check the service
kubectl get svc repo-handler-service
```

### 4. Access the API

#### Using Minikube
```bash
# Get the service URL
minikube service repo-handler-service
```

#### Using Direct URL
```bash
# Get the service URL
kubectl get svc repo-handler-service

# Access in browser
http://<service-url>:8000/upload
```

### 5. Test the API
```bash
# Test using curl
curl -X POST \
  -F "repo_type=url" \
  -F "repo_name=test" \
  -F "user=test" \
  -F "repo_url=https://github.com/test/test" \
  http://<service-url>:8000/repository/
```

## Development Workflow

1. Make changes to files in `api_script/`
2. Run update script to apply changes:
   ```bash
   cd k8
   ./update-configmap.sh
   ```
3. Changes will be automatically deployed with a new pod

## Files Structure
```
upload_api/
├── api_script/
│   ├── main.py
│   ├── facade.py
│   ├── requirements.txt
│   └── templates/
│       └── upload.html
└── k8/
    ├── deployment.yaml
    ├── service.yaml
    ├── kustomization.yaml
    └── update-configmap.sh
```

## Troubleshooting

### Check Logs
```bash
# Get pod name
kubectl get pods -l app=repo-handler

# Check logs
kubectl logs <pod-name>
```

### Check ConfigMap
```bash
# List ConfigMaps
kubectl get configmaps

# Describe specific ConfigMap (replace hash with actual hash)
kubectl describe configmap app-code-configmap-<hash>

# Check ConfigMap content
kubectl get configmap app-code-configmap-<hash> -o yaml
```

### Common Issues
1. If pod is not starting, check the logs
2. If changes not reflecting, verify the ConfigMap was updated
3. Ensure all required files are included in the ConfigMap
