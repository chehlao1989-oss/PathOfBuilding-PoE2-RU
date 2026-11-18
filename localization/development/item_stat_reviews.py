from collections import defaultdict

from generate_pob_gem_stats_ru import CSD, gamedata
from generate_pob_tree_ru import plain
from read_poe2_dat import read_rows


LOCAL_DEFENCES = (
    "{0}% increased Armour, Evasion and Energy Shield",
    "local_armour_and_evasion_and_energy_shield_+%",
)
INTIMIDATE = (
    "{0}% chance to Intimidate Enemies for 4 seconds on Hit",
    "chance_to_intimidate_on_hit_%",
)
LOSE_LIFE = ("Lose {0}% of maximum Life on Kill", "recover_%_maximum_life_on_kill")
STATIONARY_GROUND = (
    "You have Consecrated Ground around you while stationary",
    "gifts_from_above_consecrated_ground_while_stationary",
)


def reviewed_item_templates(pairs):
    general = {}
    scoped = defaultdict(dict)
    reviews = []

    def client(stat, english, russian=None):
        candidates = {
            ru for (en, ru), ids in pairs.items()
            if stat in ids and en == english and (russian is None or ru == russian)
        }
        if len(candidates) != 1:
            raise ValueError(f"{stat}: expected one client template for {english!r}, got {sorted(candidates)!r}")
        return candidates.pop()

    def add(english, russian, stat, items=()):
        if items:
            for title in items:
                scoped[title][(english, russian)] = {stat}
        else:
            general[(english, russian)] = {stat}
        reviews.append({"items": list(items), "source": english, "russian": russian, "statId": stat})

    for (english, stat), items, preferred in (
        (LOCAL_DEFENCES, ("Sine Aequo", "Ab Aeterno", "Solus Ipse", "Morior Invictus", "Atziri's Splendour"), None),
        (INTIMIDATE, ("Loreweave", "Blackheart"), None),
        (LOSE_LIFE, ("Arvil's Wheel", "Aurseize"), None),
        (STATIONARY_GROUND, ("Gifts from Above", "Loreweave"), None),
        (("{0}% increased Accuracy Rating", "accuracy_rating_+%"), ("Nocturne",), None),
        (("{0}% increased Experience gain", "experience_gain_+%"), ("Cornathaum",), None),
        (("Cannot be Poisoned", "cannot_be_poisoned"), ("Quatl's Molt",), "Не может быть отравлен"),
        (("Creates Consecrated Ground on use", "charm_create_consecrated_ground_when_used"), ("Sanguis Heroum",), None),
    ):
        add(english, client(stat, english, preferred), stat, items)

    spirit = "base_spirit_reservation_efficiency_+%"
    add("{0}% increased Spirit Reservation Efficiency",
        client(spirit, "{0}% increased Spirit Reservation Efficiency of Skills"), spirit)
    charges = "generate_x_charges_for_charms_per_minute"
    add("Charms gain 1 charge per Second", client(charges, "Charms gain {0} charges per Second").replace("{0}", "1"), charges)
    sockets = "local_has_X_sockets"
    add("Has 4 Augment Sockets", client(sockets, "Has {0} Sockets").replace("{0}", "4"), sockets,
        ("The Bringer of Rain", "Greymake"))
    projectiles = "spell_projectile_skills_fire_X_additional_projectiles_in_a_circle"
    projectile_count = "Spells fire {0:d} additional Projectiles"
    projectile_text = client(projectiles, projectile_count + "\nSpells fire Projectiles in a circle").splitlines()[0]
    add(projectile_count, projectile_text, projectiles, ("Sire of Shards",))
    movement = "movement_speed_is_only_base_+1%_per_x_evasion_rating"
    movement_tail = "Other Modifiers to Movement Speed except for Sprinting do not apply"
    movement_head = "Increases Movement Speed by 25%, plus 1% per {0} Evasion Rating, up to a maximum of 75%"
    add(movement_tail, client(movement, movement_head + "\n" + movement_tail).splitlines()[1], movement,
        ("Queen of the Forest",))

    # PoB's original line breaks occur at different points than the localized property.
    # Use the exact whole client sentence, split at the corresponding phrase.
    for title, stat, source_lines, split_before in (
        ("Window to Paradise", "unique_shield_window_of_paradise_apply_elemental_exposure_while_raised",
         ("Inflict Elemental Exposure to Enemies 3 metres in front of you", "for 4 seconds, every 0.25 seconds while raised"),
         "на 4 секунды"),
        ("Font of Power", "unique_%_maximum_mana_to_sacrifice_to_party_members_in_your_presence_when_they_cast_a_spell",
         ("When a Party Member in your Presence Casts a Spell, you", "Sacrifice {0}% of Mana and they Leech that Mana"),
         "жертвуете"),
        ("Olrovasara", "local_maximum_added_lightning_damage_equal_to_total_monster_power_of_enemies_hit_in_past_20_seconds_up_to_X",
         ("On Hitting an enemy, gains maximum added Lightning damage equal to", "the enemy's Power for 20 seconds, up to a total of {0}"),
         "на уровень угрозы"),
        ("Widow's Reign", "reserve_life_instead_of_loss_from_damage_for_x_ms",
         ("Life that would be lost by taking Damage is instead Reserved", "until you take no Damage to Life for {0} seconds"),
         "до тех пор"),
        ("The Flesh Poppet", "gain_a_modifier_from_enemies_in_presence_when_shapeshifting_ms",
         ("Copy a random Modifier from each enemy in your Presence when", "you Shapeshift to an Animal form",
          "Modifiers gained this way are lost after {0} seconds or when you next Shapeshift"),
         "вы принимаете"),
    ):
        russian = client(stat, "\n".join(source_lines)).splitlines()
        head, separator, tail = russian[0].partition(" " + split_before)
        if not separator:
            raise ValueError(f"Could not align localized description for {title}")
        target_lines = (head, split_before + tail, *russian[1:])
        for source, target in zip(source_lines, target_lines, strict=True):
            add(source, target, stat, (title,))

    bow = "consume_%_of_maximum_life_flask_charges_on_bow_attack,bow_attacks_deal_added_physical_damage_equal_to_x%_of_life_flask_recovery_amount"
    source = (CSD / "stat_descriptions.csd").read_text(encoding="utf-16")
    # The Russian Bow modifier has explicit positive bounds, and the exported English rule has open bounds.
    entry = next(row for row in gamedata.parse_csd(source, "Russian")["entries"] if ",".join(row["stats"]) == bow)
    en, ru = entry["en"], entry["want"]
    if len(en) != 1 or len(ru) != 1:
        raise ValueError("The Lethal Draw modifier now has multiple rules")
    add(plain(en[0]["text"]), plain(ru[0]["text"]), bow, ("The Lethal Draw",))

    legacy_ids = [f"local_unique_mages_legacy_{slot}" for slot in range(1, 5)]
    english_legacy = {row["Name"]: plain(row["DisplayText"]) for row in read_rows("uniquemageslegacy", ("Name", "DisplayText"))}
    legacy_templates = {client(stat, "Legacy of {0}") for stat in legacy_ids}
    if len(legacy_templates) != 1:
        raise ValueError("Mageblood legacy slots have different translations")
    russian_legacy = legacy_templates.pop()
    for row in read_rows("uniquemageslegacy", ("Name", "DisplayText"), "russian"):
        english = english_legacy[row["Name"]]
        add(f"Legacy of {english}", russian_legacy.replace("{0}", plain(row["DisplayText"])),
            ",".join(legacy_ids), ("Mageblood",))

    missing_values = {
        "PassageUniqueAmanamuAbyssalWastingReducesFireRes": "Fire",
        "PassageUniqueKurgalAbyssalWastingReducesColdRes": "Cold",
        "PassageUniqueUlamanAbyssalWastingReducesLightningRes": "Lightning",
    }
    stats = [row["Id"] for row in read_rows("stats", ("Id",))]
    for row in read_rows("mods", ("Id", "Stat1", "Stat1Value")):
        element = missing_values.get(row["Id"])
        if element:
            stat = stats[row["Stat1"]]
            source = f"Abyssal Wasting also applies {{0:-d}}% to {element} Resistance"
            target = client(stat, source).replace("{0:-d}", "…")
            add(source.replace("{0:-d}", ""), target, stat, ("Grip of Kulemak",))
            reviews[-1].update(modId=row["Id"], clientValues=row["Stat1Value"], reason="PoB source omits the value")
    return general, scoped, reviews
