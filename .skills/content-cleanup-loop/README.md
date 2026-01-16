# Content Cleanup Loop

## Quick Start

### Use this command:

```
Run the content cleanup loop on [folder path]
```

**Example:**
```
Run the content cleanup loop on /Users/cathrynlavery/BestSelf Co/Business/SEO/articles
```

## What It Does

1. **Lints** all content files in the folder
2. **Creates a todo list** prioritized by severity (FAIL → AI patterns → WARN)
3. **Fixes issues** one file at a time
4. **Re-lints** after each fix to verify
5. **Repeats** until all FAIL items are gone
6. **Reports** final status

## Options

### Fix FAIL items only (recommended first pass):
```
Run the content cleanup loop on [folder] - fix FAIL items only
```

### Fix everything including WARN items:
```
Run the content cleanup loop on [folder] - fix all issues
```

### Dry run (show what would be fixed without changing files):
```
Run the content cleanup loop on [folder] - dry run
```

## What Gets Fixed

### Automatically Fixed:
- ✅ AI vocabulary (delve → explore, underscore → emphasize)
- ✅ Filler words (really, very, just removed/rewritten)
- ✅ AI patterns (Here's the thing, I've compiled - deleted)
- ✅ Promotional language (boasts → has, nestled → located)
- ✅ Knowledge cutoff disclaimers (deleted entirely)
- ✅ Meta-commentary (deleted)

### Reviewed/Selective Fix:
- ⚠️ Conversational hooks (kept if they fit brand voice)
- ⚠️ Repetition (kept if intentional, like in lists)
- ⚠️ Passive voice (rewritten only if awkward)

## Progress Tracking

You'll see:
```
📊 ContentLint Cleanup Progress

Todo List:
✅ article-1.md (8 FAIL items) - FIXED
✅ article-2.md (5 FAIL items) - FIXED
🔄 article-3.md (4 FAIL items) - IN PROGRESS
⏳ article-4.md (12 WARN items) - PENDING
⏳ article-5.md (3 FAIL items) - PENDING

Progress: 2/5 files cleaned
```

## Expected Timeline

- Small article (1-2 issues): ~1 minute
- Medium article (5-10 issues): ~3 minutes
- Large article (15+ issues): ~5-8 minutes
- **Heavily AI-generated** (30+ issues): Consider rewriting from scratch

## Tips

**Before starting:**
- Make sure all files are committed to git
- You can revert if fixes aren't right: `git checkout -- file.md`

**During cleanup:**
- Review the fixes being made
- Stop me if you disagree with a fix
- I'll show you each change before saving

**After cleanup:**
- Review the git diff: `git diff`
- Commit the cleaned files: `git add . && git commit -m "Clean up AI-generated content patterns"`

## Example Session

```
You: Run the content cleanup loop on ./content/blog

Me: Running ContentLint on ./content/blog...

Found 3 files with issues:
- post-1.md: 8 FAIL, 4 WARN
- post-2.md: 5 FAIL, 2 WARN
- post-3.md: 2 FAIL, 8 WARN

Creating todo list...

Working on post-1.md (8 FAIL items):
- Removing AI vocabulary: "delve" → "explore" (3 instances)
- Removing significance language: "stands as testament" → deleted
- Fixing promotional language: "boasts" → "has"
...

✅ post-1.md cleaned! Re-linting... PASS

Working on post-2.md (5 FAIL items):
...

✅ All FAIL items fixed!

Summary:
- Files cleaned: 3
- FAIL items fixed: 15
- WARN items remaining: 14 (mostly acceptable)

Continue with WARN items? [y/n]
```

## Troubleshooting

**"Too many issues to fix"**
→ File might be heavily AI-generated. Better to rewrite from scratch.

**"Fixes changed the meaning"**
→ I'll show you the diff and we can adjust

**"Want to skip a file"**
→ Just say "skip this one" and I'll move to the next

**"Some WARN items should stay"**
→ That's normal! WARN items are often acceptable (repetition in lists, conversational tone, etc.)
