"""Core linting engine for ContentLint."""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from .parsers import get_parser
from .rules import RuleRegistry, Finding


class ContentLinter:
    """Main linter engine."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the linter with a configuration file.

        Args:
            config_path: Path to contentlint.yaml config file
        """
        if config_path is None:
            # Look for contentlint.yaml in current directory
            config_path = Path('contentlint.yaml')
            if not config_path.exists():
                # Use default config from package directory
                config_path = Path(__file__).parent.parent / 'contentlint.yaml'

        self.config_path = config_path
        self.config = self._load_config()
        self.rules = self._init_rules()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def _init_rules(self) -> List[Any]:
        """Initialize rule checkers from configuration."""
        rules = []
        rule_configs = self.config.get('rules', [])

        for rule_config in rule_configs:
            if rule_config.get('enabled', True):
                try:
                    checker = RuleRegistry.create_checker(rule_config)
                    rules.append(checker)
                except ValueError as e:
                    print(f"Warning: {e}")

        return rules

    def lint_file(self, file_path: Path) -> List[Finding]:
        """
        Lint a single file.

        Args:
            file_path: Path to the content file

        Returns:
            List of Finding objects
        """
        try:
            parser = get_parser(file_path)
            parsed = parser.parse(file_path)

            text = parsed['text']
            raw_text = parsed['raw']
            metadata = parsed['metadata']

            all_findings = []

            for rule in self.rules:
                findings = rule.check(text, raw_text, str(file_path), metadata)
                all_findings.extend(findings)

            return all_findings

        except Exception as e:
            print(f"Error linting {file_path}: {e}")
            return []

    def lint_directory(self, directory: Path, recursive: bool = True) -> Dict[str, List[Finding]]:
        """
        Lint all supported files in a directory.

        Args:
            directory: Path to directory
            recursive: Whether to search recursively

        Returns:
            Dictionary mapping file paths to findings
        """
        results = {}

        if recursive:
            patterns = ['**/*.md', '**/*.html', '**/*.htm']
        else:
            patterns = ['*.md', '*.html', '*.htm']

        for pattern in patterns:
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    findings = self.lint_file(file_path)
                    if findings:
                        results[str(file_path)] = findings

        return results

    def get_severity_counts(self, results: Dict[str, List[Finding]]) -> Dict[str, int]:
        """
        Calculate severity counts across all findings.

        Args:
            results: Dictionary of file paths to findings

        Returns:
            Dictionary with counts for PASS, WARN, FAIL
        """
        counts = {'PASS': 0, 'WARN': 0, 'FAIL': 0}

        for findings in results.values():
            for finding in findings:
                severity = finding.severity
                counts[severity] = counts.get(severity, 0) + 1

        return counts

    def should_fail(self, results: Dict[str, List[Finding]], fail_on: str = 'FAIL') -> bool:
        """
        Determine if linting should fail based on severity threshold.

        Args:
            results: Dictionary of file paths to findings
            fail_on: Severity level to fail on (FAIL, WARN, or PASS)

        Returns:
            True if should fail, False otherwise
        """
        counts = self.get_severity_counts(results)

        if fail_on == 'FAIL':
            return counts['FAIL'] > 0
        elif fail_on == 'WARN':
            return counts['WARN'] > 0 or counts['FAIL'] > 0
        elif fail_on == 'PASS':
            return counts['PASS'] > 0 or counts['WARN'] > 0 or counts['FAIL'] > 0

        return False
