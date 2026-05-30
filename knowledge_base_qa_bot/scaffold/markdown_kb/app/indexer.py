import math
import re
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path


# Absolute path to the 'docs' directory where raw markdown files are stored.
# Path(__file__).resolve().parents[3] dynamically finds the project root directory.
DOCS_DIR = Path(__file__).resolve().parents[3] / "docs"

# Target filepath for persisting the built search index in JSON format.
# The .kb directory and index.json are created programmatically during build_index().
INDEX_PATH = Path(__file__).resolve().parents[3] / ".kb" / "index.json"

# Regular expression to identify Markdown headings (levels 1-6).
# Group 1 captures the hashes (level), and Group 2 captures the heading text (stripped of trailing spaces).
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# Regular expression to match alphanumeric tokens (words) for indexing.
# Matches any sequence of lowercase letters (a-z) and digits (0-9).
TOKEN_RE = re.compile(r"[a-z0-9]+")

# Set of extremely common words (stop words) filtered out during tokenization.
# Using a Python Set ensures O(1) constant-time lookup during search-term filtering.
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "is",
    "it",
    "my",
    "of",
    "the",
    "to",
    "what",
    "when",
    "which",
}


@dataclass
class Section:
    """
    Represents a logical, heading-level section of a Markdown document.
    This serves as the fundamental retrieval unit for the search engine.
    
    Attributes:
        id: Unique identifier in the format 'filename.md#heading-slug' 
            (e.g., 'refund_policy.md#refund-timeline').
        file: The raw filename being parsed (e.g., 'refund_policy.md').
        heading: The raw text of the heading starting this section (e.g., 'Refund Timeline').
        heading_path: The hierarchical heading path (e.g., ['Refund Policy', 'Refund Timeline']).
        content: The accumulated raw text body of this section.
        tokens: Alphanumeric words extracted from both heading and content, used for BM25.
        
    Example:
        Given 'account_help.md':
        # Account Help
        ## Change Email
        To change your email...
        
        This translates to:
        Section(
            id="account_help.md#change-email",
            file="account_help.md",
            heading="Change Email",
            heading_path=["Account Help", "Change Email"],
            content="To change your email...",
            tokens=["change", "email", "email"]
        )
    """
    id: str
    file: str
    heading: str
    heading_path: list[str]
    content: str
    tokens: list[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file": self.file,
            "heading": self.heading,
            "heading_path": self.heading_path,
            "content": self.content,
            "tokens": self.tokens,
        }


sections: list[Section] = []
doc_freq: Counter[str] = Counter()
avg_doc_len = 0.0
files_indexed = 0


def slugify(text: str) -> str:
    """
    Converts human-readable heading text into a URL-friendly, lowercase slug.
    This creates anchor-like identifiers matching standard Markdown specifications
    (e.g., "1. Cancellation Window?!" becomes "1-cancellation-window").
    
    Transformation Flow:
    1. text.lower():
       "1. Cancellation Window?!" -> "1. cancellation window?!"
    2. re.sub(r"[^a-z0-9]+", "-", ...):
       Replaces any sequence of non-alphanumeric characters with a single hyphen.
       "1. cancellation window?!" -> "1-cancellation-window-"
    3. strip("-"):
       Trims trailing/leading hyphens.
       "1-cancellation-window-" -> "1-cancellation-window"
    4. fallback:
       If the slug is empty (e.g. only emojis "🚀🔥" -> ""), falls back to "section".
    """
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOP_WORDS]


def parse_markdown(path: Path) -> list[Section]:
    # Design decision: The retrieval unit is a heading section, not a whole file.
    #
    # Hints:
    # 1. Use HEADING_RE to detect Markdown headings.
    # 2. Track heading_path so citations include parent context.
    # 3. Each Section id should look like "refund_policy.md#refund-timeline".
    # 4. Tokens should include both headings and content.
    sections: list[Section] = []
    filename = path.name

    # Tracking variables
    active_heading_map = {}     # Maps heading level (int) -> heading text (string)
    current_heading = None      # Text of the current heading being collected
    current_heading_path = []   # Path of parent headings when this section started
    current_content_lines = []  # Content lines collected for this section

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            # Check if this line is a heading (e.g. "# Title")
            match = HEADING_RE.match(line)
            if match:
                # 1. Save the previous section if we were building one
                if current_heading is not None:
                    content_str = "".join(current_content_lines).strip()
                    sections.append(
                        Section(
                            id=f"{filename}#{slugify(current_heading)}",
                            file=filename,
                            heading=current_heading,
                            heading_path=list(current_heading_path),  # Copy the active path
                            content=content_str,
                            tokens=tokenize(f"{current_heading} {content_str}")
                        )
                    )

                # 2. Extract heading level and clean text
                hashes = match.group(1)
                heading_text = match.group(2).strip()
                level = len(hashes)

                # 3. Update the active heading hierarchy dictionary
                # Remove any deeper or equal levels from the dictionary
                active_heading_map = {k: v for k, v in active_heading_map.items() if k < level}
                active_heading_map[level] = heading_text

                # 4. Reconstruct the sorted hierarchical path list
                current_heading_path = [active_heading_map[k] for k in sorted(active_heading_map.keys())]
                current_heading = heading_text
                
                # 5. Clear the content buffer for the new section
                current_content_lines = []
            else:
                # If it's a regular text line, accumulate it
                if current_heading is not None:
                    current_content_lines.append(line)

        # 6. Save the final section remaining in the buffer at the end of the file
        if current_heading is not None:
            content_str = "".join(current_content_lines).strip()
            sections.append(
                Section(
                    id=f"{filename}#{slugify(current_heading)}",
                    file=filename,
                    heading=current_heading,
                    heading_path=list(current_heading_path),
                    content=content_str,
                    tokens=tokenize(f"{current_heading} {content_str}")
                )
            )

    return sections


def write_index_json(index_path: Path = INDEX_PATH) -> None:
    # Design decision/Hints:
    # 1. Create index_path.parent if it does not exist.
    # 2. Write {"sections": [...], "stats": {...}} as pretty JSON.
    # 3. Use section.to_dict() for each Section.
    index_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "sections": [section.to_dict() for section in sections],
        "stats": {
            "files_indexed": files_indexed,
            "sections_indexed": len(sections),
            "avg_doc_len": avg_doc_len,
            "doc_freq": dict(doc_freq)
        }
    }

    with index_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def rebuild_stats() -> None:
    # Design decision/Hints:
    # 1. files_indexed can be derived from the unique section.file values.
    # 2. doc_freq counts how many sections contain each token.
    # 3. avg_doc_len is the average token count across sections.
    global doc_freq, avg_doc_len, files_indexed

    # 1. Count unique files across all sections
    unique_files = {section.file for section in sections}
    files_indexed = len(unique_files)

    # 2. Count how many sections contain each unique token (for IDF)
    doc_freq = Counter()
    total_tokens = 0
    
    for section in sections:
        total_tokens += len(section.tokens)
        # Use a Set to ensure we only count a token ONCE per section
        unique_section_tokens = set(section.tokens)
        doc_freq.update(unique_section_tokens)

    # 3. Calculate average document (section) length in tokens
    if sections:
        avg_doc_len = total_tokens / len(sections)
    else:
        avg_doc_len = 0.0


def load_index_json(index_path: Path = INDEX_PATH) -> tuple[int, int]:
    # Design decision/Hints:
    # 1. If index_path does not exist, return (0, 0).
    # 2. Read payload["sections"] and convert each item back to Section.
    # 3. Call rebuild_stats() after assigning sections.
    # 4. Return (files_indexed, sections_indexed).
    global sections

    if not index_path.exists():
        return 0, 0

    with index_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    sections = [
        Section(
            id=item["id"],
            file=item["file"],
            heading=item["heading"],
            heading_path=item["heading_path"],
            content=item["content"],
            tokens=item["tokens"]
        )
        for item in payload.get("sections", [])
    ]

    rebuild_stats()

    return files_indexed, len(sections)


def build_index(docs_dir: Path = DOCS_DIR) -> tuple[int, int]:
    global sections, doc_freq, avg_doc_len, files_indexed

    # Design decision/Hints:
    # 1. Read all Markdown files from docs_dir.
    # 2. Call parse_markdown() for each file.
    # 3. Call rebuild_stats() to compute BM25 metadata.
    # 4. Persist .kb/index.json with write_index_json().
    # 5. Call write_index_json() so students can inspect the generated index.
    # 6. Return (files_indexed, sections_indexed).
    sections = []
    doc_freq = Counter()
    avg_doc_len = 0.0
    files_indexed = 0

    if docs_dir.exists() and docs_dir.is_dir():
        markdown_files = sorted(docs_dir.glob("*.md"))
        for filepath in markdown_files:
            parsed_sections = parse_markdown(filepath)
            sections.extend(parsed_sections)

    rebuild_stats()
    write_index_json()

    return files_indexed, len(sections)


def bm25_score(query_tokens: list[str], section: Section, k1: float = 1.5, b: float = 0.75) -> float:
    # Design decision/Hints:
    # 1. Count term frequency in the section.
    # 2. Use doc_freq to give rare terms higher weight.
    # 3. Normalize by section length using avg_doc_len.
    # 4. Add a small boost when query terms appear in heading_path.
    score = 0.0
    section_tokens = section.tokens
    doc_len = len(section_tokens)

    if avg_doc_len > 0:
        penalty = 1.0 - b + (b * (doc_len / avg_doc_len))
    else:
        penalty = 1.0

    path_tokens_lower = [t.lower() for heading in section.heading_path for t in tokenize(heading)]

    for token in query_tokens:
        tf = section_tokens.count(token)
        if tf == 0:
            continue

        N = files_indexed
        n = doc_freq.get(token, 0)
        
        idf = math.log(1.0 + (N - n + 0.5) / (n + 0.5))
        tf_payload = (tf * (k1 + 1.0)) / (tf + (k1 * penalty))
        word_score = idf * tf_payload

        if token in path_tokens_lower:
            word_score *= 1.25

        score += word_score

    return score


def search(query: str, k: int = 3) -> list[tuple[Section, float]]:
    query_tokens = tokenize(query)
    ranked = [
        (section, bm25_score(query_tokens, section))
        for section in sections
    ]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return [(section, score) for section, score in ranked[:k] if score > 0]
