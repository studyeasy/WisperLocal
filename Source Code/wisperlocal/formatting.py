"""Post-processing of raw Whisper transcripts.

Offline, rule-based cleanup: spoken layout commands, optional filler removal,
whitespace/punctuation tidying, and sentence capitalization. An optional
in-process local-LLM "polish" pass (see enhancer.py) can run afterwards.
"""

import re

# Safe, low-ambiguity spoken layout commands (words unlikely in normal prose).
_SPOKEN = [
    (re.compile(r"\bnew paragraph\b", re.I), "\n\n"),
    (re.compile(r"\bnew line\b", re.I), "\n"),
    (re.compile(r"\bnext line\b", re.I), "\n"),
    (re.compile(r"\bbullet point\b", re.I), "\n- "),
]

_FILLERS = re.compile(r"\b(?:um+|uh+|erm+|hmm+|uhh+|er|ah)\b[,]?", re.I)


def _strip_fillers(text: str) -> str:
    return _FILLERS.sub("", text)


def _apply_spoken(text: str) -> str:
    for pattern, repl in _SPOKEN:
        text = pattern.sub(repl, text)
    return text


def _tidy_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)        # collapse runs of spaces/tabs
    text = re.sub(r" *\n *", "\n", text)        # trim around newlines
    text = re.sub(r"\n{3,}", "\n\n", text)      # at most one blank line
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)  # no space before punctuation
    return text.strip()


def _capitalize(text: str) -> str:
    # Start of string.
    text = re.sub(r"^(\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    # After sentence-ending punctuation.
    text = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    # After a newline.
    text = re.sub(r"(\n\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    # Standalone "i" -> "I" (also i'm, i've, i'll, i'd).
    text = re.sub(r"\bi\b", "I", text)
    return text


def format_text(
    text: str,
    *,
    auto_capitalize: bool = True,
    spoken_commands: bool = True,
    remove_fillers: bool = False,
) -> str:
    if not text:
        return text
    if remove_fillers:
        text = _strip_fillers(text)
    if spoken_commands:
        text = _apply_spoken(text)
    text = _tidy_whitespace(text)
    if auto_capitalize:
        text = _capitalize(text)
    return text


def format_with_config(text: str, config) -> str:
    """Apply formatting according to a Config object."""
    if not text or not config.get("format_enabled"):
        return text.strip() if text else text
    return format_text(
        text,
        auto_capitalize=bool(config.get("auto_capitalize")),
        spoken_commands=bool(config.get("spoken_commands")),
        remove_fillers=bool(config.get("remove_fillers")),
    )
