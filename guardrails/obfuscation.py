"""
Prompt Injection Obfuscation Detector
Decodes Base64 payloads and checks for hidden injection tokens.
"""
import base64
import re

INJECTION_KEYWORDS = ["ignore previous instructions", "system prompt", "drop table", "act as sudo"]

def detect_obfuscated_injection(text: str) -> bool:
    b64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
    matches = re.findall(b64_pattern, text)
    for match in matches:
        try:
            decoded = base64.b64decode(match).decode("utf-8", errors="ignore").lower()
            if any(keyword in decoded for keyword in INJECTION_KEYWORDS):
                return True
        except Exception:
            continue
    return False
