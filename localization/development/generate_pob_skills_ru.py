import re
import unicodedata

from generate_pob_tree_ru import lua, plain
from read_poe2_dat import WORK, read_rows


DESTINATION = WORK.parent / "outputs/PoB2-RU/Data/Locale/skills_ru.lua"
REVIEWED_SUPPORTS = {
    "SupportColdExposurePlayer": (
        "Screenshot_24.png",
        "Supports any skill that Hits enemies, causing it to inflict Exposure when it Critically Hits an enemy.",
        "В игре описание указывает заморозку. Строка свойства и данные PoB 0.23.1 указывают критический удар уроном от холода.",
    ),
    "SupportBrambleslamPlayer": (
        "Screenshot_25.png",
        "Supports Slam Skills. Supported Skills create Hazardous Brambles on the ground that activate after a duration. "
        "Enemies which come in contact with these thorns take damage and are Maimed. A maximum of 20 Brambles are allowed "
        "at one time. Does not modify Skills used by Minions or Totems.",
        "Описание PoB 0.23.1 дополнительно указывает задержку срабатывания и лимит в 20 колючек.",
    ),
    "SupportFrozenSpitePlayer": (
        "Screenshot_26.png",
        "Supports Attack Skills, causing them to create Ice Fragments on killing Frozen Enemies. "
        "Cannot Support Totem Skills and does not modify Skills used by Minions.",
        "В PoB 0.23.1 этот камень подходит только умениям атак.",
    ),
    "SupportEshsProwess": (
        "Screenshot_27.png",
        "Supports Lightning skills that Hit targets, granting them an additional level and causing them to only roll "
        "the minimum or maximum value for Lightning damage. Does not support skills which do not have levels.",
        None,
        "Безграничное знание превзошло физическую форму.\n"
        "Её умы мельтешили по металлической решётке, когда\n"
        "сливающаяся плоть потянулась вместить её.",
    ),
    "SupportStyrnsFerocity": (
        "Screenshot_28.png",
        "Supports Shield Skills that Hit enemies, causing those Hits to Crush their targets, additionally causing any "
        "Physical Damage Hits against those targets while Crushed to Break their Armour.",
        None,
        "Каждый рыцарь, встречавший Стирна, вызывал его\n"
        "на традиционный поединок. Одолевая одного за другим,\n"
        "он пробил себе дорогу через весь Мидденгард... и за его пределы.",
    ),
}
ACTIVE_TEXT_REVISIONS = {
    "AzmerianSwarmPlayer": (("inflict Faerie Fire", "infict Faerie Fire"),),
    "ExplodingPoisonToadPlayer": (
        ("the toad then explodes", "then explodes the toad"), ("with this skill", "with skill"),
    ),
    "FlickerStrikePlayer": (("to an enemy and Strike", "to a enemy and Strike"),),
    "FlameblastPlayer": (("the longer you Channel for", "the longer you Channelled for"),),
    "GatheringStormPlayer": (("Releasing causes you to dash", "Releasing dashes"),),
    "HeraldOfThunderPlayer": (("which dealAttack damage", "which deals Attack damage"),),
    "RefutationPlayer": (("Spends all your Runic Ward", "Spends all your Ward"),),
    "RollingMagmaPlayer": (("The skillChains", "The skill Chains"),),
    "SerpentClanCurse": (("after a short delay, making Hits", "after a short delay. making Hits"),),
    "TriggeredCorruptingCryThreePlayer": (("severely damages them", "severly damages them"),),
    "VoltaicBarrierPlayer": (("Spend Runic Ward to raise a pair", "Raise a pair"),),
    "VulnerabilityPlayer": (("after a short delay, making Hits", "after a short delay. making Hits"),),
    "WolfCrossSlashPlayer": (("explode. immediately.", "explode immediately."),),
    "WolfLeapAttackMinion": (("Knocking Back back enemies", "knocking back enemies"),),
}
ACTIVE_PRIOR_TEXT = {
    # The Ward costs are already present in PoB's level data for these skills.
    "CurseOfRepulsionPlayer": "Target an area and Curse enemies within with a Verisium Rune, inflicting them with "
    "Fragility. Hitting these enemies causes the Curse to Trigger an explosion to deal damage in an area and apply "
    "significant Knockback to other enemies near the Cursed target, with more Stun buildup based on the Fragility on the target Hit.",
    "DetonateLivingPlayer": "Hit an enemy under the Culling Strike Threshold, causing them to violently explode, "
    "damaging surrounding enemies. Highlights enemies under the Culling Strike Threshold.",
    "TriggeredBrambleslamPlayer": "Hazardous thorns damage and Maim enemies with which they come in contact.",
}
SUMMON_SELECTION_LABELS = {
    "SummonBeastPlayer": ("Tamed Companion", "Призыв компаньона"),
    "SummonSpectrePlayer": ("Summon Spectre", "Призыв призрака"),
}


def localized_table(table, columns):
    return {row["Id"]: row for row in read_rows(table, ["Id", *columns], "russian")}


def gem_client_text():
    fields = ["Id", "Text"]
    translations = localized_table("clientstrings", fields[1:])
    text = {}
    for row in read_rows("clientstrings", fields):
        key = row["Id"]
        if key.startswith(("ItemDisplaySkillGem", "SkillPopupCostValue", "WeaponClassDisplayName")) or key in {
            "Level", "Quality", "Tier", "SkillIsInstant", "MonsterCorrupted", "HeistRequiresText",
            "ItemDescriptionGemQualityStatDivider", "GemStashFilterGreen",
            "ItemDisplayGemReservationSpirit", "StrengthShort", "DexterityShort", "IntelligenceShort",
            "EveryMartialWeaponTypeAndUnarmed", "EveryMartialWeaponTypeNonTalisman",
        }:
            entry = translations.get(key)
            if entry and entry["Text"]:
                value = plain(re.sub(r"<\w+>\{([^{}]+)\}", r"\1", entry["Text"]))
                text[key] = value
                if key.startswith("SkillPopupCostValue") and row["Text"].startswith("{0} "):
                    source = row["Text"].replace("Runic Ward", "Ward")
                    text[source] = value
                    text[source.replace("{0}", "{0}%")] = value.replace("{0}", "{0}%")
                elif key.startswith("WeaponClassDisplayName") or key.startswith("EveryMartialWeaponType"):
                    source = plain(row["Text"])
                    text[source] = value
                    if key == "EveryMartialWeaponTypeAndUnarmed":
                        text[source.split(",", 1)[0]] = value.split(",", 1)[0]
    return text


def localized_names(table, column="Name"):
    translated = localized_table(table, [column])
    return {
        plain(row[column]): plain(translated[row["Id"]][column])
        for row in read_rows(table, ["Id", column])
        if row[column] and translated.get(row["Id"], {}).get(column)
    }


def minion_names():
    data = WORK / "PoB2-baseline/Data"
    ids = {id_ for filename in ("Spectres.lua", "Minions.lua")
           for id_ in re.findall(r'\["(Metadata/Monsters/[^"\n]+)"\]\s*=', (data / filename).read_text(encoding="utf-8"))}
    translated = localized_table("monstervarieties", ["Name"])
    return {id_: plain(translated[id_]["Name"]) for id_ in ids if translated.get(id_, {}).get("Name")}


def gem_entries(granted):
    bases = list(read_rows("baseitemtypes", ["Id", "Name"]))
    translated_bases = localized_table("baseitemtypes", ["Name"])
    gems = list(read_rows("gemeffects", ["Id", "Name", "Description", "GrantedEffect"]))
    translated_gems = localized_table("gemeffects", ["Name", "Description"])
    identities, effects = {}, {}
    for gem in read_rows("skillgems", ["BaseItemType", "GemEffects"]):
        if gem["BaseItemType"] >= len(bases):
            continue
        base = bases[gem["BaseItemType"]]
        ru_base = translated_bases.get(base["Id"], {})
        for index in gem["GemEffects"]:
            if index >= len(gems):
                continue
            row = gems[index]
            if row["GrantedEffect"] >= len(granted):
                continue
            effect = granted[row["GrantedEffect"]]
            ru = translated_gems.get(row["Id"], {})
            names = identities.setdefault(base["Id"], {}).setdefault(effect["Id"], {})
            for en, localized in ((base["Name"], ru_base.get("Name")), (row["Name"], ru.get("Name"))):
                if en and localized:
                    source = plain(en)
                    name = plain(localized)
                    names[source] = name
                    # PoB stores some English lineage names without their accents.
                    no_accents = "".join(c for c in unicodedata.normalize("NFD", source) if not unicodedata.combining(c))
                    if no_accents.isascii():
                        names.setdefault(no_accents, name)
            selection = SUMMON_SELECTION_LABELS.get(effect["Id"])
            if selection and "{0}" in ru_base.get("Name", ""):
                names[selection[0]] = selection[1]
            if row["Description"] and ru.get("Description"):
                entry = {
                    "enDescription": plain(row["Description"]),
                    "description": plain(ru["Description"]),
                }
                reviewed = REVIEWED_SUPPORTS.get(effect["Id"])
                if reviewed:
                    screenshot, old_description, note, *flavour = reviewed
                    entry.update(screenshot=screenshot, pobDescription=old_description)
                    if note:
                        entry["comparisonNote"] = note
                    if flavour:
                        entry["flavour"] = flavour[0]
                for name, localized in names.items():
                    effects.setdefault(effect["Id"], {})[name] = {**entry, "name": localized}
    return identities, effects


def main():
    fields = ["Id", "DisplayName", "Description"]
    active = list(read_rows("activeskills", fields))
    russian = localized_table("activeskills", fields[1:])
    granted = list(read_rows("grantedeffects", ["Id", "ActiveSkill"]))
    effects = {}
    for effect in granted:
        index = effect["ActiveSkill"]
        if index >= len(active):
            continue
        source = active[index]
        localized = russian.get(source["Id"])
        if not localized or not localized["DisplayName"]:
            continue
        record = {"en": plain(source["DisplayName"]), "name": plain(localized["DisplayName"])}
        if effect["Id"] in SUMMON_SELECTION_LABELS:
            record["selectionName"] = SUMMON_SELECTION_LABELS[effect["Id"]][1]
        if source["Description"] and localized["Description"]:
            record["enDescription"] = plain(source["Description"])
            record["description"] = plain(localized["Description"])
            revision = ACTIVE_TEXT_REVISIONS.get(effect["Id"], ())
            if revision and all(record["enDescription"].count(current) == 1 for current, _ in revision):
                previous = record["enDescription"]
                for current, old in revision:
                    previous = previous.replace(current, old)
                record["pobDescription"] = previous
            elif effect["Id"] in ACTIVE_PRIOR_TEXT:
                record["pobDescription"] = ACTIVE_PRIOR_TEXT[effect["Id"]]
        effects[effect["Id"]] = record

    names, gem_effects = gem_entries(granted)
    for suffix, rank in (("", "I"), ("Two", "II"), ("Three", "III")):
        support = gem_effects["SupportBarbsPlayer" + suffix]["Barbs " + rank]
        effects["TriggeredBarbsPlayer" + suffix] = {
            "en": "Barbs " + rank,
            "name": support["name"],
            "enDescription": "Deal twice your thorns damage." if rank == "III" else "Deal your thorns damage.",
            "description": "Наносит двойной урон от ваших шипов." if rank == "III" else "Наносит урон от ваших шипов.",
        }
    lines = ["-- Skill and gem text from the PoE 2 0.5.5g Steam client, build 26650308.", "return {"]
    for field, records in (("active", effects), ("gems", names), ("gemEffects", gem_effects),
                           ("clientText", gem_client_text()), ("families", localized_names("supportgemfamily")),
                           ("tags", localized_names("gemtags")), ("statLabels", localized_names("grantedeffectlabels", "Label")),
                           ("minions", minion_names())):
        lines.append(field + "={")
        lines.extend(f"[{lua(key)}]={lua(record)}," for key, record in sorted(records.items()))
        lines.append("},")
    DESTINATION.write_text("\n".join([*lines, "}", ""]), encoding="utf-8")
    print(f"Generated {len(effects)} active skills and {len(names)} gem base records.")


if __name__ == "__main__":
    main()
