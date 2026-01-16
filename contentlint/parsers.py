"""File parsers for different content formats."""

import re
from pathlib import Path
from typing import Dict, Any
from bs4 import BeautifulSoup


class ContentParser:
    """Base parser for content files."""

    @staticmethod
    def parse(file_path: Path) -> Dict[str, Any]:
        """
        Parse a content file and return structured data.

        Returns:
            dict with keys:
                - text: str (clean text content)
                - raw: str (original content)
                - metadata: dict (any extracted metadata)
        """
        raise NotImplementedError


class MarkdownParser(ContentParser):
    """Parser for Markdown files."""

    @staticmethod
    def parse(file_path: Path) -> Dict[str, Any]:
        """Parse Markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        # Extract YAML frontmatter if present
        metadata = {}
        text = raw_content

        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', raw_content, re.DOTALL)
        if frontmatter_match:
            # Remove frontmatter from text
            text = raw_content[frontmatter_match.end():]
            metadata['has_frontmatter'] = True

        # Remove code blocks (fenced with ``` or ~~~)
        text = re.sub(r'^```[\s\S]*?^```', '', text, flags=re.MULTILINE)
        text = re.sub(r'^~~~[\s\S]*?^~~~', '', text, flags=re.MULTILINE)

        # Remove inline code
        text = re.sub(r'`[^`]+`', '', text)

        # Remove markdown links but keep the text: [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove images: ![alt](url)
        text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)

        # Remove markdown headers (keep the text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove emphasis markers but keep text
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # bold
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # italic
        text = re.sub(r'__([^_]+)__', r'\1', text)  # bold
        text = re.sub(r'_([^_]+)_', r'\1', text)  # italic

        # Remove HTML comments
        text = re.sub(r'<!--[\s\S]*?-->', '', text)

        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return {
            'text': text.strip(),
            'raw': raw_content,
            'metadata': metadata
        }


class HTMLParser(ContentParser):
    """Parser for HTML files."""

    @staticmethod
    def parse(file_path: Path) -> Dict[str, Any]:
        """Parse HTML file and extract visible text."""
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        soup = BeautifulSoup(raw_content, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'meta', 'link']):
            element.decompose()

        # Get text
        text = soup.get_text(separator=' ')

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # Extract title if present
        metadata = {}
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()

        return {
            'text': text.strip(),
            'raw': raw_content,
            'metadata': metadata
        }


def get_parser(file_path: Path) -> ContentParser:
    """Get appropriate parser based on file extension."""
    suffix = file_path.suffix.lower()

    if suffix == '.md':
        return MarkdownParser()
    elif suffix in ['.html', '.htm']:
        return HTMLParser()
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
