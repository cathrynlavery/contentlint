# ContentLint Report

## Summary

- **Total Files Scanned**: 1
- **Total Findings**: 8
- **FAIL**: 3
- **WARN**: 5
- **PASS**: 0

## Top Issues

- **banned-words**: 3 occurrences
- **weak-phrases**: 2 occurrences
- **stacked-intensifiers**: 1 occurrences
- **conjunction-starts**: 1 occurrences
- **repetition**: 1 occurrences

## Files with Issues

### 🔴 examples/sample-content.md
*3 FAIL, 5 WARN*

**FAIL:**
- [banned-words] (line 7): Overuse of 'really': 5 occurrences (15.2 per 1,000 words)
  ```
  ...going to be a really great article. Actually...
  ```
- [weak-phrases] (line 7): Weak phrase: 'I think'
  ```
  I think that this is going to be...
  ```
- [stacked-intensifiers] (line 19): Stacked intensifier: 'Really very quickly'
  ```
  Really very quickly, we can see...
  ```
- [conjunction-starts] (line 13): 4 consecutive sentences start with conjunctions
  ```
  And another thing to consider...
  ```

**WARN:**
- [banned-words] (line 7): Overuse of 'pretty': 2 occurrences (6.1 per 1,000 words)
  ```
  ...the content is pretty interesting, and I believe...
  ```
- [weak-phrases] (line 7): Weak phrase: 'I believe'
  ```
  ...and I believe it will really help...
  ```
- [transitions] (line 11): Overuse of transitions: 3 occurrences (9.1 per 1,000 words)
  ```
  Moreover, there are many things...
  ```
- [vague-this] (line 15): Vague 'this' at sentence start: 'This means'
  ```
  However, this means that we should...
  ```
- [repetition] (line 23): Word 'productivity' repeated 6 times in 150-word window
  ```
  The productivity system is designed...
  ```


## Recommendations

1. **FAIL items**: Address these immediately - they significantly impact content quality
2. **WARN items**: Review and fix where appropriate
3. Review the most common issues (Top Issues section) first for maximum impact
