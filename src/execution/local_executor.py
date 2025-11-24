"""Local code execution using subprocess (no Docker, no cloud)"""
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any
import re


class LocalCodeExecutor:
    """
    Execute code locally using subprocess

    No external dependencies - runs directly on the host system.
    Creates temporary workspaces for isolated execution.
    """

    def __init__(self, workspace_dir: str = "data/test_workspaces"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def execute_python_tests(self, code: str, tests: str) -> Dict[str, Any]:
        """
        Execute Python tests using pytest

        Args:
            code: The Python code to test
            tests: The test code (pytest format)

        Returns:
            Dictionary with test results
        """
        # Create temp workspace
        with tempfile.TemporaryDirectory(dir=self.workspace_dir) as tmpdir:
            tmpdir = Path(tmpdir)

            # Write code file
            code_file = tmpdir / "solution.py"
            with open(code_file, 'w') as f:
                f.write(code)

            # Write test file
            test_file = tmpdir / "test_solution.py"
            with open(test_file, 'w') as f:
                # Ensure test imports the solution
                test_content = f"from solution import *\n\n{tests}"
                f.write(test_content)

            # Run pytest
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "-v", "--tb=short", "--no-header"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=tmpdir
                )

                return self._parse_pytest_output(result)

            except subprocess.TimeoutExpired:
                return {
                    "passed": 0,
                    "failed": 1,
                    "errors": 1,
                    "failures": [{
                        "test_name": "execution",
                        "error_message": "Test execution timed out (30s)",
                        "stack_trace": "",
                        "line_number": 0
                    }],
                    "stdout": "",
                    "stderr": "Timeout after 30 seconds",
                    "returncode": -1
                }

            except FileNotFoundError:
                return {
                    "passed": 0,
                    "failed": 1,
                    "errors": 1,
                    "failures": [{
                        "test_name": "execution",
                        "error_message": "pytest not installed. Run: pip install pytest",
                        "stack_trace": "",
                        "line_number": 0
                    }],
                    "stdout": "",
                    "stderr": "pytest not found",
                    "returncode": -1
                }

            except Exception as e:
                return {
                    "passed": 0,
                    "failed": 1,
                    "errors": 1,
                    "failures": [{
                        "test_name": "execution",
                        "error_message": str(e),
                        "stack_trace": "",
                        "line_number": 0
                    }],
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1
                }

    def execute_code_simple(self, language: str, code: str) -> Dict[str, Any]:
        """
        Simple code execution for syntax validation

        Args:
            language: Programming language
            code: Code to execute

        Returns:
            Execution result
        """
        if language == "python":
            try:
                # Write to temp file and run
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.py',
                    dir=self.workspace_dir,
                    delete=False
                ) as f:
                    f.write(code)
                    temp_file = f.name

                result = subprocess.run(
                    ["python", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                Path(temp_file).unlink()  # Clean up

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }

            except Exception as e:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1
                }

        else:
            raise NotImplementedError(f"Language {language} not supported yet")

    def _parse_pytest_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """
        Parse pytest output to extract test results

        Args:
            result: subprocess result from pytest

        Returns:
            Parsed test results
        """
        output = result.stdout + "\n" + result.stderr

        # Count test results
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        errors = output.count(" ERROR")

        # Extract failure details
        failures = []

        if failed > 0 or errors > 0:
            # Try to parse failure information
            failures = self._extract_pytest_failures(output)

        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "failures": failures,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    def _extract_pytest_failures(self, output: str) -> list[Dict[str, Any]]:
        """
        Extract failure details from pytest output

        Args:
            output: pytest stdout/stderr

        Returns:
            List of failure details
        """
        failures = []
        lines = output.split('\n')

        current_test = None
        collecting_error = False
        error_lines = []

        for line in lines:
            # Match test failure line
            if 'FAILED' in line or 'ERROR' in line:
                if current_test and error_lines:
                    failures.append({
                        "test_name": current_test,
                        "error_message": '\n'.join(error_lines),
                        "stack_trace": "",
                        "line_number": 0
                    })

                # Extract test name
                match = re.search(r'test_\w+', line)
                current_test = match.group(0) if match else "unknown_test"
                error_lines = []
                collecting_error = True

            elif collecting_error:
                # Collect error message lines
                if line.strip() and not line.startswith('='):
                    error_lines.append(line.strip())

                # Stop collecting at separator or next test
                if line.startswith('=') or line.startswith('_'):
                    collecting_error = False

        # Add last failure
        if current_test and error_lines:
            failures.append({
                "test_name": current_test,
                "error_message": '\n'.join(error_lines),
                "stack_trace": "",
                "line_number": 0
            })

        # If we didn't extract anything, create generic failure
        if not failures and ('FAILED' in output or 'ERROR' in output):
            failures.append({
                "test_name": "unknown",
                "error_message": "Test execution failed. See logs for details.",
                "stack_trace": output[-500:],  # Last 500 chars
                "line_number": 0
            })

        return failures
