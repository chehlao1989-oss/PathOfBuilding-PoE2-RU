from collections import Counter, defaultdict
import re
import sys

from generate_pob_tree_ru import CSD, lua
from read_poe2_dat import WORK

sys.path.insert(0, str(WORK / "upstream-downloads/reference"))
import gamedata

# Keep the Russian text as it appears in the client tables.
gamedata.LANG_NAMES["Russian"] = "Russian"


PLACEHOLDER = re.compile(r"\{(\d*)(?::[+\-]?d)?\}")
IGNORED_DIRECTIVES = {"reminderstring", "canonical_line", "canonical_stat"}
BASE_SCOPES = WORK / "PoB2-baseline/Data/StatDescriptions"
OUT = WORK.parent / "outputs/PoB2-RU/Data/Locale/gem_stats_ru.lua"
GAIN_ALIASES = {
    "active_skill_base_all_damage_%_to_gain_as_chaos": (
        "Gains {0}% of damage as Chaos damage", "Gains {0}% of Damage as Extra Chaos Damage"),
    "active_skill_base_all_damage_%_to_gain_as_fire": (
        "Gains {0}% of damage as Fire damage", "Gain {0}% damage as Extra Fire Damage"),
    "active_skill_base_all_damage_%_to_gain_as_lightning": (
        "Gains {0}% of damage as Lightning damage", "Gain {0}% damage as Extra Lightning Damage"),
}
# The Gathering Storm card displays the complete Russian conversion template.
CONVERSION_TEXT = {
    "Преобразует {0}% of физического урона в урон от молнии": "{0}% физического урона становится уроном от молнии",
    "Преобразует -{0}% of физического урона в урон от молнии": "-{0}% физического урона становится уроном от молнии",
}
# These PoB variants have no corresponding Russian template in the client.
# Keep their original stats and formatting, with terminology from the other client variants.
LOCAL_TRANSLATIONS = {
    "gem_stat_descriptions": (
        ("support_retreating_assault_projectile_damage_+%_final_if_melee_hit_in_past_2_seconds",
         "Supported Skills deal {0}% more Projectile Damage if you have Damaged an Enemy with a Melee Hit in the last two seconds",
         "Усиленные умения наносят на {0}% больше урона снарядами, если за последние 2 секунды вы нанесли врагу урон ударом в ближнем бою"),
        ("support_retreating_assault_projectile_damage_+%_final_if_melee_hit_in_past_8_seconds",
         "Supported Skills deal {0}% more Projectile Damage if you have Damaged an Enemy with a Melee Hit in the last eight seconds",
         "Усиленные умения наносят на {0}% больше урона снарядами, если за последние 8 секунд вы нанесли врагу урон ударом в ближнем бою"),
        ("perfect_timing_window_ms_+%", "{0}% longer Perfect Timing window",
         "Окно идеального момента на {0}% дольше"),
    ),
    "midnight_star_statset_0": (
        ("midnight_star_attempt_to_consume_x_ice_seeds_to_create_an_ice_crystal_each_time_you_gain_ice_seeds,unique_nattblom_crystals_per_trigger",
         "Consumes {0} Arctic Petals to create {1} Ice Crystals when able",
         "При возможности поглощает Арктические лепестки ({0}), чтобы создать кристаллы льда ({1})"),
    ),
    "entangle_statset_0": (
        ("base_number_of_entangle_roots_allowed", "{0:+d} to Fissure Limit", "{0:+d} к лимиту расселин"),
    ),
    "skill_stat_descriptions": (
        ("armour_break_for_%_of_poison_damage_over_poison_duration", "Break Armour equal to {0}% of Poison damage",
         "Разрушает броню в размере {0}% от нанесённого отравлением урона"),
        ("spell_skill_%_chance_to_fire_8_additional_projectiles_in_nova",
         "+{0}% chance to fire 8 additional Projectiles in a circle",
         "+{0}% к шансу выпустить 8 дополнительных снарядов по кругу"),
    ),
}


def clean(text):
    return text.replace(r'\"', '"').replace("\r\n", "\n").strip()


def fingerprint(desc):
    limits = ",".join(f"{lower}:{upper}" for lower, upper in desc["limit"])
    directives = ",".join(f"{rule['k']}:{rule['v']}" for rule in desc["specs"]
                          if rule["k"] not in IGNORED_DIRECTIVES)
    return (limits, directives, "1" if desc.get("gem_quality") else "0")


def placeholders(text):
    return {int(index or 0) for index in PLACEHOLDER.findall(text)}


def valid_translation(text):
    return text and "[DNT" not in text and not re.search(r"\{[^}]*\}", PLACEHOLDER.sub("", text))


def matched_templates(scope, name, *, preserve_line_breaks=False):
    templates = defaultdict(set)
    for entry in scope["entries"]:
        if not entry.get("want") or not entry.get("stats"):
            continue
        stats = ",".join(entry["stats"])
        english = entry["en"]
        translated = entry["want"]
        # A few Russian blocks omit gem_quality on the corresponding line.
        aligned = len(english) == len(translated) and all(
            fingerprint(en)[:2] == fingerprint(ru)[:2] for en, ru in zip(english, translated))
        russian = defaultdict(list)
        english_rules = Counter((fingerprint(desc), frozenset(placeholders(desc["text"]))) for desc in english)
        for desc in translated:
            text = clean(desc["text"])
            if valid_translation(text):
                russian[fingerprint(desc), frozenset(placeholders(text))].append(text.replace("\n", r"\n"))
        for index, desc in enumerate(english):
            source = clean(desc["text"])
            if not source:
                continue
            signature = fingerprint(desc)
            fields = frozenset(placeholders(source))
            source_text = source.replace("\n", r"\n")
            rule = signature, fields
            translations = list(dict.fromkeys(russian[rule]))
            if (not translations or len(translations) > 1) and aligned:
                candidate = clean(translated[index]["text"])
                if valid_translation(candidate) and placeholders(candidate) == fields:
                    translations = [candidate.replace("\n", r"\n")]
            if len(translations) > 1 and english_rules[rule] == 1:
                translations = translations[:1]  # The localized block uses the first available rule.
            if desc.get("gem_quality") and (not translations or translations == [source_text]):
                same_numbers = set(russian[((*signature[:2], "0"), fields)]) - {source_text}
                if len(same_numbers) == 1:
                    translations = same_numbers
            if stats == "active_skill_base_physical_damage_%_to_convert_to_lightning":
                translations = {CONVERSION_TEXT.get(candidate, candidate) for candidate in translations}
            if translations and len(translations) == 1:
                text = source.replace("%%", "%")
                if preserve_line_breaks:
                    text = text.replace("\n", r"\n")
                else:
                    text = " ".join(text.split())
                key = "\t".join((stats, *signature, text))
                templates[key].update(translations)
                alias = GAIN_ALIASES.get(stats) if name == "skill_stat_descriptions" else None
                if alias and alias[0] == text:
                    templates["\t".join((stats, *signature, alias[1]))].update(translations)
                    templates["\t".join((stats, "#:#", signature[1], "1", alias[1]))].update(translations)
    return templates


def main():
    scope_names = {path.stem.lower() for path in BASE_SCOPES.rglob("*.lua")}
    scopes = {}
    pooled = defaultdict(set)
    for path in sorted(CSD.rglob("*.csd")):
        name = path.relative_to(CSD).with_suffix("").as_posix().lower()
        name = name.removeprefix("specific_skill_stat_descriptions/").replace("/statset", "_statset")
        if name not in scope_names and name.rsplit("_statset", 1)[0] not in scope_names:
            continue
        templates = matched_templates(gamedata.parse_csd(path.read_text(encoding="utf-16"), "Russian"), name)
        scopes[name] = {key: next(iter(values)) for key, values in templates.items() if len(values) == 1}
        for key, values in templates.items():
            pooled[key].update(values)
    common = {key: next(iter(values)) for key, values in pooled.items() if len(values) == 1}
    chunks = ["-- Gem stat templates from PoE 2 Steam build 26650308.", "return {", "scopes={"]
    for name, entries in sorted(scopes.items()):
        overrides = {key: value for key, value in entries.items() if key not in common}
        if not overrides:
            continue
        chunks.append(f"[{lua(name)}]={{")
        chunks.extend(f"[{lua(key)}]={lua(value)}," for key, value in sorted(overrides.items()))
        chunks.append("},")
    chunks.extend(["},", "common={"])
    chunks.extend(f"[{lua(key)}]={lua(value)}," for key, value in sorted(common.items()))
    supplemental = {}
    for scope, entries in LOCAL_TRANSLATIONS.items():
        supplemental[scope] = {}
        for stats, en, ru in entries:
            if placeholders(en) != placeholders(ru):
                raise ValueError(f"Different number fields in {scope}: {en}")
            supplemental[scope][stats + "\t" + en] = ru
    chunks.extend(["},", "supplemental=" + lua(supplemental) + ",", "}", ""])
    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Generated gem stat templates for {len(scopes)} scopes ({len(common)} unambiguous keys).")


if __name__ == "__main__":
    main()
