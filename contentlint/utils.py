"""Utility functions for ContentLint."""

import re
from typing import List, Tuple


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences using a reasonable heuristic.
    Handles common abbreviations but isn't exhaustive.
    """
    # Replace common abbreviations temporarily
    text = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e)\.', r'\1<PERIOD>', text, flags=re.IGNORECASE)

    # Split on sentence-ending punctuation followed by space and capital letter or end
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z]|$)', text)

    # Restore periods
    sentences = [s.replace('<PERIOD>', '.') for s in sentences if s.strip()]

    return sentences


def tokenize_words(text: str) -> List[str]:
    """Tokenize text into words, lowercase, stripping punctuation."""
    # Remove punctuation except apostrophes within words
    text = re.sub(r'[^\w\s\']|_', ' ', text)
    words = text.lower().split()
    # Remove standalone apostrophes
    words = [w.strip("'") for w in words if w.strip("'")]
    return words


def get_stopwords() -> set:
    """Return common English stopwords."""
    return {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'your', 'you', 'we', 'they', 'their',
        'this', 'these', 'those', 'or', 'but', 'not', 'can', 'have', 'had',
        'do', 'does', 'did', 'would', 'could', 'should', 'may', 'might',
        'must', 'been', 'being', 'than', 'then', 'there', 'here', 'where',
        'when', 'who', 'which', 'what', 'how', 'why', 'all', 'each', 'every',
        'both', 'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own',
        'same', 'so', 'no', 'nor', 'just', 'too', 'very', 'can', 'any', 'also'
    }


def calculate_line_number(text: str, match_start: int) -> int:
    """Calculate line number from character offset."""
    return text[:match_start].count('\n') + 1


def get_context_snippet(text: str, match_start: int, match_end: int, context_chars: int = 40) -> str:
    """Extract a snippet of text around a match for display."""
    start = max(0, match_start - context_chars)
    end = min(len(text), match_end + context_chars)

    snippet = text[start:end]

    # Add ellipsis if truncated
    if start > 0:
        snippet = '...' + snippet
    if end < len(text):
        snippet = snippet + '...'

    # Clean up whitespace
    snippet = ' '.join(snippet.split())

    return snippet


def words_per_thousand(count: int, total_words: int) -> float:
    """Calculate rate per 1000 words."""
    if total_words == 0:
        return 0.0
    return (count / total_words) * 1000


def percentage(count: int, total: int) -> float:
    """Calculate percentage."""
    if total == 0:
        return 0.0
    return (count / total) * 100
