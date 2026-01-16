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


class AIVocabularyChecker(RuleChecker):
    """Check for overuse of AI-specific vocabulary words identified by Wikipedia.

    These words appear far more frequently in AI-generated text after 2023
    compared to human-written text from before 2023.
    """

    # Default AI vocabulary from Wikipedia research
    DEFAULT_AI_WORDS = [
        'additionally', 'align', 'aligned', 'aligns', 'crucial', 'delve', 'delved', 'delves', 'delving',
        'emphasizing', 'emphasize', 'emphasized', 'enduring', 'enhance', 'enhanced', 'enhances',
        'enhancing', 'fostering', 'foster', 'fostered', 'garner', 'garnered', 'garnering',
        'highlight', 'highlighted', 'highlighting', 'highlights', 'interplay', 'intricate',
        'intricacies', 'landscape', 'pivotal', 'showcase', 'showcased', 'showcases', 'showcasing',
        'tapestry', 'testament', 'underscore', 'underscored', 'underscores', 'underscoring',
        'valuable', 'vibrant'
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        words = tokenize_words(text)
        total_words = len(words)

        if total_words == 0:
            return findings

        ai_words = self.config.get('ai_words', self.DEFAULT_AI_WORDS)
        fail_threshold = self.config.get('fail_threshold_per_1000', 5)
        warn_threshold = self.config.get('warn_threshold_per_1000', 3)
        cluster_threshold = self.config.get('cluster_threshold', 3)

        word_counts = Counter(words)

        # Count total AI vocabulary usage
        total_ai_count = 0
        detected_ai_words = []

        for ai_word in ai_words:
            count = word_counts.get(ai_word.lower(), 0)
            if count > 0:
                total_ai_count += count
                detected_ai_words.append((ai_word, count))

        rate = words_per_thousand(total_ai_count, total_words)

        # Check if we hit thresholds
        if rate > fail_threshold:
            severity = 'FAIL'
        elif rate > warn_threshold:
            severity = 'WARN'
        elif len(detected_ai_words) >= cluster_threshold:
            # Even below threshold, flag if 3+ different AI words appear (clustering effect)
            severity = 'WARN'
        else:
            return findings

        # Find first occurrence for snippet
        for ai_word, count in detected_ai_words:
            pattern = re.compile(r'\b' + re.escape(ai_word) + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            if match:
                snippet = get_context_snippet(text, match.start(), match.end())
                line = calculate_line_number(raw_text, match.start())

                word_list = ', '.join([f"'{w}' ({c}x)" for w, c in detected_ai_words[:5]])
                findings.append(Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    message=f"AI vocabulary detected: {total_ai_count} occurrences ({rate:.1f} per 1,000 words). Words: {word_list}",
                    file_path=file_path,
                    snippet=snippet,
                    line=line,
                    details={
                        'total_count': total_ai_count,
                        'rate': rate,
                        'detected_words': detected_ai_words[:10]
                    }
                ))
                break

        return findings


class SignificanceLanguageChecker(RuleChecker):
    """Check for AI patterns that overemphasize significance, legacy, and broader trends.

    LLMs tend to add statements about how topics represent or contribute to broader
    significance, using a distinct repertoire of phrases.
    """

    DEFAULT_PATTERNS = [
        # "stands/serves as" patterns
        r'\b(stands?|serves?|marks?|represents?)\s+(as\s+)?a\s+(testament|reminder|symbol|pivotal|crucial|vital|significant|key)\b',
        # Significance/importance emphasis
        r'\b(underscores?|highlights?|emphasizes?|symbolizes?)\s+(its|their|the)\s+(importance|significance|role|impact|legacy)\b',
        r'\bplays?\s+a\s+(vital|significant|crucial|pivotal|key)\s+(role|part)\b',
        # Legacy and enduring patterns
        r'\b(enduring|lasting|ongoing|continued)\s+(legacy|significance|impact|relevance|importance)\b',
        # Broader context patterns
        r'\b(reflects?|represents?|symbolizes?)\s+(broader|wider|larger)\s+(trends?|movements?|contexts?|patterns?)\b',
        # Contributing to patterns
        r'\b(contribut(es?|ing)|contribut(es?|ed))\s+to\s+the\s+(broader|wider|larger|overall)\b',
        # Setting the stage/marking patterns
        r'\b(setting\s+the\s+stage|marking|shaping)\s+(the|a)\b',
        # Deeply rooted
        r'\b(deeply|firmly)\s+(rooted|embedded|ingrained)\b',
        # Focal point, indelible mark
        r'\b(focal\s+point|indelible\s+mark|key\s+turning\s+point|pivotal\s+moment)\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)
        threshold = self.config.get('threshold_count', 2)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        if len(all_matches) >= threshold:
            # Report on first match
            match = all_matches[0]
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            severity = 'FAIL' if len(all_matches) >= 4 else 'WARN'

            findings.append(Finding(
                rule_id=self.rule_id,
                severity=severity,
                message=f"Overemphasis on significance/legacy: {len(all_matches)} instances of AI significance language",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'count': len(all_matches)}
            ))

        return findings


class PromotionalLanguageChecker(RuleChecker):
    """Check for promotional and advertisement-like language common in AI text.

    LLMs have serious problems keeping a neutral tone, especially when writing
    about cultural heritage, adding promotional language even when prompted for
    encyclopedic tone.
    """

    DEFAULT_PATTERNS = [
        # Boasts/features patterns
        r'\b(boasts?|features?|offers?|showcases?)\s+a\b',
        # Descriptive puffery
        r'\b(vibrant|rich|profound|breathtaking|stunning|remarkable|exceptional|outstanding)\s+(culture|heritage|landscape|history|tradition|community)\b',
        # Enhancing patterns
        r'\b(enhancing|enriching|elevating)\s+(its|their|the)\b',
        # Natural beauty
        r'\b(natural\s+beauty|scenic\s+landscapes?|breathtaking\s+views?)\b',
        # Nestled/located patterns
        r'\b(nestled|situated|located)\s+(in\s+the\s+heart\s+of|within|amidst)\b',
        # Groundbreaking
        r'\b(groundbreaking|revolutionary|pioneering|innovative)\s+(work|research|approach|method)\b',
        # Renowned
        r'\b(renowned|celebrated|acclaimed|distinguished|esteemed)\s+(for|as)\b',
        # Commitment to
        r'\b(commitment|dedication)\s+to\s+(excellence|quality|sustainability|innovation)\b',
        # Clean and modern
        r'\b(clean\s+and\s+modern|state-of-the-art|world-class|cutting-edge)\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)
        threshold = self.config.get('threshold_count', 2)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        if len(all_matches) >= threshold:
            match = all_matches[0]
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            severity = 'FAIL' if len(all_matches) >= 4 else 'WARN'

            findings.append(Finding(
                rule_id=self.rule_id,
                severity=severity,
                message=f"Promotional language detected: {len(all_matches)} instances of puffery/marketing language",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'count': len(all_matches)}
            ))

        return findings


class SuperficialAnalysisChecker(RuleChecker):
    """Check for superficial analysis patterns with trailing -ing phrases.

    AI chatbots tend to insert superficial analysis by attaching present participle
    phrases at the end of sentences, often with vague attributions.
    """

    DEFAULT_PATTERNS = [
        # Trailing -ing phrases about significance
        r',\s+(highlighting|underscoring|emphasizing|demonstrating|illustrating|showcasing|reflecting|symbolizing)\s+(the|its|their)\s+(importance|significance|impact|role|value|legacy)\b',
        # Ensuring/cultivating patterns
        r',\s+(ensuring|cultivating|fostering|promoting|enabling|facilitating)\s+\w+',
        # Contributing to patterns
        r',\s+(contributing\s+to|reflecting|symbolizing)\s+\w+',
        # Encompassing patterns
        r',\s+(encompassing|spanning|including)\s+\w+',
        # Aligning/resonating patterns
        r',\s+(aligning|resonating)\s+with\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)
        threshold = self.config.get('threshold_count', 3)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        if len(all_matches) >= threshold:
            match = all_matches[0]
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            severity = 'FAIL' if len(all_matches) >= 5 else 'WARN'

            findings.append(Finding(
                rule_id=self.rule_id,
                severity=severity,
                message=f"Superficial analysis detected: {len(all_matches)} trailing -ing phrases adding empty commentary",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'count': len(all_matches)}
            ))

        return findings


class CopulativeAvoidanceChecker(RuleChecker):
    """Check for AI's tendency to avoid simple 'is/are' constructions.

    LLMs often substitute 'serves as' for 'is', 'features' for 'has', making
    text sound more formal but less natural.
    """

    DEFAULT_PATTERNS = [
        # Serves as / stands as patterns (when simple "is" would work)
        r'\b(serves?|stands?)\s+as\s+(a|an|the)\s+\w+',
        # Features/offers instead of has
        r'\b(features?|offers?)\s+(a|an|the|numerous|several|many)\s+\w+',
        # Marks/represents instead of is
        r'\b(marks?|represents?)\s+(a|an|the)\s+(shift|change|transition|milestone)\b',
        # Holds the distinction
        r'\bholds?\s+the\s+(distinction|position|role)\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)
        threshold = self.config.get('threshold_count', 3)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        if len(all_matches) >= threshold:
            match = all_matches[0]
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='WARN',
                message=f"Copulative avoidance: {len(all_matches)} instances of 'serves as/features' instead of 'is/has'",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'count': len(all_matches)}
            ))

        return findings


class NegativeParallelismChecker(RuleChecker):
    """Check for negative parallelisms common in AI writing.

    Parallel constructions involving 'not', 'but', or 'however' such as
    'Not only...but...' or 'It is not just about...it's...' are common in
    LLM writing to appear balanced and thoughtful.
    """

    DEFAULT_PATTERNS = [
        # Not only...but patterns
        r'\bnot\s+only\s+\w+[\w\s,]+but\s+(also\s+)?\w+',
        # Not just/merely...but patterns
        r'\bnot\s+(just|merely|simply)\s+\w+[\w\s,]+but\s+\w+',
        # It's not...it's patterns
        r"\bit'?s\s+not\s+\w+[\w\s,]+it'?s\s+\w+",
        # No...no...just patterns
        r'\bno\s+\w+,\s+no\s+\w+,\s+just\s+\w+',
        # Not...rather patterns
        r'\bnot\s+\w+[\w\s,]+\.\s+[Rr]ather,?\s+(it|this)\s+(is|constitutes|represents)\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        # Report each instance (these are quite distinctive)
        for match in all_matches[:3]:  # Limit to first 3
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='WARN',
                message=f"Negative parallelism detected: '{match.group()[:50]}'",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'phrase': match.group()}
            ))

        return findings


class RuleOfThreeChecker(RuleChecker):
    """Check for overuse of the 'rule of three' pattern.

    LLMs overuse 'adjective, adjective, and adjective' and 'phrase, phrase,
    and phrase' constructions to make superficial analyses appear more comprehensive.
    """

    DEFAULT_PATTERNS = [
        # Three adjectives
        r'\b(\w+),\s+(\w+),?\s+and\s+(\w+)\s+(approach|method|system|framework|strategy|solution|model|perspective)\b',
        # Three nouns/phrases with repetitive structure
        r'\b(\w+\s+\w+),\s+(\w+\s+\w+),?\s+and\s+(\w+\s+\w+)\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)
        threshold = self.config.get('threshold_count', 3)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        if len(all_matches) >= threshold:
            match = all_matches[0]
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='WARN',
                message=f"Overuse of 'rule of three': {len(all_matches)} instances of formulaic X, Y, and Z patterns",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'count': len(all_matches)}
            ))

        return findings


class ChallengesConclusionsChecker(RuleChecker):
    """Check for outline-like conclusions about challenges and future prospects.

    LLM-generated articles often include a 'Challenges' section with formulaic
    'Despite its [positive], [subject] faces challenges...' followed by vaguely
    positive assessments.
    """

    DEFAULT_PATTERNS = [
        # Despite its...faces challenges
        r'\b[Dd]espite\s+(its|their|the)\s+[\w\s,]+faces?\s+(several\s+)?(challenges?|obstacles?|difficulties?)\b',
        # Challenges and Legacy/Future sections
        r'\b(Challenges?\s+and\s+(Legacy|Future|Prospects?)|Future\s+(Outlook|Prospects?))\b',
        # Despite these challenges...continues to
        r'\b[Dd]espite\s+these\s+(challenges?|obstacles?),?[\w\s,]+continues?\s+to\b',
        # Future investments/developments
        r'\b[Ff]uture\s+(investments?|developments?|initiatives?)\s+[\w\s,]+could\s+(enhance|improve|maintain)\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        if all_matches:
            match = all_matches[0]
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            severity = 'FAIL' if len(all_matches) >= 2 else 'WARN'

            findings.append(Finding(
                rule_id=self.rule_id,
                severity=severity,
                message=f"Formulaic challenges/conclusions section detected: {len(all_matches)} AI-style outline patterns",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'count': len(all_matches)}
            ))

        return findings


class KnowledgeCutoffChecker(RuleChecker):
    """Check for knowledge-cutoff disclaimers and speculation about missing information.

    LLMs often output disclaimers about their knowledge cutoff or state that
    'specific details are limited' even when they're fabricating this claim.
    """

    DEFAULT_PATTERNS = [
        # As of date disclaimers
        r'\b[Aa]s\s+of\s+(my\s+)?(last\s+)?(knowledge\s+)?(update|training|information)\b',
        r'\b[Uu]p\s+to\s+my\s+last\s+(training\s+)?(update|knowledge)\b',
        # Information limited/scarce
        r'\b([Ww]hile|[Aa]lthough)\s+(specific\s+)?(details?|information)\s+(is|are|remains?)\s+(limited|scarce|not\s+widely|not\s+extensively)\b',
        # Not documented/available
        r'\b(is\s+)?not\s+(widely\s+)?(documented|available|disclosed|known)\b',
        # Based on available information
        r'\b[Bb]ased\s+on\s+(available|provided|current)\s+(information|sources|data)\b',
        # Maintains privacy/keeps private
        r'\b(maintains?|keeps?)\s+(a\s+low\s+profile|personal\s+details\s+private|much\s+of\s+.+\s+private)\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        # Each instance is quite distinctive
        for match in all_matches[:3]:
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='FAIL',
                message=f"Knowledge cutoff disclaimer: '{match.group()}'",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'phrase': match.group()}
            ))

        return findings


class VagueAttributionChecker(RuleChecker):
    """Check for vague attributions and weasel wording.

    AI chatbots tend to attribute opinions or claims to vague authorities
    like 'observers note' or 'experts argue' without specific citations.
    """

    DEFAULT_PATTERNS = [
        # Vague authorities
        r'\b([Oo]bservers?|[Ee]xperts?|[Aa]nalysts?|[Ss]cholars?|[Rr]esearchers?)\s+(have\s+)?(noted|cited|argued|suggested|observed|pointed\s+out)\b',
        # Industry reports/studies
        r'\b[Ii]ndustry\s+(reports?|studies?|analyses?)\s+(suggest|indicate|show)\b',
        # Some critics/sources
        r'\b[Ss]ome\s+(critics?|sources?|publications?|reviewers?)\s+(argue|suggest|note|claim)\b',
        # Several sources when few cited
        r'\b[Ss]everal\s+(sources?|publications?|studies?)\s+(have\s+)?(cited|noted|described)\b',
        # Have been described as
        r'\b(has|have)\s+been\s+(described|characterized|noted|cited)\s+as\b',
        # According to research/studies (vague)
        r'\b[Aa]ccording\s+to\s+(research|studies?)\b(?!\s+by\s+\w)',  # Without specific attribution
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)
        threshold = self.config.get('threshold_count', 2)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        if len(all_matches) >= threshold:
            match = all_matches[0]
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='WARN',
                message=f"Vague attribution/weasel wording: {len(all_matches)} instances of uncited claims to vague authorities",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'count': len(all_matches)}
            ))

        return findings


class NotabilityEmphasisChecker(RuleChecker):
    """Check for overemphasis on notability and media coverage.

    LLMs act as if the best way to prove notability is to hit readers over the head
    with claims of notability, often listing sources that covered the subject.
    """

    DEFAULT_PATTERNS = [
        # Independent coverage (Wikipedia-specific language)
        r'\b[Ii]ndependent\s+coverage\b',
        # Media outlets listing
        r'\b(local|regional|national|international)\s+media\s+outlets?\b',
        r'\b(music|business|tech|entertainment)\s+outlets?\b',
        # Featured in multiple outlets
        r'\b[Ff]eatured\s+in\s+[\w\s,]+and\s+other\s+(prominent\s+)?(media\s+)?outlets?\b',
        # Coverage mentioned extensively
        r'\b(has\s+been\s+)?(mentioned|featured|covered|cited)\s+in\s+\w+[\w\s,]+and\s+\w+',
        # Active social media presence
        r'\b(maintains?|has)\s+(an\s+)?active\s+social\s+media\s+presence\b',
        # Written by leading expert
        r'\b[Ww]ritten\s+by\s+(a\s+)?leading\s+(expert|authority|scholar)\b',
    ]

    def check(self, text: str, raw_text: str, file_path: str, metadata: Dict[str, Any]) -> List[Finding]:
        findings = []
        patterns = self.config.get('patterns', self.DEFAULT_PATTERNS)
        threshold = self.config.get('threshold_count', 2)

        all_matches = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        if len(all_matches) >= threshold:
            match = all_matches[0]
            snippet = get_context_snippet(text, match.start(), match.end())
            line = calculate_line_number(raw_text, match.start())

            findings.append(Finding(
                rule_id=self.rule_id,
                severity='WARN',
                message=f"Overemphasis on notability: {len(all_matches)} instances claiming media coverage/importance",
                file_path=file_path,
                snippet=snippet,
                line=line,
                details={'count': len(all_matches)}
            ))

        return findings


class RuleRegistry:
    """Registry of all available rule checkers."""

    CHECKER_MAP = {
        # Original generic writing quality rules
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

        # Wikipedia AI detection patterns
        'ai-vocabulary': AIVocabularyChecker,
        'significance-language': SignificanceLanguageChecker,
        'promotional-language': PromotionalLanguageChecker,
        'superficial-analysis': SuperficialAnalysisChecker,
        'copulative-avoidance': CopulativeAvoidanceChecker,
        'negative-parallelism': NegativeParallelismChecker,
        'rule-of-three': RuleOfThreeChecker,
        'challenges-conclusions': ChallengesConclusionsChecker,
        'knowledge-cutoff': KnowledgeCutoffChecker,
        'vague-attribution': VagueAttributionChecker,
        'notability-emphasis': NotabilityEmphasisChecker,
    }

    @classmethod
    def create_checker(cls, rule_config: Dict[str, Any]) -> RuleChecker:
        """Create a checker instance for a rule."""
        rule_id = rule_config['id']
        checker_class = cls.CHECKER_MAP.get(rule_id)

        if checker_class is None:
            raise ValueError(f"Unknown rule type: {rule_id}")

        return checker_class(rule_config)
