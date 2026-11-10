"""
Backwards-compatibility proxy for eval_guard.obfuscation.
"""
from eval_guard.obfuscation import (
    INJECTION_KEYWORDS,
    ObfuscationCheckResult,
    detect_obfuscated_injection,
    inspect_obfuscation,
    normalize_invisible_chars,
    normalize_leetspeak,
)

__all__ = [
    "INJECTION_KEYWORDS",
    "ObfuscationCheckResult",
    "detect_obfuscated_injection",
    "inspect_obfuscation",
    "normalize_invisible_chars",
    "normalize_leetspeak",
]
