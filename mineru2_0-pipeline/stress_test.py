#!/usr/bin/env python3
"""
MinerU Tianshu 多进程 + 线程池压测脚本

用法示例:
  # 2进程 x 4线程，压测60秒
  python stress_test.py --pdf sample.pdf --processes 2 --threads 4 --duration 60

  # 单进程8线程，压测120秒，自定义服务地址
  python stress_test.py --pdf sample.pdf --threads 8 --duration 120 --url http://localhost:18000

  # 只提交不等待完成（fire-and-forget 模式）
  python stress_test.py --pdf sample.pdf --processes 4 --threads 4 --duration 30 --no-wait
"""

import argparse
import json
import multiprocessing as mp
import os
import signal
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import requests


@dataclass
class TaskResult:
    task_id: str = ""
    submit_ok: bool = False
    submit_latency: float = 0.0
    poll_ok: bool = False
    total_latency: float = 0.0
    error: str = ""
    status: str = ""


@dataclass
class WorkerStats:
    pid: int = 0
    total_submitted: int = 0
    submit_success: int = 0
    submit_fail: int = 0
    completed: int = 0
    failed: int = 0
    timeout: int = 0
    submit_latencies: list = field(default_factory=list)
    total_latencies: list = field(default_factory=list)
    errors: list = field(default_factory=list)


def submit_and_poll(
    api_url: str,
    pdf_path: str,
    poll_interval: float,
    poll_timeout: float,
    wait_complete: bool,
    backend: str,
    lang: str,
) -> TaskResult:
    """提交一个 PDF 任务并可选地轮询到完成。"""
    result = TaskResult()
    submit_url = f"{api_url}/api/v1/tasks/submit"

    t0 = time.monotonic()
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
            data = {"backend": backend, "lang": lang}
            resp = requests.post(submit_url, files=files, data=data, timeout=60)

        result.submit_latency = time.monotonic() - t0

        if resp.status_code != 200:
            result.error = f"submit HTTP {resp.status_code}: {resp.text[:200]}"
            return result

        body = resp.json()
        if not body.get("success"):
            result.error = f"submit failed: {json.dumps(body, ensure_ascii=False)[:200]}"
            return result

        result.task_id = body["task_id"]
        result.submit_ok = True

    except Exception as e:
        result.submit_latency = time.monotonic() - t0
        result.error = f"submit exception: {e}"
        return result

    if not wait_complete:
        result.total_latency = result.submit_latency
        return result

    status_url = f"{api_url}/api/v1/tasks/{result.task_id}"
    deadline = time.monotonic() + poll_timeout

    while time.monotonic() < deadline:
        try:
            r = requests.get(status_url, timeout=10)
            if r.status_code == 200:
                info = r.json()
                status = info.get("status", "")
                result.status = status
                if status == "completed":
                    result.poll_ok = True
                    result.total_latency = time.monotonic() - t0
                    return result
                elif status == "failed":
                    result.error = f"task failed: {info.get('error', 'unknown')}"
                    result.total_latency = time.monotonic() - t0
                    return result
        except Exception:
            pass
        time.sleep(poll_interval)

    result.error = "poll timeout"
    result.total_latency = time.monotonic() - t0
    return result


def _worker_loop(
    worker_id: int,
    api_url: str,
    pdf_path: str,
    num_threads: int,
    duration: float,
    poll_interval: float,
    poll_timeout: float,
    wait_complete: bool,
    backend: str,
    lang: str,
    result_queue: mp.Queue,
    stop_event,
):
    """单个子进程的工作循环：用线程池持续提交请求直到时间耗尽。"""
    stats = WorkerStats(pid=os.getpid())
    deadline = time.monotonic() + duration

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    def _run_one():
        return submit_and_poll(
            api_url, pdf_path, poll_interval, poll_timeout, wait_complete, backend, lang
        )

    with ThreadPoolExecutor(max_workers=num_threads) as pool:
        futures = []

        while time.monotonic() < deadline and not stop_event.is_set():
            active = sum(1 for ft in futures if not ft.done())
            slots = num_threads - active
            for _ in range(max(slots, 0)):
                if time.monotonic() >= deadline or stop_event.is_set():
                    break
                futures.append(pool.submit(_run_one))

            done = [ft for ft in futures if ft.done()]
            for ft in done:
                futures.remove(ft)
                try:
                    res = ft.result()
                except Exception as e:
                    stats.submit_fail += 1
                    stats.errors.append(str(e))
                    continue

                stats.total_submitted += 1
                stats.submit_latencies.append(res.submit_latency)

                if res.submit_ok:
                    stats.submit_success += 1
                else:
                    stats.submit_fail += 1
                    if res.error:
                        stats.errors.append(res.error)
                    continue

                if not wait_complete:
                    stats.completed += 1
                    continue

                if res.poll_ok:
                    stats.completed += 1
                    stats.total_latencies.append(res.total_latency)
                elif "timeout" in res.error:
                    stats.timeout += 1
                else:
                    stats.failed += 1
                    if res.error:
                        stats.errors.append(res.error)

            time.sleep(0.05)

        for ft in as_completed(futures, timeout=poll_timeout + 30):
            try:
                res = ft.result()
            except Exception as e:
                stats.submit_fail += 1
                stats.errors.append(str(e))
                continue

            stats.total_submitted += 1
            stats.submit_latencies.append(res.submit_latency)

            if res.submit_ok:
                stats.submit_success += 1
            else:
                stats.submit_fail += 1
                continue

            if not wait_complete:
                stats.completed += 1
            elif res.poll_ok:
                stats.completed += 1
                stats.total_latencies.append(res.total_latency)
            elif "timeout" in (res.error or ""):
                stats.timeout += 1
            else:
                stats.failed += 1

    result_queue.put(stats)


def percentile(data: list, p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p / 100)
    idx = min(idx, len(sorted_data) - 1)
    return sorted_data[idx]


def print_report(all_stats: list[WorkerStats], elapsed: float, args):
    """汇总并打印压测报告。"""
    total_submitted = sum(s.total_submitted for s in all_stats)
    total_submit_ok = sum(s.submit_success for s in all_stats)
    total_submit_fail = sum(s.submit_fail for s in all_stats)
    total_completed = sum(s.completed for s in all_stats)
    total_failed = sum(s.failed for s in all_stats)
    total_timeout = sum(s.timeout for s in all_stats)

    all_submit_lat = []
    all_total_lat = []
    for s in all_stats:
        all_submit_lat.extend(s.submit_latencies)
        all_total_lat.extend(s.total_latencies)

    all_errors = []
    for s in all_stats:
        all_errors.extend(s.errors)

    error_summary = defaultdict(int)
    for e in all_errors:
        key = e[:80]
        error_summary[key] += 1

    print("\n" + "=" * 70)
    print("  MinerU Tianshu 压测报告")
    print("=" * 70)
    print(f"  服务地址      : {args.url}")
    print(f"  PDF 文件      : {args.pdf}")
    print(f"  进程数        : {args.processes}")
    print(f"  每进程线程数  : {args.threads}")
    print(f"  总并发        : {args.processes * args.threads}")
    print(f"  压测时长(设定): {args.duration}s")
    print(f"  实际运行时长  : {elapsed:.1f}s")
    print(f"  等待完成      : {'是' if args.wait else '否'}")
    print("-" * 70)
    print(f"  总提交数      : {total_submitted}")
    print(f"  提交成功      : {total_submit_ok}")
    print(f"  提交失败      : {total_submit_fail}")
    if args.wait:
        print(f"  处理完成      : {total_completed}")
        print(f"  处理失败      : {total_failed}")
        print(f"  轮询超时      : {total_timeout}")
    print("-" * 70)

    if elapsed > 0:
        print(f"  提交 QPS      : {total_submitted / elapsed:.2f} req/s")
        if args.wait and total_completed > 0:
            print(f"  完成 QPS      : {total_completed / elapsed:.2f} req/s")

    if all_submit_lat:
        print("-" * 70)
        print("  提交延迟 (秒):")
        print(f"    avg  = {sum(all_submit_lat)/len(all_submit_lat):.3f}")
        print(f"    min  = {min(all_submit_lat):.3f}")
        print(f"    p50  = {percentile(all_submit_lat, 50):.3f}")
        print(f"    p90  = {percentile(all_submit_lat, 90):.3f}")
        print(f"    p99  = {percentile(all_submit_lat, 99):.3f}")
        print(f"    max  = {max(all_submit_lat):.3f}")

    if all_total_lat:
        print("-" * 70)
        print("  端到端延迟 (秒):")
        print(f"    avg  = {sum(all_total_lat)/len(all_total_lat):.3f}")
        print(f"    min  = {min(all_total_lat):.3f}")
        print(f"    p50  = {percentile(all_total_lat, 50):.3f}")
        print(f"    p90  = {percentile(all_total_lat, 90):.3f}")
        print(f"    p99  = {percentile(all_total_lat, 99):.3f}")
        print(f"    max  = {max(all_total_lat):.3f}")

    if error_summary:
        print("-" * 70)
        print("  错误汇总 (前10):")
        for err, cnt in sorted(error_summary.items(), key=lambda x: -x[1])[:10]:
            print(f"    [{cnt:>4}x] {err}")

    print("=" * 70)

    report = {
        "config": {
            "url": args.url,
            "pdf": args.pdf,
            "processes": args.processes,
            "threads": args.threads,
            "total_concurrency": args.processes * args.threads,
            "duration_setting": args.duration,
            "actual_elapsed": round(elapsed, 2),
            "wait_complete": args.wait,
        },
        "summary": {
            "total_submitted": total_submitted,
            "submit_success": total_submit_ok,
            "submit_fail": total_submit_fail,
            "completed": total_completed,
            "failed": total_failed,
            "timeout": total_timeout,
            "submit_qps": round(total_submitted / elapsed, 2) if elapsed > 0 else 0,
        },
        "submit_latency": {
            "avg": round(sum(all_submit_lat) / len(all_submit_lat), 4) if all_submit_lat else 0,
            "min": round(min(all_submit_lat), 4) if all_submit_lat else 0,
            "p50": round(percentile(all_submit_lat, 50), 4),
            "p90": round(percentile(all_submit_lat, 90), 4),
            "p99": round(percentile(all_submit_lat, 99), 4),
            "max": round(max(all_submit_lat), 4) if all_submit_lat else 0,
        },
        "total_latency": {
            "avg": round(sum(all_total_lat) / len(all_total_lat), 4) if all_total_lat else 0,
            "min": round(min(all_total_lat), 4) if all_total_lat else 0,
            "p50": round(percentile(all_total_lat, 50), 4),
            "p90": round(percentile(all_total_lat, 90), 4),
            "p99": round(percentile(all_total_lat, 99), 4),
            "max": round(max(all_total_lat), 4) if all_total_lat else 0,
        },
    }

    report_path = f"stress_report_{int(time.time())}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  报告已保存: {report_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="MinerU Tianshu 多进程+线程池 PDF 压测脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--pdf", required=True, help="待测试的 PDF 文件路径")
    parser.add_argument("--url", default="http://localhost:18000", help="服务地址 (默认 http://localhost:18000)")
    parser.add_argument("--processes", "-p", type=int, default=8, help="进程数 (默认 1)")
    parser.add_argument("--threads", "-t", type=int, default=5, help="每个进程的线程数 (默认 4)")
    parser.add_argument("--duration", "-d", type=float, default=3600, help="压测持续时长/秒 (默认 60)")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="轮询间隔/秒 (默认 2.0)")
    parser.add_argument("--poll-timeout", type=float, default=3600, help="单任务轮询超时/秒 (默认 300)")
    parser.add_argument("--no-wait", dest="wait", action="store_false", help="提交后不等待完成 (fire-and-forget)")
    parser.add_argument("--backend", default="pipeline", help="处理后端 (默认 pipeline)")
    parser.add_argument("--lang", default="ch", help="语言 (默认 ch)")
    parser.set_defaults(wait=True)
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.is_file():
        print(f"错误: PDF 文件不存在: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"准备压测: {args.processes} 进程 x {args.threads} 线程 = {args.processes * args.threads} 并发")
    print(f"目标: {args.url}  PDF: {pdf_path}  时长: {args.duration}s")

    try:
        health = requests.get(f"{args.url}/api/v1/health", timeout=5)
        if health.status_code == 200:
            print(f"服务健康检查通过: {health.json()}")
        else:
            print(f"警告: 健康检查返回 {health.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"警告: 无法连接到服务 {args.url} ({e})，仍将继续...", file=sys.stderr)

    stop_event = mp.Event()
    result_queue = mp.Queue()
    processes = []

    t_start = time.monotonic()

    for i in range(args.processes):
        p = mp.Process(
            target=_worker_loop,
            args=(
                i,
                args.url,
                str(pdf_path),
                args.threads,
                args.duration,
                args.poll_interval,
                args.poll_timeout,
                args.wait,
                args.backend,
                args.lang,
                result_queue,
                stop_event,
            ),
            daemon=True,
        )
        p.start()
        processes.append(p)
        print(f"  启动进程 #{i} (PID={p.pid})")

    print(f"\n压测进行中... (Ctrl+C 可提前终止)\n")

    try:
        for p in processes:
            remaining = args.duration - (time.monotonic() - t_start)
            extra = args.poll_timeout + 60 if args.wait else 30
            p.join(timeout=max(remaining + extra, 10))
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
        stop_event.set()
        for p in processes:
            p.join(timeout=10)

    elapsed = time.monotonic() - t_start

    all_stats = []
    while not result_queue.empty():
        all_stats.append(result_queue.get_nowait())

    if all_stats:
        print_report(all_stats, elapsed, args)
    else:
        print("没有收集到任何结果。")


if __name__ == "__main__":
    main()
