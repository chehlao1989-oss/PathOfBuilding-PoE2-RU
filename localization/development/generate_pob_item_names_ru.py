from collections import defaultdict
import json
from pathlib import PurePosixPath
import re

from generate_pob_tree_ru import lua
from read_poe2_dat import WORK, read_rows


BUILD = WORK.parent / "outputs" / "PoB2-RU"
SHRINE_BASE = "Shrine Sceptre"
SHRINE_ID_PREFIX = "Metadata/Items/Weapons/OneHandWeapons/Sceptres/"


def game_class(kind, subtype):
    return {
        ("Charm", ""): {"UtilityFlask"},
        ("Fishing Rod", ""): {"FishingRod"},
        ("Flask", "Life"): {"LifeFlask"},
        ("Flask", "Mana"): {"ManaFlask"},
        ("Shield", "Evasion"): {"Buckler"},
        ("Shield", "Armour/Evasion"): {"Shield", "Buckler"},
        ("Staff", "Warstaff"): {"Warstaff"},
        ("Transcendent Limb", "Transcendent Arm"): {"IncursionArm"},
        ("Transcendent Limb", "Transcendent Leg"): {"IncursionLeg"},
    }.get((kind, subtype), {kind})


def base_matches(inventory, ru):
    classes = list(read_rows("itemclasses", ("Id",)))
    by_name = defaultdict(list)
    for row in read_rows("baseitemtypes", ("Id", "Name", "ItemClass", "DropLevel")):
        by_name[row["Name"]].append(row)
    catalog, unresolved, shared_keys = {}, [], []
    for name, kind, subtype, visibility, req_level in inventory:
        lookup = SHRINE_BASE if name.startswith(SHRINE_BASE + " (") else name
        classes_for_base = game_class(kind, subtype)
        candidates = [
            row for row in by_name[lookup]
            if classes[row["ItemClass"]]["Id"] in classes_for_base
        ]
        if lookup == SHRINE_BASE:
            # These are the three craftable bases. The unique-only base is resolved per unique below.
            candidates = [row for row in candidates if PurePosixPath(row["Id"]).name in {
                "FourSceptre6a", "FourSceptre6b", "FourSceptre6c",
            }]
        names = {ru.get(row["Id"]) for row in candidates}
        if len(names) > 1 and req_level:
            same_level = [row for row in candidates if row["DropLevel"] == int(req_level)]
            if same_level:
                candidates = same_level
                names = {ru.get(row["Id"]) for row in candidates}
        label = next(iter(names)) if len(names) == 1 else None
        ids = sorted(row["Id"] for row in candidates)
        if not label or label.startswith("[DNT"):
            unresolved.append({"name": name, "type": kind, "visibility": visibility, "candidates": ids,
                               "reason": "ambiguous or missing client name" if ids else "no client base ID"})
            continue
        catalog[name] = {"name": label, "ids": dict(enumerate(ids, 1))}
        if len(ids) > 1:
            shared_keys.append({"name": name, "russian": label, "ids": ids})
    return catalog, unresolved, shared_keys


def unique_matches(inventory, bases):
    columns = ("Wordlist", "HASH32", "Text", "Text2")
    en_words = list(read_rows("words", columns))
    ru_words = {(word["Wordlist"], word["HASH32"]): word for word in read_rows("words", columns, "russian")}
    visuals = list(read_rows("itemvisualidentity", ("Id", "DDSFile")))
    stash_types = list(read_rows("uniquestashtypes", ("Id",)))
    stash = defaultdict(list)
    for row in read_rows("uniquestashlayout", ("WordsKey", "ItemVisualIdentity", "UniqueStashTypes")):
        word_index, visual_index, type_index = (row[key] for key in ("WordsKey", "ItemVisualIdentity", "UniqueStashTypes"))
        if word_index < len(en_words) and visual_index < len(visuals) and type_index < len(stash_types):
            stash[word_index].append((stash_types[type_index]["Id"], visuals[visual_index]))
    by_name = defaultdict(list)
    for index, word in enumerate(en_words):
        if word["Wordlist"] == 6:
            for name in {word["Text"].strip(), word["Text2"].strip()}:
                by_name[name].append(index)
    catalog, unresolved, aliases = defaultdict(dict), [], []
    for title, base, kind, _ in inventory:
        indexes = by_name["Mjölner" if title == "Mjolner" else title]
        types = {
            "Focus": {"Focii"},
            "One Hand Mace": {"Mace"},
            "Two Hand Mace": {"Mace", "MaceTwoHand"},
            "Staff": {"Warstaff" if "Quarterstaff" in base else "Staff"},
        }.get(kind, {kind})
        candidates = []
        for index in indexes:
            word = en_words[index]
            russian = ru_words.get((word["Wordlist"], word["HASH32"]))
            if not russian or russian["Text"] != word["Text"]:
                continue
            label = russian["Text2"]
            matches = [visual for stash_type, visual in stash[index] if stash_type in types]
            if title == "Grand Spectrum":
                matches = [visual for visual in matches if PurePosixPath(visual["DDSFile"]).stem == f"GrandSpectrum_{base}"]
            if matches and label and not label.startswith("[DNT"):
                candidates.append((word, label, sorted({visual["Id"] for visual in matches})))
        if len(candidates) != 1 or base not in bases:
            unresolved.append({"title": title, "base": base, "type": kind, "reason": "could not confirm word and base IDs"})
            continue
        word, label, art_ids = candidates[0]
        catalog[title][base] = {"name": label, "wordId": word["HASH32"], "visualIds": dict(enumerate(art_ids, 1))}
        if word["Text"] != title:
            aliases.append({"title": title, "clientKey": word["Text"], "wordId": word["HASH32"], "russian": label})
    return dict(catalog), unresolved, aliases


def shrine_base_reviews(uniques, ru):
    # The unidentified Sacred Flame in 31/34 has its own icon and grants Purity of Fire.
    # UniqueStashLayout shares the three Guiding Palm visual IDs with Heart, Eye, and Mind.
    assignments = {
        "Sacred Flame": (("FourSceptre6a",), "trade card, name filter and Sacred Flame icon", ("Screenshot_31.png", "Screenshot_34.png")),
        "Palm of the Dreamer": (("FourSceptreUnique1",), "identified trade card", ("Screenshot_32.png",)),
        "Guiding Palm of the Heart": (("FourSceptre6a",), "identified trade card", ("Screenshot_33.png",)),
        "Guiding Palm of the Eye": (("FourSceptre6b",), "cold member of verified Guiding Palm family", ()),
        "Guiding Palm of the Mind": (("FourSceptre6c",), "lightning member of verified Guiding Palm family", ()),
        "Guiding Palm": (("FourSceptre6a", "FourSceptre6b", "FourSceptre6c"), "all three visual IDs shared with named elemental variants", ()),
    }
    family = ("Guiding Palm of the Heart", "Guiding Palm of the Eye", "Guiding Palm of the Mind")
    family_visuals = {
        visual_id
        for title in family
        for visual_id in uniques[title][SHRINE_BASE]["visualIds"].values()
    }
    if family_visuals != set(uniques["Guiding Palm"][SHRINE_BASE]["visualIds"].values()):
        raise ValueError("Guiding Palm visual IDs no longer match the named elements")
    for title in family:
        key = assignments[title][0][0].replace("FourSceptre", "FourUniqueSceptre")
        visual_ids = uniques[title][SHRINE_BASE]["visualIds"].values()
        if {visual_id.rstrip("_") for visual_id in visual_ids} != {key}:
            raise ValueError(f"Unexpected elemental visual ID for {title}")
    reviews = []
    for title, (keys, method, screenshots) in assignments.items():
        ids = [SHRINE_ID_PREFIX + key for key in keys]
        labels = {ru[item_id] for item_id in ids}
        if len(labels) != 1:
            raise ValueError(f"Inconsistent Shrine Sceptre labels for {title}")
        unique = uniques[title][SHRINE_BASE]
        unique["baseName"] = label = labels.pop()
        reviews.append({
            "title": title, "name": unique["name"], "baseName": label, "baseIds": ids,
            "visualIds": list(unique["visualIds"].values()), "method": method, "screenshots": list(screenshots),
        })
    return reviews


def main():
    inventory = (WORK / "pob-item-names.tsv").read_text(encoding="utf-8")
    groups = {"base": [], "unique": []}
    for line in inventory.splitlines():
        row_type, *fields = line.split("\t")
        groups[row_type].append(fields)
    base_rows, unique_rows = groups["base"], groups["unique"]
    rows = list(read_rows("baseitemtypes", ("Id", "Name", "Inflection"), "russian"))
    russian_bases = {row["Id"]: row["Name"] for row in rows}
    inflections = {row["Id"]: row["Inflection"] for row in rows}
    base_catalog, missing_bases, shared_keys = base_matches(base_rows, russian_bases)
    for entry in base_catalog.values():
        forms = {inflections[item_id] for item_id in entry["ids"].values()}
        if len(forms) == 1 and (form := forms.pop()):
            entry["inflection"] = form
    unique_catalog, missing_uniques, aliases = unique_matches(unique_rows, base_catalog)
    reviewed_bases = shrine_base_reviews(unique_catalog, russian_bases)
    pending_unique_bases = sorted(
        title for title, base, *_ in unique_rows
        if base == SHRINE_BASE and not unique_catalog.get(title, {}).get(base, {}).get("baseName")
    )
    english_bases = list(read_rows("baseitemtypes", ("Id", "Name")))
    runes_by_name = defaultdict(dict)
    for entry in read_rows("soulcores", ("BaseItemTypes",)):
        index = entry["BaseItemTypes"]
        if index >= len(english_bases):
            continue
        english = english_bases[index]
        russian = russian_bases.get(english["Id"], "")
        if english["Name"] and re.search("[А-Яа-яЁё]", russian):
            runes_by_name[english["Name"]][russian] = english["Id"]
    runes = {
        name: {"name": next(iter(matches)), "id": next(iter(matches.values()))}
        for name, matches in runes_by_name.items() if len(matches) == 1
    }
    report = {
        "pobVersion": "0.23.1",
        "gameVersion": "0.5.5g",
        "steamBuildId": 26650308,
        "source": ["BaseItemTypes.Id", "ItemClasses.Id", "Words.HASH32", "UniqueStashLayout", "ItemVisualIdentity.Id"],
        "baseNames": {"total": len(base_rows), "matched": len(base_catalog), "unresolved": missing_bases,
                      "sameLabelAcrossIds": shared_keys},
        "uniqueTitles": {"total": len(unique_rows), "matched": sum(map(len, unique_catalog.values())),
                         "unresolved": missing_uniques, "clientAliases": aliases},
        "uniqueBaseReviews": reviewed_bases,
        "pendingUniqueBaseLabels": pending_unique_bases,
        "socketableNames": {"matched": len(runes), "source": "SoulCores.BaseItemTypes"},
    }
    entries = []
    for key, values in (("bases", base_catalog), ("uniques", unique_catalog), ("runes", runes)):
        entries.append(f"\t{key} = {{")
        entries.extend(f"\t\t[{lua(name)}] = {lua(entry)}," for name, entry in sorted(values.items()))
        entries.append("\t},")
    (BUILD / "Data/Locale/item_names_ru.lua").write_text(
        "-- PoE 2 0.5.5g, Steam build 26650308. Generated by generate_pob_item_names_ru.py.\n"
        + "return {\n" + "\n".join(entries) + "\n}\n", encoding="utf-8",
    )
    (BUILD / "item-names-ru-coverage.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key in ("baseNames", "uniqueTitles"):
        print(key, report[key]["matched"], "/", report[key]["total"], report[key]["unresolved"])
    print(f"Reviewed unique base labels: {len(reviewed_bases)}, pending: {len(pending_unique_bases)}")


if __name__ == "__main__":
    main()
