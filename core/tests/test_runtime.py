import shutil
import unittest

from django.test import SimpleTestCase

from core.services.runtime_executor import ExecutionService


class RuntimeExecutorTests(SimpleTestCase):
    def setUp(self):
        self.executor = ExecutionService(timeout_seconds=1, compile_timeout_seconds=5)

    def test_python_execution_success(self):
        result = self.executor.run("python", 'print("hello runtime")')
        self.assertEqual(result.status, "success")
        self.assertIn("hello runtime", result.stdout)

    def test_rejects_python_file_write(self):
        result = self.executor.run("python", 'open("evil.txt", "w").write("bad")')
        self.assertEqual(result.status, "rejected")
        self.assertIn("unsafe", result.rejection_reason)

    def test_rejects_python_network_access(self):
        result = self.executor.run("python", "import socket\nsocket.socket()")
        self.assertEqual(result.status, "rejected")

    def test_rejects_python_import_os(self):
        result = self.executor.run("python", "__import__('os')")
        self.assertEqual(result.status, "rejected")

    def test_rejects_python_dynamic_module_access(self):
        result = self.executor.run("python", "import importlib\nimportlib.import_module('os')")
        self.assertEqual(result.status, "rejected")

    def test_rejects_python_os_and_subprocess_access(self):
        payloads = {
            "os.listdir": "import os\nos.listdir('.')",
            "os.system": "import os\nos.system('echo hi')",
            "subprocess.call": "import subprocess\nsubprocess.call(['echo', 'hi'])",
        }
        for name, code in payloads.items():
            with self.subTest(name=name):
                result = self.executor.run("python", code)
                self.assertEqual(result.status, "rejected")

    def test_rejects_python_sys_access(self):
        result = self.executor.run("python", "import sys\nsys.version")
        self.assertEqual(result.status, "rejected")

    def test_rejects_python_eval_and_exec(self):
        for code in ("eval('1+1')", "exec('print(1)')"):
            with self.subTest(code=code):
                result = self.executor.run("python", code)
                self.assertEqual(result.status, "rejected")

    def test_allows_safe_builtins(self):
        result = self.executor.run("python", "print(len(list(range(3))))")
        self.assertEqual(result.status, "success")
        self.assertIn("3", result.stdout)

    def test_rejects_indirect_builtin_access(self):
        result = self.executor.run("python", 'getattr(__builtins__, "__import__")("os")')
        self.assertEqual(result.status, "rejected")

    def test_rejects_globals_bypass_attempts(self):
        """Test that __globals__ introspection bypasses are blocked."""
        bypass_attempts = {
            "__globals__ via lambda": "(lambda:0).__globals__['__builtins__']",
            "__globals__ via function": "def f(): pass\nf.__globals__",
            "__globals__ via getattr": "getattr((lambda:0), '__globals__')",
            "__dict__ access": "print.__dict__",
            "__class__ access": "().__class__",
            "__mro__ access": "[].__class__.__mro__",
            "__subclasses__ bypass": "[].__class__.__bases__[0].__subclasses__()",
        }
        for name, code in bypass_attempts.items():
            with self.subTest(bypass=name):
                result = self.executor.run("python", code)
                self.assertEqual(result.status, "rejected", f"Bypass {name} was not rejected")
                self.assertIn("unsafe", result.rejection_reason)

    def test_timeout_is_enforced(self):
        result = self.executor.run("python", "while True:\n    pass")
        self.assertEqual(result.status, "timeout")
        self.assertTrue(result.timed_out)

    def test_runtime_error_reporting(self):
        result = self.executor.run("python", "print(1/0)")
        self.assertEqual(result.status, "runtime_error")
        self.assertIn("ZeroDivisionError", result.stderr)

    @unittest.skipUnless(shutil.which("gcc"), "gcc required for C execution tests")
    def test_c_execution_success(self):
        code = '#include <stdio.h>\nint main(){printf("C OK\\n");return 0;}'
        result = self.executor.run("c", code)
        self.assertEqual(result.status, "success")
        self.assertIn("C OK", result.stdout)

    @unittest.skipUnless(shutil.which("gcc"), "gcc required for C execution tests")
    def test_c_rejects_file_write(self):
        code = '#include <stdio.h>\nint main(){FILE *f=fopen("x.txt","w");return f==NULL;}'
        result = self.executor.run("c", code)
        self.assertEqual(result.status, "rejected")

    @unittest.skipUnless(shutil.which("g++"), "g++ required for C++ execution tests")
    def test_cpp_execution_success(self):
        code = '#include <iostream>\nint main(){std::cout<<"CPP OK"<<std::endl;return 0;}'
        result = self.executor.run("cpp", code)
        self.assertEqual(result.status, "success")
        self.assertIn("CPP OK", result.stdout)
