"""CLI interface for ContentLint."""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from .engine import ContentLinter
from .reporters import get_reporter

app = typer.Typer(
    name="contentlint",
    help="ESLint for writing - scan content files for AI-tells and weak prose patterns",
    add_completion=False
)
console = Console()


@app.command()
def lint(
    path: Path = typer.Argument(
        ...,
        help="Path to file or directory to lint",
        exists=True
    ),
    format: str = typer.Option(
        "md",
        "--format",
        "-f",
        help="Output format: json or md"
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help="Output file path (if not specified, prints to stdout)"
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to contentlint.yaml config file"
    ),
    fail_on: str = typer.Option(
        "FAIL",
        "--fail-on",
        help="Exit with error if this severity level or higher is found (FAIL, WARN, or PASS)"
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        "-r/-R",
        help="Recursively scan directories"
    )
):
    """
    Lint content files for writing quality issues.

    Examples:

        contentlint lint ./content

        contentlint lint ./content --format json --out ./reports/report.json

        contentlint lint ./content --fail-on WARN

        contentlint lint ./docs/article.md --format md
    """
    try:
        # Initialize linter
        linter = ContentLinter(config_path=config)

        console.print(f"[cyan]ContentLint v1.0.0[/cyan]")
        console.print(f"Scanning: {path}")

        # Lint files
        if path.is_file():
            findings = linter.lint_file(path)
            results = {str(path): findings} if findings else {}
        else:
            results = linter.lint_directory(path, recursive=recursive)

        # Generate report
        reporter = get_reporter(format)
        output = reporter.generate(results, output_file=out)

        # Print to console if no output file specified
        if out is None:
            console.print(output)
        else:
            console.print(f"[green]Report written to: {out}[/green]")

        # Print summary table
        severity_counts = linter.get_severity_counts(results)

        table = Table(title="Summary")
        table.add_column("Severity", style="cyan")
        table.add_column("Count", justify="right")

        for severity in ['FAIL', 'WARN', 'PASS']:
            count = severity_counts.get(severity, 0)
            style = "red" if severity == 'FAIL' else "yellow" if severity == 'WARN' else "green"
            table.add_row(severity, str(count), style=style)

        console.print(table)

        # Exit with error if threshold exceeded
        if linter.should_fail(results, fail_on):
            console.print(f"[red]✗ Linting failed: Found issues at {fail_on} level or higher[/red]")
            sys.exit(1)
        else:
            console.print(f"[green]✓ Linting passed[/green]")
            sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def version():
    """Show ContentLint version."""
    from . import __version__
    console.print(f"ContentLint version {__version__}")


@app.command()
def init(
    output: Path = typer.Option(
        Path("contentlint.yaml"),
        "--output",
        "-o",
        help="Output path for config file"
    )
):
    """
    Generate a default contentlint.yaml configuration file.
    """
    from shutil import copy

    # Copy default config from package
    default_config = Path(__file__).parent.parent / 'contentlint.yaml'

    if not default_config.exists():
        console.print("[red]Error: Default config not found[/red]")
        sys.exit(1)

    if output.exists():
        overwrite = typer.confirm(f"{output} already exists. Overwrite?")
        if not overwrite:
            console.print("Cancelled.")
            sys.exit(0)

    copy(default_config, output)
    console.print(f"[green]✓ Created {output}[/green]")
    console.print("Edit this file to customize linting rules.")


if __name__ == "__main__":
    app()
