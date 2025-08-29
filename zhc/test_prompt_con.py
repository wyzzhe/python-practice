import asyncio
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import aiohttp


DEFAULT_URL = (
    "https://screen.aibee.cn/guide/get_prompt?place_id=801&name=foodRewrite"
)


@dataclass
class RequestResult:
    ok: bool
    status: Optional[int]
    elapsed_ms: float
    error: Optional[str]


async def fetch(session: aiohttp.ClientSession, url: str, timeout: float) -> RequestResult:
    start = time.perf_counter()
    try:
        async with session.get(url, timeout=timeout) as resp:
            # 读取响应以完成请求（不保存内容）
            await resp.read()
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(resp.text)
            return RequestResult(
                ok=200 <= resp.status < 400,
                status=resp.status,
                elapsed_ms=elapsed_ms,
                error=None,
            )
    except Exception as e:  # noqa: BLE001 - 捕获网络相关异常即可
        elapsed_ms = (time.perf_counter() - start) * 1000
        return RequestResult(ok=False, status=None, elapsed_ms=elapsed_ms, error=str(e))


async def worker(
    name: int,
    url: str,
    timeout: float,
    queue: "asyncio.Queue[int]",
    results: List[RequestResult],
    session: aiohttp.ClientSession,
) -> None:
    while True:
        try:
            _ = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        try:
            result = await fetch(session, url, timeout)
            results.append(result)
        finally:
            queue.task_done()


def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    k = (len(data) - 1) * p
    f = int(k)
    c = min(f + 1, len(data) - 1)
    if f == c:
        return data[f]
    return data[f] + (data[c] - data[f]) * (k - f)


def summarize(results: List[RequestResult], total_duration_s: float) -> None:
    total = len(results)
    successes = sum(1 for r in results if r.ok)
    failures = total - successes
    success_rate = (successes / total * 100) if total else 0.0
    qps = total / total_duration_s if total_duration_s > 0 else 0.0

    latencies = sorted([r.elapsed_ms for r in results])
    p50 = percentile(latencies, 0.50)
    p90 = percentile(latencies, 0.90)
    p95 = percentile(latencies, 0.95)
    p99 = percentile(latencies, 0.99)
    avg = statistics.fmean(latencies) if latencies else 0.0
    mx = max(latencies) if latencies else 0.0
    mn = min(latencies) if latencies else 0.0

    code_dist: Dict[str, int] = {}
    for r in results:
        key = str(r.status) if r.status is not None else "ERR"
        code_dist[key] = code_dist.get(key, 0) + 1

    print("==== Benchmark Result ====")
    print(f"Requests: {total}, Success: {successes}, Fail: {failures}, SuccessRate: {success_rate:.2f}%")
    print(f"Total time: {total_duration_s:.3f}s, QPS: {qps:.2f}")
    print(
        "Latency ms — avg: %.2f, p50: %.2f, p90: %.2f, p95: %.2f, p99: %.2f, min: %.2f, max: %.2f"
        % (avg, p50, p90, p95, p99, mn, mx)
    )
    print("Status distribution:")
    for k in sorted(code_dist.keys()):
        print(f"  {k}: {code_dist[k]}")


async def run_benchmark(
    url: str = DEFAULT_URL,
    concurrency: int = 20,
    total_requests: int = 200,
    timeout: float = 10.0,
    conn_limit: Optional[int] = None,
) -> None:
    if concurrency <= 0:
        raise ValueError("concurrency must be > 0")
    if total_requests <= 0:
        raise ValueError("total_requests must be > 0")

    queue: "asyncio.Queue[int]" = asyncio.Queue()
    for i in range(total_requests):
        queue.put_nowait(i)

    connector = aiohttp.TCPConnector(limit=conn_limit or concurrency)
    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    results: List[RequestResult] = []

    start = time.perf_counter()
    async with aiohttp.ClientSession(connector=connector, timeout=timeout_cfg) as session:
        workers = [
            asyncio.create_task(worker(i, url, timeout, queue, results, session))
            for i in range(concurrency)
        ]
        await queue.join()
        for t in workers:
            t.cancel()
        # 安静取消
        _ = await asyncio.gather(*workers, return_exceptions=True)
    total_duration_s = time.perf_counter() - start
    summarize(results, total_duration_s)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="并发 GET 压测脚本")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="目标 URL")
    parser.add_argument("--concurrency", type=int, default=20, help="并发协程数量")
    parser.add_argument("--total", type=int, default=200, help="总请求数")
    parser.add_argument("--timeout", type=float, default=10.0, help="每个请求超时时间(秒)")
    parser.add_argument("--conn-limit", type=int, default=None, help="TCP 连接上限(默认=并发数)")
    args = parser.parse_args()

    asyncio.run(
        run_benchmark(
            url=args.url,
            concurrency=args.concurrency,
            total_requests=args.total,
            timeout=args.timeout,
            conn_limit=args.conn_limit,
        )
    )


if __name__ == "__main__":
    main()
