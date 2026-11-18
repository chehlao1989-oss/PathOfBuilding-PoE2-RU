from collections import defaultdict
from itertools import product
import json
import re

from generate_pob_gem_stats_ru import CSD, PLACEHOLDER, gamedata, matched_templates
from generate_pob_tree_ru import lua, plain
from item_stat_reviews import reviewed_item_templates
from patch_item_names import ITEM_TOOLTIP_LABELS
from read_poe2_dat import WORK, read_rows


BUILD = WORK.parent / "outputs/PoB2-RU"
SCOPES = ("stat_descriptions", "advanced_mod_stat_descriptions", "utility_flask_buff_stat_descriptions")
ESCAPE_LUA = re.compile(r"[-+.*?^$()%\[\]]")
ESCAPE_FIELDS = re.compile(r"\{[^{}]*\}")
NUMERIC_RANGE = re.compile(r"\(-?\d+(?:[.,]\d+)?--?\d+(?:[.,]\d+)?\)")
NUMBER = re.compile(r"\d+[.,]?\d*")
PATTERN_NUMBER = r"%d+[.,]?%d*"


def normalize(text):
    return " ".join(plain(text).split()).lower()


def template_pattern(english):
    fields = list(PLACEHOLDER.finditer(english))
    indexes = [int(field[1] or 0) for field in fields]
    if len(fields) > 6 or len(indexes) != len(set(indexes)):
        return
    positions = {index + 1: position for position, index in enumerate(indexes, 1)}
    alternatives = [
        [(sign, is_range) for sign in ("+-" if ":+d" in field[0] else "-" if ":-d" in field[0] else ("",))
         for is_range in (False, True)]
        for field in fields
    ]
    for values in product(*alternatives):
        start = 0
        chunks, examples = ["^"], []
        signed_fields = {index for index, (sign, _) in zip(indexes, values) if sign}
        for field, (sign, is_range) in zip(fields, values):
            literal = english[start:field.start()]
            chunks.append(ESCAPE_LUA.sub(lambda match: "%" + match[0], literal))
            value = f"%(%-?{PATTERN_NUMBER}%-%-?{PATTERN_NUMBER}%)" if is_range else PATTERN_NUMBER
            chunks.append(f"({('%' + sign) if sign else ''}{value})")
            examples.append(literal + sign + ("(10-20)" if is_range else "10"))
            start = field.end()
        chunks.append(ESCAPE_LUA.sub(lambda match: "%" + match[0], english[start:]))
        shape = NUMBER.sub("#", NUMERIC_RANGE.sub("#", "".join(examples) + english[start:]))
        yield shape, "".join(chunks) + "$", positions, signed_fields


def paired_templates():
    results = {}
    pairs = defaultdict(set)
    fragments = defaultdict(set)
    for name in SCOPES:
        source = (CSD / f"{name}.csd").read_text(encoding="utf-16")
        scope = matched_templates(gamedata.parse_csd(source, "Russian"), name, preserve_line_breaks=True)
        for key, translations in scope.items():
            ids, _, _, _, english = key.split("\t")
            for translation in translations:
                russian = plain(translation)
                english_text = plain(english)
                if re.search("[А-Яа-яЁё]", russian) and not re.search(r"[<>\[\]]", russian):
                    values = {int(i or 0) for i in PLACEHOLDER.findall(english_text)}
                    if values != {int(i or 0) for i in PLACEHOLDER.findall(russian)}:
                        continue
                    if not any(ESCAPE_FIELDS.search(PLACEHOLDER.sub("", line))
                               for line in (english_text, russian)):
                        pairs[(english_text, russian)].add(ids)
                        en_lines, ru_lines = english_text.splitlines(), russian.splitlines()
                        if len(en_lines) == len(ru_lines) > 1:
                            for en_line, ru_line in zip(en_lines, ru_lines):
                                if PLACEHOLDER.findall(en_line) == PLACEHOLDER.findall(ru_line):
                                    fragments[(en_line, ru_line)].add(ids)
        results[name] = len(pairs)
    whole_lines = {normalize(english) for english, _ in pairs}
    for (english, russian), ids in fragments.items():
        if normalize(english) not in whole_lines:
            pairs[(english, russian)].update(ids)
    localized = {
        row["Id"]: plain(row["Text"]) for row in read_rows("clientstrings", ("Id", "Text"), "russian")
        if row["Id"].startswith(("ItemDisplayFlask", "ItemDisplayCharges"))
    }
    for row in read_rows("clientstrings", ("Id", "Text")):
        if row["Id"] in localized and row["Text"] and localized[row["Id"]]:
            pairs[(plain(row["Text"]), localized[row["Id"]])].add(row["Id"])
    results["clientstrings"] = len(pairs)
    return pairs, results


def compile_direction(pairs, reverse=False):
    grouped = defaultdict(lambda: defaultdict(dict))
    for english, russian in pairs:
        source, target = (russian, english) if reverse else (english, russian)
        source = normalize(source)
        for shape, pattern, positions, signed_fields in template_pattern(source):
            def canonical_field(field):
                index = int(field[1] or 0)
                if index in signed_fields or field[0].endswith(":d}"):
                    return "{" + str(index) + "}"
                return field[0]

            # An explicitly signed input keeps its sign regardless of the target format.
            equivalent = PLACEHOLDER.sub(canonical_field, target).lower()
            grouped[shape][pattern][equivalent] = {
                "pattern": pattern, "text": target, "positions": positions,
            }
    result = {}
    ambiguous = []
    for shape, patterns in grouped.items():
        # Specific fixed numbers and literal lines take precedence over numeric captures.
        matches = []
        for pattern, targets in sorted(patterns.items(), key=lambda entry: (entry[0].count("(%d"), entry[0])):
            if len(targets) == 1:
                matches.append(next(iter(targets.values())))
            else:
                ambiguous.append({"sourceShape": shape, "translations": sorted(targets)})
                matches.append({"pattern": pattern, "positions": {}})
        if matches:
            result[shape] = dict(enumerate(matches, 1))
    return result, ambiguous


def main():
    pairs, source_counts = paired_templates()
    display_pairs, scoped_pairs, reviews = reviewed_item_templates(pairs)
    forward, forward_ambiguity = compile_direction(pairs | display_pairs)
    reverse, reverse_ambiguity = compile_direction(pairs, reverse=True)
    reviewed_items = {item: compile_direction(templates)[0] for item, templates in scoped_pairs.items()}
    armour_rune, _ = compile_direction({
        pair: ids for pair, ids in pairs.items()
        if "local_armour_and_evasion_and_energy_shield_+%" in ids
    })
    # JewelRadiusAccuracy uses the global stat, even though the English text is also used locally on weapons.
    passive, _ = compile_direction({
        pair: ids for pair, ids in pairs.items() if "accuracy_rating_+%" in ids
    })
    item_labels = {key for _, key in ITEM_TOOLTIP_LABELS}
    item_text = {
        row["Id"]: plain(row["Text"])
        for row in read_rows("clientstrings", ("Id", "Text"), "russian")
        if row["Id"].startswith(("ItemDisplayFlask", "ItemDisplayCharges"))
        or row["Id"] in item_labels | {"ItemDisplayShamanOnly", "MonsterCorrupted"}
    }
    lines = [
        "-- PoE 2 0.5.5g item mod text. Steam Build 26650308.",
        "local forward, reverse, armourRune = {}, {}, {}",
        "local function merge(target, section)",
        "\tfor key, value in pairs(section()) do target[key] = value end",
        "end",
    ]
    for key, entries in (("forward", forward), ("reverse", reverse), ("armourRune", armour_rune)):
        ordered = sorted(entries.items())
        for start in range(0, len(ordered), 1000):
            lines.append(f"merge({key}, function() return {{")
            lines.extend(f"\t[{lua(shape)}] = {lua(variants)}," for shape, variants in ordered[start:start + 1000])
            lines.append("} end)")
    lines.append("return { forward = forward, reverse = reverse, armourRune = armourRune, passive = "
                 + lua(passive) + ", client = "
                 + lua(item_text) + ", reviewedItems = " + lua(reviewed_items) + " }")
    (BUILD / "Data/Locale/item_stats_ru.lua").write_text("\n".join([*lines, ""]), encoding="utf-8")
    report = {
        "gameVersion": "0.5.5g", "steamBuildId": 26650308, "pobVersion": "0.23.1",
        "officialTemplatePairs": len(pairs), "statGroups": len(set().union(*pairs.values())),
        "sources": list(source_counts),
        "reviewedItemTemplates": reviews,
        "ambiguousForDisplay": forward_ambiguity, "ambiguousForClipboard": reverse_ambiguity,
    }
    (BUILD / "item-stats-ru-coverage.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(pairs)} official pairs across {report['statGroups']} stat groups, {len(forward_ambiguity)} display conflicts.")


if __name__ == "__main__":
    main()
