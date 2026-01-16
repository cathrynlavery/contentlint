# ContentLint Quick Start Guide

Get up and running with ContentLint in 5 minutes.

## Installation

```bash
cd contentlint
pip install -r requirements.txt
```

Or for development:

```bash
pip install -e .
```

## Your First Lint

### 1. Try the Example

```bash
# Lint the example content
python -m contentlint lint examples/sample-content.md

# You should see output highlighting issues in the sample
```

### 2. Initialize Your Config

```bash
# Generate contentlint.yaml in your project
python -m contentlint init
```

### 3. Lint Your Content

```bash
# Lint a directory
python -m contentlint lint ./content

# Or a single file
python -m contentlint lint ./content/article.md
```

## Understanding Output

### Console Output

The default Markdown output shows:
- Summary statistics (FAIL/WARN/PASS counts)
- Top issues across all files
- Per-file breakdown with line numbers and snippets

### Severity Colors

- 🔴 **FAIL** - Must fix (e.g., 5+ "really" per 1,000 words)
- 🟡 **WARN** - Should review (e.g., 2-3 "really" per 1,000 words)
- 🟢 **PASS** - All clear

## Common Commands

```bash
# Generate JSON report
python -m contentlint lint ./content --format json --out report.json

# Fail on warnings (not just errors)
python -m contentlint lint ./content --fail-on WARN

# Use custom config
python -m contentlint lint ./content --config ./my-rules.yaml

# Non-recursive scan (single directory only)
python -m contentlint lint ./content --no-recursive
```

## Customizing Rules

Edit `contentlint.yaml`:

```yaml
rules:
  - id: banned-words
    enabled: true
    banned_words:
      - just
      - really
      - very
      # Add your own words
    fail_threshold_per_1000: 3  # Adjust threshold
    warn_threshold_per_1000: 2
```

## Next Steps

1. **Review the example output** - See `examples/sample-output.md`
2. **Tune your thresholds** - Adjust based on your content's baseline
3. **Set up CI** - Use the GitHub Action in `.github/workflows/`
4. **Read the full docs** - Check `README.md` for all features

## Common Issues

### "Config file not found"

Solution: Run `python -m contentlint init` to create `contentlint.yaml`

### "No files found"

Solution: Check that you're scanning a directory with `.md` or `.html` files

### "Module not found"

Solution: Install dependencies with `pip install -r requirements.txt`

## Quick Tips

- Start with default thresholds, then tighten as quality improves
- Focus on fixing FAIL items first
- Use `--fail-on WARN` in CI once you've addressed the basics
- Use directory overrides for different content types (blog vs. marketing)

## Help

```bash
# Show all commands
python -m contentlint --help

# Show lint command options
python -m contentlint lint --help
```

For full documentation, see [README.md](README.md).
