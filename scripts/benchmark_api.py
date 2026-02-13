#!/usr/bin/env python3
"""
Simple API benchmark runner for ~10k queries.

Supports:
- .txt file: one query string per line -> {"query": "..."}
- .jsonl file: one JSON body per line
"""

import argparse
import itertools
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark API endpoint.")
    parser.add_argument("--url", required=True, help="Base URL, e.g. http://68.183.101.165")
    parser.add_argument("--endpoint", default="/faucets", help="Endpoint path, e.g. /faucets")
    parser.add_argument("--queries-file", required=True, help="Path to .txt or .jsonl queries file")
    parser.add_argument("--requests", type=int, default=10000, help="Total requests to send")
    parser.add_argument("--concurrency", type=int, default=20, help="Number of parallel workers")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout (sec)")
    parser.add_argument("--warmup", type=int, default=100, help="Warmup request count")
    return parser.parse_args()


def load_payloads(path: str) -> list[dict]:
    payloads: list[dict] = []
    if path.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                payloads.append(json.loads(line))
    else:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                q = line.strip()
                if q:
                    payloads.append({"query": q})

    if not payloads:
        raise RuntimeError("No payloads loaded from queries file.")
    return payloads


def one_call(url: str, payload: dict, timeout: float) -> tuple[bool, float, int, str, str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            _ = resp.read()
            latency = (time.perf_counter() - start) * 1000.0
            status = getattr(resp, "status", 200)
            ok = 200 <= status < 300
            return ok, latency, status, "", json.dumps(payload, ensure_ascii=False)
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000.0
        return False, latency, e.code, f"HTTPError: {e.reason}", json.dumps(payload, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        latency = (time.perf_counter() - start) * 1000.0
        return False, latency, 0, str(e), json.dumps(payload, ensure_ascii=False)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    k = (len(values) - 1) * p
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def run_phase(name: str, target_url: str, payloads: list[dict], total_requests: int, concurrency: int, timeout: float):
    latencies: list[float] = []
    ok_count = 0
    fail_count = 0
    fail_samples: list[str] = []

    stream = itertools.islice(itertools.cycle(payloads), total_requests)
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(one_call, target_url, payload, timeout) for payload in stream]
        for fut in as_completed(futures):
            ok, latency, status, err, payload_text = fut.result()
            latencies.append(latency)
            if ok:
                ok_count += 1
            else:
                fail_count += 1
                if len(fail_samples) < 10:
                    fail_samples.append(f"status={status}, err={err}, payload={payload_text}")

    elapsed = time.perf_counter() - start
    latencies.sort()

    rps = total_requests / elapsed if elapsed > 0 else 0.0
    print(f"\n=== {name} ===")
    print(f"Requests: {total_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"RPS: {rps:.2f}")
    print(f"Success: {ok_count}")
    print(f"Failed: {fail_count}")
    print(f"Error rate: {(fail_count / total_requests) * 100:.2f}%")
    if latencies:
        print(f"Latency mean: {statistics.mean(latencies):.2f} ms")
        print(f"Latency p50:  {percentile(latencies, 0.50):.2f} ms")
        print(f"Latency p95:  {percentile(latencies, 0.95):.2f} ms")
        print(f"Latency p99:  {percentile(latencies, 0.99):.2f} ms")
        print(f"Latency max:  {max(latencies):.2f} ms")

    if fail_samples:
        print("Sample failures:")
        for s in fail_samples:
            print(f"- {s}")


def main():
    args = parse_args()
    payloads = load_payloads(args.queries_file)
    base = args.url.rstrip("/")
    endpoint = args.endpoint if args.endpoint.startswith("/") else f"/{args.endpoint}"
    target_url = f"{base}{endpoint}"

    print(f"Target: {target_url}")
    print(f"Payload templates loaded: {len(payloads)}")

    if args.warmup > 0:
        run_phase("Warmup", target_url, payloads, args.warmup, min(args.concurrency, 10), args.timeout)

    run_phase("Benchmark", target_url, payloads, args.requests, args.concurrency, args.timeout)


if __name__ == "__main__":
    main()
