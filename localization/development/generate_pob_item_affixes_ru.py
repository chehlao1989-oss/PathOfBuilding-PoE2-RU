from collections import defaultdict
import re

from generate_pob_tree_ru import lua
from read_poe2_dat import WORK, read_rows


def inflected(text):
    forms = dict(re.findall(r"<(?:if|elif):([A-Z]{2})>\{([^{}]+)\}", text))
    if forms:
        if re.sub(r"<(?:if|elif):[A-Z]{2}>\{[^{}]+\}", "", text):
            return None
        return forms
    return text if text and not re.search(r"[<>{}\[\]]", text) else None


def resolve(rows):
    grouped = defaultdict(dict)
    for name, key, value in rows:
        if value and re.search("[А-Яа-яЁё]", "".join(value.values()) if isinstance(value, dict) else value):
            grouped[name][lua(value)] = {"name": value, "id": key}
    return {name: next(iter(forms.values())) for name, forms in grouped.items() if len(forms) == 1}


def main():
    cols = ("Wordlist", "HASH32", "Text", "Text2", "Inflection")
    russian = {(r["Wordlist"], r["HASH32"]): r for r in read_rows("words", cols, "russian")}
    parts = defaultdict(list)
    for row in read_rows("words", cols):
        word_list = row["Wordlist"]
        if word_list not in (1, 2):
            continue
        source = row["Text2"].strip()
        translated = russian[(word_list, row["HASH32"])]
        label = inflected(translated["Text2"].strip())
        if word_list == 2:
            if not isinstance(label, str) or not translated["Inflection"]:
                continue
            label = {"noun": label, "inflection": translated["Inflection"]}
        parts[word_list].append((source, row["HASH32"], label))

    cols = ("Id", "Name", "GenerationType")
    russian = {r["Id"]: r for r in read_rows("mods", cols, "russian")}
    mods = defaultdict(list)
    by_id = {}
    for row in read_rows("mods", cols):
        translated = russian.get(row["Id"])
        kind = row["GenerationType"]
        if kind not in (1, 2) or not translated or translated["GenerationType"] != kind:
            continue
        name, text = row["Name"].strip(), translated["Name"].strip()
        forms = inflected(text)
        if not name or not forms or text == name:
            continue
        mods[kind].append((name, row["Id"], forms))
        by_id[row["Id"]] = {"en": name, "name": forms}

    client_text = {
        row["Id"]: row["Text"] for row in read_rows("clientstrings", ("Id", "Text"), "russian")
        if row["Id"].startswith(("MagicName", "RareNameFormat"))
    }
    data = {
        "rarePrefixes": resolve(parts[1]), "rareNouns": resolve(parts[2]),
        "magicPrefixes": resolve(mods[1]), "magicSuffixes": resolve(mods[2]), "mods": by_id,
        "formats": client_text,
    }
    out = WORK.parent / "outputs/PoB2-RU/Data/Locale/item_affixes_ru.lua"
    lines = ["-- PoE 2 0.5.5g Words.HASH32, Mods.Id, and ClientStrings.", "return {"]
    for key, entries in data.items():
        lines.append(f"\t{key} = {{")
        lines.extend(f"\t\t[{lua(name)}] = {lua(entry)}," for name, entry in sorted(entries.items()))
        lines.append("\t},")
    out.write_text("\n".join([*lines, "}", ""]), encoding="utf-8")
    print({key: len(value) for key, value in data.items()})


if __name__ == "__main__":
    main()
