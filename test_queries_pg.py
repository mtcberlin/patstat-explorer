#!/usr/bin/env python3
"""Test all PATSTAT queries, measure execution times, and report errors."""

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from queries_pg import QUERIES

load_dotenv()


def format_time(seconds: float) -> str:
    """Format seconds into human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"


def test_all_queries(verbose: bool = True):
    """Test all queries and return results with timing."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)

    print(f"Connecting to database...")
    engine = create_engine(database_url)

    # Test connection first
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful\n")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)

    results = []
    total = 0
    passed = 0
    failed = 0
    total_time = 0

    for stakeholder, queries in QUERIES.items():
        print(f"\n{'='*70}")
        print(f"  {stakeholder}")
        print('='*70)

        for query_name, query_info in queries.items():
            total += 1
            sql = query_info["sql"]
            estimated = query_info.get("estimated_seconds", 0)

            if verbose:
                print(f"\n  [{total}] {query_name}")
                print(f"      Estimated: ~{format_time(estimated)}")
                print(f"      Running...", end=" ", flush=True)

            try:
                start = time.time()
                with engine.connect() as conn:
                    result = conn.execute(text(sql))
                    rows = result.fetchall()
                elapsed = time.time() - start
                total_time += elapsed

                # Compare to estimate
                if estimated > 0:
                    diff = elapsed - estimated
                    diff_pct = (diff / estimated) * 100
                    comparison = f"({'+' if diff > 0 else ''}{diff_pct:.0f}% vs estimate)"
                else:
                    comparison = "(no estimate)"

                if verbose:
                    print(f"✓ {len(rows)} rows in {format_time(elapsed)} {comparison}")

                passed += 1
                results.append({
                    "stakeholder": stakeholder,
                    "query": query_name,
                    "status": "PASS",
                    "rows": len(rows),
                    "actual_seconds": round(elapsed, 2),
                    "estimated_seconds": estimated,
                    "diff_seconds": round(elapsed - estimated, 2) if estimated else None,
                    "error": None
                })

            except Exception as e:
                elapsed = time.time() - start
                total_time += elapsed
                error_msg = str(e)

                if verbose:
                    print(f"✗ ERROR after {format_time(elapsed)}")
                    print(f"      {error_msg[:150]}...")

                failed += 1
                results.append({
                    "stakeholder": stakeholder,
                    "query": query_name,
                    "status": "FAIL",
                    "rows": 0,
                    "actual_seconds": round(elapsed, 2),
                    "estimated_seconds": estimated,
                    "diff_seconds": None,
                    "error": error_msg
                })

    # Print Summary
    print(f"\n\n{'='*70}")
    print(f"  SUMMARY")
    print('='*70)
    print(f"  Total queries:  {total}")
    print(f"  Passed:         {passed} ✓")
    print(f"  Failed:         {failed} ✗")
    print(f"  Total time:     {format_time(total_time)}")
    print('='*70)

    # Timing Table
    print(f"\n\n{'='*70}")
    print(f"  TIMING RESULTS")
    print('='*70)
    print(f"  {'Query':<45} {'Actual':>10} {'Est.':>10} {'Diff':>10}")
    print(f"  {'-'*45} {'-'*10} {'-'*10} {'-'*10}")

    for r in results:
        status = "✓" if r["status"] == "PASS" else "✗"
        name = f"{status} {r['query'][:42]}"
        actual = format_time(r["actual_seconds"])
        est = format_time(r["estimated_seconds"]) if r["estimated_seconds"] else "-"
        if r["diff_seconds"] is not None:
            diff = f"{'+' if r['diff_seconds'] > 0 else ''}{format_time(abs(r['diff_seconds']))}"
        else:
            diff = "-"
        print(f"  {name:<45} {actual:>10} {est:>10} {diff:>10}")

    # Failed queries detail
    if failed > 0:
        print(f"\n\n{'='*70}")
        print(f"  FAILED QUERIES - DETAILS")
        print('='*70)
        for r in results:
            if r["status"] == "FAIL":
                print(f"\n  [{r['stakeholder']}] {r['query']}")
                print(f"  Error: {r['error'][:500]}")

    # Save results to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_results_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "total": total,
            "passed": passed,
            "failed": failed,
            "total_time_seconds": round(total_time, 2),
            "results": results
        }, f, indent=2)
    print(f"\n\nResults saved to: {output_file}")

    # Generate estimated_seconds update suggestions
    if passed > 0:
        print(f"\n\n{'='*70}")
        print(f"  SUGGESTED estimated_seconds UPDATES")
        print('='*70)
        print("  Copy these values to queries.py:\n")
        for r in results:
            if r["status"] == "PASS":
                # Round up to nearest 5 seconds for estimates, minimum 1
                suggested = max(1, int((r["actual_seconds"] + 4) // 5) * 5)
                if r["estimated_seconds"] != suggested:
                    print(f'  "{r["query"]}": estimated_seconds = {suggested}  # actual: {r["actual_seconds"]:.1f}s')

    return results


def test_single_query(stakeholder: str, query_name: str):
    """Test a single query by name."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    if stakeholder not in QUERIES:
        print(f"Unknown stakeholder: {stakeholder}")
        print(f"Available: {list(QUERIES.keys())}")
        sys.exit(1)

    if query_name not in QUERIES[stakeholder]:
        print(f"Unknown query: {query_name}")
        print(f"Available: {list(QUERIES[stakeholder].keys())}")
        sys.exit(1)

    query_info = QUERIES[stakeholder][query_name]
    sql = query_info["sql"]

    print(f"Testing: [{stakeholder}] {query_name}")
    print(f"SQL:\n{sql}\n")

    engine = create_engine(database_url)

    try:
        start = time.time()
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
        elapsed = time.time() - start

        print(f"✓ SUCCESS: {len(rows)} rows in {format_time(elapsed)}")
        if rows:
            print(f"\nFirst row: {rows[0]}")
    except Exception as e:
        print(f"✗ ERROR: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Run all tests
        test_all_queries()
    elif len(sys.argv) == 3:
        # Test single query: python test_queries.py "Stakeholder" "Query Name"
        test_single_query(sys.argv[1], sys.argv[2])
    else:
        print("Usage:")
        print("  python test_queries.py                          # Test all queries")
        print('  python test_queries.py "Overview" "Database Tables (detailed)"  # Test single query')
