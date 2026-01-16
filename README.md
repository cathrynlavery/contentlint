# ContentLint

**ESLint for writing** - A deterministic linter that scans content files and flags AI-generated content patterns, based on Wikipedia's research into AI writing detection.

ContentLint helps you maintain high-quality, human-written content by automatically detecting the distinctive patterns that appear in AI-generated text. Built on patterns documented in [Wikipedia's "Signs of AI writing" guide](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), which catalogs observations from thousands of instances of AI-generated text.

## Features

- ✅ **Deterministic** - No LLM calls, consistent results every time
- ⚙️ **Configurable** - Define rules and thresholds in YAML
- 📁 **Multi-format** - Supports Markdown (.md) and HTML (.html, .htm)
- 📊 **Rich reporting** - JSON for machines, Markdown for humans
- 🔄 **CI-friendly** - Built for automation and continuous integration
- 🎯 **Extensible** - Add new rules without code changes

## Quick Start

### Installation

```bash
# Install from source
cd contentlint
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

### Basic Usage

```bash
# Lint a single file
contentlint lint ./content/article.md

# Lint a directory recursively
contentlint lint ./content

# Generate JSON report
contentlint lint ./content --format json --out report.json

# Fail on warnings (not just errors)
contentlint lint ./content --fail-on WARN

# Use custom config
contentlint lint ./content --config ./my-rules.yaml
```

### Initialize Configuration

```bash
# Generate default contentlint.yaml in current directory
contentlint init
```

## What ContentLint Detects

ContentLint implements three categories of checks:

1. **Wikipedia AI Detection Patterns** - Formal/encyclopedic AI writing patterns based on rigorous linguistic research
2. **Conversational AI Detection Patterns** - Blog/marketing/listicle AI patterns with different tells
3. **General Writing Quality Rules** - Traditional writing quality checks for clarity and conciseness

**Important:** AI writes in different styles. Wikipedia's patterns catch formal encyclopedic AI (significance language, promotional puffery). Our conversational patterns catch blog/marketing AI (empathy hooks, meta-commentary). Both are needed for comprehensive detection.

### Wikipedia AI Detection Patterns

These patterns are based on Wikipedia's extensive documentation of AI writing tells, observed across thousands of instances.

#### A) AI Vocabulary Overuse

Detects words that appear far more frequently in AI-generated text than in human writing:

**Most distinctive AI words:**
- **delve** - Famously overused by ChatGPT in 2023-2024
- **underscore, underscored, underscoring** - Used as verb meaning "emphasize"
- **tapestry** - Used abstractly (e.g., "rich tapestry of culture")
- **pivotal** - Overused for significance
- **landscape** - Used abstractly (e.g., "the technological landscape")
- **testament** - In phrases like "stands as a testament"
- **vibrant** - Promotional descriptor
- **fostering, cultivate** - Used figuratively
- **showcase, showcasing** - Promotional verb
- **intricate, intricacies** - Empty sophistication marker

**Additional AI vocabulary:**
- additionally, align/aligned, crucial, emphasizing, enduring, enhance, garner, highlight, interplay, valuable

**Detection logic:**
- FAIL if > 5 per 1,000 words
- WARN if > 3 per 1,000 words
- WARN if 3+ different AI words appear (clustering effect)

#### B) Significance/Legacy Language

Detects AI's tendency to overemphasize significance using distinctive phrases:

**Common patterns:**
- "stands as a testament to"
- "serves as a reminder"
- "plays a pivotal/crucial/vital role"
- "underscores its importance/significance"
- "enduring legacy/impact"
- "reflects broader trends"
- "contributing to the broader"
- "deeply rooted in"
- "indelible mark"
- "setting the stage for"

**Why this matters:** LLMs add these even for mundane subjects, constantly reminding readers of importance while the actual content becomes vaguer.

**Thresholds:**
- WARN if 2+ instances
- FAIL if 4+ instances

#### C) Promotional Language

Detects advertisement-like puffery that LLMs add even when prompted for neutral tone:

**Common patterns:**
- "boasts a" (instead of "has a")
- "nestled in the heart of"
- "vibrant/rich cultural heritage"
- "natural beauty", "breathtaking views"
- "renowned for", "celebrated as"
- "commitment to excellence"
- "groundbreaking/revolutionary" (used loosely)
- "clean and modern", "state-of-the-art"

**Thresholds:**
- WARN if 2+ instances
- FAIL if 4+ instances

#### D) Superficial Analysis

Detects empty commentary added via trailing present participle (-ing) phrases:

**Common patterns:**
- ", highlighting the importance of"
- ", underscoring its significance"
- ", emphasizing the need for"
- ", ensuring quality"
- ", fostering innovation"
- ", reflecting the broader"
- ", contributing to"

**Why this matters:** These add no actual analysis, just noise that makes text sound more "thoughtful."

**Thresholds:**
- WARN if 3+ instances
- FAIL if 5+ instances

#### E) Copulative Avoidance

Detects AI's tendency to avoid simple "is/are" and "has/have" constructions:

**Patterns:**
- "serves as a" instead of "is a"
- "stands as a" instead of "is a"
- "features a/numerous" instead of "has"
- "offers a" instead of "has"
- "holds the distinction of" instead of "is"

**Why this matters:** A study documented over 10% decrease in "is/are" usage in academic writing in 2023, with no prior changes.

**Threshold:** WARN if 3+ instances

#### F) Negative Parallelisms

Detects formulaic "balanced" constructions common in AI writing:

**Patterns:**
- "not only...but also..."
- "not just about...it's about..."
- "it's not...it's..." (across sentences)
- "no...no...just..."
- "not...rather, it..."

**Why distinctive:** Each instance is reported individually as these are quite formulaic.

#### G) Rule of Three Overuse

Detects excessive use of three-part lists:

**Patterns:**
- "adjective, adjective, and adjective approach/method/system"
- Repetitive three-part phrase structures

**Why this matters:** LLMs overuse this rhetorical device to make superficial analysis appear comprehensive.

**Threshold:** WARN if 3+ instances

#### H) Challenges/Conclusions Sections

Detects formulaic outline-style conclusions:

**Patterns:**
- "Despite its [positive words], [subject] faces challenges..."
- "Despite these challenges, [subject] continues to thrive"
- Section titles: "Challenges and Legacy", "Future Outlook"
- "Future investments/initiatives could enhance..."

**Why distinctive:** Very formulaic AI pattern, especially common in Wikipedia-style articles.

**Thresholds:**
- WARN if 1 instance
- FAIL if 2+ instances

#### I) Knowledge Cutoff Disclaimers

Detects AI disclaimers and speculation about missing information:

**Patterns:**
- "as of my last knowledge update"
- "up to my last training update"
- "specific details are limited/not widely documented"
- "not extensively documented in available sources"
- "maintains a low profile", "keeps personal details private"

**Why this is FAIL-worthy:** These are often completely fabricated claims. AI will say "details are limited" even when it's just making things up.

Each instance reported individually as FAIL.

#### J) Vague Attribution/Weasel Wording

Detects uncited claims attributed to vague authorities:

**Patterns:**
- "Observers have noted/cited"
- "Experts argue/suggest"
- "Industry reports indicate"
- "Some critics/sources argue"
- "Several publications have described"
- "Has been described as" (without source)

**Threshold:** WARN if 2+ instances

#### K) Notability Overemphasis

Detects AI's tendency to "prove" notability by listing media coverage:

**Patterns:**
- "independent coverage" (Wikipedia-specific language)
- "featured in [outlet], [outlet], and other prominent media outlets"
- "local/regional/national media outlets"
- "maintains an active social media presence"
- "written by a leading expert"

**Why distinctive:** Uses Wikipedia's own notability guidelines language, but in article text rather than talk pages.

**Threshold:** WARN if 2+ instances

---

### Conversational AI Detection Patterns

Wikipedia's patterns detect formal/encyclopedic AI writing. But AI also generates blog posts, listicles, and marketing content with different tells. These patterns catch conversational AI writing.

#### L) Conversational Hooks

Detects formulaic empathy phrases AI uses to create artificial connection:

**Common patterns:**
- "You know the feeling"
- "You know what I mean"
- "You've been there"
- "We've all been there"
- "Let's be honest"
- "Admit it"
- "Sound familiar?"
- "I get it"

**Why distinctive:** Human writers use these occasionally, but AI overuses them as a formula to establish rapport without actually understanding reader experience.

**Threshold:** WARN if 2+ instances

#### M) Formulaic Empathy/Emphasis

Detects AI's predictable transition and emphasis phrases:

**Common patterns:**
- "Here's the thing:"
- "The truth is:"
- "Here's what you need to know:"
- "The reality is:"
- "Here's why:"
- "The bottom line is:"
- "What this means:"

**Why distinctive:** These phrases create false emphasis. They signal "pay attention" without adding substance.

**Threshold:** WARN if 2+ instances

#### N) Permission-Giving Language

Detects AI's tendency to reassure readers repetitively:

**Common patterns:**
- "It's okay to..."
- "That's okay/normal/fine."
- "Don't worry."
- "No need to..."
- "You don't have to..."
- "It's perfectly normal"

**Why distinctive:** AI uses reassurance as filler. Human writers give permission more sparingly and contextually.

**Threshold:** WARN if 3+ instances

#### O) Meta-Commentary

Detects self-referential statements about the content:

**Common patterns:**
- "I've compiled/gathered/collected"
- "Before you scroll/read"
- "Want a ready-made..."
- "In this article/post/guide"
- "Below you'll find"
- "I'm going to show you"
- "Keep reading to discover"

**Why distinctive:** AI explicitly tells you what it's doing. Human writers usually just do it.

**Threshold:** WARN if 2+ instances

#### P) Parallel Emphasis Structures

Detects parallel sentence structures used for artificial impact:

**Pattern:** Adjacent sentences with identical verb structures
- "Surface conversations maintain relationships. Deep conversations transform them."
- "X creates Y. Z creates Y."

**Why distinctive:** AI loves this rhetorical device for creating "impact" that feels manufactured rather than earned.

**Threshold:** WARN if 2+ instances

#### Q) Formulaic Section Transitions

Detects predictable transitions between sections:

**Common patterns:**
- "Now what?"
- "Here's how:"
- "The goal:"
- "So what does this mean?"
- "What does this look like?"
- "Let's break it down"
- "Here's what you need to know"

**Why distinctive:** AI uses these as structural scaffolding. The transitions are so predictable they become tells.

**Threshold:** WARN if 2+ instances

---

### General Writing Quality Rules

#### Word Choice & Filler Words

Detects overuse of weak, filler words that dilute your message:
- **Banned words**: just, that, really, actually, pretty, very, etc.
- **Thresholds**: FAIL if > 3 per 1,000 words; WARN if 2-3 per 1,000 words

#### Weak Phrases

Flags hedging phrases that undermine authority:
- "I think", "I believe", "it seems", "in my opinion"
- FAIL if used in assertive contexts (with claim verbs like "is", "causes", "shows")

#### Adverbs

Monitors -ly adverb usage:
- WARN if > 8 per 1,000 words
- FAIL if > 15 per 1,000 words
- Always FAIL on stacked intensifiers: "really very quickly", "extremely clearly"

#### Transitions

Detects overuse of formal transitions:
- "moreover", "furthermore", "in addition", "however", "on the other hand"
- WARN if > 4 per 1,000 words

#### Sentence Mechanics

**Conjunction Starts:**
- WARN if > 20% of sentences start with And/But/So/Because/However
- FAIL if 3+ consecutive sentences start with conjunctions

**Vague "This":**
- WARN when sentences start with "This is/means/suggests" (vague reference)

**Sentence Length Variance (Burstiness):**
- WARN if 70%+ of sentences fall within a 10-word band
- Helps detect monotonous rhythm

#### Passive Voice

Uses heuristics to detect passive constructions:
- Patterns like "was implemented", "were created", "is shown"
- WARN if > 12% of sentences are passive (configurable)

#### Repetition

Flags repeated non-stopwords within paragraphs:
- WARN if any word repeats > 4 times within 150 words
- Helps catch unnatural repetition patterns

## Configuration

### contentlint.yaml Structure

```yaml
version: "1.0"

settings:
  exclude:
    - "**/node_modules/**"
    - "**/vendor/**"
  file_types:
    - .md
    - .html

rules:
  - id: banned-words
    enabled: true
    description: "Check for overuse of filler words"
    category: word-choice
    banned_words:
      - just
      - really
      - very
    fail_threshold_per_1000: 3
    warn_threshold_per_1000: 2

  - id: weak-phrases
    enabled: true
    category: word-choice
    phrases:
      - "I think"
      - "I believe"

  # ... more rules

# Directory-specific overrides
overrides:
  - path: "blog/**"
    rules:
      banned-words:
        fail_threshold_per_1000: 4
```

### Rule Configuration

Each rule supports:
- `id` - Unique identifier
- `enabled` - true/false to activate
- `description` - Human-readable explanation
- `category` - Grouping for organization
- Rule-specific thresholds and settings

### Severity Levels

- **PASS** - Informational (currently unused, reserved for future use)
- **WARN** - Should review, may be acceptable in context
- **FAIL** - Significant quality issue, should fix

## Output Formats

### JSON Output

Machine-readable format with full details:

```json
{
  "summary": {
    "total_files": 1,
    "total_findings": 8,
    "severity_counts": {
      "FAIL": 3,
      "WARN": 5,
      "PASS": 0
    },
    "top_rules": {
      "banned-words": 3,
      "weak-phrases": 2
    }
  },
  "files": {
    "article.md": [
      {
        "rule_id": "banned-words",
        "severity": "FAIL",
        "message": "Overuse of 'really': 5 occurrences (15.2 per 1,000 words)",
        "file_path": "article.md",
        "snippet": "...going to be a really great article...",
        "line": 7,
        "details": {
          "word": "really",
          "count": 5,
          "rate": 15.2
        }
      }
    ]
  }
}
```

### Markdown Output

Human-readable report with summary and file-by-file breakdown:

```markdown
# ContentLint Report

## Summary
- **Total Files Scanned**: 1
- **Total Findings**: 8
- **FAIL**: 3
- **WARN**: 5

## Files with Issues

### 🔴 article.md
*3 FAIL, 5 WARN*

**FAIL:**
- [banned-words] (line 7): Overuse of 'really': 5 occurrences
  ```
  ...going to be a really great article...
  ```
```

## CLI Reference

### Commands

#### `lint`

Lint content files for quality issues.

```bash
contentlint lint <path> [options]
```

**Options:**
- `--format, -f` - Output format: `json` or `md` (default: md)
- `--out, -o` - Output file path (default: stdout)
- `--config, -c` - Path to config file (default: ./contentlint.yaml)
- `--fail-on` - Severity level to fail on: `FAIL`, `WARN`, or `PASS` (default: FAIL)
- `--recursive / --no-recursive, -r / -R` - Scan directories recursively (default: true)

**Examples:**

```bash
# Lint directory with markdown output to console
contentlint lint ./content

# Generate JSON report
contentlint lint ./content --format json --out ./reports/report.json

# Fail on warnings
contentlint lint ./content --fail-on WARN

# Single file
contentlint lint ./docs/article.md

# Non-recursive scan
contentlint lint ./content --no-recursive

# Custom config
contentlint lint ./content --config ./custom-rules.yaml
```

#### `init`

Generate a default `contentlint.yaml` configuration file.

```bash
contentlint init [options]
```

**Options:**
- `--output, -o` - Output path for config (default: ./contentlint.yaml)

#### `version`

Show ContentLint version.

```bash
contentlint version
```

## CI Integration

### GitHub Actions

Add this workflow to `.github/workflows/contentlint.yml`:

```yaml
name: ContentLint

on:
  pull_request:
    paths:
      - '**/*.md'
      - '**/*.html'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install ContentLint
        run: |
          pip install -r requirements.txt

      - name: Run ContentLint
        run: |
          python -m contentlint lint ./content \
            --format json \
            --out ./report.json \
            --fail-on FAIL

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: contentlint-report
          path: report.json
```

The workflow will:
1. Run on PRs that modify content files
2. Execute ContentLint
3. Fail the build if FAIL-level issues are found
4. Upload reports as artifacts

### Exit Codes

- `0` - Success, no issues at or above `--fail-on` threshold
- `1` - Failure, issues found at or above threshold, or execution error

## Adding Custom Rules

While the current implementation requires Python code changes to add entirely new rule types, you can easily extend existing rules:

### 1. Add Words to Banned List

Edit `contentlint.yaml`:

```yaml
rules:
  - id: banned-words
    banned_words:
      - just
      - really
      - your-custom-word
```

### 2. Adjust Thresholds

```yaml
rules:
  - id: adverbs
    warn_threshold_per_1000: 6  # More strict
    fail_threshold_per_1000: 10
```

### 3. Add Weak Phrases

```yaml
rules:
  - id: weak-phrases
    phrases:
      - "I think"
      - "your custom phrase"
```

### 4. Directory Overrides

Apply different thresholds to different content types:

```yaml
overrides:
  - path: "blog/**"
    rules:
      banned-words:
        fail_threshold_per_1000: 4  # More lenient for blog

  - path: "marketing/**"
    rules:
      passive-voice:
        threshold_percent: 8  # Stricter for marketing
```

## Tuning Thresholds

### Understanding Rates

**Per 1,000 words**: Normalized frequency
- 3 per 1,000 = 0.3% of content
- A 1,000-word article with 4 instances would be 4 per 1,000

**Percentages**: Relative to total count
- 20% of sentences starting with conjunctions
- 12% passive voice sentences

### Recommended Starting Points

These defaults work well for most content:

| Rule | WARN Threshold | FAIL Threshold |
|------|----------------|----------------|
| Banned words | 2 per 1,000 | 3 per 1,000 |
| Adverbs | 8 per 1,000 | 15 per 1,000 |
| Transitions | 4 per 1,000 | N/A |
| Conjunction starts | 20% | 3 consecutive |
| Passive voice | 12% | N/A |
| Repetition | 4 in 150 words | N/A |

### Tuning Process

1. **Run baseline** - Lint your existing content
2. **Review distribution** - Look at the JSON report's `top_rules`
3. **Adjust thresholds** - Start with FAIL thresholds slightly above your median
4. **Iterate** - Tighten over time as quality improves

## Interpreting Scores

### Severity Interpretation

**FAIL (🔴)**
- Clear quality issues
- Should fix before publishing
- Examples: 5+ uses of "really" per 1,000 words, 4 consecutive sentences starting with "And"

**WARN (🟡)**
- Potential issues worth reviewing
- May be acceptable in context
- Examples: 2-3 "really" per 1,000 words, sentence length uniformity

**PASS (🟢)**
- Currently unused
- Reserved for future positive signals

### What to Fix First

1. **FAIL items** - Always address these
2. **High-frequency rules** - Check `top_rules` in JSON report
3. **Low-hanging fruit** - Banned words are easiest to fix
4. **Structural issues** - Sentence variance and passive voice require more rewriting

### Context Matters

Not every finding requires action:
- Technical content may legitimately use more passive voice
- Conversational blog posts may accept some filler words
- Use directory overrides to reflect these differences

## Architecture

### File Structure

```
contentlint/
├── contentlint/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # CLI entry point (Typer)
│   ├── engine.py            # Core linting engine
│   ├── rules.py             # Rule checker implementations
│   ├── parsers.py           # Markdown & HTML parsers
│   ├── reporters.py         # JSON & Markdown reporters
│   └── utils.py             # Shared utilities
├── contentlint.yaml         # Default rule configuration
├── examples/                # Sample content and outputs
├── .github/workflows/       # CI configuration
└── README.md
```

### Design Principles

1. **Deterministic** - No randomness, LLMs, or external APIs
2. **Fast** - Pure Python with regex and heuristics
3. **Configurable** - All thresholds in YAML, no code changes needed
4. **Extensible** - New rule types can be added in `rules.py`
5. **Transparent** - Every finding includes location, snippet, and details

## Development

### Running from Source

```bash
# Install in development mode
pip install -e .

# Run directly
python -m contentlint lint ./content
```

### Project Requirements

- Python 3.8+
- typer (CLI framework)
- pyyaml (config parsing)
- beautifulsoup4 (HTML parsing)
- rich (terminal output)

## Limitations

### What ContentLint Does NOT Do

- ❌ **Rewrite text** - Only flags issues, doesn't fix them
- ❌ **Grammar checking** - Use Grammarly or LanguageTool for this
- ❌ **Style enforcement** - Not for brand voice or tone
- ❌ **Plagiarism detection** - Not a content similarity tool
- ❌ **SEO optimization** - Doesn't check keywords, meta tags, etc.

### Known Edge Cases

- **Sentence splitting** - Handles common abbreviations but not exhaustive
- **HTML line numbers** - Best effort; may be approximate
- **Passive voice** - Heuristic-based; may have false positives/negatives
- **Context-free** - Doesn't understand semantic meaning of text

## Roadmap

Future enhancements:
- [ ] Support for more file formats (DocX, plain text)
- [ ] Custom rule definitions in YAML (regex patterns without code)
- [ ] Readability scores (Flesch, Gunning Fog)
- [ ] Integration with popular CMSs
- [ ] VS Code extension
- [ ] Pre-commit hooks

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

- **Issues**: Report bugs at [GitHub Issues](https://github.com/yourusername/contentlint/issues)
- **Documentation**: See this README and inline code comments
- **Examples**: Check the `examples/` directory

---

Built with ❤️ for better content quality.
