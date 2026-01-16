# Content Cleanup Loop Skill

## Purpose
Systematically clean up a folder of articles by linting, creating a prioritized todo list, fixing issues, and repeating until all content passes ContentLint checks.

## When to Use
- User says "clean up my articles"
- User wants to lint and fix a directory of content
- User asks to "run contentlint and fix issues"
- User wants automated content cleanup

## Instructions

You are implementing a systematic content cleanup workflow. Your goal is to take a directory of content files, lint them, identify issues, fix them, and repeat until all files pass ContentLint checks.

### Step 1: Initial Lint and Assessment

First, run ContentLint on the specified directory:

```bash
cd /path/to/contentlint
python3 -m contentlint lint /path/to/content-folder --format json --out /tmp/lint-report.json
```

### Step 2: Analyze Results and Create Todo List

Read the lint report and create a prioritized todo list using the TodoWrite tool:

**Priority order:**
1. **FAIL items** - Must be fixed (highest priority)
2. **AI detection patterns** - Shows AI-generated content
3. **WARN items** - Should be reviewed/fixed

**Organize by:**
- File with most issues first
- Within each file: FAIL → AI patterns → WARN

**Create todos like:**
```
- Fix 'article1.md': 5 FAIL items (ai-vocabulary, banned-words)
- Fix 'article2.md': 3 FAIL items (knowledge-cutoff, promotional-language)
- Review 'article3.md': 8 WARN items (conversational-hooks, meta-commentary)
```

### Step 3: Work Through Files Systematically

For each file in your todo list:

1. **Read the file**
2. **Identify the specific issues** from the lint report
3. **Fix the issues:**
   - **AI vocabulary** - Replace AI words with natural alternatives
     - "delve into" → "explore" or "examine"
     - "underscore" → "emphasize" or "show"
     - "tapestry" → "collection" or specific term
     - "pivotal" → "important" or "key"
     - "landscape" → specific term (market, field, etc.)

   - **Banned words (filler)** - Remove or rephrase
     - "really", "very", "just" → often can be deleted
     - "that" → rewrite sentence structure

   - **AI patterns** - Rewrite to sound human
     - "Here's the thing:" → Delete or rephrase naturally
     - "I've compiled" → Delete meta-commentary
     - Parallel emphasis → Vary sentence structure
     - "Not only...but" → Rewrite more naturally

   - **Promotional language** - Neutralize
     - "boasts" → "has" or "includes"
     - "nestled" → "located"
     - "vibrant" → Delete or be specific

   - **Knowledge cutoff disclaimers** - Delete entirely
     - "Based on available information" → Delete
     - "as of my last update" → Delete

4. **Save the fixes** using the Edit tool
5. **Mark the todo as completed**
6. **Re-lint just that file** to verify fixes:
   ```bash
   python3 -m contentlint lint /path/to/fixed-file.md
   ```

### Step 4: Loop Until Clean

After fixing each file:

1. **Re-run ContentLint** on the entire directory
2. **Check if any FAIL items remain**
3. **If issues remain:**
   - Update todo list with remaining issues
   - Continue to next file
4. **If all files pass:**
   - Report completion
   - Show final summary

### Step 5: Final Report

When all files are clean (or only acceptable WARN items remain):

```
✅ Content cleanup complete!

Summary:
- Files processed: 15
- FAIL items fixed: 47
- WARN items fixed: 23
- AI patterns removed: 31

Remaining WARN items: 8 (acceptable - natural repetition in lists)

All files now pass ContentLint FAIL threshold.
```

## Important Guidelines

### DO:
- ✅ Work on ONE file at a time
- ✅ Re-lint after each file to verify fixes
- ✅ Preserve the author's voice and meaning
- ✅ Mark todos completed as you go
- ✅ Show progress after each file

### DON'T:
- ❌ Try to fix all files at once
- ❌ Remove personality or brand voice
- ❌ Change technical terms or product names
- ❌ Fix acceptable WARN items (like repetition in question lists)
- ❌ Make the content generic by over-editing

### When to Stop:

Stop when:
1. All FAIL items are fixed
2. All AI detection patterns are removed or justified
3. Only acceptable WARN items remain (repetition in lists, intentional conversational hooks, etc.)

**Ask the user** if they want to continue with WARN items, or if FAIL-only cleanup is sufficient.

## Example Workflow

**User:** "Clean up my articles in /content/blog"

**Assistant:**
1. Runs ContentLint on /content/blog
2. Creates todo list:
   ```
   - Fix article-1.md: 8 FAIL (ai-vocabulary, significance-language)
   - Fix article-2.md: 5 FAIL (knowledge-cutoff, promotional-language)
   - Review article-3.md: 12 WARN (conversational-hooks, repetition)
   ```
3. Works on article-1.md:
   - Reads file
   - Identifies: "delve into" (3x), "underscore the importance" (2x), "stands as testament"
   - Fixes issues
   - Saves file
   - Re-lints to verify
   - Marks todo complete
4. Works on article-2.md:
   - Same process
5. Continues until all FAIL items fixed
6. Reports completion:
   ```
   ✅ All FAIL items fixed! 3 files cleaned.
   Remaining: 12 WARN items (mostly natural repetition)

   Continue with WARN items? [y/n]
   ```

## Monitoring Progress

After each file:
```
Progress: 2/5 files cleaned
Current: article-3.md (4 FAIL items remaining)
```

## Edge Cases

**If a file has too many issues (20+):**
- Ask user: "article-1.md has 23 issues. This might be AI-generated. Rewrite from scratch or try to fix?"

**If fixes break content:**
- Show diff
- Ask for approval before saving

**If stuck on an issue:**
- Skip that specific issue
- Note it in final report
- Continue with other issues