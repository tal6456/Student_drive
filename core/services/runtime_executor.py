"""
Runtime execution service with security controls.

Security considerations:
- Runs code in an isolated workspace under runtime_sandbox.
- Sanitizes environment variables to avoid leaking secrets.
- Applies strict timeouts to prevent infinite loops.
- Best-effort resource limits (CPU/memory/file size) on POSIX systems.
 - Enforces a strict Python allowlist for builtins and modules.
- Uses Python isolated mode (-I) and disables bytecode writes (-B).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"python", "c", "cpp"}

PYTHON_REJECTION_REASON = "Blocked potentially unsafe operation (sandbox allowlist)."

# Allowlist-only Python execution. Any name/module not explicitly permitted is rejected.
SAFE_BUILTINS = {
    "abs",
    "all",
    "any",
    "bool",
    "dict",
    "enumerate",
    "float",
    "int",
    "len",
    "list",
    "max",
    "min",
    "print",
    "range",
    "reversed",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
}
ALLOWED_BUILTINS = SAFE_BUILTINS
ALLOWED_MODULES: set[str] = set()
PYTHON_BLOCKED_IDENTIFIERS = {
    "__bases__",
    "__builtins__",
    "__class__",
    "__dict__",
    "__globals__",
    "__import__",
    "__loader__",
    "__mro__",
    "__subclasses__",
    "compile",
    "eval",
    "exec",
    "os",
    "subprocess",
    "sys",
}

C_DENYLIST = [
    r"#include\s*<sys/socket\.h>",
    r"#include\s*<winsock2\.h>",
    r"#include\s*<fstream>",
    r"\bsocket\s*\(",
    r"\bconnect\s*\(",
    r"\bfopen\s*\(",
    r"\bfreopen\s*\(",
    r"\bopen\s*\(",
    r"\bpopen\s*\(",
    r"\bsystem\s*\(",
    r"\bfork\s*\(",
    r"\bexec\w*\s*\(",
    r"\bCreateFile\w*\s*\(",
    r"\bWinExec\s*\(",
    r"\bShellExecute\w*\s*\(",
    r"\bWSAStartup\s*\(",
]

CPP_DENYLIST = C_DENYLIST + [
    r"\bstd::ofstream\b",
    r"\bstd::ifstream\b",
    r"\bstd::fstream\b",
]


@dataclass
class ExecutionResult:
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    timed_out: bool = False
    compile_stdout: str = ""
    compile_stderr: str = ""
    compile_exit_code: Optional[int] = None
    duration_ms: float = 0.0
    rejection_reason: Optional[str] = None


class ExecutionService:
    def __init__(
        self,
        *,
        timeout_seconds: int = 5,
        compile_timeout_seconds: int = 10,
        memory_limit_mb: int = 128,
        cpu_time_seconds: int = 2,
        max_output_chars: int = 20_000,
        base_dir: Optional[Path] = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.compile_timeout_seconds = compile_timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.cpu_time_seconds = cpu_time_seconds
        self.max_output_chars = max_output_chars
        self.base_dir = base_dir or self._default_base_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._c_compiler = shutil.which("gcc")
        self._cpp_compiler = shutil.which("g++")

    def run(self, language: str, code: str, *, input_data: str = "") -> ExecutionResult:
        start_time = time.monotonic()
        language = language.lower().strip()
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        rejection_reason = self._validate_code(language, code)
        if rejection_reason:
            logger.warning("Execution rejected for %s: %s", language, rejection_reason)
            return ExecutionResult(
                status="rejected",
                rejection_reason=rejection_reason,
                duration_ms=self._elapsed_ms(start_time),
            )

        workspace = Path(tempfile.mkdtemp(prefix="runtime_", dir=self.base_dir))
        try:
            if language == "python":
                source_path = workspace / "user_code.py"
                source_path.write_text(code, encoding="utf-8")
                runner_path = workspace / "runner.py"
                runner_path.write_text(
                    self._python_runner_source(source_path.name),
                    encoding="utf-8",
                )
                command = [
                    sys.executable,
                    "-I",
                    "-B",
                    str(runner_path),
                ]
                result = self._execute(
                    command,
                    workspace,
                    input_data=input_data,
                    timeout_seconds=self.timeout_seconds,
                )
            else:
                compiler = self._c_compiler if language == "c" else self._cpp_compiler
                if not compiler:
                    logger.error("Compiler missing for %s", language)
                    return ExecutionResult(
                        status="compile_error",
                        compile_stderr="Compiler not available on this host.",
                        duration_ms=self._elapsed_ms(start_time),
                    )

                extension = "c" if language == "c" else "cpp"
                source_path = workspace / f"main.{extension}"
                source_path.write_text(code, encoding="utf-8")
                output_path = workspace / "program"
                compile_command = self._compile_command(language, compiler, source_path, output_path)
                compile_result = self._execute(
                    compile_command,
                    workspace,
                    timeout_seconds=self.compile_timeout_seconds,
                    is_compile=True,
                )
                if compile_result.status != "success":
                    return ExecutionResult(
                        status="compile_error",
                        compile_stdout=compile_result.stdout,
                        compile_stderr=compile_result.stderr,
                        compile_exit_code=compile_result.exit_code,
                        timed_out=compile_result.timed_out,
                        duration_ms=self._elapsed_ms(start_time),
                    )

                output_path = self._apply_executable_suffix(output_path)
                command = [str(output_path)]
                result = self._execute(
                    command,
                    workspace,
                    input_data=input_data,
                    timeout_seconds=self.timeout_seconds,
                )

            result.duration_ms = self._elapsed_ms(start_time)
            logger.info(
                "Execution finished: language=%s status=%s duration_ms=%.2f",
                language,
                result.status,
                result.duration_ms,
            )
            return result
        finally:
            self._cleanup_workspace(workspace)

    def _validate_code(self, language: str, code: str) -> Optional[str]:
        if language == "python":
            return self._validate_python_code(code)
        patterns = C_DENYLIST if language == "c" else CPP_DENYLIST
        for pattern in patterns:
            if re.search(pattern, code, flags=re.IGNORECASE):
                return "Blocked potentially unsafe operation (filesystem/network/system access)."
        return None

    def _validate_python_code(self, code: str) -> Optional[str]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "Invalid Python syntax."
        validator = _PythonAllowlistValidator(
            allowed_builtins=ALLOWED_BUILTINS,
            allowed_modules=ALLOWED_MODULES,
            blocked_identifiers=PYTHON_BLOCKED_IDENTIFIERS,
        )
        validator.visit(tree)
        return validator.rejection_reason

    def _execute(
        self,
        command: Iterable[str],
        workspace: Path,
        *,
        input_data: str = "",
        timeout_seconds: int,
        is_compile: bool = False,
    ) -> ExecutionResult:
        env = self._sanitized_env(workspace)
        if not is_compile:
            self._make_readonly(workspace)

        process = subprocess.Popen(
            list(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(workspace),
            env=env,
            start_new_session=True,
            preexec_fn=self._posix_limits(),
        )
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            self._terminate_process(process)
            return ExecutionResult(
                status="timeout",
                stdout="",
                stderr="Execution timed out.",
                timed_out=True,
            )
        finally:
            if not is_compile:
                self._make_writable(workspace)

        stdout = self._trim_output(stdout)
        stderr = self._trim_output(stderr)
        status = "success" if process.returncode == 0 else "runtime_error"
        return ExecutionResult(
            status=status,
            stdout=stdout,
            stderr=stderr,
            exit_code=process.returncode,
        )

    def _compile_command(
        self,
        language: str,
        compiler: str,
        source_path: Path,
        output_path: Path,
    ) -> list[str]:
        if language == "c":
            return [compiler, str(source_path), "-std=c11", "-O2", "-pipe", "-o", str(output_path)]
        return [compiler, str(source_path), "-std=c++17", "-O2", "-pipe", "-o", str(output_path)]

    def _sanitized_env(self, workspace: Path) -> dict[str, str]:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "HOME": str(workspace),
            "USERPROFILE": str(workspace),
        }
        return env

    @staticmethod
    def _python_runner_source(code_filename: str) -> str:
        safe_builtin_names = sorted(SAFE_BUILTINS)
        return "\n".join(
            [
                "import builtins",
                "import types",
                f"SAFE_BUILTINS = {safe_builtin_names!r}",
                "safe_builtins = {name: getattr(builtins, name) for name in SAFE_BUILTINS}",
                "safe_globals = {'__builtins__': types.MappingProxyType(safe_builtins)}",
                "safe_locals = {}",
                f"with open({code_filename!r}, 'r', encoding='utf-8') as handle:",
                "    code = handle.read()",
                "exec(compile(code, '<sandbox>', 'exec'), safe_globals, safe_locals)",
            ]
        )

    def _posix_limits(self):
        if os.name == "nt":
            return None
        try:
            import resource
        except ImportError:  # pragma: no cover - resource unavailable
            return None

        memory_bytes = self.memory_limit_mb * 1024 * 1024

        def _apply_limits():
            resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_time_seconds, self.cpu_time_seconds))
            if hasattr(resource, "RLIMIT_AS"):
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            if hasattr(resource, "RLIMIT_FSIZE"):
                resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
            if hasattr(resource, "RLIMIT_CORE"):
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            if hasattr(resource, "RLIMIT_NPROC"):
                resource.setrlimit(resource.RLIMIT_NPROC, (4, 4))

        return _apply_limits

    def _make_readonly(self, workspace: Path) -> None:
        for root, dirs, files in os.walk(workspace):
            for name in files:
                os.chmod(Path(root) / name, stat.S_IREAD | stat.S_IEXEC)
            for name in dirs:
                os.chmod(Path(root) / name, stat.S_IREAD | stat.S_IEXEC)
        os.chmod(workspace, stat.S_IREAD | stat.S_IEXEC)

    def _make_writable(self, workspace: Path) -> None:
        for root, dirs, files in os.walk(workspace):
            for name in files:
                os.chmod(Path(root) / name, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
            for name in dirs:
                os.chmod(Path(root) / name, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        os.chmod(workspace, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)

    def _cleanup_workspace(self, workspace: Path) -> None:
        if not workspace.exists():
            return

        def _on_error(func, path, _exc):
            try:
                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                func(path)
            except OSError:
                logger.warning("Failed cleaning runtime workspace: %s", path)

        shutil.rmtree(workspace, onerror=_on_error)

    def _apply_executable_suffix(self, output_path: Path) -> Path:
        if os.name == "nt":
            exe_path = output_path.with_suffix(".exe")
            if exe_path.exists():
                return exe_path
        return output_path

    def _terminate_process(self, process: subprocess.Popen) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
        except Exception:
            process.kill()

    def _trim_output(self, output: str) -> str:
        if len(output) <= self.max_output_chars:
            return output
        return output[: self.max_output_chars] + "\n...[output truncated]"

    def _default_base_dir(self) -> Path:
        return Path(__file__).resolve().parents[3] / "runtime_sandbox"

    def _elapsed_ms(self, start_time: float) -> float:
        return (time.monotonic() - start_time) * 1000


class _PythonAllowlistValidator(ast.NodeVisitor):
    def __init__(
        self,
        *,
        allowed_builtins: set[str],
        allowed_modules: set[str],
        blocked_identifiers: set[str],
    ) -> None:
        self.allowed_builtins = allowed_builtins
        self.allowed_modules = allowed_modules
        self.blocked_identifiers = blocked_identifiers
        self.rejection_reason: Optional[str] = None
        self._scopes: list[_Scope] = [_Scope()]

    def visit(self, node):
        if self.rejection_reason:
            return None
        return super().visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root_name = alias.name.split(".")[0]
            if root_name not in self.allowed_modules:
                self._reject()
                return
            self._current_scope().define(alias.asname or root_name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root_name = module.split(".")[0]
        if root_name not in self.allowed_modules:
            self._reject()
            return
        for alias in node.names:
            self._current_scope().define(alias.asname or alias.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_scope().define(node.name)
        self._push_scope()
        self._define_args(node.args)
        self.generic_visit(node)
        self._pop_scope()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._current_scope().define(node.name)
        self._push_scope()
        self.generic_visit(node)
        self._pop_scope()

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._push_scope()
        self._define_args(node.args)
        self.generic_visit(node)
        self._pop_scope()

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_comprehension(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_comprehension(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_comprehension(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._current_scope().define(node.name)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        for name in node.names:
            self._current_scope().define(name)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        for name in node.names:
            self._current_scope().define(name)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self.blocked_identifiers:
            self._reject()
            return
        if isinstance(node.ctx, ast.Store):
            self._current_scope().define(node.id)
            return
        if isinstance(node.ctx, ast.Load):
            if not self._current_scope().is_defined(node.id) and node.id not in self.allowed_builtins:
                self._reject()
                return
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in self.blocked_identifiers:
            self._reject()
            return
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_getattr_call(node):
            attr_name = node.args[1]
            if isinstance(attr_name, ast.Constant) and attr_name.value in self.blocked_identifiers:
                self._reject()
                return
        self.generic_visit(node)

    def _visit_comprehension(self, node: ast.AST) -> None:
        self._push_scope()
        self.generic_visit(node)
        self._pop_scope()

    def _define_args(self, args: ast.arguments) -> None:
        for arg in args.posonlyargs + args.args + args.kwonlyargs:
            self._current_scope().define(arg.arg)
        if args.vararg:
            self._current_scope().define(args.vararg.arg)
        if args.kwarg:
            self._current_scope().define(args.kwarg.arg)

    def _current_scope(self) -> "_Scope":
        return self._scopes[-1]

    def _push_scope(self) -> None:
        self._scopes.append(_Scope(self._current_scope()))

    def _pop_scope(self) -> None:
        self._scopes.pop()

    def _reject(self) -> None:
        if not self.rejection_reason:
            self.rejection_reason = PYTHON_REJECTION_REASON

    @staticmethod
    def _is_getattr_call(node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Name):
            return False
        return node.func.id == "getattr" and len(node.args) >= 2


class _Scope:
    def __init__(self, parent: Optional["_Scope"] = None) -> None:
        self.parent = parent
        self.defined: set[str] = set()

    def define(self, name: str) -> None:
        self.defined.add(name)

    def is_defined(self, name: str) -> bool:
        if name in self.defined:
            return True
        return self.parent.is_defined(name) if self.parent else False
