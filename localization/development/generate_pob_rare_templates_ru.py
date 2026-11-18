from pathlib import Path
import json
import re


BUILD = Path(__file__).resolve().parent.parent / "outputs" / "PoB2-RU"

TITLES = {
    "+2 Critical Quiver": "+2 Колчан для крит. ударов",
    "+2 Energy Shield": "+2 Фокус с эн. щитом",
    "+2 Poison Quiver": "+2 Колчан для яда",
    "+4 Chaos Bow": "+4 Лук хаоса",
    "+4 Elemental Bow": "+4 Стихийный лук",
    "+4 Elemental Spear": "+4 Стихийное копьё",
    "+4 Lightning Spear": "+4 Копьё молнии",
    "+4 Minion Sceptre": "+4 Скипетр приспешников",
    "+4 Physical Bow": "+4 Физический лук",
    "+4 Physical Spear": "+4 Физическое копьё",
    "+6 Elemental Crossbow": "+6 Стихийный самострел",
    "+6 Physical Crossbow": "+6 Физический самострел",
    "Attribute Amulet": "Амулет характеристик",
    "Belt": "Пояс",
    "Chaos Resistance Ring": "Кольцо сопротивления хаосу",
    "Chaos Wand": "Жезл хаоса",
    "Cold Staff": "Посох холода",
    "Dexterity Amulet": "Амулет ловкости",
    "Discipline Sceptre": "Скипетр «Дисциплина»",
    "Elemental 1H Mace": "Стихийная одноручная булава",
    "Elemental 2H Mace": "Стихийная двуручная булава",
    "Elemental Staff": "Стихийный посох",
    "Elemental Talisman": "Стихийный талисман",
    "Elemental Wand": "Стихийный жезл",
    "Energy Shield Amulet": "Амулет энергетического щита",
    "Fire Staff": "Огненный посох",
    "Fire Wand": "Огненный жезл",
    "Intelligence Amulet": "Амулет интеллекта",
    "Jewel": "Самоцвет",
    "Lightning Staff": "Посох молнии",
    "Malice Sceptre": "Скипетр «Злость»",
    "Mana Amulet": "Амулет маны",
    "Mana Ring": "Кольцо маны",
    "Movement Speed Chest": "Доспех на скорость передвижения",
    "Physical 1H Mace": "Физическая одноручная булава",
    "Physical 2H Mace": "Физическая двуручная булава",
    "Physical Staff": "Физический боевой посох",
    "Physical Talisman": "Физический талисман",
    "Physical Wand": "Физический жезл",
    "Purity Aura Sceptre": "Скипетр с аурой спасения",
    "Radius Jewel": "Самоцвет с радиусом",
    "Resistance Ring": "Кольцо сопротивлений",
    "Ring": "Кольцо",
    "Spirit Amulet": "Амулет духа",
    "Spirit Chest": "Доспех с духом",
    "Strength Amulet": "Амулет силы",
}
DEFENCES = {
    "Armour": "броня",
    "Evasion": "уклонение",
    "Energy Shield": "эн. щит",
    "Armour/Evasion": "броня/уклонение",
    "Armour/Energy Shield": "броня/эн. щит",
    "Evasion/Energy Shield": "уклонение/эн. щит",
}
EQUIPMENT = {
    "Helmet": "Шлем",
    "Gloves": "Перчатки",
    "Chest": "Доспех",
    "Boots": "Сапоги",
    "Shield": "Щит",
}


def write_rare_template_catalog():
    translations = dict(TITLES)
    for defence, russian_defence in DEFENCES.items():
        for slot, russian_slot in EQUIPMENT.items():
            translations[f"{defence} {slot}"] = f"{russian_slot} — {russian_defence}"

    catalog = {}
    source = (BUILD / "Data/Rares.lua").read_text(encoding="utf-8")
    for block in re.findall(r"\[\[(.*?)\]\]", source, re.S):
        lines = [line.strip() for line in block.strip().splitlines()]
        if lines[0].startswith("Rarity:"):
            continue
        title, base = lines[:2]
        translated = translations[title]
        if title == "Elemental Staff" and base.endswith("Quarterstaff"):
            translated = "Стихийный боевой посох"
        catalog.setdefault(title, {})[base] = translated

    quote = lambda value: json.dumps(value, ensure_ascii=False)
    lines = ["-- PoB 0.23.1 built-in rare template labels, scoped by original title and base.", "return {"]
    for title, bases in sorted(catalog.items()):
        lines.append(f"\t[{quote(title)}] = {{")
        for base, translated in sorted(bases.items()):
            lines.append(f"\t\t[{quote(base)}] = {quote(translated)},")
        lines.append("\t},")
    lines.extend(["}", ""])
    (BUILD / "Data/Locale/rare_templates_ru.lua").write_text("\n".join(lines), encoding="utf-8")
    print(f"Localized {sum(map(len, catalog.values()))} template entries with {len(catalog)} original titles.")


if __name__ == "__main__":
    write_rare_template_catalog()
