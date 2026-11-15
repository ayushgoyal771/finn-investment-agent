"""Run checks with fresh, workspace-local scratch paths on Windows and Linux."""
import pathlib
import shutil
import subprocess
import sys
import uuid

root = pathlib.Path(__file__).resolve().parent.parent
scratch = root / "artifacts"
scratch.mkdir(exist_ok=True)
test_path = scratch / ("pytest-" + uuid.uuid4().hex[:10])
commands = [[sys.executable, "-m", "pytest", "-q", "--basetemp", str(test_path)],
            [sys.executable, "-m", "pip", "check"]]
if shutil.which("node"):
    commands.append(["node", "--check", "frontend/app.js"])
for command in commands:
    result = subprocess.run(command, cwd=root)
    if result.returncode:
        sys.exit(result.returncode)
print("All configured checks passed.")
