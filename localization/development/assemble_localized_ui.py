from pathlib import Path
from shutil import copyfile
import json
from tarfile import open as open_tar
from zipfile import ZipFile

from patch_ui_layout import patch_layout
from patch_item_filter import patch_item_filter, write_item_filter_catalog
from patch_item_names import patch_item_names
from patch_calcs_config import patch_calcs_config, replace_region
from patch_item_runes import patch_item_runes
from patch_item_clipboard import patch_item_clipboard
from patch_build_warnings import patch_build_warnings
from generate_pob_rare_templates_ru import write_rare_template_catalog
from patch_trade_locale import patch_trade_locale
from patch_character_import_locale import patch_character_import_locale
from patch_project_support import patch_project_support


WORK = Path(__file__).resolve().parent
BASE = WORK / "PoB2-baseline"
BUILD = WORK.parent / "outputs" / "PoB2-RU"
UPSTREAM = WORK / "upstream-downloads" / "reference"


def edit(relative_path, replacements, *, source=BASE):
    original = (source / relative_path).read_text(encoding="utf-8")
    for old, new, *expected_count in replacements:
        expected = expected_count[0] if expected_count else 1
        if original.count(old) != expected:
            raise ValueError(f"{relative_path}: expected {expected} match(es) for {old!r}")
        original = original.replace(old, new, expected)
    (BUILD / relative_path).write_text(original, encoding="utf-8", newline="\n")


def compile_catalog(source_name, output_name):
    messages = {}
    for number, line in enumerate((WORK / source_name).read_text(encoding="utf-8").splitlines(), 1):
        if not line or (line.startswith("#") and "\t" not in line):
            continue
        english, russian = (part.replace(r"\n", "\n").replace(r"\t", "\t") for part in line.split("\t", 1))
        if english in messages:
            raise ValueError(f"Duplicate msgid on line {number}: {english!r}")
        messages[english] = russian
    result = BUILD / "Data" / "Locale" / output_name
    result.parent.mkdir(parents=True, exist_ok=True)
    quote = lambda string: json.dumps(string, ensure_ascii=False)
    lines = [f"\t[{quote(en)}] = {quote(ru)}," for en, ru in sorted(messages.items())]
    result.write_text("-- Russian interface catalog\nreturn {\n" + "\n".join(lines) + "\n}\n", encoding="utf-8")
    print(f"{source_name}: compiled {len(messages)} messages.")


def main():
    compile_catalog("interface.ru.tsv", "ru.lua")
    compile_catalog("config.ru.tsv", "config_ru.lua")
    compile_catalog("trade.ru.tsv", "trade_ru.lua")
    write_rare_template_catalog()
    write_item_filter_catalog(BUILD / "Data" / "Locale" / "item_filter_ru.lua")
    archive = UPSTREAM.parent / "i18n-portable.zip"
    with ZipFile(archive) as release:
        for name in ("SimpleGraphic.dll", "fmt.dll", "re2.dll", "abseil_dll.dll"):
            destination = BUILD / name
            binary = release.read(name)
            if not destination.exists() or destination.read_bytes() != binary:
                destination.write_bytes(binary)
    copyfile(UPSTREAM / "LICENSE-i18n.md", BUILD / "LICENSE-i18n.md")
    fonts = BUILD / "SimpleGraphic" / "Fonts"
    font_version = "liberation-fonts-ttf-2.1.5"
    with open_tar(UPSTREAM.parent / "liberation-fonts-2.1.5.tar.gz", "r:gz") as release:
        for filename in ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"):
            with release.extractfile(f"{font_version}/{filename}") as font:
                (fonts / filename).write_bytes(font.read())
        with release.extractfile(f"{font_version}/LICENSE") as license_file:
            (fonts / "Liberation-Fonts-OFL.txt").write_bytes(license_file.read())
    for style, filename in (
        ("Liberation Sans", "LiberationSans-Regular.ttf"),
        ("Liberation Sans Bold", "LiberationSans-Bold.ttf"),
        ("UnicodeFallback", "LiberationSans-Regular.ttf"),
    ):
        (fonts / (style + ".tgf")).write_text(
            json.dumps({"fonts": [{"file": filename, "scale": 1.0}]}) + "\n",
            encoding="utf-8",
        )

    edit("Launch.lua", [
        ('APP_NAME = "Path of Building (PoE2)"', 'APP_NAME = "Path of Building (PoE2) RU"'),
        ('\tRenderInit("DPI_AWARE")', '\tRenderInit("DPI_AWARE")\n\tUILocale = LoadModule("Modules/UILocale")'),
        ('function launch:CheckForUpdate(inBackground)\n\tif self.updateCheckRunning then',
         'function launch:CheckForUpdate(inBackground)\n\t-- Official releases would overwrite this localized installation.\n\tif UILocale or self.updateCheckRunning then'),
    ])

    edit("Modules/Main.lua", [
        ('return not launch.devMode and (not launch.updateAvailable or launch.updateAvailable == "none")',
         'return not UILocale and not launch.devMode and (not launch.updateAvailable or launch.updateAvailable == "none")'),
        ('self.unicode = type(_G.utf8) == "table"', 'self.unicode = true'),
        ('elseif node.elem == "Misc" then\n', 'elseif node.elem == "Misc" then\n\t\t\t\tUILocale.setLanguage(node.attrib.uiLanguage)\n'),
        ('t_insert(setXML, { elem = "Misc", attrib = {\n', 't_insert(setXML, { elem = "Misc", attrib = {\n\t\tuiLanguage = UILocale.language,\n'),
        ('\tlocal oneColumnHeightReq = 850', '\tlocal oneColumnHeightReq = 876'),
        ('\tdrawSectionHeader("app", "Application options")\n',
         '''\tdrawSectionHeader("app", "Application options")

\tcontrols.uiLanguage = new("DropDownControl", { "TOPLEFT", controls.sectionAnchor, "TOPLEFT" }, { currentX + defaultLabelPlacementX, currentY, 150, 18 }, {
\t\t{ label = "Русский", language = "ru" },
\t\t{ label = "English", language = "en" },
\t})
\tcontrols.uiLanguage:SelByValue(UILocale.language, "language")
\tcontrols.uiLanguage.tooltipText = "Choose the interface language."
\tcontrols.uiLanguageLabel = new("LabelControl", { "RIGHT", controls.uiLanguage, "LEFT" }, { defaultLabelSpacingPx, 0, 0, 16 }, "^7Language:")
\tnextRow()
'''),
        ('\t\tlaunch.connectionProtocol = tonumber(self.connectionProtocol)',
         '\t\tUILocale.setLanguage(controls.uiLanguage.list[controls.uiLanguage.selIndex].language)\n\t\tlaunch.connectionProtocol = tonumber(self.connectionProtocol)'),
        ('\t\tif not launch.devMode then\n\t\t\tmain:SetManifestBranch', '\t\tif not UILocale and not launch.devMode then\n\t\t\tmain:SetManifestBranch'),
        ('{0, 0, 68, 20}, "Options"', '{0, 0, 99, 20}, "Options"'),
        ('{72, 0, 68, 20}, "About"', '{103, 0, 68, 20}, "About"'),
        ('{148, -2, 0, 16}, ""', '{176, -2, 0, 16}, ""'),
        ('\tcontrols.betaTest.state = self.betaTest', '\tcontrols.betaTest.enabled = false\n\tcontrols.betaTest.state = self.betaTest'),
    ])

    patch_project_support(BUILD)

    edit("Modules/Build.lua", [
        ('\tself.controls.statBox.height = function(control)',
         '\tself.controls.statBox.wrapStatColumns = true\n\tself.controls.statBox.height = function(control)'),
        ('local valStr = s_format("%"..statData.fmt, val)\n\tvalStr:gsub("%.", main.decimalSeparator)',
         'local valStr = UILocale.language == "ru" and math.abs(val) == math.huge and (val < 0 and "−∞" or "∞")\n\t\tor s_format("%"..statData.fmt, val)\n\tvalStr:gsub("%.", main.decimalSeparator)'),
        ('.. " (" .. statData.val  .. ")"', '.. " (" .. UILocale.translate(statData.val) .. ")"'),
        ('local lhsString = labelColor..skillData.name..triggerStr..":"',
         'local localSkillName = UILocale.effectCaption(skillData.name)\n\t\t\t\t\t\t\tlocal lhsString = labelColor..localSkillName..triggerStr..":"'),
        ('.."x "..skillData.name..triggerStr..":"', '.."x "..localSkillName..triggerStr..":"'),
        ('"^8"..skillData.skillPart', '"^8"..UILocale.effectCaption(skillData.skillPart)'),
        ('{0, 0, 60, 20}, "<< Back"', '{0, 0, 68, 20}, "<< Back"'),
        ('{8, 0, 50, 20}, "Save"', '{8, 0, 80, 20}, "Save"'),
        ('{8, 0, 70, 20}, "Save As"', '{8, 0, 110, 20}, "Save As"'),
        replace_region(
            (BASE / "Modules/Build.lua").read_text(encoding="utf-8"),
            "\t-- conditional for smaller screens", "\t-- Controls: top bar, right side",
            '''	local buildCaption = "Current build:"
	local function buildNameTopX()
		return self.controls.saveAs:GetPos() + self.controls.saveAs:GetProperty("width") + 8
	end
	local function buildNameTopWidth()
		return self.controls.pointDisplay:GetPos() - buildNameTopX() - 8
	end
	local function buildNameCaptionWidth()
		return DrawStringWidth(16, "VAR", buildCaption) + 8
	end
	local function buildNameConditional()
		return buildNameTopWidth() < buildNameCaptionWidth() + 110
	end
	local function buildNameLayout()
		local name = self.buildName
		if not self.dbFileName and name == "Unnamed build" then
			name = UILocale.translate(name)
		end
		local captionWidth = buildNameCaptionWidth()
		local available = buildNameConditional() and 300 or buildNameTopWidth()
		local nameWidth = UILocale.measureRaw(16, "VAR", name)
		local textWidth = m_min(nameWidth, available - captionWidth - 8)
		return name, captionWidth, textWidth, textWidth < nameWidth
	end
	self.controls.buildName = new("Control", nil, {0, 4, 0, 20})
	self.controls.buildName.width = function()
		local _, captionWidth, textWidth = buildNameLayout()
		return captionWidth + textWidth + 8
	end
	self.controls.buildName.x = function(control)
		return buildNameConditional() and 304 - control:GetProperty("width") or buildNameTopX()
	end
	self.controls.buildName.y = function()
		return buildNameConditional() and 36 or 4
	end
	self.controls.buildName.Draw = function(control)
		local x, y = control:GetPos()
		local name, captionWidth, textWidth, truncated = buildNameLayout()
		local frameX, frameWidth = x + captionWidth, textWidth + 8
		SetDrawColor(0.5, 0.5, 0.5)
		DrawImage(nil, frameX, y, frameWidth, 20)
		SetDrawColor(0, 0, 0)
		DrawImage(nil, frameX + 1, y + 1, frameWidth - 2, 18)
		SetDrawColor(1, 1, 1)
		DrawString(x, y + 2, "LEFT", 16, "VAR", buildCaption)
		SetViewport(frameX + 4, y + 2, textWidth + 1, 16)
		UILocale.drawRaw(0, 0, "LEFT", 16, "VAR", name)
		SetViewport()
		if control:IsMouseInBounds() then
			SetDrawLayer(nil, 10)
			miscTooltip:Clear()
			if self.dbFileSubPath and self.dbFileSubPath ~= "" then
				miscTooltip:AddLine(16, self.dbFileSubPath..name)
			elseif truncated then
				miscTooltip:AddLine(16, name)
			end
			miscTooltip:Draw(x, y, control:GetProperty("width"), 20, main.viewPort)
			SetDrawLayer(nil, 0)
		end
	end

''',
        ),
        ('{-90, 70, 80, 20}, "Save"', '{-112, 70, 94, 20}, "Save"'),
        ('{0, 70, 80, 20}, "Don\'t Save"', '{0, 70, 112, 20}, "Don\'t Save"'),
        ('{90, 70, 80, 20}, "Cancel"', '{112, 70, 94, 20}, "Cancel"'),
        ('tooltip:AddLine(14, header)', 'tooltip:AddLine(14, UILocale.translate(header))'),
        ('local line = s_format("%s%s %s", color, valStr, statData.label)',
         'local line = s_format("%s%s %s", color, valStr, UILocale.translate(statData.label))'),
        ('.."%s per point]", diff * ((statData.pc or statData.mod) and 100 or 1) / nodeCount, pcPerPt)',
         '.."%s %s]", diff * ((statData.pc or statData.mod) and 100 or 1) / nodeCount, pcPerPt, UILocale.translate("per point"))'),
        ('{ val = i, label = socketGroup.displayLabel }', '{ val = i, label = UILocale.skillGroupName(socketGroup) }'),
        ('s_format("^7Level %s%d", main:StatColor(level, nil, self.characterLevel), level)',
         's_format("^7%s %s%d", UILocale.gemText("Level", "Level"), main:StatColor(level, nil, self.characterLevel), level)'),
        ('s_format("^x7F7F7FLevel %s%d", main:StatColor(level, nil, self.characterLevel), level)',
         's_format("^x7F7F7F%s %s%d", UILocale.gemText("Level", "Level"), main:StatColor(level, nil, self.characterLevel), level)'),
        ('local attrTextColor = (tooltip.tooltipHeader == "GEM") and "^7" or "^x7F7F7F"',
         '''local attrTextColor = (tooltip.tooltipHeader == "GEM") and "^7" or "^x7F7F7F"
			local ruRequirements = UILocale.language == "ru"'''),
        ('attrTextColor, level and "Str" or "Strength"', 'attrTextColor, ruRequirements and UILocale.gemText("StrengthShort", "Str") or (level and "Str" or "Strength")'),
        ('attrTextColor, level and "Dex" or "Dexterity"', 'attrTextColor, ruRequirements and UILocale.gemText("DexterityShort", "Dex") or (level and "Dex" or "Dexterity")'),
        ('attrTextColor, level and "Int" or "Intelligence"', 'attrTextColor, ruRequirements and UILocale.gemText("IntelligenceShort", "Int") or (level and "Int" or "Intelligence")'),
        ('"^x7F7F7FRequires "..table.concat(req, "^x7F7F7F, ")',
         '"^x7F7F7F" .. (UILocale.language == "ru" and UILocale.gemText("HeistRequiresText", "Requires") .. ": " or "Requires ") .. table.concat(req, "^x7F7F7F, ")'),
        ('"   ^x7F7F7FRequires: "..table.concat(req, "^7, ")',
         '"   ^x7F7F7F" .. UILocale.gemText("HeistRequiresText", "Requires") .. ": " .. table.concat(req, "^7, ")'),
        ('t_insert(controls.mainSkill.list, { val = i, label = colourCoded or self.calcsTab.calcs.getActiveSkillDisplayName(activeSkill) })',
         '''local label = self.calcsTab.calcs.getActiveSkillDisplayName(activeSkill)
			local effect = activeSkill.activeEffect.grantedEffect
			t_insert(controls.mainSkill.list, { val = i, label = colourCoded or UILocale.skillDisplayName(effect, label, activeSkill.activeEffect.srcInstance.skillMinion) })'''),
        ('label = statSet.label, grantedEffectId = activeEffect.grantedEffect.id',
         'label = UILocale.skillVariantLabel(statSet.label, activeEffect.grantedEffect), grantedEffectId = activeEffect.grantedEffect.id'),
        ('label =  statSet.label, grantedEffectId = activeEffect.grantedEffect.id',
         'label = UILocale.skillVariantLabel(statSet.label), grantedEffectId = activeEffect.grantedEffect.id'),
        ('{ val = i, label = part.name }', '{ val = i, label = UILocale.skillVariantLabel(part.name) }'),
        ('t_insert(controls.mainSkillMinionSkill.list, minionSkill.activeEffect.grantedEffect.name)',
         't_insert(controls.mainSkillMinionSkill.list, UILocale.effectName(minionSkill.activeEffect.grantedEffect))'),
        ('label = minion.name,', 'label = UILocale.minionName(minionId, minion.name),\n\t\t\t\t\t\t\t\t\toriginalName = minion.name,'),
        ('srcInstance.nameSpec = "Spectre: ".. value.label',
         'srcInstance.nameSpec = "Spectre: ".. (value.originalName or value.label)', 2),
        ('srcInstance.nameSpec = "Companion: ".. value.label',
         'srcInstance.nameSpec = "Companion: ".. (value.originalName or value.label)', 2),
        ('main:OpenPopup(300, 100, "Save Changes", controls)', 'main:OpenPopup(350, 100, "Save Changes", controls)'),
    ])

    edit("Classes/GemSelectControl.lua", [
        ('local t_insert = table.insert', '''local utf8 = require("lua-utf8")
local function normalizeGemName(text)
	return (utf8.lower(text):gsub("'", ""):gsub("‘", ""):gsub("’", ""))
end

local t_insert = table.insert'''),
        ('self.EditControl(anchor, rect, nil, nil, "^ %a\':-")', 'self.EditControl(anchor, rect, nil, nil, "%c")'),
        ('''local patternList = {
			"^ " .. searchTerm:lower().."$", -- Exact match
			"^" .. searchTerm:lower():gsub("%a", " %0%%l+") .. "$", -- Simple abbreviation ("CtF" -> "Cold to Fire")
			"^ " .. searchTerm:lower(), -- Starts with
			searchTerm:lower(), -- Contains
		}''', '''local term = normalizeGemName(searchTerm)
		local literal = term:gsub("([%%%^%$%(%)%.%[%]%*%+%-%?])", "%%%1")
		local patternList = { "^ " .. literal .. "$" }
		if term:match("^[a-z]+$") then
			t_insert(patternList, "^" .. term:gsub("%a", " %0%%l+") .. "$")
		end
		t_insert(patternList, "^ " .. literal)
		t_insert(patternList, literal)'''),
        ('if self:FilterSupport(gemId, gemData) and not added[gemId] and ((" "..gemData.name:lower()):match(pattern)) then',
         '''if not added[gemId] and self:FilterSupport(gemId, gemData)
					and ((" " .. normalizeGemName(gemData.name)):match(pattern)
						or (" " .. normalizeGemName(UILocale.gemName(gemData))):match(pattern)) then'''),
        ('local bufMatchesGem = (self.gems[gemId] and self.buf:lower() == self.gems[gemId].name:lower())',
         '''local gemData = self.gems[gemId]
	local entered = normalizeGemName(self.buf)
	local bufMatchesGem = gemData and (entered == normalizeGemName(gemData.name) or entered == normalizeGemName(UILocale.gemName(gemData)))'''),
        ('self.gemName = bufMatchesGem and (self.gemId and self.gems[self.gemId].name) or ""',
         'self.gemName = bufMatchesGem and UILocale.gemName(gemData) or ""'),
        ('local gemText = gemData and gemData.name or "<No matches>"',
         'local gemText = gemData and UILocale.gemName(gemData) or "<No matches>"'),
        ('if self.gems[gemId].name == self.buf then',
         'if self.gems[gemId].name == self.buf or UILocale.gemName(self.gems[gemId]) == self.buf then'),
        ('self:SetText(self.gems[self.list[self.selIndex]].name)',
         'self:SetText(UILocale.gemName(self.gems[self.list[self.selIndex]]))', 4),
    ])

    gem_labels = [
        ("Tier", "Tier", 1), ("Level", "Level", 2), ("Quality", "Quality", 1),
        ("Cost & Reservation Multiplier", "ItemDisplaySkillGemCostAndReservationMultiplier", 1),
        ("Cost Multiplier", "ItemDisplaySkillGemCostMultiplier", 1),
        ("Reservation Multiplier", "ItemDisplaySkillGemReservationMultiplier", 1),
        ("Additional Reservation", "ItemDisplaySkillGemReservationFromSupport", 1),
        ("Reservation", "ItemDisplaySkillGemManaReserved", 2), ("Cost", "ItemDisplaySkillGemManaCost", 1),
        ("Cooldown Time", "ItemDisplaySkillGemCooldownTime", 1),
        ("Attack Speed", "ItemDisplaySkillGemAttackSpeedMultiplier", 1),
        ("Attack Time", "ItemDisplaySkillGemAttackTimeOverride", 1),
        ("Attack Damage", "ItemDisplaySkillGemAttackDamageEffectiveness", 1),
        ("Cast Time", "ItemDisplaySkillGemCastTime", 2),
        ("Critical Hit Chance", "ItemDisplaySkillGemCriticalStrikeChance", 1),
    ]
    edit("Classes/GemTooltip.lua", [
        *((f'"   {label}: ', f'"   " .. UILocale.gemText("{key}", "{label}") .. ": ', count)
          for label, key, count in gem_labels),
        ('"Critical Hit Chance: ^7%.2f%%"', 'UILocale.gemText("ItemDisplaySkillGemCriticalStrikeChance", "Critical Hit Chance") .. ": ^7%.2f%%"'),
        ('"Attack Damage: ^7%d%%"', 'UILocale.gemText("ItemDisplaySkillGemAttackDamageEffectiveness", "Attack Damage") .. ": ^7%d%%"'),
        ('"   ^7" .. gemInstance.level .. " Levels from Gem" .. ((gemInstance.level >= gemInstance.gemData.naturalMaxLevel) and " (Max)" or "")',
         '''"   ^7" .. (gemInstance.level >= gemInstance.gemData.naturalMaxLevel
				and UILocale.gemText("ItemDisplaySkillGemLevelsFromGemMaxLevel", "{0} Levels from Gem (Max)", gemInstance.level)
				or UILocale.gemText("ItemDisplaySkillGemLevelsFromGem", "{0} Levels from Gem", gemInstance.level))'''),
        ('totalLevel .. ((gemInstance.level >= gemInstance.gemData.naturalMaxLevel) and " (Max)" or "")',
         '(gemInstance.level >= gemInstance.gemData.naturalMaxLevel and UILocale.gemText("ItemDisplaySkillGemMaxLevel", "{0} (Max)", totalLevel) or totalLevel)'),
        ('"   +" .. corruptLevel .. " Level from Corruption"',
         '"   " .. UILocale.gemText("ItemDisplaySkillGemPlusLevelFromCorruption", "+{0} Level from Corruption", corruptLevel)'),
        ('"   " .. corruptLevel .. " Level from Corruption"',
         '"   " .. UILocale.gemText("ItemDisplaySkillGemMinusLevelFromCorruption", "-{0} Level from Corruption", -corruptLevel)'),
        ('"   +" .. totalGlobalLevels .. " Levels from Global Modifiers"',
         '"   " .. UILocale.gemText("ItemDisplaySkillGemPlusLevelsFromGlobalStats", "+{0} Levels from Global Modifiers", totalGlobalLevels)'),
        ('"   +" .. totalLevel - gemInstance.level - corruptLevel - totalGlobalLevels .. " Levels from Supports"',
         '"   " .. UILocale.gemText("ItemDisplaySkillGemPlusLevelsFromSupport", "+{0} Levels from Supports", totalLevel - gemInstance.level - corruptLevel - totalGlobalLevels)'),
        ('"   +" .. totalLevel - gemInstance.level - corruptLevel .. " Levels from Supports"',
         '"   " .. UILocale.gemText("ItemDisplaySkillGemPlusLevelsFromSupport", "+{0} Levels from Supports", totalLevel - gemInstance.level - corruptLevel)'),
        ('^7%d Spirit", levelStats.spiritReservationFlat)',
         '^7%s", UILocale.gemText("SkillPopupCostValueSpirit", "{0} Spirit", levelStats.spiritReservationFlat))'),
        ('^7%s Spirit", valueOrRange("spiritReservationFlat"))',
         '^7%s %s", valueOrRange("spiritReservationFlat"), UILocale.gemText("ItemDisplayGemReservationSpirit", "Spirit"))'),
        ('^7%s%% Spirit", valueOrRange("spiritReservationPercent", "%.1f"))',
         '^7%s%% %s", UILocale.gemResourceNumber(valueOrRange("spiritReservationPercent", "%.1f")), UILocale.gemText("ItemDisplayGemReservationSpirit", "Spirit"))'),
        ('res.ResourceString:gsub("{0}", value)', 'UILocale.gemText(res.ResourceString, res.ResourceString, UILocale.gemResourceNumber(value))'),
        ('^7%s sec", valueOrRange("cooldown", "%.2f")',
         '^7%s", UILocale.gemText("ItemDisplaySkillGemCastTimeValue", "{0} sec", valueOrRange("cooldown", "%.2f"))'),
        ('string.format(" (%s uses)", valueOrRange("storedUses"))',
         'UILocale.format(" (%s uses)", valueOrRange("storedUses"))'),
        ('^7%s sec", valueOrRange("attackTime", "%.2f", nil, 1000)',
         '^7%s", UILocale.gemText("ItemDisplaySkillGemCastTimeValue", "{0} sec", valueOrRange("attackTime", "%.2f", nil, 1000))'),
        ('^7%.2f sec", grantedEffect.castTime',
         '^7%s", UILocale.gemText("ItemDisplaySkillGemCastTimeValue", "{0} sec", string.format("%.2f", grantedEffect.castTime))'),
        ('^7Instant", "FONTIN SC"', '^7" .. UILocale.gemText("SkillIsInstant", "Instant"), "FONTIN SC"'),
        ('"   ^x7F7F7FRequires: ^7" .. gemInstance.gemData.weaponRequirements',
         '"   ^x7F7F7F" .. UILocale.gemText("HeistRequiresText", "Requires") .. ": ^7" .. UILocale.gemWeaponRequirements(gemInstance.gemData.weaponRequirements)'),
        ('colorCodes.NEGATIVE .. "Corrupted", "FONTIN SC"',
         'colorCodes.NEGATIVE .. UILocale.gemText("MonsterCorrupted", "Corrupted"), "FONTIN SC"'),
        ('"\\n^7Additional Effects From Quality:", "FONTIN SC"',
         '"\\n^7" .. UILocale.gemText("ItemDescriptionGemQualityStatDivider", "Additional Effects From Quality:"), "FONTIN SC"'),
        ('iconTagIndent .. gemInstance.gemData.gemType',
         'iconTagIndent .. (grantedEffect.support and UILocale.gemText("GemStashFilterGreen", gemInstance.gemData.gemType) or UILocale.gemTags(gemInstance.gemData.gemType))'),
        ('"   ^x7F7F7F" .. gemInstance.gemData.tagString',
         '"   ^x7F7F7F" .. UILocale.gemTags(gemInstance.gemData.tagString)'),
        ('"   Category: ^7" .. gemInstance.gemData.gemFamily',
         '"   " .. UILocale.translate("Category:") .. " ^7" .. UILocale.gemFamily(gemInstance.gemData.gemFamily)'),
        ('^7%s%% of base", valueOrRange("attackSpeedMultiplier", nil, 100))',
         '^7%s%% %s", valueOrRange("attackSpeedMultiplier", nil, 100), UILocale.translate("of base"))'),
        ('^7%s%% of base", valueOrRange("baseMultiplier", "%g", nil, nil, 100))',
         '^7%s", UILocale.format("%s%% of base", valueOrRange("baseMultiplier", "%g", nil, nil, 100)))'),
        ('tooltip:AddLine(fontSizeBig, colorCodes.GEMDESCRIPTION .. grantedEffect.description, "FONTIN ITALIC")',
         '''local description, comparisonNote = UILocale.effectDescription(grantedEffect)
		tooltip:AddLine(fontSizeBig, colorCodes.GEMDESCRIPTION .. description, "FONTIN ITALIC")
		if comparisonNote then
			tooltip:AddLine(14, colorCodes.WARNING .. comparisonNote)
		end'''),
        ('for _, line in ipairs(grantedEffect.flavourText) do', 'for _, line in ipairs(UILocale.effectFlavourText(grantedEffect)) do'),
        ('(gemInstance.displayEffect and gemInstance.displayEffect.nameSpec or gemInstance.gemData.name)',
         'UILocale.skillDisplayName(grantedEffect, (gemInstance.displayEffect and gemInstance.displayEffect.nameSpec) or UILocale.gemName(gemInstance.gemData), gemInstance.skillMinion)'),
        ('colorCodes.GEM .. statSet.label, "FONTIN SC"',
         'colorCodes.GEM .. UILocale.skillVariantLabel(statSet.label, grantedEffect), "FONTIN SC"'),
        ('colorCodes.GEM .. iconNameIndent .. gemInstance.gemData.name',
         'colorCodes.GEM .. iconNameIndent .. UILocale.gemName(gemInstance.gemData)'),
        ('colorCodes.GEM .. additional.name, "FONTIN SC"',
         'colorCodes.GEM .. UILocale.effectName(additional), "FONTIN SC"'),
        ('build.data.describeStats(stats, statSet.statDescriptionScope)',
         'build.data.describeStats(stats, statSet.statDescriptionScope, false, UILocale.gemStatTemplate)'),
        ('build.data.describeStats(stats, statSet.statDescriptionScope, true)',
         'build.data.describeStats(stats, statSet.statDescriptionScope, true, UILocale.gemStatTemplate, stat.stat)'),
        replace_region((BASE / "Classes/GemTooltip.lua").read_text(encoding="utf-8"),
                       '\t\t\t\t-- Let StatDescriber format the real 20 quality value',
                       '\t\t\t\taddDescriptionLine(tooltip, build, statSet, line, statName', ''),
    ])

    edit("Classes/MinionListControl.lua", [
        ('return minion.name', 'return UILocale.minionName(minionId, minion.name)'),
        ('"^7"..minion.name, "FONTIN SC"', '"^7"..UILocale.minionName(minionId, minion.name), "FONTIN SC"'),
        ('color .. self.data.skills[skillId].name', 'color .. UILocale.effectName(self.data.skills[skillId])'),
    ])

    edit("Modules/StatDescriber.lua", [
        ('return function(stats, scopeName, quality)',
         'return function(stats, scopeName, quality, translateTemplate, qualityRangeStat)'),
        ('{ depth = depth, order = scope[s], description = scope[scope[s]] }',
         '{ depth = depth, order = scope[s], description = descriptor, scopeName = scope.name }'),
        replace_region((BASE / "Modules/StatDescriber.lua").read_text(encoding="utf-8"),
                       '\t\t\tlocal statDesc = desc.text:', '\t\t\tfor line in (statDesc', '''			local function formatValue(index, sign)
				local value = val[index]
				if value.min == value.max then
					local formatted = s_format("%" .. sign .. value.fmt, value.min)
					if qualityRangeStat and descriptor.description.stats[index] == qualityRangeStat and type(value.min) == "number" then
						local prefix = formatted:match("^[+-]") or ""
						return prefix .. "(0-" .. formatted:sub(#prefix + 1) .. ")"
					end
					return formatted
				elseif sign == "+" then
					if value.max < 0 then
						return s_format("-(%d-%d)", -value.min, -value.max)
					end
					return s_format("+(%d-%d)", value.min, value.max)
				end
				return s_format("(%" .. value.fmt .. "-%" .. value.fmt .. ")", value.min, value.max)
			end
			local template = translateTemplate and translateTemplate(descriptor.scopeName, descriptor.description.stats, desc) or desc.text
			local statDesc = template:gsub("{(%d)}", function(n)
				return formatValue(tonumber(n) + 1, "")
			end):gsub("{}", function()
				return formatValue(1, "")
			end):gsub("{:%+?d}", function()
				return formatValue(1, "")
			end):gsub("{(%d):(%+?)d}", function(n, sign)
				return formatValue(tonumber(n) + 1, sign)
			end):gsub("%%%%", "%%")
'''),
    ])

    edit("Classes/ImportTab.lua", [
        ('..(type(self.charImportStatus) == "function" and self.charImportStatus() or self.charImportStatus)',
         '..UILocale.translate(type(self.charImportStatus) == "function" and self.charImportStatus() or self.charImportStatus)'),
        ('{100, 0, 18}, "Export Support"', '''{function()
		return UILocale.measureRaw(14, "VAR", UILocale.translate("Export Support")) + 12
	end, 0, 18}, "Export Support"'''),
        ('\tself.controls.generateCodeCopy.enabled = function()',
         '\tUILocale.fitButton(self.controls.generateCode)\n\tUILocale.fitButton(self.controls.generateCodeCopy)\n\tself.controls.generateCodeCopy.enabled = function()'),
    ])

    edit("Classes/PassiveSpec.lua", [
        ('main:SetWindowTitleSubtext(string.format("%s (%s)", self.build.buildName, self.curAscendClassId == 0 and self.curClassName or self.curAscendClassName))',
         'main:SetWindowTitleSubtext(string.format("%s (%s)", self.build.buildName, UILocale.translate(self.curAscendClassId == 0 and self.curClassName or self.curAscendClassName)))'),
    ])

    edit("Modules/BuildList.lua", [
        ('\tself.controls.sort = new("DropDownControl"', '''\tfor _, name in ipairs({ "new", "newFolder", "open", "copy", "rename", "delete" }) do
\t\tUILocale.fitButton(self.controls[name])
\tend
\tself.controls.sort = new("DropDownControl"'''),
    ])

    edit("Classes/BuildListControl.lua", [
        ('''			return s_format("%sLevel %d %s", 
				build.className and colorCodes[build.className:upper()] or "^7", 
				build.level or 1, 
				(build.ascendClassName ~= "None" and build.ascendClassName) or build.className or "?"
			)''', '''			local color = build.className and colorCodes[build.className:upper()] or "^7"
			local class = (build.ascendClassName ~= "None" and build.ascendClassName) or build.className or "?"
			return color .. UILocale.format("Level %d %s", build.level or 1, UILocale.translate(class))'''),
    ])

    edit("Classes/TextListControl.lua", [
        ('\tlocal contentHeight = 0', '''\tlocal fitted = {}
\tlocal lineHeight, labelRight, valueLeft = 14, math.floor((width - 20) * 0.68)
\tvalueLeft = labelRight + 4
\tif self.wrapStatColumns then
\t\tfor _, line in ipairs(self.list) do
\t\t\tif line[2] then
\t\t\t\tline.valueWrap = line.valueWrap or {}
\t\t\t\tlocal name, nameLines = UILocale.wrap(line, line[1], lineHeight, "VAR", labelRight - 3)
\t\t\t\tlocal value, valueLines = UILocale.wrap(line.valueWrap, line[2], lineHeight, "VAR", width - 22 - valueLeft)
\t\t\t\tfitted[line] = { name, value, height = math.max(line.height, math.max(nameLines, valueLines) * lineHeight + 2) }
\t\t\tend
\t\tend
\tend
\tlocal contentHeight = 0'''),
        ('contentHeight = contentHeight + lineInfo.height', 'contentHeight = contentHeight + (fitted[lineInfo] or lineInfo).height'),
        ('''			if lineInfo[colIndex] then''', '''			local fit = fitted[lineInfo]
			if fit then
				local anchor = colIndex == 1 and labelRight or valueLeft
				local top = lineY + 1
				for line in (fit[colIndex] .. "\\n"):gmatch("(.-)\\n") do
					UILocale.drawRaw(anchor, top, colInfo.align, lineHeight, "VAR", line)
					top = top + lineHeight
				end
			elseif lineInfo[colIndex] then'''),
        ('lineY = lineY + lineInfo.height', 'lineY = lineY + (fit or lineInfo).height'),
    ])

    edit("Classes/EditControl.lua", [
        ("local utf8 = require('lua-utf8')",
         "local utf8 = require('lua-utf8')\nlocal DrawString = UILocale.drawRaw\nlocal DrawStringWidth = UILocale.measureRaw"),
        ('self.disableCol..self.prompt)', 'self.disableCol..UILocale.translate(self.prompt))'),
        ('self.textCol..self.prompt..":"', 'self.textCol..UILocale.translate(self.prompt..":")'),
        ('self.prompt and DrawStringWidth(textHeight, self.font, self.prompt)',
         'self.prompt and DrawStringWidth(textHeight, self.font, UILocale.translate(self.prompt))'),
        ('textX = textX + DrawStringWidth(textHeight, self.font, self.prompt)',
         'textX = textX + DrawStringWidth(textHeight, self.font, UILocale.translate(self.prompt..":"))', 2),
        ('self.font, self.placeholder)', 'self.font, UILocale.translate(self.placeholder))'),
    ])

    edit("Classes/Tooltip.lua", [
        ('\tself.recipe = recipe', '''	self.recipe = nil
	if not recipe then return end
	self.recipe = {}
	for index, entry in ipairs(recipe) do
		self.recipe[index] = { name = UILocale.emotionName(entry.name), sprite = entry.sprite }
	end'''),
        ('''			local recipeName = recipeInfo.name
			-- Trim "Oil" from the recipe name, which normally looks like "GoldenOil"
			local recipeNameShort = recipeName
			if #recipeNameShort > 3 and recipeNameShort:sub(-3) == "Oil" then
				recipeNameShort = recipeNameShort:sub(1, #recipeNameShort - 3)
			end
			imageX = imageX + DrawStringWidth(recipeTextSize, font, recipeNameShort) + title.size * 1.25''',
         '''			imageX = imageX + DrawStringWidth(recipeTextSize, font, recipeInfo.name) + title.size * 1.25'''),
        ('''				local rn = r.name
				if #rn > 3 and rn:sub(-3) == "Oil" then
					rn = rn:sub(1, #rn - 3)
				end''', '\t\t\t\tlocal rn = r.name'),
    ])

    edit("Classes/PassiveTreeView.lua", [
        ('local m_min = math.min', "local utf8 = require('lua-utf8')\nlocal m_min = math.min"),
        ('if self.searchStrCached ~= self.searchStr then\n\t\tself.searchStrCached = self.searchStr',
         'if self.searchStrCached ~= self.searchStr or self.searchLanguage ~= UILocale.language then\n\t\tself.searchStrCached = self.searchStr\n\t\tself.searchLanguage = UILocale.language'),
        ('search = search:lower()', 'search = utf8.lower(search)'),
        ('\tif needMatches[1] == "oil:" then', '''	local recipePrefix = needMatches[1]
	if recipePrefix == "oil:" or recipePrefix == "эмоции:" then'''),
        ('''				err, needMatches = PCall(search, recipeName:gsub("Oil",""):lower(), needMatches)
				if err then return false end
				if #needMatches == 1 and needMatches[1] == "oil:" then''', '''				err, needMatches = PCall(search, recipeName:gsub("Oil$", ""):lower(), needMatches)
				if err then return false end
				err, needMatches = PCall(search, utf8.lower(UILocale.emotionName(recipeName)), needMatches)
				if err then return false end
				if #needMatches == 1 and needMatches[1] == recipePrefix then'''),
        ('\t-- Check node description\n', '''\tlocal translatedNode = UILocale.passive(build.spec.treeVersion, node.id, node.dn)
\tif translatedNode then
\t\terr, needMatches = PCall(search, utf8.lower(translatedNode.name), needMatches)
\t\tif err then return false end
\t\tif #needMatches == 0 then return true end
\t\tlocal index = 1
\t\twhile node.sd and node.sd[index] do
\t\t\tlocal description, length = UILocale.passiveStat(translatedNode, node.sd, index, true)
\t\t\terr, needMatches = PCall(search, utf8.lower(description), needMatches)
\t\t\tif err then return false end
\t\t\tif #needMatches == 0 then return true end
\t\t\tindex = index + length
\t\tend
\tend

\t-- Check node description
'''),
        ('\tlocal nodeName = node.dn\n\tif main.showFlavourText then\n\t\tnodeName = "^xF8E6CA" .. node.dn',
         '\tlocal nodeName = UILocale.passiveName(build.spec.treeVersion, node)\n\tif main.showFlavourText then\n\t\tnodeName = "^xF8E6CA" .. nodeName'),
        ('\tlocal function addModInfoToTooltip(node, i, line, localIncEffect)',
         '\tlocal translatedNode = UILocale.passive(build.spec.treeVersion, node.id, node.dn)\n\tlocal function addModInfoToTooltip(node, i, line, localIncEffect)'),
        ('\t\t\tif line ~= " " and (node.mods[i].extra or not node.mods[i].list) then',
         '\t\t\tline = UILocale.passiveLine(translatedNode, line)\n\t\t\tif line ~= " " and (node.mods[i].extra or not node.mods[i].list) then'),
        ('line .. main.notSupportedTooltipText', 'line .. UILocale.translate(main.notSupportedTooltipText)'),
        ('''		for i, line in ipairs(mNode.sd) do
			addModInfoToTooltip(mNode, i, line, localIncEffect)
		end''', '''		local combine = not launch.devModeAlt and localIncEffect == 0 and not (incSmallPassiveSkillEffect > 0 and mNode.type == "Normal")
		local index = 1
		while mNode.sd[index] do
			local text, length = UILocale.passiveStat(translatedNode, mNode.sd, index, combine)
			addModInfoToTooltip(mNode, index, length > 1 and text or mNode.sd[index], localIncEffect)
			index = index + length
		end'''),
        ('colorCodes.UNIQUE..node.flavourText, "FONTIN ITALIC"',
         'colorCodes.UNIQUE..(translatedNode and translatedNode.flavour or node.flavourText), "FONTIN ITALIC"'),
        ('\t-- Mod differences\n', '''\tif translatedNode and translatedNode.versionNote then
		tooltip:AddLine(14, colorCodes.WARNING .. translatedNode.versionNote)
	end

	-- Mod differences
'''),
        ('colorCodes.WARNING.."Requires allocation of node: "..reqNode.dn',
         'colorCodes.WARNING..UILocale.format("Requires allocation of node: %s", UILocale.passiveName(build.spec.treeVersion, reqNode))'),
        ('string.format("^7This node is granted by an item. Removing it will cause no changes")',
         'UILocale.translate("^7This node is granted by an item. Removing it will cause no changes")'),
        ('string.format("^7No changes from %s this node%s.", node.alloc and "unallocating" or "allocating", node.intuitiveLeapLikesAffecting == 0 and pathLength > 1 and " or the nodes leading to it" or "")',
         '''UILocale.format("^7No changes from %s this node%s.", UILocale.translate(node.alloc and "unallocating" or "allocating"),
					node.intuitiveLeapLikesAffecting == 0 and pathLength > 1 and " " .. UILocale.translate("or the nodes leading to it") or "")'''),
        ('"^7"..#self.tracePath .. " nodes in trace path"',
         'UILocale.format("^7%d nodes in trace path", #self.tracePath)'),
        ('"^7"..node.pathDist .. " points to node" .. (#node.intuitiveLeapLikesAffecting > 0 and " ^8(Can be allocated without pathing to it)" or "")',
         '''UILocale.format("^7%s points to node", node.pathDist)
				.. (#node.intuitiveLeapLikesAffecting > 0 and " ^8" .. UILocale.translate("(Can be allocated without pathing to it)") or "")'''),
        ('"^7"..dependCount .. " points gained from unallocating these nodes"',
         'UILocale.format("^7%d points gained from unallocating these nodes", dependCount)'),
        ('"^xFFD700"..formatNumSep(dependCount * goldCost) .. " Gold ^7required to unallocate these nodes"',
         'UILocale.format("^xFFD700%s Gold ^7required to unallocate these nodes", formatNumSep(dependCount * goldCost))'),
        ('"^xFFD700"..formatNumSep(#node.depends * goldCost) .. " Gold ^7required to unallocate this node"',
         'UILocale.format("^xFFD700%s Gold ^7required to unallocate this node", formatNumSep(#node.depends * goldCost))'),
    ])

    edit("Classes/NotableDBControl.lua", [
        ('local pairs = pairs', "local utf8 = require('lua-utf8')\nlocal pairs = pairs"),
        ('{0, 6, 100, 16}, "Emotions: "',
         '{0, 6, function() return m_max(100, UILocale.measureRaw(16, "VAR", UILocale.translate("Emotions:")) + 6) end, 16}, "Emotions: "'),
        ('if i == 11 then', 'if i == 8 then'),
        ('"Distilled "..name, true)', 'function() return UILocale.emotionName(name, true) end, true)'),
        ('"Distilled "..emo, true)', 'function() return UILocale.emotionName(emo, true) end, true)'),
        ('line .. main.notSupportedTooltipText', 'line .. UILocale.translate(main.notSupportedTooltipText)'),
        replace_region(
            (BASE / "Classes/NotableDBControl.lua").read_text(encoding="utf-8"),
            '\tlocal searchStr = self.controls.search.buf:lower()', '\n\treturn true\nend',
            '''	local searchStr = utf8.lower(self.controls.search.buf):gsub("[%-%.%+%[%]%$%^%%%?%*]", "%%%0")
	if searchStr:match("%S") then
		local version = self.itemsTab.build.spec.treeVersion
		local entry = UILocale.passive(version, node.id, node.dn)
		local function matches(text)
			local err, match = PCall(string.matchOrPattern, utf8.lower(text), searchStr)
			return not err and match
		end
		local mode = self.controls.searchMode.selIndex
		if (mode == 1 or mode == 2) and (matches(node.dn) or (entry and matches(entry.name))) then
			return true
		end
		if mode == 1 or mode == 3 then
			for index, line in ipairs(node.sd) do
				local translated = UILocale.passiveStat(entry, node.sd, index, true)
				if matches(line) or (translated ~= line and matches(translated)) then
					return true
				end
			end
		end
		return false
	end''',
        ),
        ('function NotableDBClass:GetRowValue(column, index, node)\n\tif column == 1 then',
         'function NotableDBClass:GetRowValue(column, index, node)\n\tif column == 1 then\n\t\tlocal nodeName = UILocale.passiveName(self.itemsTab.build.spec.treeVersion, node)'),
        ('..node.dn\n', '..nodeName\n', 3),
        ('\t\t\tfor i, line in ipairs(node.sd) do',
         '''			local entry = UILocale.passive(self.itemsTab.build.spec.treeVersion, node.id, node.dn)
			local i = 1
			while node.sd[i] do
				local line, length = UILocale.passiveStat(entry, node.sd, i, true)'''),
        ('tooltip:AddLine(16, colorCodes.MAGIC..line)\n\t\t\t\tend',
         'tooltip:AddLine(16, colorCodes.MAGIC..line)\n\t\t\t\tend\n\t\t\t\ti = i + length'),
    ])

    patch_layout(edit)
    patch_item_filter(edit)
    patch_calcs_config(edit, BASE)
    patch_item_names(lambda path, replacements: edit(path, replacements, source=BUILD if path in {
        "Classes/DropDownControl.lua", "Classes/ItemDBControl.lua", "Classes/ItemListControl.lua",
        "Classes/ItemsTab.lua", "Classes/SharedItemListControl.lua", "Classes/SkillsTab.lua",
    } else BASE))
    patch_item_runes(edit)
    patch_item_clipboard(edit, BUILD)
    patch_build_warnings(edit, BUILD)
    patch_trade_locale(edit, BUILD)
    patch_character_import_locale(edit, BUILD)


if __name__ == "__main__":
    main()
