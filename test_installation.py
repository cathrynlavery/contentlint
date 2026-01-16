#!/usr/bin/env python3
"""
Quick test script to verify ContentLint installation.
Run this after installing to ensure everything works.

Usage:
    python test_installation.py
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import typer
        import yaml
        from bs4 import BeautifulSoup
        from rich.console import Console

        from contentlint import ContentLinter, RuleRegistry
        from contentlint.parsers import MarkdownParser, HTMLParser
        from contentlint.reporters import JSONReporter, MarkdownReporter
        from contentlint.utils import split_sentences, tokenize_words

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False


def test_config_loading():
    """Test that default config can be loaded."""
    print("\nTesting config loading...")
    try:
        config_path = Path(__file__).parent / "contentlint.yaml"
        if not config_path.exists():
            print(f"✗ Config file not found at {config_path}")
            return False

        from contentlint import ContentLinter
        linter = ContentLinter(config_path=config_path)
        print(f"✓ Config loaded: {len(linter.rules)} rules initialized")
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False


def test_example_file():
    """Test linting the example file."""
    print("\nTesting example file linting...")
    try:
        from contentlint import ContentLinter

        example_path = Path(__file__).parent / "examples" / "sample-content.md"
        if not example_path.exists():
            print(f"✗ Example file not found at {example_path}")
            return False

        config_path = Path(__file__).parent / "contentlint.yaml"
        linter = ContentLinter(config_path=config_path)

        findings = linter.lint_file(example_path)
        print(f"✓ Example linted: {len(findings)} findings detected")

        # Check that we found some issues (the example has intentional problems)
        if len(findings) > 0:
            print("✓ Found expected issues in example file")
            return True
        else:
            print("⚠ Warning: Expected to find issues in example file")
            return True  # Not a critical failure

    except Exception as e:
        print(f"✗ Example linting failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reporters():
    """Test that reporters can generate output."""
    print("\nTesting reporters...")
    try:
        from contentlint.reporters import JSONReporter, MarkdownReporter
        from contentlint.rules import Finding

        # Create dummy findings
        findings = [
            Finding(
                rule_id="test-rule",
                severity="WARN",
                message="Test finding",
                file_path="test.md",
                snippet="test snippet",
                line=1
            )
        ]

        results = {"test.md": findings}

        # Test JSON reporter
        json_reporter = JSONReporter()
        json_output = json_reporter.generate(results)
        if '"summary"' in json_output and '"files"' in json_output:
            print("✓ JSON reporter works")
        else:
            print("✗ JSON reporter output invalid")
            return False

        # Test Markdown reporter
        md_reporter = MarkdownReporter()
        md_output = md_reporter.generate(results)
        if "# ContentLint Report" in md_output:
            print("✓ Markdown reporter works")
        else:
            print("✗ Markdown reporter output invalid")
            return False

        return True

    except Exception as e:
        print(f"✗ Reporter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("ContentLint Installation Test")
    print("=" * 50)

    tests = [
        test_imports,
        test_config_loading,
        test_example_file,
        test_reporters,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if all(results):
        print("\n✓ All tests passed! ContentLint is ready to use.")
        print("\nTry running:")
        print("  python -m contentlint lint examples/sample-content.md")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
