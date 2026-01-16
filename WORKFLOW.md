# ContentLint Workflow Guide

This guide shows how to integrate ContentLint into your content creation workflow.

## Table of Contents

1. [Individual Writer Workflow](#individual-writer-workflow)
2. [Team Workflow](#team-workflow)
3. [CI/CD Integration](#cicd-integration)
4. [Editor Integration](#editor-integration)
5. [Custom Rule Configuration](#custom-rule-configuration)

---

## Individual Writer Workflow

### Basic Usage

**Before you start writing:**
```bash
# Initialize config in your content directory
cd my-content-folder
contentlint init
```

**While writing (check your work):**
```bash
# Lint current file
contentlint lint article.md

# Get human-readable output
contentlint lint article.md --format md

# See only failures
contentlint lint article.md --fail-on FAIL
```

**Before publishing:**
```bash
# Lint entire folder
contentlint lint ./content

# Generate report for review
contentlint lint ./content --format md --out content-review.md
```

### Recommended Workflow

1. **Draft** - Write without linting (let ideas flow)
2. **First pass** - Run ContentLint, fix FAIL items
3. **Second pass** - Review WARN items, fix what makes sense
4. **Final check** - Run one more time before publishing

**Pro tip:** Not every finding requires action. Use your judgment, especially for:
- Repetition in question lists (expected pattern)
- Conversational hooks in truly conversational content
- Rule of three in intentional rhetorical devices

---

## Team Workflow

### Pre-Commit Hooks (Catch issues before commit)

**Setup once per repo:**
```bash
# Copy pre-commit hook
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**What happens:**
- Every time someone commits .md files, ContentLint runs automatically
- If FAIL items are found, commit is blocked
- Writer fixes issues and commits again
- Can skip with `git commit --no-verify` (emergencies only)

### Content Review Process

**1. Writer creates content:**
```bash
# Write article
vim new-article.md

# Self-lint
contentlint lint new-article.md

# Fix FAIL items, review WARN items
# Commit when clean
git add new-article.md
git commit -m "Add new article"
```

**2. Editor reviews:**
```bash
# Pull latest
git pull

# Generate full report
contentlint lint ./content --format md --out editorial-review.md

# Review report alongside content
# Provide feedback on what to fix vs what to keep
```

**3. Final approval:**
```bash
# After fixes, final lint
contentlint lint ./content --fail-on WARN

# If passes, approve for publish
```

### Team Rules Configuration

Create different configs for different content types:

**Blog posts** (more lenient):
```yaml
# blog-contentlint.yaml
rules:
  - id: conversational-hooks
    enabled: true
    threshold_count: 4  # More lenient for blogs

  - id: banned-words
    fail_threshold_per_1000: 5  # Higher tolerance
```

**Marketing pages** (stricter):
```yaml
# marketing-contentlint.yaml
rules:
  - id: ai-vocabulary
    enabled: true
    fail_threshold_per_1000: 2  # Very strict

  - id: promotional-language
    enabled: false  # Marketing is supposed to be promotional
```

**Use with:**
```bash
contentlint lint blog/ --config blog-contentlint.yaml
contentlint lint marketing/ --config marketing-contentlint.yaml
```

---

## CI/CD Integration

### GitHub Actions (Automatic PR checks)

Already configured in `.github/workflows/contentlint.yml`

**What happens:**
1. Someone opens PR with .md file changes
2. GitHub Actions runs ContentLint automatically
3. If fails, PR shows red X
4. Report uploaded as artifact
5. PR comment shows summary

**To enable:**
```bash
git add .github/workflows/contentlint.yml
git commit -m "Add ContentLint CI/CD"
git push
```

**Adjust strictness:**
```yaml
# In contentlint.yml, change this line:
--fail-on FAIL  # Only fail on FAIL items

# To:
--fail-on WARN  # Stricter: fail on warnings too
```

### GitLab CI

Create `.gitlab-ci.yml`:
```yaml
contentlint:
  image: python:3.11
  before_script:
    - pip install beautifulsoup4 pyyaml typer rich
  script:
    - python3 -m contentlint lint ./content --fail-on FAIL
  artifacts:
    reports:
      junit: report.json
  only:
    changes:
      - "**/*.md"
      - "**/*.html"
```

---

## Editor Integration

### VSCode

**Setup (one-time):**

Tasks already configured in `.vscode/tasks.json`

**Usage:**

1. Open Command Palette (`Cmd+Shift+P`)
2. Type "Tasks: Run Task"
3. Select "ContentLint: Current File"

**Keyboard shortcut (recommended):**

Add to your `keybindings.json`:
```json
{
  "key": "cmd+shift+l",
  "command": "workbench.action.tasks.runTask",
  "args": "ContentLint: Current File"
}
```

Now `Cmd+Shift+L` lints current file.

### Vim/Neovim

**With ALE:**
```vim
" In .vimrc or init.vim
let g:ale_linters = {
\   'markdown': ['contentlint'],
\}

let g:ale_markdown_contentlint_executable = 'python3'
let g:ale_markdown_contentlint_options = '-m contentlint lint'
```

**Manual command:**
```vim
:!python3 -m contentlint lint %
```

### Emacs

```elisp
;; In .emacs or init.el
(defun contentlint-buffer ()
  "Run ContentLint on current buffer"
  (interactive)
  (shell-command
   (format "python3 -m contentlint lint %s"
           (shell-quote-argument (buffer-file-name)))))

(global-set-key (kbd "C-c l") 'contentlint-buffer)
```

---

## Custom Rule Configuration

### Disable Rules You Don't Need

**For your content style:**
```yaml
# contentlint.yaml
rules:
  # Keep AI detection
  - id: ai-vocabulary
    enabled: true

  # Disable conversational checks (if you WANT conversational tone)
  - id: conversational-hooks
    enabled: false

  - id: formulaic-empathy
    enabled: false

  # Keep generic quality checks
  - id: banned-words
    enabled: true
```

### Adjust Thresholds Per Content Type

**Example: Listicle content naturally has repetition**
```yaml
rules:
  - id: repetition
    enabled: true
    threshold_count: 8  # Higher tolerance for lists
    window_words: 200   # Larger window

overrides:
  - path: "listicles/**"
    rules:
      repetition:
        threshold_count: 12  # Even higher for listicle directory
```

### Project-Specific Words

**Add domain-specific vocabulary:**
```yaml
rules:
  - id: banned-words
    enabled: true
    banned_words:
      - just
      - really
      - very
      # But NOT your product names or domain terms:
      # - "intimacy"  # This is our product name
      # - "conversation"  # Core to our content
```

---

## Common Workflows

### Pre-Publish Checklist

```bash
# 1. Lint everything
contentlint lint ./content

# 2. Generate report
contentlint lint ./content --format md --out review.md

# 3. Review report
cat review.md

# 4. Fix FAIL items
# (edit files)

# 5. Verify fixes
contentlint lint ./content --fail-on FAIL

# 6. Review WARN items (optional but recommended)
# Decide what to keep vs fix

# 7. Final check
contentlint lint ./content

# 8. If clean enough, publish
git add .
git commit -m "Publish content batch"
git push
```

### Batch Content Audit

```bash
# Audit entire content library
contentlint lint ./all-content --format json --out audit.json

# Process results
python3 << EOF
import json
with open('audit.json') as f:
    data = json.load(f)

# Find worst offenders
files_by_issues = sorted(
    data['files'].items(),
    key=lambda x: len(x[1]),
    reverse=True
)

print("Top 10 files needing attention:")
for file_path, findings in files_by_issues[:10]:
    fail_count = sum(1 for f in findings if f['severity'] == 'FAIL')
    print(f"{file_path}: {fail_count} FAIL items")
EOF
```

### Quick Fix Common Issues

**Remove filler words:**
```bash
# Find all instances of "really"
grep -r "really" ./content

# Use sed for bulk replacement (backup first!)
find ./content -name "*.md" -exec sed -i.bak 's/\breally\b//g' {} \;
```

**Check before committing fixes:**
```bash
contentlint lint ./content
git diff  # Review all changes
```

---

## Tips & Best Practices

### Do:
✅ Run ContentLint before committing
✅ Review WARN items - they might be fine in context
✅ Adjust thresholds for your content style
✅ Disable rules that don't fit your voice
✅ Use pre-commit hooks to catch issues early

### Don't:
❌ Blindly fix every warning
❌ Let perfect be the enemy of good
❌ Use `--no-verify` as a habit
❌ Ignore all FAIL items
❌ Run on content mid-draft (wait until first complete draft)

### When to Override:

**It's okay to keep flagged patterns when:**
- Repetition is intentional (questions, examples)
- Conversational hooks fit your brand voice
- Parallel structures are rhetorical choices
- You're writing genuinely conversational content (not AI-generated)

**The goal:** Catch AI-generated slop and improve quality, not eliminate personality.

---

## Troubleshooting

**ContentLint too strict?**
```bash
# Adjust thresholds in contentlint.yaml
# Or use custom config per directory
```

**False positives on human content?**
```bash
# Disable specific rules that don't fit your style
# Keep AI detection rules, adjust general quality rules
```

**Want to see what's being flagged?**
```bash
# Use --format md for detailed explanations
contentlint lint file.md --format md | less
```

**Need help?**
- Check GitHub issues: [github.com/yourusername/contentlint/issues](https://github.com/yourusername/contentlint/issues)
- Read full docs: `README.md`
- Review rule descriptions: `contentlint.yaml`
