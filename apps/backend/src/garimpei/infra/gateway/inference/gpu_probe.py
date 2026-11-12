import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Event, Thread


class NvidiaGpuProbe:
    @contextmanager
    def measure(self) -> Iterator[list[dict[str, object]]]:
        samples: list[dict[str, object]] = []
        stopped = Event()
        thread = Thread(target=self._sample, args=(stopped, samples), daemon=True)
        thread.start()
        try:
            yield samples
        finally:
            stopped.set()
            thread.join(timeout=1.1)

    def _sample(self, stopped: Event, samples: list[dict[str, object]]) -> None:
        while not stopped.is_set() and len(samples) < 721:
            self._one_sample(samples)
            stopped.wait(0.25)

    @staticmethod
    def _one_sample(samples: list[dict[str, object]]) -> None:
        try:
            value = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=1,
            )
            memory, utilization = value.stdout.strip().splitlines()[0].split(",")
            samples.append(
                {
                    "monotonic": time.monotonic(),
                    "memory_mib": int(memory),
                    "utilization_percent": int(utilization),
                    "scope": "host",
                }
            )
        except (OSError, subprocess.TimeoutExpired, ValueError, IndexError):
            samples.append({"error": "gpu_probe_unavailable"})
