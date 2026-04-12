import sys
import unittest
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["STORE_BACKEND"] = "memory"

try:
    from fastapi.testclient import TestClient

    from app.domain import UserRole
    from app.main import app, store
except ModuleNotFoundError:
    TestClient = None
    UserRole = None
    app = None
    store = None


@unittest.skipIf(TestClient is None, "FastAPI test dependencies are not installed")
class AuthBootstrapTests(unittest.TestCase):
    def setUp(self):
        if hasattr(store, "users"):
            store.users.clear()

    def test_first_registered_user_becomes_admin_and_gets_token(self):
        with TestClient(app) as client:
            status = client.get("/api/v1/auth/bootstrap-status")
            self.assertEqual(status.status_code, 200)
            self.assertTrue(status.json()["registration_open"])

            registered = client.post(
                "/api/v1/auth/register",
                json={"email": "Owner@Example.com", "password": "strong-pass"},
            )
            self.assertEqual(registered.status_code, 200)
            body = registered.json()
            self.assertEqual(body["token_type"], "bearer")
            self.assertEqual(body["user"]["role"], UserRole.ADMIN.value)
            self.assertEqual(body["user"]["email"], "owner@example.com")

            me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
            self.assertEqual(me.status_code, 200)
            self.assertEqual(me.json()["role"], UserRole.ADMIN.value)

    def test_registration_closes_after_admin_exists(self):
        with TestClient(app) as client:
            first = client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "strong-pass"})
            self.assertEqual(first.status_code, 200)

            status = client.get("/api/v1/auth/bootstrap-status")
            self.assertFalse(status.json()["registration_open"])

            second = client.post("/api/v1/auth/register", json={"email": "b@example.com", "password": "strong-pass"})
            self.assertEqual(second.status_code, 403)

    def test_seed_admin_requires_explicit_call(self):
        with TestClient(app) as client:
            status = client.get("/api/v1/auth/bootstrap-status")
            self.assertTrue(status.json()["registration_open"])


if __name__ == "__main__":
    unittest.main()
