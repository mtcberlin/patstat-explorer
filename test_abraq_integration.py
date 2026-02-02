"""
Test script for Abra-Q integration
Validates authentication and query generation functionality
"""
import os
from dotenv import load_dotenv
from modules.abra_q_client import AbraQClient, get_abraq_client, is_abraq_available

# Load environment variables
load_dotenv()


def test_abraq_availability():
    """Test if Abra-Q is properly configured."""
    print("=" * 60)
    print("TEST 1: Abra-Q Availability Check")
    print("=" * 60)

    available = is_abraq_available()
    print(f"✓ Abra-Q Available: {available}")

    if available:
        print(f"✓ API URL: {os.getenv('ABRAQ_API_URL')}")
        print(f"✓ Datasource: {os.getenv('ABRAQ_DATASOURCE')}")
        print(f"✓ Email: {os.getenv('ABRAQ_EMAIL')}")
        print("✓ Password: [CONFIGURED]")
    else:
        print("✗ Abra-Q not available - check environment configuration")

    return available


def test_abraq_authentication():
    """Test Abra-Q authentication."""
    print("\n" + "=" * 60)
    print("TEST 2: Abra-Q Authentication")
    print("=" * 60)

    try:
        client = get_abraq_client()
        if not client:
            print("✗ Failed to get Abra-Q client")
            return False

        # Trigger authentication by getting token
        token = client._get_token()

        if token:
            print(f"✓ Authentication successful")
            print(f"✓ Token received: {token[:20]}...")
            return True
        else:
            print("✗ Authentication failed - no token received")
            return False

    except Exception as e:
        print(f"✗ Authentication error: {str(e)}")
        return False


def test_query_generation():
    """Test query generation via Abra-Q."""
    print("\n" + "=" * 60)
    print("TEST 3: Query Generation")
    print("=" * 60)

    test_question = "Show me the top 10 companies filing wind energy patents in Germany since 2018"

    try:
        client = get_abraq_client()
        if not client:
            print("✗ Failed to get Abra-Q client")
            return False

        print(f"Question: {test_question}")
        print("\nGenerating query...")

        result = client.generate_query(test_question)

        if result['success']:
            print("✓ Query generation successful\n")
            print(f"Explanation:\n{result['explanation'][:200]}...\n")
            print(f"SQL Preview:\n{result['sql'][:300]}...\n")
            print(f"Full SQL length: {len(result['sql'])} characters")
            return True
        else:
            print(f"✗ Query generation failed: {result['error']}")
            return False

    except Exception as e:
        print(f"✗ Query generation error: {str(e)}")
        return False


def test_provider_routing():
    """Test provider routing logic."""
    print("\n" + "=" * 60)
    print("TEST 4: Provider Routing")
    print("=" * 60)

    current_provider = os.getenv("QUERY_PROVIDER", "claude")
    print(f"Current provider: {current_provider}")

    if current_provider == "abra-q":
        print("✓ Configured for Abra-Q")
        from modules.logic import is_ai_available, generate_sql_query

        available = is_ai_available()
        print(f"✓ AI available through routing: {available}")

        if available:
            print("\nTesting query through routing layer...")
            result = generate_sql_query("Show patent trends for AI technology")

            if result['success']:
                print("✓ Provider routing successful")
                print(f"✓ Received SQL: {len(result['sql'])} characters")
                return True
            else:
                print(f"✗ Provider routing failed: {result.get('error', 'Unknown error')}")
                return False
    else:
        print(f"⚠ Provider set to '{current_provider}', not testing Abra-Q routing")
        return True


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "ABRA-Q INTEGRATION TESTS" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = {
        "Availability": test_abraq_availability(),
        "Authentication": test_abraq_authentication(),
        "Query Generation": test_query_generation(),
        "Provider Routing": test_provider_routing()
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} | {test_name}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
