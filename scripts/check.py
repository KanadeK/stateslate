"""Run StateSlate's complete local, CI, and release acceptance gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import cast
from zipfile import ZipFile

ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "examples"
DEMO = EXAMPLES / "moonlit-letter.json"
COMMITTED_DEMO = ROOT / "docs" / "demo"
INVALID_EXAMPLES = {
    "invalid-duplicate-order.json": "DUPLICATE_STORY_ORDER",
    "invalid-unknown-track.json": "UNKNOWN_TRACK",
    "invalid-transition-mismatch.json": "TRANSITION_MISMATCH",
}
ARTIFACT_NAMES = {
    "continuity.json",
    "report.html",
    "reset-checklist.md",
    "shoot-plan.csv",
    "timeline.svg",
}
ENVIRONMENT = os.environ.copy()
ENVIRONMENT["PYTHONUTF8"] = "1"
ENVIRONMENT["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
ENVIRONMENT.setdefault("UV_CACHE_DIR", str(ROOT / ".uv-cache"))


def run(
    command: Sequence[str], *, expected: int = 0, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(command)}", flush=True)
    result = subprocess.run(
        list(command),
        cwd=ROOT,
        env=ENVIRONMENT,
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode != expected:
        if capture:
            print(result.stdout, end="", file=sys.stdout)
            print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(
            f"command exited {result.returncode}; expected {expected}: {' '.join(command)}"
        )
    return result


def project_version() -> str:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    return cast(str, project["version"])


def check_runtime_dependencies() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    dependencies = cast(list[object], project["dependencies"])
    if dependencies:
        raise SystemExit(f"runtime dependencies must remain empty: {dependencies}")


def assert_artifact_set(directory: Path) -> None:
    actual = {path.name for path in directory.iterdir()}
    if actual != ARTIFACT_NAMES:
        raise SystemExit(f"unexpected artifacts in {directory}: {sorted(actual)}")


def compare_artifacts(actual: Path, expected: Path) -> None:
    assert_artifact_set(actual)
    assert_artifact_set(expected)
    for name in sorted(ARTIFACT_NAMES):
        if (actual / name).read_bytes() != (expected / name).read_bytes():
            raise SystemExit(f"generated {name} differs from the committed demo")


def load_report(directory: Path) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((directory / "continuity.json").read_text(encoding="utf-8")),
    )


def exercise_examples(temporary: Path) -> None:
    python = sys.executable
    source_output = temporary / "source-example"
    demo_output = temporary / "built-in-demo"
    gated_output = temporary / "risk-gated"

    run([python, "-m", "stateslate", "validate", str(DEMO)])
    run([python, "-m", "stateslate", "compile", str(DEMO), "--out", str(source_output)])
    compare_artifacts(source_output, COMMITTED_DEMO)
    report = load_report(source_output)
    expected_summary = {
        "high_risk_count": 2,
        "medium_risk_count": 2,
        "prepare_count": 3,
        "reset_count": 3,
        "scene_count": 4,
        "track_count": 3,
    }
    if report["summary"] != expected_summary:
        raise SystemExit(f"demo summary changed unexpectedly: {report['summary']}")

    run([python, "-m", "stateslate", "demo", "--out", str(demo_output)])
    compare_artifacts(demo_output, COMMITTED_DEMO)
    gated = run(
        [
            python,
            "-m",
            "stateslate",
            "compile",
            str(DEMO),
            "--out",
            str(gated_output),
            "--fail-on",
            "high",
        ],
        expected=1,
        capture=True,
    )
    if "RISK GATE" not in gated.stderr:
        raise SystemExit("risk gate did not emit its stable diagnostic")
    compare_artifacts(gated_output, COMMITTED_DEMO)

    for index, (name, code) in enumerate(INVALID_EXAMPLES.items()):
        output = temporary / f"invalid-{index}"
        result = run(
            [python, "-m", "stateslate", "compile", str(EXAMPLES / name), "--out", str(output)],
            expected=2,
            capture=True,
        )
        if output.exists() or code not in result.stderr or "Repair:" not in result.stderr:
            raise SystemExit(f"blocking example did not preserve its contract: {name}")

    existing = temporary / "existing-output"
    existing.mkdir()
    sentinel = existing / "owner.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    refusal = run(
        [python, "-m", "stateslate", "compile", str(DEMO), "--out", str(existing)],
        expected=2,
        capture=True,
    )
    if "OUTPUT_EXISTS" not in refusal.stderr or sentinel.read_text(encoding="utf-8") != "preserve":
        raise SystemExit("existing output refusal did not preserve owner data")


def executable_in(virtual_environment: Path, name: str) -> Path:
    if os.name == "nt":
        return virtual_environment / "Scripts" / f"{name}.exe"
    return virtual_environment / "bin" / name


def python_in(virtual_environment: Path) -> Path:
    if os.name == "nt":
        return virtual_environment / "Scripts" / "python"
    return virtual_environment / "bin" / "python"


def verify_checksums(directory: Path) -> None:
    lines = (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    names: list[str] = []
    for line in lines:
        expected, name = line.split("  ", 1)
        names.append(name)
        actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"checksum mismatch for {name}")
    expected_names = sorted(path.name for path in directory.iterdir() if path.name != "SHA256SUMS")
    if names != expected_names:
        raise SystemExit(f"checksum manifest names differ: {names} != {expected_names}")


def exercise_package(temporary: Path) -> None:
    version = project_version()
    distribution = temporary / "dist"
    release = temporary / "release"
    run(
        [
            "uv",
            "build",
            "--no-sources",
            "--clear",
            "--no-create-gitignore",
            "--out-dir",
            str(distribution),
        ]
    )
    expected_distribution = {
        f"stateslate-{version}-py3-none-any.whl",
        f"stateslate-{version}.tar.gz",
    }
    if {path.name for path in distribution.iterdir()} != expected_distribution:
        raise SystemExit("build did not produce the exact wheel and sdist pair")

    wheel = distribution / f"stateslate-{version}-py3-none-any.whl"
    with ZipFile(wheel) as archive:
        names = set(archive.namelist())
        required = {
            "stateslate/__init__.py",
            "stateslate/__main__.py",
            "stateslate/cli.py",
            "stateslate/compiler.py",
            "stateslate/demo.py",
            "stateslate/errors.py",
            "stateslate/models.py",
            "stateslate/parser.py",
            "stateslate/render.py",
        }
        if not required.issubset(names):
            raise SystemExit(f"wheel is missing modules: {sorted(required - names)}")

    run(
        [
            sys.executable,
            "scripts/package_release.py",
            "--dist",
            str(distribution),
            "--out",
            str(release),
        ]
    )
    expected_release = {
        "SHA256SUMS",
        *expected_distribution,
        f"stateslate-examples-v{version}.zip",
    }
    if {path.name for path in release.iterdir()} != expected_release:
        raise SystemExit("release package has an unexpected asset set")
    verify_checksums(release)

    clean_environment = temporary / "clean-environment"
    run([sys.executable, "-m", "venv", str(clean_environment)])
    clean_python = python_in(clean_environment)
    run([str(clean_python), "-m", "pip", "install", "--no-deps", str(release / wheel.name)])
    executable = executable_in(clean_environment, "stateslate")
    installed_version = run([str(executable), "--version"], capture=True)
    if installed_version.stdout.strip() != f"stateslate {version}":
        raise SystemExit(f"unexpected installed version: {installed_version.stdout!r}")

    installed_demo = temporary / "installed-demo"
    run([str(executable), "demo", "--out", str(installed_demo)])
    compare_artifacts(installed_demo, COMMITTED_DEMO)

    extracted = temporary / "extracted"
    with ZipFile(release / f"stateslate-examples-v{version}.zip") as archive:
        archive.extractall(extracted)
    bundled_example = (
        extracted / f"stateslate-examples-v{version}" / "examples" / "moonlit-letter.json"
    )
    installed_source = temporary / "installed-source"
    run([str(executable), "compile", str(bundled_example), "--out", str(installed_source)])
    compare_artifacts(installed_source, COMMITTED_DEMO)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="skip only when the locked dependency audit was run separately",
    )
    arguments = parser.parse_args(argv)
    run(["uv", "lock", "--check"])
    run(
        [
            "uv",
            "run",
            "--no-sync",
            "ruff",
            "format",
            "--check",
            "src",
            "tests",
            "scripts",
        ]
    )
    run(["uv", "run", "--no-sync", "ruff", "check", "src", "tests", "scripts"])
    run(["uv", "run", "--no-sync", "mypy", "src", "tests", "scripts"])
    with tempfile.TemporaryDirectory(prefix="stateslate-check-") as directory:
        temporary = Path(directory)
        if arguments.skip_audit:
            print("STATESLATE_DEPENDENCY_AUDIT=SKIPPED_SEPARATELY", flush=True)
        else:
            audit_requirements = temporary / "locked-requirements.txt"
            run(
                [
                    "uv",
                    "export",
                    "--quiet",
                    "--locked",
                    "--all-groups",
                    "--no-emit-project",
                    "--format",
                    "requirements.txt",
                    "--output-file",
                    str(audit_requirements),
                ]
            )
            run(
                [
                    "uv",
                    "run",
                    "--no-sync",
                    "pip-audit",
                    "--requirement",
                    str(audit_requirements),
                    "--require-hashes",
                    "--disable-pip",
                    "--cache-dir",
                    str(ROOT / ".audit-cache"),
                    "--strict",
                    "--progress-spinner",
                    "off",
                ]
            )
        run(
            [
                "uv",
                "run",
                "--no-sync",
                "pytest",
                "--basetemp",
                str(temporary / "pytest"),
                "--cov=stateslate",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-fail-under=90",
            ]
        )
        check_runtime_dependencies()
        exercise_examples(temporary)
        exercise_package(temporary)
    print("STATESLATE_RELEASE_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
