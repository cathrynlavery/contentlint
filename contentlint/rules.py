"""Rule implementations for ContentLint."""

import re
from typing import List, Dict, Any, Tuple
from collections import Counter
from .utils import (
    split_sentences,
    tokenize_words,
    get_stopwords,
    calculate_line_number,
    get_context_snippet,
    words_per_thousand,
    percentage
)


class Finding:
    """Represents a single linting finding."""

    def __init__(
        self,
        rule_id: str,
        severity: str,
        message: str,
        file_path: str,
        snippet: str,
        line: int = None,
        details: Dict[str, Any] = None
    ):
        self.rule_id = rule_id
        self.severity = severity  # PASS, WARN, FAIL
        self.message = message
        self.file_path = file_path
        self.snippet = snippet
        self.line = line
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            'rule_id': self.rule_id,
            'severity': self.severity,
            'message': self.message,
            'file_path': self.file_path,
            'snippet': self.snippet,
            'line': self.line,
            'details': self.details
        }


class RuleChecker:
    """Base class for rule checkers."""

    def __init__(self, rule_config: Dict[str, Any]):
        self.config = rule_config
        self.rule_id = rule_config['id']
        self.description = rule_config.get('description', '')
        self.category = rule_config.get('category', 'general')

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        """Check text against this rule and return findings."""
        raise NotImplementedError


class BannedWordsChecker(RuleChecker):
    """Check for overuse of banned/filler words."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        words = tokenize_words(text)
        total_words = len(words)

        if total_words == 0:
            return findings

        banned_words = self.config.get('banned_words', [])
        fail_threshold = self.config.get('fail_threshold_per_1000', 3)
        warn_threshold = self.config.get('warn_threshold_per_1000', 2)

        word_counts = Counter(words)

        for banned_word in banned_words:
            count = word_counts.get(banned_word.lower(), 0)
            rate = words_per_thousand(count, total_words)

            if rate > fail_threshold:
                severity = 'FAIL'
            elif rate > warn_threshold:
                severity = 'WARN'
            else:
                continue

            # Find first occurrence for snippet
            pattern = re.compile(r'\b' + re.escape(banned_word) + r'\b', re.IGNORECASE)
            match = pattern.search(text)

            if match:
                snippet = get_context_snippet(text, match.start(), match.end())
                line = calculate_line_number(raw_text, match.start())

                findings.append(Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    message=f"Overuse of '{banned_word}': {count} occurrences ({rate:.1f} per 1,000 words)",
                    file_path=file_path,
                    snippet=snippet,
                    line=line,
                    details={'word': banned_word, 'count': count, 'rate': rate}
                ))

        return findings


class WeakPhrasesChecker(RuleChecker):
    """Check for weak phrases like 'I think', 'I believe'."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        weak_phrases = self.config.get('phrases', [])

        for phrase in weak_phrases:
            pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(text))

            for match in matches:
                snippet = get_context_snippet(text, match.start(), match.end())
                line = calculate_line_number(raw_text, match.start())

                # Check if in assertive context (heuristic)
                # Get surrounding sentence
                sentence_start = max(0, text.rfind('.', 0, match.start()) + 1)
                sentence_end = text.find('.', match.end())
                if sentence_end == -1:
                    sentence_end = len(text)

                sentence = text[sentence_start:sentence_end].lower()

                # Check for claim verbs
                claim_verbs = ['is', 'are', 'causes', 'leads to', 'results in', 'means', 'shows', 'proves']
                is_assertive = any(verb in sentence for verb in claim_verbs)

                severity = 'FAIL' if is_assertive else 'WARN'

                findings.append(Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    message=f"Weak phrase: '{match.group()}'",
                    file_path=file_path,
                    snippet=snippet,
                    line=line,
                    details={'phrase': match.group(), 'assertive_context': is_assertive}
                ))

        return findings


class AdverbsChecker(RuleChecker):
    """Check for overuse of -ly adverbs."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        words = tokenize_words(text)
        total_words = len(words)

        if total_words == 0:
            return findings

        # Find -ly words (excluding common non-adverbs)
        ly_exceptions = {'fly', 'supply', 'apply', 'reply', 'multiply', 'early', 'only', 'daily', 'family', 'july', 'likely'}
        ly_words = [w for w in words if w.endswith('ly') and w not in ly_exceptions and len(w) > 3]

        ly_count = len(ly_words)
        ly_rate = words_per_thousand(ly_count, total_words)

        warn_threshold = self.config.get('warn_threshold_per_1000', 8)
        fail_threshold = self.config.get('fail_threshold_per_1000', 15)

        if ly_rate > fail_threshold:
            severity = 'FAIL'
        elif ly_rate > warn_threshold:
            severity = 'WARN'
        else:
            return findings

        # Find first occurrence for snippet
        if ly_words:
            first_ly = ly_words[0]
            pattern = re.compile(r'\b' + re.escape(first_ly) + r'\b', re.IGNORECASE)
            match = pattern.search(text)

            if match:
                snippet = get_context_snippet(text, match.start(), match.end())
                line = calculate_line_number(raw_text, match.start())

                findings.append(Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    message=f"Overuse of -ly adverbs: {ly_count} occurrences ({ly_rate:.1f} per 1,000 words)",
                    file_path=file_path,
                    snippet=snippet,
                    line=line,
                    details={'count': ly_count, 'rate': ly_rate}
                ))

        return findings


class StackedIntensifiersChecker(RuleChecker):
    """Check for stacked intensifiers like 'really very' or 'extremely quickly'."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []

        # Pattern: intensifier + -ly word
        intensifiers = r'\b(really|very|extremely|incredibly|absolutely|totally|completely)\s+\w+ly\b'
        pattern = re.compile(intensifiers, re.IGNORECASE)

        matches = pattern.finditer(text)

        for match in matches:
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='FAIL',
                message=f"Stacked intensifier: '{match.group()}'",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'phrase': match.group()}
            ))

        return findings


class TransitionsChecker(RuleChecker):
    """Check for overuse of transition words."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        words = tokenize_words(text)
        total_words = len(words)

        if total_words == 0:
            return findings

        transitions = self.config.get('transitions', [])
        threshold = self.config.get('threshold_per_1000', 4)

        # Count all transitions
        transition_count = 0
        for transition in transitions:
            # Handle multi-word transitions
            transition_lower = transition.lower()
            text_lower = text.lower()
            transition_count += text_lower.count(transition_lower)

        rate = words_per_thousand(transition_count, total_words)

        if rate > threshold:
            # Find first occurrence
            for transition in transitions:
                pattern = re.compile(r'\b' + re.escape(transition) + r'\b', re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    snippet = get_context_snippet(text, match.start(), match.end())
                    line = calculate_line_number(raw_text, match.start())

                    findings.append(Finding(
                        rule_id=self.rule_id,
                        severity='WARN',
                        message=f"Overuse of transitions: {transition_count} occurrences ({rate:.1f} per 1,000 words)",
                        file_path=file_path,
                        snippet=snippet,
                        line=line,
                        details={'count': transition_count, 'rate': rate}
                    ))
                    break

        return findings


class ConjunctionStartChecker(RuleChecker):
    """Check for sentences starting with conjunctions."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        sentences = split_sentences(text)

        if len(sentences) == 0:
            return findings

        conjunctions = self.config.get('conjunctions', ['and', 'but', 'so', 'because', 'however'])
        threshold_percent = self.config.get('threshold_percent', 20)
        consecutive_threshold = self.config.get('consecutive_threshold', 3)

        conjunction_starts = []
        consecutive_count = 0
        max_consecutive = 0

        for i, sentence in enumerate(sentences):
            first_word = sentence.split()[0].lower().rstrip('.,!?;:') if sentence.split() else ''

            if first_word in conjunctions:
                conjunction_starts.append(i)
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0

        percent = percentage(len(conjunction_starts), len(sentences))

        # Check consecutive first
        if max_consecutive >= consecutive_threshold:
            # Find the consecutive sequence
            consecutive_count = 0
            for i, sentence in enumerate(sentences):
                first_word = sentence.split()[0].lower().rstrip('.,!?;:') if sentence.split() else ''
                if first_word in conjunctions:
                    consecutive_count += 1
                    if consecutive_count >= consecutive_threshold:
                        # Find this sentence in raw text
                        pattern = re.compile(re.escape(sentence[:30]), re.IGNORECASE)
                        match = pattern.search(text)
                        if match:
                            snippet = get_context_snippet(text, match.start(), match.end())
                            line = calculate_line_number(raw_text, match.start())

                            findings.append(Finding(
                                rule_id=self.rule_id,
                                severity='FAIL',
                                message=f"{max_consecutive} consecutive sentences start with conjunctions",
                                file_path=file_path,
                                snippet=snippet,
                                line=line,
                                details={'consecutive_count': max_consecutive}
                            ))
                            break
                else:
                    consecutive_count = 0

        # Check overall percentage
        elif percent > threshold_percent:
            # Find first occurrence
            for idx in conjunction_starts[:1]:
                sentence = sentences[idx]
                pattern = re.compile(re.escape(sentence[:30]), re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    snippet = get_context_snippet(text, match.start(), match.end())
                    line = calculate_line_number(raw_text, match.start())

                    findings.append(Finding(
                        rule_id=self.rule_id,
                        severity='WARN',
                        message=f"{percent:.1f}% of sentences start with conjunctions (threshold: {threshold_percent}%)",
                        file_path=file_path,
                        snippet=snippet,
                        line=line,
                        details={'percent': percent, 'count': len(conjunction_starts), 'total_sentences': len(sentences)}
                    ))

        return findings


class VagueThisChecker(RuleChecker):
    """Check for vague 'this' at start of sentences."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []

        # Pattern: sentence starts with "This" followed by vague verb
        vague_patterns = [
            r'\bThis\s+(is|means|suggests|indicates|shows|implies)\b',
            r'\bThis\s+can\b',
            r'\bThis\s+will\b',
        ]

        for pattern_str in vague_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.finditer(text)

            for match in matches:
                # Check if this is near sentence start
                preceding = text[max(0, match.start() - 5):match.start()]
                if not preceding or preceding.strip() == '' or preceding.strip().endswith('.'):
                    snippet = get_context_snippet(text, match.start(), match.end())
                    line = calculate_line_number(raw_text, match.start())

                    findings.append(Finding(
                        rule_id=self.rule_id,
                        severity='WARN',
                        message=f"Vague 'this' at sentence start: '{match.group()}'",
                        file_path=file_path,
                        snippet=snippet,
                        line=line,
                        details={'phrase': match.group()}
                    ))

        return findings


class SentenceLengthVarianceChecker(RuleChecker):
    """Check sentence length variance (burstiness)."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        sentences = split_sentences(text)

        if len(sentences) < 5:
            return findings

        # Calculate word count per sentence
        sentence_lengths = [len(tokenize_words(s)) for s in sentences]

        if not sentence_lengths:
            return findings

        # Find the most common 10-word band
        min_len = min(sentence_lengths)
        max_len = max(sentence_lengths)

        best_band_count = 0
        best_band = (0, 10)

        for start in range(min_len, max_len):
            end = start + 10
            count = sum(1 for length in sentence_lengths if start <= length < end)
            if count > best_band_count:
                best_band_count = count
                best_band = (start, end)

        percent_in_band = percentage(best_band_count, len(sentences))
        threshold = self.config.get('threshold_percent', 70)

        if percent_in_band >= threshold:
            # Report on first sentence
            snippet = sentences[0][:60] + '...' if len(sentences[0]) > 60 else sentences[0]
            line = calculate_line_number(raw_text, 0)

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='WARN',
                message=f"Low sentence length variance: {percent_in_band:.1f}% of sentences are {best_band[0]}-{best_band[1]} words",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={
                    'percent_in_band': percent_in_band,
                    'band_range': best_band,
                    'sentence_count': len(sentences),
                    'avg_length': sum(sentence_lengths) / len(sentence_lengths)
                }
            ))

        return findings


class PassiveVoiceChecker(RuleChecker):
    """Check for passive voice usage."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        sentences = split_sentences(text)

        if len(sentences) == 0:
            return findings

        # Heuristic: was/were/is/are + past participle
        passive_pattern = r'\b(was|were|is|are|been|be)\s+(\w+ed|been|done|made|taken|given|shown|seen|found|used|known)\b'
        pattern = re.compile(passive_pattern, re.IGNORECASE)

        passive_count = 0
        first_match = None

        for sentence in sentences:
            if pattern.search(sentence):
                passive_count += 1
                if first_match is None:
                    match = pattern.search(text)
                    first_match = match

        percent = percentage(passive_count, len(sentences))
        threshold = self.config.get('threshold_percent', 12)

        if percent > threshold and first_match:
            snippet = get_context_snippet(text, first_match.start(), first_match.end())
            line = calculate_line_number(raw_text, first_match.start())

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='WARN',
                message=f"High passive voice usage: {percent:.1f}% of sentences (threshold: {threshold}%)",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'percent': percent, 'count': passive_count, 'total_sentences': len(sentences)}
            ))

        return findings


class RepetitionChecker(RuleChecker):
    """Check for repeated words within paragraphs."""

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []

        # Split into paragraphs
        paragraphs = text.split('\n\n')
        stopwords = get_stopwords()
        threshold = self.config.get('threshold_count', 4)
        window_words = self.config.get('window_words', 150)

        for para in paragraphs:
            words = tokenize_words(para)

            # Use sliding window
            for i in range(0, len(words), window_words // 2):
                window = words[i:i + window_words]
                word_counts = Counter(w for w in window if w not in stopwords and len(w) > 4)

                for word, count in word_counts.items():
                    if count > threshold:
                        # Find first occurrence in text
                        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                        match = pattern.search(para)

                        if match:
                            snippet = get_context_snippet(para, match.start(), match.end())
                            # Find in original text
                            para_match = re.search(re.escape(para[:50]), text)
                            line = calculate_line_number(raw_text, para_match.start() if para_match else 0)

                            findings.append(Finding(
                                rule_id=self.rule_id,
                                severity='WARN',
                                message=f"Word '{word}' repeated {count} times in {window_words}-word window",
                                file_path=file_path,
                                snippet=snippet,
                                line=line,
                                details={'word': word, 'count': count, 'window_size': window_words}
                            ))

        return findings


class RuleRegistry:
    """Registry of all available rule checkers."""

    CHECKER_MAP = {
        'banned-words': BannedWordsChecker,
        'weak-phrases': WeakPhrasesChecker,
        'adverbs': AdverbsChecker,
        'stacked-intensifiers': StackedIntensifiersChecker,
        'transitions': TransitionsChecker,
        'conjunction-starts': ConjunctionStartChecker,
        'vague-this': VagueThisChecker,
        'sentence-variance': SentenceLengthVarianceChecker,
        'passive-voice': PassiveVoiceChecker,
        'repetition': RepetitionChecker,
    }

    @classmethod
    def create_checker(cls, rule_config: Dict[str, Any]) -> RuleChecker:
        """Create a checker instance for a rule."""
        rule_id = rule_config['id']
        checker_class = cls.CHECKER_MAP.get(rule_id)

        if checker_class is None:
            raise ValueError(f"Unknown rule type: {rule_id}")

        return checker_class(rule_config)
