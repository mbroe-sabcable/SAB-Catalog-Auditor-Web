import re
from typing import Any


class ValueNormalizer:
    @staticmethod
    def normalize(value: Any) -> str:
        if value is None:
            return ""

        text = str(value).strip()
        if not text:
            return ""

        text = re.sub(r"\s+", " ", text)
        text = text.lower()

        if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text):
            numeric_text = text
            if "." in numeric_text:
                numeric_text = numeric_text.rstrip("0").rstrip(".")
                if not numeric_text:
                    numeric_text = "0"
            return numeric_text

        return text
