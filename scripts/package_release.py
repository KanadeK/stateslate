"""Create deterministic StateSlate release assets and checksums."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from collections.abc import Sequence
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from stateslate import __version__

ROOT = Path(__file__).parents[1]
WHEEL_NAME = f"stateslate-{__version__}-py3-none-any.whl"
SDIST_NAME = f"stateslate-{__version__}.tar.gz"
EXAMPLES_NAME = f"stateslate-examples-v{__version__}.zip"


class ReleasePackagingError(RuntimeError):
    """The checked release inputs do not match the packaging contract."""


def _release_sources() -> tuple[Path, ...]:
    fixed = (
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
        ROOT / "docs" / "FORMAT.md",
        ROOT / "docs" / "REPAIR.md",
    )
    discovered = tuple(
        sorted(
            (
                *(ROOT / "examples").glob("*"),
                *(ROOT / "docs" / "demo").glob("*"),
            ),
            key=lambda path: path.as_posix(),
        )
    )
    sources = tuple(path for path in (*fixed, *discovered) if path.is_file())
    missing = [str(path.relative_to(ROOT)) for path in fixed if not path.is_file()]
    if missing:
        raise ReleasePackagingError(f"missing release sources: {missing}")
    return sources


def _write_examples_zip(destination: Path) -> None:
    prefix = f"stateslate-examples-v{__version__}"
    entries = sorted(
        (
            f"{prefix}/{source.relative_to(ROOT).as_posix()}",
            source,
        )
        for source in _release_sources()
    )
    with ZipFile(destination, "w") as archive:
        for archive_name, source in entries:
            info = ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())


def _write_checksums(directory: Path) -> None:
    assets = sorted(path for path in directory.iterdir() if path.name != "SHA256SUMS")
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in assets]
    (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def package_release(distribution: Path, output: Path) -> None:
    """Package an exact wheel/sdist pair, examples, and SHA-256 manifest."""

    expected = {WHEEL_NAME, SDIST_NAME}
    actual = {path.name for path in distribution.iterdir()} if distribution.is_dir() else set()
    if actual != expected:
        raise ReleasePackagingError(
            f"unexpected distribution assets: expected {sorted(expected)}, got {sorted(actual)}"
        )
    if output.exists():
        raise ReleasePackagingError(f"release output already exists: {output}")
    if not output.parent.is_dir():
        raise ReleasePackagingError(f"release output parent does not exist: {output.parent}")

    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.stateslate-release-", dir=output.parent)
    )
    try:
        for name in sorted(expected):
            shutil.copyfile(distribution / name, temporary / name)
        _write_examples_zip(temporary / EXAMPLES_NAME)
        _write_checksums(temporary)
        temporary.rename(output)
    except OSError as error:
        raise ReleasePackagingError(f"could not package release: {error}") from error
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        package_release(arguments.dist, arguments.out)
    except ReleasePackagingError as error:
        parser.exit(2, f"package_release: {error}\n")
    print(f"Release assets: {arguments.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
