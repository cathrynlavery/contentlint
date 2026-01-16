"""Output reporters for ContentLint results."""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from .rules import Finding


class Reporter:
    """Base reporter class."""

    def generate(self, results: Dict[str, List[Finding]], output_file: Path = None) -> str:
        """Generate report from results."""
        raise NotImplementedError


class JSONReporter(Reporter):
    """Generate JSON report."""

    def generate(self, results: Dict[str, List[Finding]], output_file: Path = None) -> str:
        """Generate JSON report."""
        # Convert findings to dictionaries
        report = {
            'summary': self._generate_summary(results),
            'files': {}
        }

        for file_path, findings in results.items():
            report['files'][file_path] = [f.to_dict() for f in findings]

        json_output = json.dumps(report, indent=2)

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(json_output)

        return json_output

    def _generate_summary(self, results: Dict[str, List[Finding]]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_files = len(results)
        total_findings = sum(len(findings) for findings in results.values())

        severity_counts = {'PASS': 0, 'WARN': 0, 'FAIL': 0}
        rule_counts = defaultdict(int)
        category_counts = defaultdict(int)

        for findings in results.values():
            for finding in findings:
                severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
                rule_counts[finding.rule_id] += 1
                category_counts[finding.details.get('category', 'general')] += 1

        return {
            'total_files': total_files,
            'total_findings': total_findings,
            'severity_counts': severity_counts,
            'top_rules': dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'category_counts': dict(category_counts)
        }


class MarkdownReporter(Reporter):
    """Generate Markdown report."""

    def generate(self, results: Dict[str, List[Finding]], output_file: Path = None) -> str:
        """Generate Markdown report."""
        lines = []

        # Header
        lines.append("# ContentLint Report\n")

        # Summary
        lines.append("## Summary\n")
        summary = self._generate_summary(results)

        lines.append(f"- **Total Files Scanned**: {summary['total_files']}")
        lines.append(f"- **Total Findings**: {summary['total_findings']}")
        lines.append(f"- **FAIL**: {summary['severity_counts']['FAIL']}")
        lines.append(f"- **WARN**: {summary['severity_counts']['WARN']}")
        lines.append(f"- **PASS**: {summary['severity_counts']['PASS']}")
        lines.append("")

        # Top issues
        if summary['top_rules']:
            lines.append("## Top Issues\n")
            for rule_id, count in list(summary['top_rules'].items())[:5]:
                lines.append(f"- **{rule_id}**: {count} occurrences")
            lines.append("")

        # Files with issues
        lines.append("## Files with Issues\n")

        # Sort files by number of FAIL findings first, then WARN
        sorted_files = sorted(
            results.items(),
            key=lambda x: (
                sum(1 for f in x[1] if f.severity == 'FAIL'),
                sum(1 for f in x[1] if f.severity == 'WARN')
            ),
            reverse=True
        )

        for file_path, findings in sorted_files:
            if not findings:
                continue

            # Count severities for this file
            fail_count = sum(1 for f in findings if f.severity == 'FAIL')
            warn_count = sum(1 for f in findings if f.severity == 'WARN')

            status = "🔴" if fail_count > 0 else "🟡" if warn_count > 0 else "🟢"

            lines.append(f"### {status} {file_path}")
            lines.append(f"*{fail_count} FAIL, {warn_count} WARN*\n")

            # Group by severity
            for severity in ['FAIL', 'WARN']:
                severity_findings = [f for f in findings if f.severity == severity]
                if severity_findings:
                    lines.append(f"**{severity}:**")
                    for finding in severity_findings[:10]:  # Limit to top 10 per severity
                        line_info = f" (line {finding.line})" if finding.line else ""
                        lines.append(f"- [{finding.rule_id}]{line_info}: {finding.message}")
                        if finding.snippet:
                            lines.append(f"  ```")
                            lines.append(f"  {finding.snippet}")
                            lines.append(f"  ```")
                    lines.append("")

            lines.append("")

        # Recommendations
        lines.append("## Recommendations\n")
        lines.append("1. **FAIL items**: Address these immediately - they significantly impact content quality")
        lines.append("2. **WARN items**: Review and fix where appropriate")
        lines.append("3. Review the most common issues (Top Issues section) first for maximum impact")
        lines.append("")

        markdown_output = "\n".join(lines)

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(markdown_output)

        return markdown_output

    def _generate_summary(self, results: Dict[str, List[Finding]]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_files = len(results)
        total_findings = sum(len(findings) for findings in results.values())

        severity_counts = {'PASS': 0, 'WARN': 0, 'FAIL': 0}
        rule_counts = defaultdict(int)

        for findings in results.values():
            for finding in findings:
                severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
                rule_counts[finding.rule_id] += 1

        return {
            'total_files': total_files,
            'total_findings': total_findings,
            'severity_counts': severity_counts,
            'top_rules': dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True))
        }


def get_reporter(format: str) -> Reporter:
    """Get reporter instance based on format."""
    if format == 'json':
        return JSONReporter()
    elif format == 'md' or format == 'markdown':
        return MarkdownReporter()
    else:
        raise ValueError(f"Unsupported format: {format}")
