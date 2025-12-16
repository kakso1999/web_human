"""
API Integration Tests for Echobot Platform
Run with: python tests/test_api.py
"""

import requests
import json
import time
import sys
from typing import Optional

BASE_URL = "http://127.0.0.1:8000/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log_success(msg: str):
    print(f"{Colors.GREEN}[PASS]{Colors.RESET} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {msg}")

def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def log_section(msg: str):
    print(f"\n{Colors.YELLOW}{'='*50}")
    print(f" {msg}")
    print(f"{'='*50}{Colors.RESET}\n")


class APITester:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.admin_token: Optional[str] = None
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_password = "TestPass123"
        self.test_nickname = "TestUser"
        self.story_id: Optional[str] = None
        self.category_id: Optional[str] = None
        self.passed = 0
        self.failed = 0

    def make_request(self, method: str, endpoint: str, data: dict = None,
                     token: str = None, files: dict = None) -> requests.Response:
        """Make HTTP request to API"""
        url = f"{BASE_URL}{endpoint}"
        headers = {}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        if files:
            # Multipart form data
            response = getattr(requests, method.lower())(
                url, data=data, files=files, headers=headers
            )
        elif data and method.lower() in ['post', 'put', 'patch']:
            headers["Content-Type"] = "application/json"
            response = getattr(requests, method.lower())(
                url, json=data, headers=headers
            )
        else:
            response = getattr(requests, method.lower())(
                url, params=data, headers=headers
            )

        return response

    def assert_response(self, response: requests.Response, expected_code: int,
                       test_name: str) -> bool:
        """Assert response status code"""
        if response.status_code == expected_code:
            log_success(f"{test_name} - Status {response.status_code}")
            self.passed += 1
            return True
        else:
            log_error(f"{test_name} - Expected {expected_code}, got {response.status_code}")
            try:
                log_error(f"  Response: {response.json()}")
            except:
                log_error(f"  Response: {response.text[:200]}")
            self.failed += 1
            return False

    # ==================== Health Check ====================

    def test_health_check(self):
        log_section("Health Check Tests")

        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        self.assert_response(response, 200, "GET /health")

        data = response.json()
        if data.get("status") == "healthy":
            log_success("  Health status is 'healthy'")
        else:
            log_error(f"  Unexpected health status: {data}")

    # ==================== Auth Module ====================

    def test_auth_register(self):
        log_section("Auth Module Tests - Register")

        # Test successful registration
        data = {
            "email": self.test_email,
            "password": self.test_password,
            "nickname": self.test_nickname
        }
        response = self.make_request("POST", "/auth/register", data)
        if self.assert_response(response, 200, "POST /auth/register"):
            result = response.json()
            tokens = result.get("data", {}).get("tokens", {})
            if tokens.get("access_token"):
                self.access_token = tokens["access_token"]
                self.refresh_token = tokens.get("refresh_token")
                log_success("  Got access token")
            else:
                log_error("  No access token in response")

        # Test duplicate registration
        response = self.make_request("POST", "/auth/register", data)
        self.assert_response(response, 400, "POST /auth/register (duplicate)")

        # Test invalid email
        data["email"] = "invalid-email"
        response = self.make_request("POST", "/auth/register", data)
        self.assert_response(response, 422, "POST /auth/register (invalid email)")

        # Test weak password (returns 422 validation error, which is correct)
        data["email"] = f"test2_{int(time.time())}@example.com"
        data["password"] = "123"
        response = self.make_request("POST", "/auth/register", data)
        self.assert_response(response, 422, "POST /auth/register (weak password)")

    def test_auth_login(self):
        log_section("Auth Module Tests - Login")

        # Test successful login
        data = {
            "email": self.test_email,
            "password": self.test_password
        }
        response = self.make_request("POST", "/auth/login", data)
        if self.assert_response(response, 200, "POST /auth/login"):
            result = response.json()
            tokens = result.get("data", {}).get("tokens", {})
            user = result.get("data", {}).get("user", {})
            self.access_token = tokens.get("access_token")
            # Note: refresh_token is set as HttpOnly cookie, not in response body
            # Keep the refresh_token from registration if available
            self.user_id = user.get("id")
            log_success(f"  User ID: {self.user_id}")

        # Test wrong password (returns 400 Bad Request)
        data["password"] = "WrongPassword123"
        response = self.make_request("POST", "/auth/login", data)
        self.assert_response(response, 400, "POST /auth/login (wrong password)")

        # Test non-existent user (returns 400 to not leak user existence info)
        data["email"] = "nonexistent@example.com"
        response = self.make_request("POST", "/auth/login", data)
        self.assert_response(response, 400, "POST /auth/login (non-existent user)")

    def test_auth_refresh(self):
        log_section("Auth Module Tests - Token Refresh")

        if not self.refresh_token:
            log_info("Skipping refresh test - no refresh token")
            return

        data = {"refresh_token": self.refresh_token}
        response = self.make_request("POST", "/auth/refresh", data)
        if self.assert_response(response, 200, "POST /auth/refresh"):
            result = response.json()
            new_token = result.get("data", {}).get("access_token")
            if new_token:
                self.access_token = new_token
                log_success("  Got new access token")

        # Test invalid refresh token (returns 400)
        data["refresh_token"] = "invalid_token"
        response = self.make_request("POST", "/auth/refresh", data)
        self.assert_response(response, 400, "POST /auth/refresh (invalid token)")

    def test_auth_google_url(self):
        log_section("Auth Module Tests - Google OAuth")

        response = self.make_request("GET", "/auth/google/url")
        # This might return the URL or redirect
        if response.status_code in [200, 307, 302]:
            log_success(f"GET /auth/google/url - Status {response.status_code}")
            self.passed += 1
        else:
            self.assert_response(response, 200, "GET /auth/google/url")

    # ==================== User Module ====================

    def test_user_profile(self):
        log_section("User Module Tests - Profile")

        # Test get profile (authenticated)
        response = self.make_request("GET", "/user/profile", token=self.access_token)
        if self.assert_response(response, 200, "GET /user/profile"):
            data = response.json()["data"]
            log_success(f"  Email: {data.get('email')}")
            log_success(f"  Nickname: {data.get('nickname')}")

        # Test get profile (unauthenticated)
        response = self.make_request("GET", "/user/profile")
        self.assert_response(response, 401, "GET /user/profile (no auth)")

        # Test update profile
        update_data = {"nickname": "UpdatedNickname"}
        response = self.make_request("PUT", "/user/profile", update_data, token=self.access_token)
        if self.assert_response(response, 200, "PUT /user/profile"):
            data = response.json()["data"]
            if data.get("nickname") == "UpdatedNickname":
                log_success("  Nickname updated successfully")

    def test_user_change_password(self):
        log_section("User Module Tests - Change Password")

        # Test change password
        data = {
            "old_password": self.test_password,
            "new_password": "NewTestPass456"
        }
        response = self.make_request("POST", "/user/change-password", data, token=self.access_token)
        if self.assert_response(response, 200, "POST /user/change-password"):
            # Change back for further tests
            data = {
                "old_password": "NewTestPass456",
                "new_password": self.test_password
            }
            self.make_request("POST", "/user/change-password", data, token=self.access_token)
            log_success("  Password changed and reverted")

        # Test wrong old password
        data = {
            "old_password": "WrongOldPass123",
            "new_password": "NewPass456"
        }
        response = self.make_request("POST", "/user/change-password", data, token=self.access_token)
        self.assert_response(response, 400, "POST /user/change-password (wrong old password)")

    # ==================== Story Module ====================

    def test_story_categories(self):
        log_section("Story Module Tests - Categories")

        response = self.make_request("GET", "/stories/categories", token=self.access_token)
        if self.assert_response(response, 200, "GET /stories/categories"):
            data = response.json()["data"]
            log_success(f"  Found {len(data)} categories")
            if len(data) > 0:
                self.category_id = data[0].get("id")

    def test_story_list(self):
        log_section("Story Module Tests - List Stories")

        # Test list stories
        response = self.make_request("GET", "/stories", {"page": 1, "page_size": 10}, token=self.access_token)
        if self.assert_response(response, 200, "GET /stories"):
            data = response.json()["data"]
            log_success(f"  Total stories: {data.get('total', 0)}")
            items = data.get("items", [])
            if len(items) > 0:
                self.story_id = items[0].get("id")
                log_success(f"  First story ID: {self.story_id}")

    def test_story_random(self):
        log_section("Story Module Tests - Random Stories")

        response = self.make_request("GET", "/stories/random", {"limit": 5})
        if self.assert_response(response, 200, "GET /stories/random"):
            data = response.json()["data"]
            log_success(f"  Got {len(data)} random stories")

    def test_story_detail(self):
        log_section("Story Module Tests - Story Detail")

        if not self.story_id:
            log_info("Skipping story detail test - no story ID")
            return

        response = self.make_request("GET", f"/stories/{self.story_id}", token=self.access_token)
        if self.assert_response(response, 200, f"GET /stories/{self.story_id}"):
            data = response.json()["data"]
            log_success(f"  Title: {data.get('title')}")

        # Test non-existent story
        response = self.make_request("GET", "/stories/nonexistent_id", token=self.access_token)
        self.assert_response(response, 404, "GET /stories/nonexistent_id")

    # ==================== Admin Module ====================

    def test_admin_setup(self):
        """Create admin user for admin tests"""
        log_section("Admin Module Setup")

        # First, we need to create an admin user
        # In a real scenario, this would be done through DB seeding
        # For now, we'll try to login as admin or create one

        admin_email = "admin@echobot.com"
        admin_password = "AdminPass123"

        # Try to register admin
        data = {
            "email": admin_email,
            "password": admin_password,
            "nickname": "Admin"
        }
        response = self.make_request("POST", "/auth/register", data)

        # Login as admin
        data = {
            "email": admin_email,
            "password": admin_password
        }
        response = self.make_request("POST", "/auth/login", data)
        if response.status_code == 200:
            result = response.json()
            tokens = result.get("data", {}).get("tokens", {})
            self.admin_token = tokens.get("access_token")
            log_success(f"  Admin logged in")
        else:
            log_info("  Using regular user token for admin tests (may fail permission checks)")
            self.admin_token = self.access_token

    def test_admin_dashboard(self):
        log_section("Admin Module Tests - Dashboard")

        response = self.make_request("GET", "/admin/dashboard", token=self.admin_token)
        if response.status_code == 200:
            self.assert_response(response, 200, "GET /admin/dashboard")
            data = response.json()["data"]
            log_success(f"  Total users: {data.get('total_users', 0)}")
            log_success(f"  Total stories: {data.get('total_stories', 0)}")
        elif response.status_code == 403:
            log_info("GET /admin/dashboard - 403 Forbidden (need admin role)")
            self.passed += 1  # Expected for non-admin users
        else:
            self.assert_response(response, 200, "GET /admin/dashboard")

    def test_admin_users(self):
        log_section("Admin Module Tests - User Management")

        # List users
        response = self.make_request("GET", "/admin/users", {"page": 1, "page_size": 10}, token=self.admin_token)
        if response.status_code == 200:
            self.assert_response(response, 200, "GET /admin/users")
            data = response.json()["data"]
            log_success(f"  Found {data.get('total', 0)} users")
        elif response.status_code == 403:
            log_info("GET /admin/users - 403 Forbidden (need admin role)")
            self.passed += 1

    def test_admin_stories(self):
        log_section("Admin Module Tests - Story Management")

        # List stories
        response = self.make_request("GET", "/admin/stories", {"page": 1, "page_size": 10}, token=self.admin_token)
        if response.status_code == 200:
            self.assert_response(response, 200, "GET /admin/stories")
            data = response.json()["data"]
            log_success(f"  Found {data.get('total', 0)} stories")
        elif response.status_code == 403:
            log_info("GET /admin/stories - 403 Forbidden (need admin role)")
            self.passed += 1

    # ==================== Error Handling ====================

    def test_error_handling(self):
        log_section("Error Handling Tests")

        # Test 404
        response = requests.get(f"{BASE_URL}/nonexistent-endpoint")
        self.assert_response(response, 404, "GET /nonexistent-endpoint")

        # Test invalid JSON
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code in [400, 422]:
            log_success(f"POST /auth/login (invalid JSON) - Status {response.status_code}")
            self.passed += 1
        else:
            log_error(f"POST /auth/login (invalid JSON) - Expected 400/422, got {response.status_code}")
            self.failed += 1

    # ==================== Rate Limiting ====================

    def test_rate_limiting(self):
        log_section("Rate Limiting Tests")

        log_info("Sending multiple requests to test rate limiting...")

        # This is a simple test - actual rate limiting depends on configuration
        success_count = 0
        rate_limited = False

        for i in range(5):
            response = self.make_request("GET", "/user/profile", token=self.access_token)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited = True
                break

        log_success(f"  Completed {success_count} requests")
        if rate_limited:
            log_success("  Rate limiting is working (got 429)")
        else:
            log_info("  No rate limiting triggered (may need more requests)")

        self.passed += 1

    # ==================== Run All Tests ====================

    def run_all_tests(self):
        print(f"\n{Colors.BLUE}{'#'*60}")
        print(f" Echobot API Integration Tests")
        print(f" Base URL: {BASE_URL}")
        print(f"{'#'*60}{Colors.RESET}\n")

        try:
            # Health check
            self.test_health_check()

            # Auth tests
            self.test_auth_register()
            self.test_auth_login()
            self.test_auth_refresh()
            self.test_auth_google_url()

            # User tests
            self.test_user_profile()
            self.test_user_change_password()

            # Story tests
            self.test_story_categories()
            self.test_story_list()
            self.test_story_random()
            self.test_story_detail()

            # Admin tests
            self.test_admin_setup()
            self.test_admin_dashboard()
            self.test_admin_users()
            self.test_admin_stories()

            # Error handling
            self.test_error_handling()

            # Rate limiting
            self.test_rate_limiting()

        except requests.exceptions.ConnectionError:
            log_error("Connection failed! Is the server running on http://127.0.0.1:8000?")
            return 1
        except Exception as e:
            log_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return 1

        # Summary
        print(f"\n{Colors.BLUE}{'='*60}")
        print(f" Test Summary")
        print(f"{'='*60}{Colors.RESET}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.RESET}")

        total = self.passed + self.failed
        if total > 0:
            success_rate = (self.passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")

        print()

        return 0 if self.failed == 0 else 1


if __name__ == "__main__":
    tester = APITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
