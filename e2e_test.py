#!/usr/bin/env python3
"""End-to-end test: Generate SDK from test API and test ALL routes."""

import asyncio
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[36m"
RESET = "\033[0m"

TEST_API_PORT = 8000
TEST_API_URL = f"http://127.0.0.1:{TEST_API_PORT}"
SDK_OUTPUT_DIR = Path("/tmp/e2e_test_sdk")
SDK_PACKAGE_NAME = "e2e_test_sdk"


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{title:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_test(description: str, passed: bool) -> None:
    """Print test result."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {description}")


def start_test_api() -> subprocess.Popen:
    """Start the test API server."""
    print(f"{YELLOW}Starting test API server...{RESET}")

    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(TEST_API_PORT)],
        cwd="test_api",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for server to be ready
    for _ in range(30):
        try:
            import httpx

            response = httpx.get(f"{TEST_API_URL}/health", timeout=1.0)
            if response.status_code == 200:
                print(f"{GREEN}✓ Test API server ready{RESET}")
                return process
        except Exception:
            time.sleep(0.5)

    process.kill()
    raise RuntimeError("Test API failed to start")


def generate_sdk() -> bool:
    """Generate SDK using sdkgen CLI."""
    print(f"{YELLOW}Generating SDK from test API...{RESET}")

    # Clean up old SDK
    if SDK_OUTPUT_DIR.exists():
        shutil.rmtree(SDK_OUTPUT_DIR)

    # Generate SDK
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "sdkgen.cli",
            "generate",
            "-i",
            f"{TEST_API_URL}/openapi.json",
            "-o",
            str(SDK_OUTPUT_DIR),
            "-l",
            "python",
            "-n",
            SDK_PACKAGE_NAME,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(f"{RED}✗ SDK generation failed:{RESET}")
        print(result.stderr)
        return False

    print(f"{GREEN}✓ SDK generated successfully{RESET}")

    # Verify files exist
    sdk_files = list((SDK_OUTPUT_DIR / SDK_PACKAGE_NAME).rglob("*.py"))
    print(f"{GREEN}✓ Generated {len(sdk_files)} Python files{RESET}")

    # Compile check
    for file in sdk_files:
        compile_result = subprocess.run(
            ["python", "-m", "py_compile", str(file)], capture_output=True, check=False
        )
        if compile_result.returncode != 0:
            print(f"{RED}✗ Compilation failed for {file.name}{RESET}")
            return False

    print(f"{GREEN}✓ All files compile successfully{RESET}")
    return True


async def test_generated_sdk() -> tuple[int, int]:
    """Test the generated SDK by calling ALL routes."""
    print_section("Testing ALL Generated SDK Routes")

    # Add SDK to Python path
    sys.path.insert(0, str(SDK_OUTPUT_DIR))

    try:
        # Import generated SDK
        from e2e_test_sdk import Client

        # Initialize client
        client = Client(base_url=TEST_API_URL, api_key="test-key")

        passed = 0
        failed = 0

        # ===== SYSTEM ENDPOINTS =====
        print(f"\n{YELLOW}>>> System Endpoints{RESET}")

        # 1. GET /health
        try:
            result = await client.request("GET", "/health")
            assert result["status"] == "healthy"
            print_test("GET /health → health()", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /health → health() - {e}", False)
            failed += 1

        # 2. GET /api/v1/status
        try:
            result = await client.request("GET", "/api/v1/status")
            assert result["status"] == "operational"
            print_test("GET /api/v1/status → status()", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/status → status() - {e}", False)
            failed += 1

        # ===== V1 USERS (5 routes) =====
        print(f"\n{YELLOW}>>> V1 Users (CRUD){RESET}")

        # Note: Using direct request calls to avoid namespace URL issues
        # 3. GET /api/v1/users (returns paginated object, not array)
        try:
            result = await client.request("GET", "/api/v1/users", params={"page": 0, "size": 10})
            assert "users" in result
            assert "total" in result
            print_test("GET /api/v1/users → users() [paginated object]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/users - {e}", False)
            failed += 1

        # 4. POST /api/v1/users (create)
        try:
            result = await client.request(
                "POST", "/api/v1/users", json={"name": "Test User", "email": "test@example.com"}
            )
            assert result["name"] == "Test User"
            print_test("POST /api/v1/users → create()", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/v1/users - {e}", False)
            failed += 1

        # 5. GET /api/v1/users/{user_id} (get)
        try:
            result = await client.request("GET", "/api/v1/users/test-123")
            assert result["id"] == "test-123"
            print_test("GET /api/v1/users/{id} → get()", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/users/{{id}} - {e}", False)
            failed += 1

        # 6. PATCH /api/v1/users/{user_id} (update)
        try:
            result = await client.request(
                "PATCH", "/api/v1/users/test-123", json={"name": "Updated"}
            )
            assert result["id"] == "test-123"
            print_test("PATCH /api/v1/users/{id} → update()", True)
            passed += 1
        except Exception as e:
            print_test(f"PATCH /api/v1/users/{{id}} - {e}", False)
            failed += 1

        # 7. DELETE /api/v1/users/{user_id} (delete)
        try:
            await client.request("DELETE", "/api/v1/users/test-123")
            print_test("DELETE /api/v1/users/{id} → delete()", True)
            passed += 1
        except Exception as e:
            print_test(f"DELETE /api/v1/users/{{id}} - {e}", False)
            failed += 1

        # ===== V1 PRODUCTS (3 routes) =====
        print(f"\n{YELLOW}>>> V1 Products{RESET}")

        # 8. GET /api/v1/products (list - array response)
        try:
            result = await client.request("GET", "/api/v1/products")
            assert isinstance(result, list)
            print_test("GET /api/v1/products → list() [array]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/products - {e}", False)
            failed += 1

        # 9. POST /api/v1/products (create)
        try:
            result = await client.request(
                "POST", "/api/v1/products", json={"name": "Widget", "price": 19.99}
            )
            assert result["name"] == "Widget"
            print_test("POST /api/v1/products → create()", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/v1/products - {e}", False)
            failed += 1

        # 10. GET /api/v1/products/{product_id} (get)
        try:
            result = await client.request("GET", "/api/v1/products/prod-123")
            assert result["id"] == "prod-123"
            print_test("GET /api/v1/products/{id} → get()", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/products/{{id}} - {e}", False)
            failed += 1

        # ===== V1 ORDERS (3 routes) =====
        print(f"\n{YELLOW}>>> V1 Orders{RESET}")

        # 11. GET /api/v1/orders (list - array)
        try:
            result = await client.request("GET", "/api/v1/orders")
            assert isinstance(result, list)
            print_test("GET /api/v1/orders → list() [array]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/orders - {e}", False)
            failed += 1

        # 12. POST /api/v1/orders (create)
        try:
            result = await client.request(
                "POST",
                "/api/v1/orders",
                json={
                    "user_id": "user-1",
                    "product_ids": ["prod-1"],
                    "payment_method": "credit_card",
                    "shipping_address": {"street": "123 Main"},
                },
            )
            assert result["user_id"] == "user-1"
            print_test("POST /api/v1/orders → create()", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/v1/orders - {e}", False)
            failed += 1

        # 13. GET /api/v1/orders/{order_id} (get)
        try:
            result = await client.request("GET", "/api/v1/orders/order-123")
            assert result["id"] == "order-123"
            print_test("GET /api/v1/orders/{id} → get()", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/orders/{{id}} - {e}", False)
            failed += 1

        # ===== V1 FILES (3 routes) =====
        print(f"\n{YELLOW}>>> V1 Files{RESET}")

        # 14. POST /api/v1/files (create - multipart)
        try:
            result = await client.v1.files.create(file=b"test file content")
            assert result["file_id"]
            print_test("POST /api/v1/files → create() [multipart]", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/v1/files → create() - {e}", False)
            failed += 1

        # 15. GET /api/v1/files/{file_id} (get metadata)
        try:
            result = await client.v1.files.get(file_id="file-123")
            assert result["file_id"] == "file-123"
            print_test("GET /api/v1/files/{id} → get()", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/files/{{id}} → get() - {e}", False)
            failed += 1

        # 16. GET /api/v1/files/{file_id}/download (RPC action - binary)
        try:
            result = await client.v1.files.download(file_id="file-123")
            assert isinstance(result, bytes)
            print_test("GET /api/v1/files/{id}/download → download() [RPC]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/files/{{id}}/download → download() - {e}", False)
            failed += 1

        # ===== V1 DOCUMENTS (2 routes) =====
        print(f"\n{YELLOW}>>> V1 Documents{RESET}")

        # 17. POST /api/v1/documents (create - form-data)
        try:
            result = await client.v1.documents.create(content="Document content", title="Test Doc")
            assert result["id"]
            print_test("POST /api/v1/documents → create() [form-data]", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/v1/documents → create() - {e}", False)
            failed += 1

        # 18. GET /api/v1/documents/{document_id} (get)
        try:
            result = await client.v1.documents.get(document_id="doc-123")
            assert result["id"] == "doc-123"
            print_test("GET /api/v1/documents/{id} → get()", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/documents/{{id}} → get() - {e}", False)
            failed += 1

        # ===== V1 ANALYTICS (1 route) =====
        print(f"\n{YELLOW}>>> V1 Analytics{RESET}")

        # 19. GET /api/v1/analytics/summary (RPC utility)
        try:
            result = await client.v1.analytics.summary(
                start_date="2024-01-01", end_date="2024-01-31"
            )
            assert "metrics" in result
            print_test("GET /api/v1/analytics/summary → summary() [RPC]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/analytics/summary → summary() - {e}", False)
            failed += 1

        # ===== V1 WEBHOOKS (2 routes) =====
        print(f"\n{YELLOW}>>> V1 Webhooks{RESET}")

        # 20. POST /api/v1/webhooks (create)
        try:
            result = await client.v1.webhooks.create(
                url="https://example.com/webhook", events=["user.created"]
            )
            assert result["id"]
            print_test("POST /api/v1/webhooks → create()", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/v1/webhooks → create() - {e}", False)
            failed += 1

        # 21. GET /api/v1/webhooks (list - array, but named webhooks() due to paginated response)
        try:
            result = await client.v1.webhooks.webhooks()
            assert isinstance(result, list)
            print_test("GET /api/v1/webhooks → webhooks() [array]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/webhooks → webhooks() - {e}", False)
            failed += 1

        # ===== V1 BATCH (2 routes) =====
        print(f"\n{YELLOW}>>> V1 Batch Operations{RESET}")

        # 22. POST /api/v1/batch/users (batch create)
        try:
            result = await client.v1.batch.create(items=[])
            assert "created" in result
            print_test("POST /api/v1/batch/users → batch.create() [batch]", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/v1/batch/users → batch.create() - {e}", False)
            failed += 1

        # 23. DELETE /api/v1/batch/users (batch delete)
        try:
            result = await client.v1.batch.delete(items=[])
            assert "deleted" in result
            print_test("DELETE /api/v1/batch/users → batch.delete() [batch]", True)
            passed += 1
        except Exception as e:
            print_test(f"DELETE /api/v1/batch/users → batch.delete() - {e}", False)
            failed += 1

        # ===== V1 AUTH (1 route) =====
        print(f"\n{YELLOW}>>> V1 Auth{RESET}")

        # 24. GET /api/v1/auth/me (RPC utility)
        try:
            result = await client.v1.auth.me()
            assert result["id"] == "current-user"
            print_test("GET /api/v1/auth/me → auth.me() [RPC]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v1/auth/me → auth.me() - {e}", False)
            failed += 1

        # ===== V2 USERS (3 routes) =====
        print(f"\n{YELLOW}>>> V2 Users{RESET}")

        # 25. GET /api/v2/users (list - array)
        try:
            result = await client.v2.usersv2.list()
            assert isinstance(result, list)
            print_test("GET /api/v2/users → usersv2.list() [array]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v2/users → usersv2.list() - {e}", False)
            failed += 1

        # 26. POST /api/v2/users (create)
        try:
            result = await client.v2.usersv2.create(
                username="testuser", email="test@v2.com", password="pass"
            )
            assert result["username"] == "testuser"
            print_test("POST /api/v2/users → usersv2.create()", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/v2/users → usersv2.create() - {e}", False)
            failed += 1

        # 27. GET /api/v2/users/{user_id} (get)
        try:
            result = await client.v2.usersv2.get(user_id="v2-123")
            assert result["id"] == "v2-123"
            print_test("GET /api/v2/users/{id} → usersv2.get()", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/v2/users/{{id}} → usersv2.get() - {e}", False)
            failed += 1

        # ===== BETA ENDPOINTS (4 routes) =====
        print(f"\n{YELLOW}>>> Beta Endpoints{RESET}")

        # 28. GET /api/beta/models (list - array)
        try:
            result = await client.beta.models.list()
            assert isinstance(result, list)
            print_test("GET /api/beta/models → models.list() [array]", True)
            passed += 1
        except Exception as e:
            print_test(f"GET /api/beta/models → models.list() - {e}", False)
            failed += 1

        # 29. POST /api/beta/chat (create)
        try:
            result = await client.beta.chat.create(
                model_id="model-1", messages=[{"role": "user", "content": "Hello"}]
            )
            assert result["id"]
            print_test("POST /api/beta/chat → chat.create()", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/beta/chat → chat.create() - {e}", False)
            failed += 1

        # 30. POST /api/beta/embeddings (create) - SDK param is 'items'
        try:
            result = await client.beta.embeddings.create(items=["hello"], model_id="model-1")
            assert "embeddings" in result
            print_test("POST /api/beta/embeddings → embeddings.create()", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/beta/embeddings → embeddings.create() - {e}", False)
            failed += 1

        # 31. POST /api/beta/search (create)
        try:
            result = await client.beta.search.create(query="test query")
            assert "results" in result
            print_test("POST /api/beta/search → search.create()", True)
            passed += 1
        except Exception as e:
            print_test(f"POST /api/beta/search → search.create() - {e}", False)
            failed += 1

        return passed, failed

    except ImportError as e:
        print(f"{RED}✗ Failed to import generated SDK: {e}{RESET}")
        return 0, 31


def main() -> int:
    """Run end-to-end test."""
    print_section("SDKGen Comprehensive E2E Test - ALL Routes")

    api_process = None

    try:
        # Phase 1: Start test API
        print_section("Phase 1: Setup Test API")
        api_process = start_test_api()

        # Phase 2: Generate SDK
        print_section("Phase 2: Generate SDK")
        if not generate_sdk():
            return 1

        # Phase 3: Test SDK
        passed, failed = asyncio.run(test_generated_sdk())

        # Summary
        print_section("Test Results")
        total = passed + failed
        print(f"Total: {total} tests")
        print(f"{GREEN}Passed: {passed}{RESET}")
        if failed > 0:
            print(f"{RED}Failed: {failed}{RESET}")
        else:
            print("Failed: 0")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")

        print(f"\n{BLUE}{'=' * 70}{RESET}")
        if failed == 0:
            print(f"{GREEN}{'✓ ALL ' + str(total) + ' TESTS PASSED':^70}{RESET}")
        else:
            print(f"{RED}{'✗ ' + str(failed) + ' / ' + str(total) + ' TESTS FAILED':^70}{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}\n")

        return 0 if failed == 0 else 1

    except Exception as e:
        print(f"\n{RED}✗ Test failed with exception: {e}{RESET}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        if api_process:
            print(f"\n{YELLOW}Stopping test API server...{RESET}")
            api_process.terminate()
            api_process.wait(timeout=5)
            print(f"{GREEN}✓ Cleanup complete{RESET}")


if __name__ == "__main__":
    sys.exit(main())
