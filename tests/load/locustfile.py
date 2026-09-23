"""Locust scenario for the public backend API.

Set ``LOCUST_USERNAME`` and ``LOCUST_PASSWORD`` to a dedicated load-test user
that already exists in the target environment. Prediction traffic is opt-in:
provide ``LOCUST_IMAGE_PATH`` to avoid accidentally loading the model endpoint
without a representative leaf image.
"""

import os
from pathlib import Path

from locust import HttpUser, between, task


class PlantDiseaseApiUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        username = os.getenv("LOCUST_USERNAME")
        password = os.getenv("LOCUST_PASSWORD")
        if not username or not password:
            raise RuntimeError("Set LOCUST_USERNAME and LOCUST_PASSWORD before starting Locust.")

        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
            name="/api/v1/auth/login",
        )
        if response.status_code != 200:
            raise RuntimeError(f"Load-test login failed with HTTP {response.status_code}: {response.text}")
        self.headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        image_path = os.getenv("LOCUST_IMAGE_PATH")
        self.image_path = Path(image_path) if image_path else None
        if self.image_path and not self.image_path.is_file():
            raise RuntimeError(f"LOCUST_IMAGE_PATH does not exist: {self.image_path}")

    @task(4)
    def health(self) -> None:
        self.client.get("/health", name="/health")

    @task(3)
    def history(self) -> None:
        self.client.get("/api/v1/history?page=1&page_size=10", headers=self.headers, name="/api/v1/history")

    @task(2)
    def knowledge(self) -> None:
        self.client.get("/api/v1/knowledge", headers=self.headers, name="/api/v1/knowledge")

    @task(1)
    def predict(self) -> None:
        if self.image_path is None:
            return
        with self.image_path.open("rb") as image_file:
            self.client.post(
                "/api/v1/predict",
                headers=self.headers,
                files={"file": (self.image_path.name, image_file, "image/jpeg")},
                name="/api/v1/predict",
            )
