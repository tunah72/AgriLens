import json
import os
import subprocess
from pathlib import Path

import pytest
import requests
import yaml

DOMAIN = "plant-disease-demo.duckdns.org"
NAMESPACE = "plant-disease"

# Skip remote tests unless explicitly enabled with SKIP_REMOTE_TESTS=false
SKIP_REMOTE = os.getenv("SKIP_REMOTE_TESTS", "true").lower() in ("true", "1") or os.getenv("GITHUB_ACTIONS") == "true"


def run_local_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def run_remote_cmd(cmd):
    # Connect via SSH to k3s-deploy
    ssh_cmd = f'ssh k3s-deploy "export KUBECONFIG=~/.kube/config && {cmd}"'
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


# ==========================================
# 1. LOCAL CHECKS
# ==========================================


def test_helm_lint():
    """Verify that the Helm chart in deployment/helm contains no errors."""
    code, stdout, stderr = run_local_cmd("helm lint deployment/helm")
    assert code == 0, f"Helm lint failed:\n{stdout}\n{stderr}"
    assert "0 chart(s) failed" in stdout


def test_helm_template_rendering():
    """Verify that Helm templates render correctly without parsing errors."""
    code, stdout, stderr = run_local_cmd("helm template deployment/helm")
    assert code == 0, f"Helm template failed:\n{stdout}\n{stderr}"
    assert len(stdout) > 0

    # Verify key manifests are generated
    assert "kind: Deployment" in stdout
    assert "kind: StatefulSet" in stdout
    assert "kind: Ingress" in stdout
    assert "kind: Secret" in stdout
    assert "name: backend" in stdout
    assert "name: frontend" in stdout


def test_github_workflows_exist_and_valid():
    """Verify GitHub Actions workflow files exist and have valid YAML syntax."""
    ci_path = Path(".github/workflows/ci.yml")
    deploy_path = Path(".github/workflows/deploy.yml")

    if not ci_path.exists() or not deploy_path.exists():
        pytest.skip("GitHub Actions workflows not configured in this repository")

    with open(ci_path, encoding="utf-8") as f:
        ci_yaml = yaml.safe_load(f)
    assert ci_yaml["name"] is not None
    assert "jobs" in ci_yaml

    with open(deploy_path, encoding="utf-8") as f:
        deploy_yaml = yaml.safe_load(f)
    assert deploy_yaml["name"] is not None
    assert "jobs" in deploy_yaml
    assert "build-and-push" in deploy_yaml["jobs"]
    assert "deploy" in deploy_yaml["jobs"]
    assert "smoke-test" in deploy_yaml["jobs"]


# ==========================================
# 2. REMOTE KUBERNETES & SYSTEMD CHECKS
# ==========================================


@pytest.mark.skipif(SKIP_REMOTE, reason="Remote K3s cluster not available in CI environment")
def test_remote_k3s_nodes_ready():
    """Verify that all nodes in the K3s cluster are in Ready status."""
    code, stdout, stderr = run_remote_cmd("kubectl get nodes --no-headers")
    assert code == 0, f"Failed to get nodes: {stderr}"
    assert "Ready" in stdout


@pytest.mark.skipif(SKIP_REMOTE, reason="Remote K3s cluster not available in CI environment")
def test_remote_system_pods_healthy():
    """Verify core system pods in cert-manager and kube-system namespaces are running."""
    # Check cert-manager namespace
    code_cm, stdout_cm, _ = run_remote_cmd("kubectl get pods -n cert-manager -o json")
    assert code_cm == 0
    cm_pods = json.loads(stdout_cm)
    for pod in cm_pods.get("items", []):
        status = pod["status"]["phase"]
        assert status == "Running", f"Cert-manager pod {pod['metadata']['name']} is {status}"

    # Check kube-system namespace
    code_ks, stdout_ks, _ = run_remote_cmd("kubectl get pods -n kube-system -o json")
    assert code_ks == 0
    ks_pods = json.loads(stdout_ks)
    for pod in ks_pods.get("items", []):
        # Exclude completed helm install jobs
        if pod["metadata"]["name"].startswith("helm-install"):
            continue
        status = pod["status"]["phase"]
        assert status == "Running", f"System pod {pod['metadata']['name']} is {status}"


@pytest.mark.skipif(SKIP_REMOTE, reason="Remote K3s cluster not available in CI environment")
def test_remote_app_pods_running():
    """Verify that all application pods in the plant-disease namespace are running and healthy."""
    code, stdout, stderr = run_remote_cmd(f"kubectl get pods -n {NAMESPACE} -o json")
    assert code == 0, f"Failed to list pods in namespace {NAMESPACE}: {stderr}"

    pods = json.loads(stdout)
    assert len(pods.get("items", [])) >= 5, "Not all application pods are deployed"

    expected_components = ["backend", "frontend", "postgres", "redis", "minio"]
    found_components = []

    for pod in pods["items"]:
        pod_name = pod["metadata"]["name"]
        status = pod["status"]["phase"]
        assert status == "Running", f"Pod {pod_name} is in phase {status}"

        # Check readiness of container
        for container_status in pod["status"].get("containerStatuses", []):
            c_name = container_status["name"]
            assert container_status["ready"] is True, f"Container {c_name} in Pod {pod_name} is not ready"

        # Track which component this is
        for comp in expected_components:
            if comp in pod_name:
                found_components.append(comp)

    # Unique components found
    missing = set(expected_components) - set(found_components)
    assert set(expected_components).issubset(set(found_components)), f"Missing components in deployment: {missing}"


@pytest.mark.skipif(SKIP_REMOTE, reason="Remote K3s cluster not available in CI environment")
def test_remote_pvcs_bound():
    """Verify all Persistent Volume Claims (PVC) are bound to Persistent Volumes."""
    code, stdout, stderr = run_remote_cmd(f"kubectl get pvc -n {NAMESPACE} -o json")
    assert code == 0, f"Failed to list PVCs: {stderr}"

    pvcs = json.loads(stdout)
    assert len(pvcs.get("items", [])) >= 3, "Missing expected PVCs"

    for pvc in pvcs["items"]:
        pvc_name = pvc["metadata"]["name"]
        phase = pvc["status"]["phase"]
        assert phase == "Bound", f"PVC {pvc_name} is in status {phase} (expected Bound)"


@pytest.mark.skipif(SKIP_REMOTE, reason="Remote K3s cluster not available in CI environment")
def test_remote_cert_manager_issuance():
    """Verify cert-manager ClusterIssuer and Certificate are fully ready and valid."""
    # Check ClusterIssuer letsencrypt-prod
    code, stdout, stderr = run_remote_cmd("kubectl get clusterissuer letsencrypt-prod -o json")
    assert code == 0, f"ClusterIssuer letsencrypt-prod not found: {stderr}"
    issuer = json.loads(stdout)
    ready_status = False
    for cond in issuer["status"].get("conditions", []):
        if cond["type"] == "Ready" and cond["status"] == "True":
            ready_status = True
    assert ready_status is True, "ClusterIssuer is not Ready"

    # Check Certificate plant-disease-tls
    code, stdout, stderr = run_remote_cmd(f"kubectl get certificate plant-disease-tls -n {NAMESPACE} -o json")
    assert code == 0, f"Certificate plant-disease-tls not found: {stderr}"
    cert = json.loads(stdout)
    cert_ready = False
    for cond in cert["status"].get("conditions", []):
        if cond["type"] == "Ready" and cond["status"] == "True":
            cert_ready = True
    assert cert_ready is True, "Certificate plant-disease-tls is not Ready"


@pytest.mark.skipif(SKIP_REMOTE, reason="Remote K3s cluster not available in CI environment")
def test_remote_duckdns_timer_active():
    """Verify DuckDNS update systemd timer is active and running."""
    code, stdout, stderr = run_remote_cmd("systemctl is-active duckdns-update.timer")
    assert code == 0, f"duckdns-update.timer is not active: {stdout} {stderr}"
    assert stdout.strip() == "active"


# ==========================================
# 3. EXTERNAL PUBLIC HTTPS ENDPOINTS CHECKS
# ==========================================


@pytest.mark.skipif(SKIP_REMOTE, reason="External public HTTPS endpoints not checked in CI environment")
def test_public_https_health_check():
    """Verify that backend /health endpoint is publicly reachable over HTTPS with HTTP 200."""
    url = f"https://{DOMAIN}/health"
    response = requests.get(url, timeout=10)
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") == "ok", f"Expected 'status': 'ok', got: {data}"


@pytest.mark.skipif(SKIP_REMOTE, reason="External public HTTPS endpoints not checked in CI environment")
def test_public_https_knowledge_api():
    """Verify that backend /api/v1/knowledge endpoint serves the correct knowledge base schema."""
    url = f"https://{DOMAIN}/api/v1/knowledge"
    response = requests.get(url, timeout=10)
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}"
    data = response.json()
    assert "items" in data, "Response data missing 'items'"
    assert len(data["items"]) > 0, "No crop diseases returned in knowledge base"
    assert "label" in data["items"][0], "Disease items missing 'label'"
    assert "crop" in data["items"][0], "Disease items missing 'crop'"


@pytest.mark.skipif(SKIP_REMOTE, reason="External public HTTPS endpoints not checked in CI environment")
def test_public_https_frontend_routing():
    """Verify that root URL routes to Next.js frontend and serves correct HTML structure."""
    url = f"https://{DOMAIN}/"
    response = requests.get(url, timeout=10)
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}"
    assert "html" in response.text.lower(), "Frontend response is not an HTML page"
    assert "_next/static" in response.text, "Frontend response does not look like a Next.js production build"
