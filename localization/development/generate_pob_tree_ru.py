from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import json
import re

from read_poe2_dat import WORK, read_rows


CSD = WORK / "PoE2-game-extract" / "data" / "statdescriptions"
OUT = WORK.parent / "outputs" / "PoB2-RU" / "Data" / "Locale" / "tree_0_5_ru.lua"
PLACEHOLDER = re.compile(r"\{(\d*)(?::([+-]?d))?\}")
CSD_VARIANT = re.compile(r'^([ #0-9|!\-]+)\s*\w*\s*"((?:[^"\\]|\\.)*)"\s*(.*)')
NUMBER = r"[+\-]?[0-9]+(?:[.,][0-9]+)?"
RENAMED_ENGLISH = {
    16568: "Defences and Companion Life",
    37688: "Devastating Devices",
    48583: "Life Leech, Armour and Evasion while Leeching",
    58783: "Life Leech, Armour and Evasion while Leeching",
}
GRANTED_SKILL_ALIASES = {"Fire Spell on Hit": "Fire Spell on Melee Hit"}
DOMINUS_PROVIDENCE_ID = 58894
DOMINUS_OLD_EFFECT = "Unaffected by Elemental Weakness"
DOMINUS_NEW_EFFECT = "30% reduced effect of Curses on you"


def plain(text):
    text = re.sub(r"\[[^\[\]|]+\|([^\[\]]+)\]", r"\1", text)
    text = re.sub(r"\[([^\[\]|]+)\]", r"\1", text)
    return text.replace(r"\n", "\n").replace(r'\"', '"').strip()


def comparable(text):
    text = re.sub(r"^\s*•\s*", "", plain(text), flags=re.MULTILINE)
    return " ".join(text.replace("’", "'").split()).casefold()


def recipe_emotions():
    fields = ("Id", "Name")
    item_id = re.compile(r"Metadata/Items/Currency/(?:Endgame)?DistilledEmotion\d+$")
    russian = {row["Id"]: plain(row["Name"]) for row in read_rows("baseitemtypes", fields, "russian")
               if item_id.fullmatch(row["Id"])}
    result = {}
    for row in read_rows("baseitemtypes", fields):
        if row["Id"] in russian:
            key = row["Name"].rsplit(" ", 1)[-1]
            name = russian[row["Id"]]
            result[key] = {"id": row["Id"], "name": name, "short": name.rsplit(" ", 1)[-1].capitalize()}
    if len(result) != len(russian):
        raise ValueError("Ambiguous liquid emotion recipe keys")
    return result


def limit_matches(limit, value):
    if limit == "#":
        return True
    if limit.startswith("!"):
        return int(limit[1:]) != value
    if "|" in limit:
        lower, upper = limit.split("|")
        return (lower in ("#", "-") or int(lower) <= value) and (upper in ("#", "-") or value <= int(upper))
    return int(limit) == value


@dataclass
class Variant:
    limits: list[str]
    text: str
    negated: tuple[str, ...] = ()
    pattern: re.Pattern = field(init=False)
    indices: list[int] = field(init=False)

    def __post_init__(self):
        clean = comparable(self.text)
        segments = []
        self.indices = []
        finish = 0
        for placeholder in PLACEHOLDER.finditer(clean):
            segments.append(re.escape(clean[finish:placeholder.start()]))
            segments.append(f"({NUMBER})")
            self.indices.append(int(placeholder[1]) if placeholder[1] else len(self.indices))
            finish = placeholder.end()
        segments.append(re.escape(clean[finish:]))
        self.pattern = re.compile("".join(segments))

    def allowed(self, values):
        return len(self.limits) == len(values) and all(
            limit_matches(limit, value) for limit, value in zip(self.limits, values)
        )

    def read_numbers(self, source):
        match = self.pattern.fullmatch(source)
        if match is None:
            return None
        return dict(zip(self.indices, match.groups()))

    def render(self, numbers):
        counter = 0

        def add_number(match):
            nonlocal counter
            index = int(match[1]) if match[1] else counter
            counter += 1
            number = numbers[index]
            if match[2] == "+d" and not number.startswith(("+", "-")):
                return "+" + number
            if match[2] != "+d" and number.startswith("+"):
                return number[1:]
            return number

        return PLACEHOLDER.sub(add_number, plain(self.text))


@dataclass
class Description:
    stat_ids: list[str]
    english: list[Variant] = field(default_factory=list)
    russian: list[Variant] = field(default_factory=list)


def descriptions(path):
    current = None
    waiting_for_ids = False
    lang = None
    with path.open(encoding="utf-16") as source:
        for line in source:
            line = line.strip()
            if re.fullmatch(r"(?:handed_)?description(?:\s+.*)?", line):
                if current and current.english and current.russian:
                    yield current
                current = None
                waiting_for_ids = True
                continue
            if waiting_for_ids:
                columns = line.split()
                if len(columns) >= 2 and columns[0].isdigit():
                    current = Description(columns[1:])
                    lang = current.english
                    waiting_for_ids = False
                continue
            if current is None:
                continue
            if line.startswith('lang "'):
                lang = current.russian if line == 'lang "Russian"' else None
                continue
            if line.startswith(("no_description ", "include ")):
                continue
            match = CSD_VARIANT.match(line)
            if lang is not None and match and "table_only" not in line and "[DNT" not in match[2]:
                negated = tuple(re.findall(r"\bnegate (\d+)", match[3]))
                lang.append(Variant(match[1].split(), match[2], negated))
    if current and current.english and current.russian:
        yield current


def resolve_stat(source, stats, catalogs):
    normalized = comparable(source)
    matched = set()
    for entries in catalogs:
        for stat in stats:
            for descriptor in entries.get(stat, ()):
                # This flag defaults to zero when the stat is supplied by a passive, without an active skill.
                mode = "active_skill_additional_projectiles_description_mode"
                if not all(stat_id in stats or stat_id == mode for stat_id in descriptor.stat_ids):
                    continue
                values = [stats.get(stat_id, 0) for stat_id in descriptor.stat_ids]
                for english in descriptor.english:
                    numbers = english.read_numbers(normalized)
                    if numbers is None or not english.allowed(values):
                        continue
                    options = [russian for russian in descriptor.russian
                               if russian.negated == english.negated and russian.allowed(values)]
                    same_limits = [russian for russian in options if russian.limits == english.limits]
                    for russian in same_limits or options:
                        try:
                            translated = russian.render(numbers)
                        except KeyError:
                            continue
                        if translated and not PLACEHOLDER.search(translated):
                            matched.add(translated)
        if matched:
            break
    return next(iter(matched)) if len(matched) == 1 else None


def read_names(table, column="Name"):
    keys = ("Id", column)
    rus = {row["Id"]: row[column] for row in read_rows(table, keys, "russian")}
    alternatives = defaultdict(set)
    for row in read_rows(table, keys):
        translated = rus.get(row["Id"])
        if row[column] and translated:
            alternatives[row[column]].add(translated)
    return {name: next(iter(values)) for name, values in alternatives.items() if len(values) == 1}


def granted_skill_names(indices, skills):
    gems = list(read_rows("skillgems", ["GemEffects"]))
    gem_effects = list(read_rows("gemeffects", ["GrantedEffect"]))
    effects = list(read_rows("grantedeffects", ["ActiveSkill"]))
    active = list(read_rows("activeskills", ["DisplayName"]))
    result = {}
    for index in indices:
        names = {}
        if index < len(gems):
            for gem_effect in gems[index]["GemEffects"]:
                if gem_effect >= len(gem_effects):
                    continue
                effect = gem_effects[gem_effect]["GrantedEffect"]
                if effect < len(effects) and effects[effect]["ActiveSkill"] < len(active):
                    name = active[effects[effect]["ActiveSkill"]]["DisplayName"]
                    if name in skills:
                        names[name] = skills[name]
        result[index] = names
    return result


def resolve_signed_reservation(line, stat_sets, catalogs):
    match = re.fullmatch(r"(-\d+)% increased Spirit Reservation Efficiency", line)
    stat = "base_spirit_reservation_efficiency_+%"
    if match and any(stats.get(stat) == int(match[1]) for stats in stat_sets):
        # A negative increase in PoB is written as a reduction by the client.
        for catalog in catalogs:
            for descriptor in catalog.get(stat, ()):
                if descriptor.stat_ids == [stat]:
                    for russian in descriptor.russian:
                        if russian.negated == ("1",) and russian.allowed([int(match[1])]):
                            return russian.render({0: match[1][1:]})
    return None


def resolve_lines(lines, stat_sets, catalogs, points, weapon_points, skills, granted, client_strings):
    translations = {}
    groups = {}
    missing = []
    count = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        skill = line.removeprefix("Grants Skill: ")
        grant = re.fullmatch(r"Grants (\d+) Passive Skill Points?", line)
        weapon_grant = re.fullmatch(r"(\d+) Passive Skill Points? becomes? (?:a )?Weapon Set Skill Points?", line)
        translation = None
        linked_skill = GRANTED_SKILL_ALIASES.get(skill, skill)
        skill_translation = granted.get(linked_skill) or skills.get(skill)
        if skill != line and skill_translation:
            template = client_strings["ItemDisplayGrantedSkillNoScaling"]
            translation = plain(template.replace("<underline>{{{0}}}", skill_translation))
        elif grant and int(grant[1]) in points:
            key = "PassiveNodeGrantsPassivePoint" if grant[1] == "1" else "PassiveNodeGrantsPassivePoints"
            translation = plain(client_strings[key].replace("{0}", grant[1]))
        elif weapon_grant and int(weapon_grant[1]) in weapon_points:
            key = "PassiveNodeGrantsSpecialisationPoint" if weapon_grant[1] == "1" else "PassiveNodeGrantsSpecialisationPoints"
            translation = plain(client_strings[key].replace("{0}", weapon_grant[1]))

        length = 1
        if not translation:
            for end in range(index + 1, len(lines) + 1):
                source = "\n".join(lines[index:end])
                alternatives = {resolve_stat(source, stats, catalogs) for stats in stat_sets} - {None}
                if len(alternatives) == 1:
                    translation = alternatives.pop()
                    length = end - index
                    break
        if not translation:
            translation = resolve_signed_reservation(line, stat_sets, catalogs)

        if not translation:
            missing.append(line)
        elif length == 1:
            translations[line] = translation
        else:
            groups[index + 1] = {"source": "\n".join(lines[index:index + length]), "text": translation, "length": length}
        if translation:
            count += length
        index += length
    return translations, groups, missing, count


def lua(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        return "{" + ",".join(f"[{lua(key)}]={lua(val)}" for key, val in value.items()) + "}"
    return str(value)


def main():
    import sys

    version = sys.argv[1] if len(sys.argv) > 1 else "0_5"
    stem = "pob-tree" if version == "0_5" else f"pob-tree-{version}"
    source_tree = json.loads((WORK / f"{stem}.json").read_text(encoding="utf-8"))
    stats_table = [row["Id"] for row in read_rows("stats", ["Id"])]
    fields = ["Id", "Name", "PassiveSkillNodeId", "Stats", "AscendancyStart",
              "PassivePointsGranted", "WeaponPointsGranted", "AnointOnly", "GrantedSkill"]
    fields += [f"Stat{i}" for i in range(1, 8)]
    rows = defaultdict(list)
    for row in read_rows("passiveskills", fields):
        rows[row["PassiveSkillNodeId"]].append(row)
    native_rows = {row["Id"]: row for row in read_rows("passiveskills", ["Id", "Name", "FlavourText"], "russian")}
    skill_names = read_names("activeskills", "DisplayName")
    linked_skills = granted_skill_names({row["GrantedSkill"] for choices in rows.values() for row in choices}, skill_names)
    client_strings = {row["Id"]: row["Text"] for row in read_rows("clientstrings", ["Id", "Text"], "russian")}
    catalogs = []
    for filename in ("passive_skill_stat_descriptions.csd", "stat_descriptions.csd"):
        by_stat = defaultdict(list)
        for descriptor in descriptions(CSD / filename):
            for stat_id in descriptor.stat_ids:
                by_stat[stat_id].append(descriptor)
        catalogs.append(by_stat)

    classes = read_names("characters")
    ascendancies = read_names("ascendancy")
    result = {}
    misses = {"name": [], "description": []}
    total_lines = 0
    translated_lines = 0
    special = defaultdict(list)
    version_differences = []
    for id_text, node in source_tree["nodes"].items():
        node_id = int(id_text)
        name = node["name"]
        lines = node["stats"]
        total_lines += len(lines)
        source_name = RENAMED_ENGLISH.get(node_id, plain(name))
        choices = [row for row in rows[node_id] if plain(row["Name"]) == source_name and native_rows.get(row["Id"], {}).get("Name")]
        names = {plain(native_rows[row["Id"]]["Name"]) for row in choices}
        if not names and name in ascendancies and any(row["AscendancyStart"] for row in rows[node_id]):
            names.add(ascendancies[name])
        if len(names) != 1:
            misses["name"].append({"id": node_id, "en": name})
            if lines:
                misses["description"].append({"id": node_id, "en": name, "lines": lines})
            continue
        stat_sets = [
            {stats_table[stat_id]: row[f"Stat{i + 1}"]
             for i, stat_id in enumerate(row["Stats"][:7]) if stat_id < len(stats_table)}
            for row in choices
        ]
        points = {row["PassivePointsGranted"] for row in choices}
        weapon_points = {row["WeaponPointsGranted"] for row in choices}
        granted = {key: value for row in choices for key, value in linked_skills[row["GrantedSkill"]].items()}
        description_lines, groups, unmatched, count = resolve_lines(
            lines, stat_sets, catalogs, points, weapon_points, skill_names, granted, client_strings,
        )
        version_note = None
        if node_id == DOMINUS_PROVIDENCE_ID and DOMINUS_OLD_EFFECT in unmatched:
            # PoE 2 patch 0.5.4b replaced the effect, but kept its original text template.
            legacy = resolve_stat(DOMINUS_OLD_EFFECT, {"unaffected_by_elemental_weakness": 1}, catalogs)
            active = {resolve_stat(DOMINUS_NEW_EFFECT, stats, catalogs)
                      for stats in stat_sets if stats.get("curse_effect_on_self_+%") == -30} - {None}
            if legacy and len(active) == 1:
                current = active.pop()
                description_lines[DOMINUS_OLD_EFFECT] = legacy
                unmatched.remove(DOMINUS_OLD_EFFECT)
                count += 1
                version_note = f"С патча 0.5.4b в PoE 2: {current}"
                version_differences.append({
                    "id": node_id, "name": next(iter(names)), "pob": legacy,
                    "game": current, "since": "0.5.4b",
                    "source": "https://www.pathofexile.com/forum/view-thread/3980516",
                })
        translated_lines += count
        record = {"en": name, "name": next(iter(names)), "stats": description_lines}
        if version_note:
            record["versionNote"] = version_note
        if groups:
            record["groups"] = groups
        if node.get("flavourText"):
            flavour = {native_rows[row["Id"]]["FlavourText"] for row in choices} - {""}
            if len(flavour) == 1:
                record["flavour"] = plain(flavour.pop())
        result[node_id] = record
        constraint = node.get("unlockConstraint")
        category = None
        if constraint:
            category = "oracle" if constraint.get("ascendancy") == "Oracle" else "otherPrerequisites"
        elif any(row["AnointOnly"] for row in choices) and node.get("recipe"):
            category = "anointOnly"
        if category:
            special[category].append({
                "id": node_id, "en": name, "ru": record["name"],
                "lines": {"translated": count, "total": len(lines)},
                **({"requires": constraint["nodes"]} if constraint else {"recipe": node["recipe"]}),
            })
        if unmatched:
            misses["description"].append({
                "id": node_id, "en": name, "lines": unmatched,
                "reason": "No unambiguous Russian template for the PoB text and client stat IDs/values.",
            })

    class_names = {}
    for class_ in source_tree["classes"]:
        if class_["name"] in classes:
            class_names[class_["name"]] = classes[class_["name"]]
        for ascendancy in class_["ascendancies"]:
            if ascendancy["name"] in ascendancies:
                class_names[ascendancy["name"]] = ascendancies[ascendancy["name"]]

    header = f"-- GGG game text. Source: local Steam PoE2 build 26650308. PoB v0.23.1, tree {version}."
    areas = {
        name.lower(): plain(localized)
        for name, localized in read_names("worldareas").items()
        if re.fullmatch(r"[A-Za-z][A-Za-z '–-]+", name)
    }
    emotions = recipe_emotions()
    recipe_keys = {key for node in source_tree["nodes"].values() for key in node.get("recipe", [])}
    if missing_emotions := recipe_keys - emotions.keys():
        raise ValueError(f"Missing recipe emotion names: {sorted(missing_emotions)}")
    lines = [header, "return {", "classes=" + lua(class_names) + ",", "areas=" + lua(areas) + ","]
    if version == "0_5":
        lines.append("emotions=" + lua(emotions) + ",")
    lines.append("nodes={")
    lines.extend(f"[{id_}]={lua(record)}," for id_, record in sorted(result.items()))
    OUT.with_name(f"tree_{version}_ru.lua").write_text("\n".join([*lines, "}", "}", ""]), encoding="utf-8")
    report = {
        "pob": "0.23.1", "tree": version, "steamBuildId": "26650308",
        "names": {"translated": len(result), "total": len(source_tree["nodes"])},
        "lines": {"translated": translated_lines, "total": total_lines},
        "classes": class_names,
        "recipeEmotions": {key: emotions[key] for key in sorted(recipe_keys)},
        "special": {key: sorted(nodes, key=lambda node: node["id"]) for key, nodes in special.items()},
        "decorativeOracleNodes": source_tree["decorativeOracleNodes"],
        "versionDifferences": version_differences,
        "missing": misses,
    }
    report_name = "tree-ru-coverage.json" if version == "0_5" else f"tree-{version}-ru-coverage.json"
    (WORK / report_name).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report["names"], report["lines"])
    print({id_: result.get(id_) for id_ in (39567, 53188)})
    print(class_names)


if __name__ == "__main__":
    main()
