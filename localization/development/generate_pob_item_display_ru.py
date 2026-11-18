import re

from generate_pob_tree_ru import lua, plain
from read_poe2_dat import WORK, read_rows


BUILD = WORK.parent / "outputs/PoB2-RU"
SOURCE_IDS = {
    "monstervarieties": {
        "Arbiter of Ash": "Metadata/Monsters/AtlasBosses/DemonClawBoss/DemonClawBoss",
        "Kosis, The Revelation": "Metadata/Monsters/LeagueDelirium/DeliriumDemonBossFinal",
        "Olroth, Origin of the Fall": "Metadata/Monsters/LeagueExpeditionNew/Olroth/Olroth",
        "The King in the Mists": "Metadata/Monsters/VoodooKing/VoodooKingBoss2",
        "Trialmaster": "Metadata/Monsters/TrialMaster/TheTrialmaster_",
        "Vessel of Kulemak": "Metadata/Monsters/LeagueAbyss/LichBoss/KulemakBoss",
        "Xesht, We That Are One": "Metadata/Monsters/Breach/BreachOverseerBoss/ItThatReturned",
        "Zarokh, the Temporal": "Metadata/Monsters/ApparitionBoss/SilentSpiresApparition",
    },
    "chests": {"Atziri's Vault": "Metadata/Chests/LeagueIncursion/AtziriVaultChestPrimary"},
    "worldareas": {
        "The Burning Monolith": "MapUberBoss_Monolith",
        "Vaal Temple": "IncursionTemple",
        "Crux of Nothingness": "RitualLeagueBoss",
        "The Trial of Chaos": "G3_10",
        "Twisted Domain": "BreachDomain_01",
    },
}


def names_by_id(table, column):
    return {row["Id"]: plain(row[column]) for row in read_rows(table, ("Id", column), "russian")}


def main():
    flavour_source = (BUILD / "Data/FlavourText.lua").read_text(encoding="utf-8")
    flavour_ids = set(re.findall(r'\["id"\]\s*=\s*"([^"]+)"', flavour_source))
    russian_flavour = names_by_id("flavourtext", "Text")
    flavour = {key: russian_flavour[key].splitlines() for key in sorted(flavour_ids) if russian_flavour.get(key)}
    russian_leagues = names_by_id("leaguenames", "Name1")
    leagues = {row["Name1"].lower(): russian_leagues[row["Id"]]
               for row in read_rows("leaguenames", ("Id", "Name1")) if russian_leagues.get(row["Id"])}
    origins = names_by_id("origin", "Format")
    sources = {}
    for table, ids in SOURCE_IDS.items():
        russian = names_by_id(table, "Name")
        for english, source_id in ids.items():
            if not russian[source_id]:
                raise ValueError(f"Missing source name for {source_id}")
            sources[english] = russian[source_id]
    lines = ["-- GGG game text from PoE 2 0.5.5g, Steam build 26650308.", "return {", "\tflavour = {"]
    lines.extend(f"\t\t[{lua(key)}] = {lua(dict(enumerate(value, 1)))}," for key, value in flavour.items())
    lines.extend(["\t},", "\tleagues = " + lua(leagues) + ",", "\torigins = " + lua(origins) + ",",
                  "\tsources = " + lua(sources) + ",", "}", ""])
    (BUILD / "Data/Locale/item_display_ru.lua").write_text("\n".join(lines), encoding="utf-8")
    print(f"Flavour text: {len(flavour)}; empty or missing client records: {sorted(flavour_ids - flavour.keys())}.")


if __name__ == "__main__":
    main()
