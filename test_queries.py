#!/usr/bin/env python3
"""Test all BigQuery queries and generate timing report."""

import os
import json
import time
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv
from queries_bq import QUERIES

load_dotenv()


def get_client():
    """Create BigQuery client."""
    project = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")
    service_account_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if service_account_json:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(service_account_json)
        )
        return bigquery.Client(credentials=credentials, project=project)
    return bigquery.Client(project=project)


def run_query(client, query):
    """Execute query and return execution time."""
    project = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")
    dataset = os.getenv("BIGQUERY_DATASET", "patstat")
    job_config = bigquery.QueryJobConfig(default_dataset=f"{project}.{dataset}")

    start = time.time()
    result = client.query(query, job_config=job_config).to_dataframe()
    elapsed = time.time() - start
    return elapsed, len(result)


def format_time(seconds):
    """Format seconds to display string."""
    if seconds < 1:
        return f"{int(seconds*1000)}ms"
    return f"{seconds:.1f}s"


def main():
    client = get_client()
    results = []
    total_time = 0
    passed = 0
    failed = 0

    print("=" * 70)
    print(" SUMMARY (BigQuery)")
    print("=" * 70)
    print("Running queries...\n")

    # Collect all queries
    all_queries = []
    for category, queries in QUERIES.items():
        for name, info in queries.items():
            all_queries.append((category, name, info))

    print(f"Total queries: {len(all_queries)}")
    print()

    # Run each query
    for category, name, info in all_queries:
        sql = info["sql"]
        est_first = info.get("estimated_seconds_first_run", 1)
        est_cached = info.get("estimated_seconds_cached", 1)

        try:
            elapsed, rows = run_query(client, sql)
            total_time += elapsed
            passed += 1
            status = "cached" if elapsed < est_first * 0.8 else "uncached"
            results.append({
                "name": name,
                "actual": elapsed,
                "est_first": est_first,
                "est_cached": est_cached,
                "rows": rows,
                "status": status,
                "error": None
            })
            print(f"  ✓ {name}: {format_time(elapsed)}")
        except Exception as e:
            failed += 1
            results.append({
                "name": name,
                "actual": 0,
                "est_first": est_first,
                "est_cached": est_cached,
                "rows": 0,
                "status": "FAILED",
                "error": str(e)
            })
            print(f"  ✗ {name}: FAILED - {str(e)[:50]}")

    # Print summary
    print()
    print("=" * 70)
    print(" SUMMARY (BigQuery)")
    print("=" * 70)
    print(f"Total queries: {len(all_queries)}")
    print(f"Passed:        {passed} ✓")
    print(f"Failed:        {failed} ✗")
    print(f"Total time:    {format_time(total_time)}")
    print()

    # Print detailed results
    print("=" * 70)
    print(" TIMING RESULTS (BigQuery)")
    print("=" * 70)
    print()
    print(f"{'Query':<45} {'Actual':>8} {'1st Run':>8} {'Cached':>8} {'Status':>8}")
    print("-" * 45 + " " + "-" * 8 + " " + "-" * 8 + " " + "-" * 8 + " " + "-" * 8)

    for r in results:
        status_icon = "✓" if r["status"] != "FAILED" else "✗"
        name = r["name"][:43] if len(r["name"]) > 43 else r["name"]
        print(f"{status_icon} {name:<43} {format_time(r['actual']):>8} {format_time(r['est_first']):>8} {format_time(r['est_cached']):>8} {r['status']:>8}")

    print()

    # Save results to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_bq_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "total_queries": len(all_queries),
            "passed": passed,
            "failed": failed,
            "total_time": total_time,
            "results": results
        }, f, indent=2)
    print(f"Results saved to: {filename}")
    print()

    # Cache analysis
    cached_queries = [r for r in results if r["status"] == "cached"]
    uncached_queries = [r for r in results if r["status"] == "uncached"]

    print("=" * 70)
    print(" CACHE ANALYSIS")
    print("=" * 70)
    print(f"Queries from cache: {len(cached_queries)}")
    print(f"Cold queries:       {len(uncached_queries)}")
    if cached_queries:
        avg_cached = sum(r["actual"] for r in cached_queries) / len(cached_queries)
        print(f"Avg cached time:    {format_time(avg_cached)}")
    print()


if __name__ == "__main__":
    main()
