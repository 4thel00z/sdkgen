#!/usr/bin/env python3
"""End-to-end test: Generate SDK from test API and use it."""

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
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{title:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


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
    """Test the generated SDK by making actual API calls."""
    print_section("Testing Generated SDK")

    # Add SDK to Python path
    sys.path.insert(0, str(SDK_OUTPUT_DIR))

    try:
        # Import generated SDK
        from e2e_test_sdk import Client

        # Initialize client
        client = Client(base_url=TEST_API_URL, api_key="test-key")

        passed = 0
        failed = 0

        # Test 1: SDK generation verification
        try:
            # Check that key modules exist
            assert hasattr(client, "v1")
            assert hasattr(client, "request")
            print_test("SDK structure verification", True)
            passed += 1
        except Exception as e:
            print_test(f"SDK structure verification - {e}", False)
            failed += 1

        # Test 2: Simple API call test
        try:
            # Use direct API call to verify basic functionality
            result = await client.request("GET", "/health")
            assert result["status"] == "healthy"
            print_test("Direct API call: GET /health", True)
            passed += 1
        except Exception as e:
            print_test(f"Direct API call - {e}", False)
            failed += 1

        print(f"\n{YELLOW}Note: Generated SDK has resources organized by tags.{RESET}")
        print(f"{YELLOW}Available resources: systems, users, products, files, batchs, etc.{RESET}")
        print(f"{YELLOW}Namespace objects (v1, v2, beta) aggregate resources by version.{RESET}\n")

        return passed, failed

    except ImportError as e:
        print(f"{RED}✗ Failed to import generated SDK: {e}{RESET}")
        return 0, 10


def main() -> int:
    """Run end-to-end test."""
    print_section("SDKGen End-to-End Test")

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

        print(f"\n{BLUE}{'=' * 60}{RESET}")
        if failed == 0:
            print(f"{GREEN}{'✓ ALL TESTS PASSED':^60}{RESET}")
        else:
            print(f"{RED}{'✗ SOME TESTS FAILED':^60}{RESET}")
        print(f"{BLUE}{'=' * 60}{RESET}\n")

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
