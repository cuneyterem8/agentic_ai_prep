import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChainTraceEvent:
    event: str
    chain: str
    latency_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ChainCallbackHandler:
    """Framework-independent callback handler — LangSmith benzeri trace mantığı."""

    def __init__(self) -> None:
        self.events: list[ChainTraceEvent] = []

    def on_chain_start(self, chain: str, inputs: dict[str, Any]) -> None:
        self.events.append(
            ChainTraceEvent(event="chain_start", chain=chain, metadata={"inputs": inputs})
        )

    def on_llm_end(self, chain: str, *, latency_ms: float, model: str, tokens: int) -> None:
        self.events.append(
            ChainTraceEvent(
                event="llm_end",
                chain=chain,
                latency_ms=latency_ms,
                metadata={"model": model, "tokens": tokens},
            )
        )

    def on_parse_success(self, chain: str, output: dict[str, Any]) -> None:
        self.events.append(
            ChainTraceEvent(event="parse_success", chain=chain, metadata={"output": output})
        )

    def on_parse_error(self, chain: str, error: str, raw_output: str) -> None:
        self.events.append(
            ChainTraceEvent(
                event="parse_error",
                chain=chain,
                metadata={"error": error, "raw_output": raw_output[:500]},
            )
        )

    def on_chain_end(self, chain: str, *, latency_ms: float) -> None:
        self.events.append(
            ChainTraceEvent(event="chain_end", chain=chain, latency_ms=latency_ms)
        )


class ChainTimer:
    def __init__(self) -> None:
        self._started = time.perf_counter()

    def elapsed_ms(self) -> float:
        return round((time.perf_counter() - self._started) * 1000, 2)
