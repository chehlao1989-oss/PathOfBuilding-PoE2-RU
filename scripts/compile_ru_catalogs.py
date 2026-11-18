"""Compile maintained RU interface catalogs; game-object catalogs are ID-derived."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for source_name, target_name in (("interface.ru.tsv", "ru.lua"), ("config.ru.tsv", "config_ru.lua"), ("trade.ru.tsv", "trade_ru.lua")):
    messages = {}
    for number, line in enumerate((root / "localization/catalogs" / source_name).read_text(encoding="utf-8").splitlines(), 1):
        if not line or (line.startswith("#") and "\t" not in line):
            continue
        english, russian = (part.replace(r"\n", "\n").replace(r"\t", "\t") for part in line.split("\t", 1))
        if english in messages:
            raise ValueError(f"Duplicate key at {source_name}:{number}")
        messages[english] = russian
    quote = lambda text: json.dumps(text, ensure_ascii=False)
    lines = [f"\t[{quote(en)}] = {quote(ru)}," for en, ru in sorted(messages.items())]
    (root / "src/Data/Locale" / target_name).write_text("-- Russian interface catalog\nreturn {\n" + "\n".join(lines) + "\n}\n", encoding="utf-8", newline="\n")
    print(f"{source_name}: {len(messages)} entries")
