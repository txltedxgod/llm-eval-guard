"""
Prompt Injection Obfuscation Detector
Multi-vector decoding engine for adversarial LLM prompt injections.
Detects Base64, Hexadecimal, Rot13, Leetspeak, Zero-width invisible characters,
and Reversed attack payloads.
"""
from __future__ import annotations

import base64
import codecs
import re
from dataclasses import dataclass

INJECTION_KEYWORDS: tuple[str, ...] = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard all prior",
    "disregard previous instructions",
    "system override",
    "you are now in developer mode",
    "act as sudo",
    "bypass security filters",
    "bypass safety filters",
    "reveal secret key",
    "reveal internal prompt",
    "drop table",
    "drop tables",
    "jailbreak",
    "dan mode",
)

# Invisible / Zero-width characters often used to evade tokenizers
ZERO_WIDTH_CHARS = re.compile(r"[\u200B-\u200D\uFEFF\u00AD\u2060\u200E\u200F]")

# Leetspeak translation table
_LEET_MAP = {
    ord("@"): "a",
    ord("4"): "a",
    ord("8"): "b",
    ord("3"): "e",
    ord("1"): "i",
    ord("!"): "i",
    ord("|"): "i",
    ord("0"): "o",
    ord("5"): "s",
    ord("$"): "s",
    ord("7"): "t",
    ord("+"): "t",
}


@dataclass
class ObfuscationCheckResult:
    detected: bool
    vector: str | None = None
    decoded_payload: str | None = None
    matched_keyword: str | None = None


def normalize_invisible_chars(text: str) -> str:
    """Strip zero-width and invisible unicode characters."""
    return ZERO_WIDTH_CHARS.sub("", text)


def normalize_leetspeak(text: str) -> str:
    """Normalize simple 1337-speak substitutions to standard ASCII lowercase."""
    return text.translate(_LEET_MAP).lower()


def _check_plain_keywords(text: str) -> str | None:
    lowered = text.lower()
    for kw in INJECTION_KEYWORDS:
        if kw in lowered:
            return kw
    return None


def inspect_obfuscation(text: str) -> ObfuscationCheckResult:
    """
    Perform deep inspection across multiple obfuscation vectors.
    Returns ObfuscationCheckResult with detailed detection metadata.
    """
    if not text or not isinstance(text, str):
        return ObfuscationCheckResult(detected=False)

    # 1. Zero-width / invisible unicode characters evasion
    cleaned_text = normalize_invisible_chars(text)
    if cleaned_text != text:
        kw = _check_plain_keywords(cleaned_text)
        if kw:
            return ObfuscationCheckResult(
                detected=True,
                vector="zero_width_unicode",
                decoded_payload=cleaned_text,
                matched_keyword=kw,
            )

    # 2. Leetspeak obfuscation
    leet_normalized = normalize_leetspeak(cleaned_text)
    if leet_normalized != cleaned_text.lower():
        kw = _check_plain_keywords(leet_normalized)
        if kw:
            return ObfuscationCheckResult(
                detected=True,
                vector="leetspeak",
                decoded_payload=leet_normalized,
                matched_keyword=kw,
            )

    # 3. Base64 payload obfuscation
    # Match alphanumeric + plus/slash blocks of at least 16 chars with optional padding
    b64_pattern = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
    for match in b64_pattern.findall(text):
        try:
            # Add padding if needed
            pad_len = (-len(match)) % 4
            candidate = match + ("=" * pad_len)
            decoded_bytes = base64.b64decode(candidate, validate=True)
            decoded_str = decoded_bytes.decode("utf-8", errors="ignore").lower()
            for kw in INJECTION_KEYWORDS:
                if kw in decoded_str:
                    return ObfuscationCheckResult(
                        detected=True,
                        vector="base64",
                        decoded_payload=decoded_str,
                        matched_keyword=kw,
                    )
        except Exception:
            continue

    # 4. Hexadecimal encoding (e.g., 69676e6f726520... or \x69\x67... or 0x69 0x67)
    hex_escaped_pattern = re.compile(r"(?:\\x[0-9a-fA-F]{2})+")
    for match in hex_escaped_pattern.findall(text):
        try:
            raw_hex = match.replace(r"\x", "")
            decoded_bytes = bytes.fromhex(raw_hex)
            decoded_str = decoded_bytes.decode("utf-8", errors="ignore").lower()
            for kw in INJECTION_KEYWORDS:
                if kw in decoded_str:
                    return ObfuscationCheckResult(
                        detected=True,
                        vector="hex_escaped",
                        decoded_payload=decoded_str,
                        matched_keyword=kw,
                    )
        except Exception:
            continue

    # Raw contiguous hex strings (32+ hex characters)
    raw_hex_pattern = re.compile(r"\b[0-9a-fA-F]{32,}\b")
    for match in raw_hex_pattern.findall(text):
        if len(match) % 2 == 0:
            try:
                decoded_bytes = bytes.fromhex(match)
                decoded_str = decoded_bytes.decode("utf-8", errors="ignore").lower()
                for kw in INJECTION_KEYWORDS:
                    if kw in decoded_str:
                        return ObfuscationCheckResult(
                            detected=True,
                            vector="raw_hex",
                            decoded_payload=decoded_str,
                            matched_keyword=kw,
                        )
            except Exception:
                continue

    # 5. Rot13 / Caesar cipher
    try:
        rot13_candidate = codecs.decode(text, "rot_13").lower()
        for kw in INJECTION_KEYWORDS:
            if kw in rot13_candidate:
                return ObfuscationCheckResult(
                    detected=True,
                    vector="rot13",
                    decoded_payload=rot13_candidate,
                    matched_keyword=kw,
                )
    except Exception:
        pass

    # 6. Reversed text attack (e.g., "snoitcurtsni suoiverp erongi")
    reversed_candidate = text[::-1].lower()
    for kw in INJECTION_KEYWORDS:
        if kw in reversed_candidate:
            return ObfuscationCheckResult(
                detected=True,
                vector="reversed_text",
                decoded_payload=reversed_candidate,
                matched_keyword=kw,
            )

    return ObfuscationCheckResult(detected=False)


def detect_obfuscated_injection(text: str) -> bool:
    """Quick boolean check whether text contains obfuscated prompt injection."""
    return inspect_obfuscation(text).detected
