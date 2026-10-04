"""Fail-closed macOS Python isolation for untrusted policy-development tools.

Only runtime libraries and a fresh scratch directory are readable. Each call is
a fresh interpreter; neither the API key nor the parent environment is inherited.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time


class SandboxUnavailable(RuntimeError):
    pass


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    returncode: int
    elapsed_seconds: float
    timed_out: bool = False

    def to_dict(self):
        return asdict(self)


class PythonSandbox:
    def __init__(self, python_executable: str, scratch_parent: Path | None = None):
        self.python_executable = str(Path(python_executable).absolute())
        self.scratch_parent = scratch_parent
        self.sandbox_exec = shutil.which("sandbox-exec")
        if not self.sandbox_exec:
            raise SandboxUnavailable("OS sandbox-exec is unavailable; refusing unisolated execution")
        # Trusted runtime inspection only; the inspected code never comes from a model.
        probe = (
            "import json,sys,sysconfig,numpy,scipy;"
            "print(json.dumps(dict(executable=sys.executable,base=sys.base_prefix,"
            "stdlib=sysconfig.get_path('stdlib'),"
            "numpy=numpy.__file__,scipy=scipy.__file__)))"
        )
        try:
            p = subprocess.run([self.python_executable, "-I", "-c", probe],
                               capture_output=True, text=True, timeout=30, check=True)
            self.runtime = json.loads(p.stdout)
        except Exception as exc:
            raise SandboxUnavailable("Selected Python must provide NumPy and SciPy") from exc
        app_interpreter = Path(self.runtime["base"]).resolve() / "Resources/Python.app/Contents/MacOS/Python"
        self._runner = str(app_interpreter if app_interpreter.exists() else Path(self.python_executable).resolve())
        self._probed = False

    def _profile(self, scratch: Path) -> str:
        def quoted(p):
            return json.dumps(str(p))
        literals = {Path(self.python_executable), Path(self.python_executable).resolve(), Path(self._runner),
                    Path("/"), Path("/dev/null"), Path("/dev/urandom"), Path("/dev/random")}
        subpaths = {scratch.resolve(), Path("/usr/lib"), Path("/System/Library"),
                    Path("/System/Volumes/Preboot/Cryptexes/OS/usr/lib")}
        stdlib = Path(self.runtime["stdlib"]).resolve()
        literals.add(stdlib)
        # Do not grant the stdlib's site-packages subtree wholesale.
        for child in stdlib.iterdir():
            if child.name == "site-packages":
                continue
            (subpaths if child.is_dir() else literals).add(child.resolve())
        base = Path(self.runtime["base"]).resolve()
        for name in ("Python", "Resources/Info.plist"):
            literals.add(base / name)
        for name in ("numpy", "scipy"):
            package = Path(self.runtime[name]).resolve().parent
            literals.add(package.parent)
            subpaths.add(package)
            for sibling in package.parent.glob(name + "*.libs"):
                subpaths.add(sibling.resolve())
            for sibling in package.parent.glob(name + "*.dist-info"):
                subpaths.add(sibling.resolve())
        # Homebrew extension modules may depend on these public runtime libraries.
        for library in ("openssl@3", "libffi", "xz", "zstd", "bzip2", "gettext",
                        "readline", "sqlite", "mpdecimal", "gdbm", "ncurses"):
            p = Path("/opt/homebrew/opt") / library
            if p.exists():
                subpaths.add((p.resolve() / "lib"))
        reads = "\n".join("(allow file-read* (literal " + quoted(p) + "))" for p in sorted(literals))
        reads += "\n" + "\n".join("(allow file-read* (subpath " + quoted(p) + "))" for p in sorted(subpaths))
        return "\n".join([
            "(version 1)", "(deny default)", "(allow sysctl-read)",
            # Path traversal does not permit reading/listing directory contents.
            "(allow file-read-metadata)", reads,
            "(allow file-write* (subpath " + quoted(scratch.resolve()) + "))",
            "(allow file-write-data (literal \"/dev/null\"))",
            "(allow process-exec (literal " + quoted(Path(self.python_executable).resolve()) + "))",
            "(allow process-exec (literal " + quoted(self.python_executable) + "))",
            "(allow process-exec (literal " + quoted(self._runner) + "))",
        ])

    def run(self, code: str, timeout_seconds: float, max_output_bytes: int = 65536) -> SandboxResult:
        if not isinstance(code, str) or len(code.encode()) > 16_000_000:
            raise ValueError("Python source must be a string smaller than 16 MB")
        if not 1 <= max_output_bytes <= 16_777_216:
            raise ValueError("Output capture limit must be between 1 byte and 16 MiB")
        if timeout_seconds <= 0:
            raise ValueError("Python execution budget exhausted")
        with tempfile.TemporaryDirectory(prefix="baek-python-", dir=self.scratch_parent) as raw:
            scratch = Path(raw).resolve()
            os.chmod(scratch, 0o700)
            source = scratch / "tool.py"
            source.write_text(code)
            siteparents = sorted({str(Path(self.runtime[n]).resolve().parent.parent) for n in ("numpy", "scipy")})
            wrapper = scratch / "bootstrap.py"
            wrapper.write_text(
                "import sys, resource\n"
                "sys.path[:] = " + repr([str(Path(self.runtime["stdlib"]).resolve()),
                                          str(Path(self.runtime["stdlib"]).resolve() / "lib-dynload")] + siteparents) + "\n"
                "resource.setrlimit(resource.RLIMIT_FSIZE, (16777216, 16777216))\n"
                "resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))\n"
                f"resource.setrlimit(resource.RLIMIT_CPU, ({math.ceil(timeout_seconds) + 1}, {math.ceil(timeout_seconds) + 1}))\n"
                f"exec(compile(open({str(source)!r}).read(), 'tool.py', 'exec'), {{'__name__': '__main__'}})\n"
            )
            profile = scratch / "sandbox.sb"
            profile.write_text(self._profile(scratch))
            env = {"HOME": str(scratch), "TMPDIR": str(scratch), "PATH": "/usr/bin:/bin",
                   "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "OPENBLAS_NUM_THREADS": "1",
                   "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
            started = time.monotonic()
            timed_out = False
            with (scratch / "stdout").open("wb") as out, (scratch / "stderr").open("wb") as err:
                proc = subprocess.Popen([self.sandbox_exec, "-f", str(profile), self._runner,
                                         "-I", "-B", "-S", str(wrapper)], cwd=scratch, env=env,
                                        stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
                try:
                    proc.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
            elapsed = time.monotonic() - started
            def captured(name):
                with (scratch / name).open("rb") as f:
                    data = f.read(max_output_bytes + 1)
                return data[:max_output_bytes].decode("utf-8", errors="replace") + ("\n[output truncated]" if len(data) > max_output_bytes else "")
            return SandboxResult(captured("stdout"), captured("stderr"), proc.returncode, elapsed, timed_out)

    def probe(self, forbidden_path: str | None = None) -> SandboxResult:
        """Check numeric imports, secret-file denial and network denial before paid work."""
        forbidden_path = forbidden_path or str(Path(__file__).resolve())
        code = (
            "import os,socket,numpy,scipy\n"
            "from scipy import optimize,stats\n"
            "assert numpy.isfinite(optimize.minimize_scalar(lambda x:(x-2)**2).fun)\n"
            f"try:\n open({forbidden_path!r}).read()\nexcept PermissionError:\n pass\nelse:\n raise AssertionError('repository readable')\n"
            "assert not any(('KEY' in k or 'TOKEN' in k or 'SECRET' in k) for k in os.environ)\n"
            "try:\n socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect(('127.0.0.1',9))\nexcept PermissionError:\n pass\nelse:\n raise AssertionError('network connection permitted')\n"
            "print('sandbox isolation verified')\n"
        )
        result = self.run(code, 30)
        if result.returncode != 0 or "sandbox isolation verified" not in result.stdout:
            raise SandboxUnavailable("OS sandbox isolation probe failed: " + result.stderr[:2000])
        self._probed = True
        return result
