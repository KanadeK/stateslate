from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from stateslate.demo import DEMO_JSON
from stateslate.render import ARTIFACT_NAMES

ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "examples"
COMMITTED_DEMO = ROOT / "docs" / "demo"


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "stateslate", *arguments],
        cwd=ROOT,
        check=False,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def test_public_example_is_the_exact_embedded_demo() -> None:
    assert (EXAMPLES / "moonlit-letter.json").read_text(encoding="utf-8") == DEMO_JSON


def test_public_example_reproduces_committed_demo(tmp_path: Path) -> None:
    output = tmp_path / "demo"

    result = run_cli(
        "compile",
        str(EXAMPLES / "moonlit-letter.json"),
        "--out",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    assert {path.name for path in output.iterdir()} == ARTIFACT_NAMES
    assert {path.name for path in COMMITTED_DEMO.iterdir()} == ARTIFACT_NAMES
    for name in sorted(ARTIFACT_NAMES):
        assert (output / name).read_bytes() == (COMMITTED_DEMO / name).read_bytes()


@pytest.mark.parametrize(
    ("name", "error_code"),
    [
        ("invalid-duplicate-order.json", "DUPLICATE_STORY_ORDER"),
        ("invalid-unknown-track.json", "UNKNOWN_TRACK"),
        ("invalid-transition-mismatch.json", "TRANSITION_MISMATCH"),
    ],
)
def test_blocking_examples_fail_without_reports(tmp_path: Path, name: str, error_code: str) -> None:
    output = tmp_path / name

    result = run_cli("compile", str(EXAMPLES / name), "--out", str(output))

    assert result.returncode == 2
    assert error_code in result.stderr
    assert "Repair:" in result.stderr
    assert not output.exists()
