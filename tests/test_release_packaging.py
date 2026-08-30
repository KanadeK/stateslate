from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).parents[1]


def fake_distribution(directory: Path) -> Path:
    directory.mkdir()
    (directory / "stateslate-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
    (directory / "stateslate-0.1.0.tar.gz").write_bytes(b"sdist")
    return directory


def run_packaging(distribution: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "package_release.py"),
            "--dist",
            str(distribution),
            "--out",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def test_package_release_creates_deterministic_assets_and_checksums(tmp_path: Path) -> None:
    output = tmp_path / "release"

    result = run_packaging(fake_distribution(tmp_path / "dist"), output)

    assert result.returncode == 0, result.stderr
    assert {path.name for path in output.iterdir()} == {
        "SHA256SUMS",
        "stateslate-0.1.0-py3-none-any.whl",
        "stateslate-0.1.0.tar.gz",
        "stateslate-examples-v0.1.0.zip",
    }
    checksum_lines = (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    assert [line.split("  ", 1)[1] for line in checksum_lines] == [
        "stateslate-0.1.0-py3-none-any.whl",
        "stateslate-0.1.0.tar.gz",
        "stateslate-examples-v0.1.0.zip",
    ]
    for line in checksum_lines:
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected

    with ZipFile(output / "stateslate-examples-v0.1.0.zip") as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert "stateslate-examples-v0.1.0/examples/moonlit-letter.json" in names
        assert "stateslate-examples-v0.1.0/docs/demo/report.html" in names
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())


def test_package_release_refuses_existing_output_directory(tmp_path: Path) -> None:
    output = tmp_path / "release"
    output.mkdir()

    result = run_packaging(fake_distribution(tmp_path / "dist"), output)

    assert result.returncode == 2
    assert "already exists" in result.stderr


def test_package_release_requires_exact_distribution_assets(tmp_path: Path) -> None:
    distribution = fake_distribution(tmp_path / "dist")
    (distribution / "unexpected.txt").write_text("no", encoding="utf-8")

    result = run_packaging(distribution, tmp_path / "release")

    assert result.returncode == 2
    assert "unexpected distribution assets" in result.stderr
