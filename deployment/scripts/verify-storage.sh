#!/bin/bash
# Database & Storage verification script on K3s VM
# Run this on the target VM after deployment

set -e

NAMESPACE="${1:-plant-disease}"

echo "=================================================="
echo "Storage & Database Integrity Verification (K3s)"
echo "Namespace: $NAMESPACE"
echo "=================================================="

echo -e "\n1. Verifying PersistentVolumeClaims (PVCs) Status:"
kubectl -n "$NAMESPACE" get pvc
if kubectl -n "$NAMESPACE" get pvc | grep -q "Pending"; then
    echo "[WARNING] One or more PVCs are in Pending state!"
else
    echo "[OK] All PVCs are successfully Bound."
fi

echo -e "\n2. Verifying Probes and Pod Health:"
kubectl -n "$NAMESPACE" get pods -l 'app.kubernetes.io/component in (backend, frontend)'
kubectl -n "$NAMESPACE" get pods -l 'app in (postgres, minio, redis)'

echo -e "\n3. Verifying PostgreSQL (Liveness & Backup):"
PG_POD=$(kubectl -n "$NAMESPACE" get pod -l app=postgres -o jsonpath="{.items[0].metadata.name}")
if kubectl -n "$NAMESPACE" exec "$PG_POD" -- pg_isready -U admin -d plant_disease; then
    echo "[OK] PostgreSQL is ready (pg_isready: OK)"
else
    echo "[ERROR] PostgreSQL is NOT ready!"
fi

echo "Checking Backup CronJob:"
kubectl -n "$NAMESPACE" get cronjob

echo -e "\n4. Verifying MinIO (Liveness):"
MINIO_POD=$(kubectl -n "$NAMESPACE" get pod -l app=minio -o jsonpath="{.items[0].metadata.name}")
if kubectl -n "$NAMESPACE" exec "$MINIO_POD" -- curl -sf http://localhost:9000/minio/health/live >/dev/null; then
    echo "[OK] MinIO is ready (Liveness: OK)"
else
    echo "[ERROR] MinIO is NOT ready!"
fi

echo -e "\n5. Verifying Redis (Liveness):"
REDIS_POD=$(kubectl -n "$NAMESPACE" get pod -l app=redis -o jsonpath="{.items[0].metadata.name}")
if kubectl -n "$NAMESPACE" exec "$REDIS_POD" -- redis-cli ping | grep -q "PONG"; then
    echo "[OK] Redis is ready (PING: PONG)"
else
    echo "[ERROR] Redis is NOT ready!"
fi

echo -e "\n=================================================="
echo "Verification Complete!"
echo "=================================================="
