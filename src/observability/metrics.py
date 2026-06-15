from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any

from src.common.config import get_settings


@dataclass
class LatencyStats:
    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def record(self, latency_ms: float) -> None:
        self.count += 1
        self.total_ms += latency_ms
        self.max_ms = max(self.max_ms, latency_ms)

    def to_dict(self) -> dict[str, float | int]:
        avg_ms = round(self.total_ms / self.count, 2) if self.count else 0.0
        return {
            "count": self.count,
            "avg_ms": avg_ms,
            "max_ms": round(self.max_ms, 2),
        }


class MetricsCollector:
    """Basit in-memory metrics — Prometheus/OpenTelemetry öncesi demo katmanı."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.counters: dict[str, int] = defaultdict(int)
        self.latencies: dict[str, LatencyStats] = defaultdict(LatencyStats)
        self.gauges: dict[str, float] = {}

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self.counters[name] += value

    def record_latency(self, name: str, latency_ms: float) -> None:
        with self._lock:
            self.latencies[name].record(latency_ms)

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self.gauges[name] = value

    def record_http_request(
        self,
        *,
        route: str,
        method: str,
        status_code: int,
        latency_ms: float,
    ) -> None:
        self.increment("http_requests_total")
        if status_code >= 500:
            self.increment("http_errors_total")
        self.record_latency(f"http_latency_ms:{method}:{route}", latency_ms)

    def record_llm_call(
        self,
        *,
        model: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        retry_count: int,
        status: str,
    ) -> None:
        self.increment("llm_calls_total")
        if status != "ok":
            self.increment("llm_errors_total")
        if retry_count > 1:
            self.increment("llm_retries_total", retry_count - 1)

        self.record_latency(f"llm_latency_ms:{model}", latency_ms)
        self.increment("llm_prompt_tokens_total", prompt_tokens)
        self.increment("llm_completion_tokens_total", completion_tokens)

        cost = estimate_llm_cost_usd(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self.set_gauge("llm_estimated_cost_usd_last", cost)
        with self._lock:
            self.gauges["llm_estimated_cost_usd_total"] = (
                self.gauges.get("llm_estimated_cost_usd_total", 0.0) + cost
            )

    def record_workflow_run(
        self,
        *,
        status: str,
        latency_ms: float,
        step_latencies: dict[str, float],
    ) -> None:
        self.increment("workflow_runs_total")
        if status == "failed":
            self.increment("workflow_failures_total")
        if status == "awaiting_approval":
            self.increment("workflow_approval_required_total")

        self.record_latency("workflow_total_latency_ms", latency_ms)
        for step, step_latency in step_latencies.items():
            self.record_latency(f"workflow_step_latency_ms:{step}", step_latency)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self.counters),
                "latencies": {
                    name: stats.to_dict() for name, stats in self.latencies.items()
                },
                "gauges": dict(self.gauges),
            }

    def reset(self) -> None:
        with self._lock:
            self.counters.clear()
            self.latencies.clear()
            self.gauges.clear()


_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    return _metrics


def estimate_llm_cost_usd(*, prompt_tokens: int, completion_tokens: int) -> float:
    settings = get_settings()
    prompt_cost = (prompt_tokens / 1000) * settings.llm_prompt_cost_per_1k_usd
    completion_cost = (completion_tokens / 1000) * settings.llm_completion_cost_per_1k_usd
    return prompt_cost + completion_cost
