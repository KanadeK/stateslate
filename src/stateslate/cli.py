"""Command-line interface for StateSlate."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from stateslate import __version__
from stateslate.compiler import Compilation, compile_project
from stateslate.demo import demo_project
from stateslate.errors import StateSlateError
from stateslate.parser import load_project
from stateslate.render import render_artifacts


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stateslate",
        description="Compile story continuity into shoot-day reset sheets.",
    )
    parser.add_argument("--version", action="version", version=f"stateslate {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate syntax and story-state semantics")
    validate.add_argument("project", type=Path)
    validate.add_argument("--risk-days", type=_positive_integer, default=3)

    compile_command = commands.add_parser("compile", help="compile a project into five reports")
    compile_command.add_argument("project", type=Path)
    _add_output_options(compile_command)

    demo = commands.add_parser("demo", help="compile the built-in Moonlit Letter example")
    _add_output_options(demo)
    return parser


def _add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--out", type=Path, required=True, help="new report directory")
    parser.add_argument("--risk-days", type=_positive_integer, default=3)
    parser.add_argument(
        "--fail-on",
        choices=("none", "medium", "high"),
        default="none",
        help="return exit 1 when compiled risks meet this severity",
    )


def _write_artifacts(output: Path, artifacts: dict[str, str]) -> None:
    if output.exists():
        raise StateSlateError(
            "OUTPUT_EXISTS",
            f"output path already exists: {output}",
            "Choose a new --out directory; StateSlate never merges or overwrites reports.",
        )
    parent = output.parent
    if not parent.is_dir():
        raise StateSlateError(
            "OUTPUT_PARENT",
            f"output parent is not a directory: {parent}",
            "Create the parent directory, then run the command again.",
        )
    try:
        temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.stateslate-", dir=parent))
    except OSError as error:
        raise StateSlateError(
            "OUTPUT_WRITE",
            f"cannot create a temporary report directory beside {output}: {error}",
            "Check the output parent permissions and available disk space.",
        ) from error
    try:
        for name, text in artifacts.items():
            (temporary / name).write_text(text, encoding="utf-8", newline="\n")
        temporary.rename(output)
    except OSError as error:
        raise StateSlateError(
            "OUTPUT_WRITE",
            f"cannot publish report directory {output}: {error}",
            "Check path permissions, remove no files, and retry with a new --out path.",
        ) from error
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def _risk_gate(compilation: Compilation, fail_on: str) -> bool:
    if fail_on == "high":
        return compilation.summary.high_risk_count > 0
    if fail_on == "medium":
        return compilation.summary.high_risk_count + compilation.summary.medium_risk_count > 0
    return False


def _print_summary(compilation: Compilation, output: Path | None = None) -> None:
    summary = compilation.summary
    destination = f" Reports: {output}" if output else ""
    print(
        f"StateSlate: {summary.scene_count} scenes, {summary.track_count} tracks, "
        f"{summary.prepare_count} prepare, {summary.reset_count} reset, "
        f"{summary.high_risk_count} high risk, {summary.medium_risk_count} medium risk."
        f"{destination}"
    )


def _compile_and_write(compilation: Compilation, output: Path, fail_on: str) -> int:
    _write_artifacts(output, render_artifacts(compilation))
    _print_summary(compilation, output)
    if _risk_gate(compilation, fail_on):
        print(
            f"RISK GATE: report contains findings at or above {fail_on!r}; "
            "inspect continuity.json.",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run StateSlate and return its stable process exit code."""

    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "validate":
            compilation = compile_project(
                load_project(arguments.project), risk_days=arguments.risk_days
            )
            print(f"VALID: {arguments.project}")
            _print_summary(compilation)
            return 0
        if arguments.command == "compile":
            compilation = compile_project(
                load_project(arguments.project), risk_days=arguments.risk_days
            )
            return _compile_and_write(compilation, arguments.out, arguments.fail_on)
        compilation = compile_project(demo_project(), risk_days=arguments.risk_days)
        return _compile_and_write(compilation, arguments.out, arguments.fail_on)
    except StateSlateError as error:
        print(error, file=sys.stderr)
        return 2
