"""Per-worker resident-memory guard for the eight-GiB experiment machine.

Mixin for the existing isolated numerical sandboxes. This monitors resident
memory, not virtual address space; it preserves the underlying OS read/network
isolation and kills the entire worker process group on an explicit violation.
"""
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

from ..baek_comparison.sandbox import SandboxResult


@dataclass
class GuardedSandboxResult(SandboxResult):
    memory_guard_exceeded: bool = False
    memory_limit_bytes: int = 1024 ** 3
    observed_peak_rss_bytes: int = 0

    def to_dict(self):
        return asdict(self)


class MemoryGuardMixin:
    """Place before NumericalSandbox in the subclass's inheritance list."""
    memory_limit_bytes = 1024 ** 3
    memory_poll_seconds = 0.1

    def run(self, code, timeout_seconds, max_output_bytes=65536):
        if not isinstance(code, str) or len(code.encode()) > 16_000_000:
            raise ValueError("Python source must be a string smaller than 16 MB")
        if not 1 <= max_output_bytes <= 16_777_216:
            raise ValueError("Output capture limit must be between one byte and 16 MiB")
        if timeout_seconds <= 0:
            raise ValueError("Python execution budget exhausted")
        if self.memory_limit_bytes <= 0:
            raise ValueError("Resident-memory guard must be positive")
        with tempfile.TemporaryDirectory(prefix="inventory-guarded-", dir=self.scratch_parent) as raw:
            scratch = Path(raw).resolve()
            os.chmod(scratch, 0o700)
            source = scratch / "tool.py"
            source.write_text(code)
            stdlib = Path(self.runtime["stdlib"]).resolve()
            siteparents = sorted({str(Path(self.runtime[n]).resolve().parent.parent) for n in ("numpy", "scipy")})
            wrapper = scratch / "bootstrap.py"
            wrapper.write_text(
                "import sys,resource\n"
                + "sys.path[:] = " + repr([str(stdlib), str(stdlib / "lib-dynload")] + siteparents) + "\n"
                + "resource.setrlimit(resource.RLIMIT_FSIZE,(16777216,16777216))\n"
                + "resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))\n"
                + f"resource.setrlimit(resource.RLIMIT_CPU,({math.ceil(timeout_seconds)+1},{math.ceil(timeout_seconds)+1}))\n"
                + f"exec(compile(open({str(source)!r}).read(),'tool.py','exec'),{{'__name__':'__main__'}})\n"
            )
            profile = scratch / "sandbox.sb"
            profile.write_text(self._profile(scratch))
            env = {"HOME": str(scratch), "TMPDIR": str(scratch), "PATH": "/usr/bin:/bin",
                   "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "OPENBLAS_NUM_THREADS": "1",
                   "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
            start = time.monotonic()
            timed_out = memory_exceeded = False
            peak_rss = 0
            with (scratch / "stdout").open("wb") as stdout, (scratch / "stderr").open("wb") as stderr:
                proc = subprocess.Popen([self.sandbox_exec, "-f", str(profile), self._runner,
                                         "-I", "-B", "-S", str(wrapper)],
                                        cwd=scratch, env=env, stdin=subprocess.DEVNULL,
                                        stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    while proc.poll() is None:
                        if time.monotonic() - start >= timeout_seconds:
                            timed_out = True
                            break
                        sampled = subprocess.run(["/bin/ps", "-o", "rss=", "-p", str(proc.pid)],
                                                 capture_output=True, text=True, timeout=3)
                        if sampled.returncode == 0 and sampled.stdout.strip():
                            # macOS ps RSS is expressed in KiB.
                            rss = int(sampled.stdout.strip().split()[0]) * 1024
                            peak_rss = max(peak_rss, rss)
                            if rss > self.memory_limit_bytes:
                                memory_exceeded = True
                                break
                        time.sleep(min(self.memory_poll_seconds,
                                       max(0., timeout_seconds-(time.monotonic()-start))))
                finally:
                    if proc.poll() is None:
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    proc.wait()
            def captured(name):
                with (scratch / name).open("rb") as handle:
                    data = handle.read(max_output_bytes + 1)
                return data[:max_output_bytes].decode("utf-8", errors="replace") + (
                    "\n[output truncated]" if len(data) > max_output_bytes else "")
            error = captured("stderr")
            if memory_exceeded:
                error += (f"\nMemory guard exceeded: observed resident bytes {peak_rss}; "
                          f"per-worker limit {self.memory_limit_bytes}. Worker group terminated.\n")
            return GuardedSandboxResult(captured("stdout"), error, proc.returncode,
                                        time.monotonic()-start, timed_out,
                                        memory_exceeded, int(self.memory_limit_bytes), peak_rss)
