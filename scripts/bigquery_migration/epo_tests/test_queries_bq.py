#!/usr/bin/env python3
"""Test all PATSTAT BigQuery queries, measure execution times, and report errors."""

import sys
import time
import json
from datetime import datetime

try:
    from epo.tipdata.patstat import PatstatClient
except ImportError:
    print("ERROR: epo.tipdata.patstat module not found.")
    print("This script requires the EPO PATSTAT BigQuery client.")
    print("Please ensure you have access to the EPO environment.")
    sys.exit(1)

from queries_bq import QUERIES


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
    print("Connecting to BigQuery via PatstatClient...")

    try:
        patstat = PatstatClient(env='PROD')
        print("✓ PatstatClient connection successful\n")
    except Exception as e:
        print(f"✗ PatstatClient connection failed: {e}")
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
            est_first = query_info.get("estimated_seconds_first_run", query_info.get("estimated_seconds", 0))
            est_cached = query_info.get("estimated_seconds_cached", 0)

            if verbose:
                print(f"\n  [{total}] {query_name}")
                print(f"      Expected: first run ~{format_time(est_first)}, cached ~{format_time(est_cached)}")
                print(f"      Running...", end=" ", flush=True)

            try:
                start = time.time()
                result = patstat.sql_query(sql, use_legacy_sql=False)
                elapsed = time.time() - start
                total_time += elapsed

                row_count = len(result) if result is not None else 0

                # Determine if this was likely cached (< 2x cached estimate)
                is_cached = elapsed < (est_cached * 2 + 0.5) if est_cached > 0 else elapsed < 1
                cache_status = "cached" if is_cached else "first run"

                if verbose:
                    print(f"✓ {row_count} rows in {format_time(elapsed)} ({cache_status})")

                passed += 1
                results.append({
                    "stakeholder": stakeholder,
                    "query": query_name,
                    "status": "PASS",
                    "rows": row_count,
                    "actual_seconds": round(elapsed, 2),
                    "estimated_seconds_first_run": est_first,
                    "estimated_seconds_cached": est_cached,
                    "likely_cached": is_cached,
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
                    "estimated_seconds_first_run": est_first,
                    "estimated_seconds_cached": est_cached,
                    "likely_cached": False,
                    "error": error_msg
                })

    # Print Summary
    print(f"\n\n{'='*70}")
    print(f"  SUMMARY (BigQuery)")
    print('='*70)
    print(f"  Total queries:  {total}")
    print(f"  Passed:         {passed} ✓")
    print(f"  Failed:         {failed} ✗")
    print(f"  Total time:     {format_time(total_time)}")
    print('='*70)

    # Timing Table
    print(f"\n\n{'='*70}")
    print(f"  TIMING RESULTS (BigQuery)")
    print('='*70)
    print(f"  {'Query':<40} {'Actual':>8} {'1st Run':>8} {'Cached':>8} {'Status':>8}")
    print(f"  {'-'*40} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for r in results:
        status_icon = "✓" if r["status"] == "PASS" else "✗"
        name = f"{status_icon} {r['query'][:37]}"
        actual = format_time(r["actual_seconds"])
        est_first = format_time(r["estimated_seconds_first_run"]) if r["estimated_seconds_first_run"] else "-"
        est_cached = format_time(r["estimated_seconds_cached"]) if r["estimated_seconds_cached"] else "-"
        cache_status = "cached" if r.get("likely_cached") else "cold"
        print(f"  {name:<40} {actual:>8} {est_first:>8} {est_cached:>8} {cache_status:>8}")

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
    output_file = f"test_results_bq_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump({
            "database": "BigQuery",
            "timestamp": timestamp,
            "total": total,
            "passed": passed,
            "failed": failed,
            "total_time_seconds": round(total_time, 2),
            "results": results
        }, f, indent=2)
    print(f"\n\nResults saved to: {output_file}")

    # Cache statistics
    cached_count = sum(1 for r in results if r.get("likely_cached"))
    cold_count = passed - cached_count
    print(f"\n\n{'='*70}")
    print(f"  CACHE ANALYSIS")
    print('='*70)
    print(f"  Queries from cache:  {cached_count}")
    print(f"  Cold queries:        {cold_count}")
    if cached_count > 0:
        cached_avg = sum(r["actual_seconds"] for r in results if r.get("likely_cached")) / cached_count
        print(f"  Avg cached time:     {format_time(cached_avg)}")
    if cold_count > 0:
        cold_results = [r for r in results if r["status"] == "PASS" and not r.get("likely_cached")]
        if cold_results:
            cold_avg = sum(r["actual_seconds"] for r in cold_results) / len(cold_results)
            print(f"  Avg cold time:       {format_time(cold_avg)}")

    return results


def test_single_query(stakeholder: str, query_name: str):
    """Test a single query by name."""
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

    print("Connecting to BigQuery via PatstatClient...")
    patstat = PatstatClient(env='PROD')

    try:
        start = time.time()
        result = patstat.sql_query(sql, use_legacy_sql=False)
        elapsed = time.time() - start

        row_count = len(result) if result is not None else 0

        print(f"✓ SUCCESS: {row_count} rows in {format_time(elapsed)}")
        if result is not None and len(result) > 0:
            print(f"\nFirst row: {result.iloc[0].to_dict()}")
    except Exception as e:
        print(f"✗ ERROR: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Run all tests
        test_all_queries()
    elif len(sys.argv) == 3:
        # Test single query: python test_queries_bq.py "Stakeholder" "Query Name"
        test_single_query(sys.argv[1], sys.argv[2])
    else:
        print("Usage:")
        print("  python test_queries_bq.py                          # Test all queries")
        print('  python test_queries_bq.py "Overview" "Query Name"  # Test single query')
