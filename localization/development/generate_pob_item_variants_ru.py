from collections import Counter, defaultdict
import json
import re

from generate_pob_tree_ru import lua
from read_poe2_dat import WORK


BUILD = WORK.parent / "outputs/PoB2-RU"
ABYSS_NAMES = {"Amanamu": "Аманаму", "Kurgal": "Каргал", "Ulaman": "Уламан"}
SPECIAL_CAPTIONS = {
    ("From Nothing", "Everything (QoL Test Variant)"): "Все ключевые умения (тестовый вариант PoB)",
    ("Loreweave", "Bereks Grip Shocked Ground Boost 1"): "Уловка Берека · Заряженная земля",
    ("Loreweave", "Bereks Pass Chilled Ground Boost 1"): "Прыть Берека · Охлаждённая земля",
    ("Loreweave", "Bereks Respite Ignited Ground Boost 1"): "Передышка Берека · Подожжённая земля",
}


def caption(title, option):
    label = option["name"]
    if label == "Shield":
        return "Щит"
    if (title, label) in SPECIAL_CAPTIONS:
        return SPECIAL_CAPTIONS[title, label]
    if not option["properties"] or not all(mod["display"] != mod["source"] or re.search("[А-Яа-яЁё]", mod["display"])
                                           for mod in option["properties"]):
        return None
    properties = list(dict.fromkeys(mod["display"] for mod in option["properties"]))
    if title == "Megalomaniac":
        return properties[0].removeprefix("Активирует ")
    if title == "From Nothing":
        node = re.fullmatch(r"Пассивные умения в радиусе (.+) могут быть выбраны без связи с остальным деревом", properties[0])
        if node:
            return node[1]
    if title in {"Cursecarver", "Prism of Belief"}:
        skill = re.match(r".+ к уровню (?:всех )?умений (.+)$", properties[0])
        if skill:
            return skill[1]
    if title in {"Purity Aura Sceptre", "The Unborn Lich", "Guiding Palm"}:
        skill = re.fullmatch(r"Дарует умение: (.+) [()\d-]+ уровня", properties[0])
        if skill:
            version = re.search(r"\(Pre ([\d.]+) *\)$", label)
            return f"{skill[1]} (до {version[1]})" if version else skill[1]

    text = " · ".join(prop.replace("\n", " ") for prop in properties)
    if title == "Grip of Kulemak":
        group, _, role = label.partition(" ")
        if group in ABYSS_NAMES:
            prefix = "Сочетание свойств · " if role.startswith("Hybrid ") else ""
            text = f"{ABYSS_NAMES[group]} · {prefix}{text}"
    elif title == "Heart of the Well":
        role = label.partition(" ")[0]
        if role in {"Prefix", "Suffix"}:
            text = ("Префикс · " if role == "Prefix" else "Суффикс · ") + text
    elif title == "Loreweave" and "Combined With Base Gold Ring" in label:
        text = "С базовым свойством золотого кольца · " + text
    return text


def main():
    source = json.loads((WORK / "item-variants-input.json").read_text(encoding="utf-8"))
    catalog = defaultdict(dict)
    unresolved = []
    translated = 0
    for item in sorted(source["items"], key=lambda row: (row.get("title", ""), row["base"])):
        title, base = item.get("title", ""), item["base"]
        candidates = {}
        for index, option in enumerate(item["options"], 1):
            name = option["name"]
            if name == option["display"] and re.search("[A-Za-z]", name):
                text = caption(title, option)
                if text:
                    candidates[name] = (index, text)
                else:
                    unresolved.append({"title": title, "base": base, "variant": name})
                translated += bool(text)
        if candidates:
            counts = Counter(text for _, text in candidates.values())
            catalog[title][base] = {
                name: text if counts[text] == 1 else f"{text} · вариант {index}"
                for name, (index, text) in candidates.items()
            }
    lines = ["-- Russian item variant captions, derived from the stock options and game property descriptions.", "return {"]
    for title, bases in catalog.items():
        lines.append(f"\t[{lua(title)}] = {{")
        for base, variants in bases.items():
            lines.append(f"\t\t[{lua(base)}] = {{")
            lines.extend(f"\t\t\t[{lua(name)}] = {lua(text)}," for name, text in variants.items())
            lines.append("\t\t},")
        lines.append("\t},")
    lines.extend(["}", ""])
    (BUILD / "Data/Locale/item_variants_ru.lua").write_text("\n".join(lines), encoding="utf-8")
    print(f"Translated {translated} more variant occurrences. Remaining: {len(unresolved)}.")
    if unresolved:
        print(json.dumps(unresolved, ensure_ascii=False))


if __name__ == "__main__":
    main()
