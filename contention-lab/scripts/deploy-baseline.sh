#!/bin/bash
set -e

echo "🚀 Deploying baseline configuration (with contention)..."

# Create namespace
kubectl apply -f k8s-configs/1-baseline/namespace.yaml

# Deploy services without resource limits
kubectl apply -f k8s-configs/1-baseline/api-service.yaml
kubectl apply -f k8s-configs/1-baseline/cpu-hog-service.yaml

echo "⏳ Waiting for deployments to be ready..."
kubectl -n contention-lab rollout status deployment/api-service --timeout=120s
kubectl -n contention-lab rollout status deployment/cpu-hog-service --timeout=120s

echo "✅ Baseline deployment completed!"
echo "🌐 API available at: http://localhost:30080"
echo "🔥 CPU hog is running - watch for performance degradation!"

echo ""
echo "📊 Monitor with:"
echo "  kubectl -n contention-lab top pods"
echo "  kubectl -n contention-lab get pods -o wide"
echo ""
echo "🧪 Test with:"
echo "  curl http://localhost:30080/work?delay_ms=50"
echo "  ./scripts/test-latency.sh 60"
