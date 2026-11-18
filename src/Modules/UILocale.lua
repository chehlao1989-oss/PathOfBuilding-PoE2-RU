local ui = { language = "ru" }
local messages = LoadModule("Data/Locale/ru")
local tradeMessages = LoadModule("Data/Locale/trade_ru")
local tree = LoadModule("Data/Locale/tree_0_5_ru")
local historicalTree
local skills = LoadModule("Data/Locale/skills_ru")
local gemWeaponTypes = LoadModule("Data/Locale/item_filter_ru")
local itemNames = LoadModule("Data/Locale/item_names_ru")
local utf8 = require("lua-utf8")
local gemStats, itemStats, itemAffixes, itemDisplay
local configMessages, itemVariants, rareTemplates
local itemBaseSkills = {
	["Shrine Sceptre (Purity of Fire)"] = "PurityOfFirePlayer",
	["Shrine Sceptre (Purity of Cold)"] = "PurityOfIcePlayer",
	["Shrine Sceptre (Purity of Lighting)"] = "PurityOfLightningPlayer",
}

function ui.itemBaseName(baseName, uniqueTitle)
	if not baseName then return end
	if ui.language == "ru" then
		local variants = uniqueTitle and itemNames.uniques[uniqueTitle]
		local unique = variants and variants[baseName]
		if unique and unique.baseName then return unique.baseName end
		if baseName ~= "Shrine Sceptre" or not uniqueTitle then
			local base = itemNames.bases[baseName]
			if base then return base.name end
		end
	end
	return (baseName:gsub(" %(.+%)", ""))
end

local function itemAffixCatalog()
	itemAffixes = itemAffixes or LoadModule("Data/Locale/item_affixes_ru")
	return itemAffixes
end

local function wordForm(entry, inflection)
	if not entry then return end
	return type(entry.name) == "string" and entry.name or entry.name[inflection]
end

local function itemNameFormat(locale, key, ...)
	local parts = { ... }
	return (locale.formats[key]:gsub("{(%d+)}", function(index) return parts[tonumber(index) + 1] end))
end

local function generatedRareName(item)
	if not item.title or item.crafted then return end
	local locale = itemAffixCatalog()
	local prefixes, nouns = locale.rarePrefixes, locale.rareNouns
	local result
	for position in item.title:gmatch("()%s+") do
		local noun = nouns[item.title:sub(position + 1)]
		if noun then
			local prefix = wordForm(prefixes[item.title:sub(1, position - 1)], noun.name.inflection)
			if prefix then
				local name = itemNameFormat(locale, "RareNameFormat2Words", prefix, noun.name.noun)
				if result and result ~= name then return end
				result = name
			end
		end
	end
	return result
end

local function magicAffix(locale, list, entries, name, inflection)
	for _, selected in ipairs(list or {}) do
		local entry = locale.mods[selected.modId]
		if entry and entry.en == name then return wordForm(entry, inflection) end
	end
	return wordForm(entries[name], inflection)
end

function ui.itemNameWithoutTitle(item, base)
	local prefix, suffix = item.namePrefix or "", item.nameSuffix or ""
	if ui.language ~= "ru" or item.rarity ~= "MAGIC" then return prefix .. base .. suffix end
	local locale = itemAffixCatalog()
	local entry = itemNames.bases[item.baseName]
	local inflection = entry and entry.inflection
	local prefixName, suffixName = prefix:match("^%s*(.-)%s*$"), suffix:match("^%s*(.-)%s*$")
	local translatedPrefix = magicAffix(locale, item.prefixes, locale.magicPrefixes, prefixName, inflection)
	local translatedSuffix = magicAffix(locale, item.suffixes, locale.magicSuffixes, suffixName, inflection)
	if prefixName ~= "" and not translatedPrefix or suffixName ~= "" and not translatedSuffix then
		return prefix .. base .. suffix
	end
	if translatedPrefix and translatedSuffix then
		return itemNameFormat(locale, "MagicNamePrefixSuffix", base, translatedPrefix, translatedSuffix)
	elseif translatedPrefix then
		return itemNameFormat(locale, "MagicNamePrefix", base, translatedPrefix)
	elseif translatedSuffix then
		return itemNameFormat(locale, "MagicNameSuffix", base, translatedSuffix)
	end
	return base
end

function ui.itemTitle(item)
	if item.rarity == "RARE" and item.crafted and item.title == "New Item" then
		return ui.translate("New Item")
	end
	if ui.language == "ru" and (item.rarity == "UNIQUE" or item.rarity == "RELIC") then
		local variants = itemNames.uniques[item.title]
		local unique = variants and variants[item.baseName]
		if unique then return unique.name end
	end
	if ui.language == "ru" and item.rarity == "RARE" then
		if item.crafted then
			rareTemplates = rareTemplates or LoadModule("Data/Locale/rare_templates_ru")
			local bases = rareTemplates[item.title]
			if bases and bases[item.baseName] then return bases[item.baseName] end
		end
		return generatedRareName(item) or item.title
	end
	return item.title
end

function ui.itemSlotLabel(label)
	local index = label:match("^Socket #(%d+)$") or label:match("^Jewel #(%d+)$")
	if index then return ui.format("Socket #%s", index) end
	return (ui.translate(label .. ":"):gsub(":$", ""))
end

function ui.itemRuneName(name)
	local entry = itemNames.runes[name]
	return (ui.language == "ru" and entry and entry.name) or ui.translate(name)
end

local function itemDisplayCatalog()
	itemDisplay = itemDisplay or LoadModule("Data/Locale/item_display_ru")
	return itemDisplay
end

function ui.itemFlavourText(entry)
	return (ui.language == "ru" and itemDisplayCatalog().flavour[entry.id]) or entry.text
end

function ui.itemLeague(name)
	if type(name) ~= "string" then return name end
	return (ui.language == "ru" and itemDisplayCatalog().leagues[name:lower()]) or name
end

function ui.tradeSlotName(slot)
	if ui.language ~= "ru" then return slot.slotName end
	if slot.unique then
		for _, entry in pairs(itemNames.uniques[slot.slotName] or {}) do return entry.name end
	end
	return ui.itemSlotLabel(slot.slotName)
end

local currencyNames = {
	exalted = "Exalted Orb", chaos = "Chaos Orb", divine = "Divine Orb",
	aug = "Orb of Augmentation", transmute = "Orb of Transmutation", regal = "Regal Orb",
	vaal = "Vaal Orb", annul = "Orb of Annulment", alch = "Orb of Alchemy", mirror = "Mirror of Kalandra",
}

function ui.tradeCurrencyName(name)
	if ui.language ~= "ru" then return name end
	return ui.translate(currencyNames[name] or name)
end

function ui.tradeResultLabel(entry)
	if not entry then return end
	return colorCodes[entry.item.rarity] .. ui.itemName(entry.item)
		.. string.format(" %s(%s %s)", colorCodes.CURRENCY, entry.amount, ui.tradeCurrencyName(entry.currency))
end

function ui.fitTradeTotal(control, maxWidth)
	control.width = maxWidth
	local host = new("TooltipHost")
	host.tooltipFunc = function(tooltip)
		tooltip:Clear()
		tooltip.maxWidth = 600
		tooltip:AddLine(16, ui.translate(control:GetProperty("label")))
	end
	control.Draw = function(self, viewPort)
		local x, y = self:GetPos()
		local text = ui.translate(self:GetProperty("label"))
		local size = self:GetProperty("height")
		while size > 12 and ui.measureRaw(size, "VAR", text) > maxWidth do size = size - 1 end
		if ui.measureRaw(size, "VAR", text) > maxWidth then
			local plain = StripEscapes(text)
			local low, high = 0, utf8.len(plain)
			while low < high do
				local mid = math.floor((low + high + 1) / 2)
				if ui.measureRaw(size, "VAR", utf8.sub(plain, 1, mid) .. "…") <= maxWidth then low = mid else high = mid - 1 end
			end
			text = utf8.sub(plain, 1, low) .. "…"
		end
		SetDrawColor(1, 1, 1)
		local textX = x + math.floor((maxWidth - ui.measureRaw(size, "VAR", text)) / 2)
		ui.drawRaw(textX, y, "LEFT", size, "VAR", text)
		if self:IsMouseInBounds() then host:DrawTooltip(x, y, maxWidth, self:GetProperty("height"), viewPort) end
	end
	control.fullPriceTooltip = host
end

function ui.tradeActionLabel(action, price)
	local text = price and ui.format(action .. " for %s", price) or ui.translate(action)
	if ui.language == "ru" and ui.measureRaw(16, "VAR", text) > 141 then return ui.translate(action) end
	return text
end

function ui.tradeModLabel(entry)
	local label = type(entry) == "table" and entry.label or entry
	if ui.language ~= "ru" then return label end
	local plain = StripEscapes(label)
	local body, kind = plain:match("^(.-) %((%a+)%)$")
	if kind ~= "Implicit" and kind ~= "Corrupted" then body, kind = plain, nil end
	body = body:gsub("^Small: ", "Small Passive Skills in Radius also grant ")
		:gsub("^Notable: ", "Notable Passive Skills in Radius also grant ")
	local prefix = label:match("^(%^x%x%x%x%x%x%x)") or label:match("^(%^%d)") or ""
	local kindColor = kind and label:match("(%^x%x%x%x%x%x%x)%(" .. kind .. "%)$") or ""
	local suffix = kind and (" " .. (kindColor or "") .. "(" .. ui.translate(kind) .. ")") or ""
	local exact = ui.translate(body)
	if exact ~= body then return prefix .. exact .. suffix end
	body = body:gsub(" %((Local)%)$", ""):gsub(" %((Jewel)%)$", ""):gsub(" %((Charm)%)$", "")
	local sample = body:gsub("#", "987654321")
	local translated = ui.itemModifier(sample)
	if translated == sample then
		local signed = body:gsub("#", "+987654321")
		translated = ui.itemModifier(signed)
		if translated == signed then translated = sample end
	end
	if translated ~= sample then body = translated:gsub("987654321", "#") end
	return prefix .. ui.translate(body) .. suffix
end

function ui.tradeText(text)
	local weight, stat = text:match("^(%d+[.,]?%d*%s*:%s*)(.+)$")
	if weight then return weight .. ui.translate(stat) end
	local minionStat = text:match("^Minion (.+)$")
	if minionStat then
		local translated = ui.translate(minionStat)
		if translated ~= minionStat then return "Приспешник — " .. translated end
	end
	local sort = text:match("^Sorted by (.+)$")
	if sort then return ui.format("Sorted by %s", ui.translate(sort)) end
	local seconds = text:match("^Logging in%.%.%. %((%d+)%)$")
	if seconds then return ui.format("Logging in... (%s)", seconds) end
	seconds = text:match("^Conversion Rates are less than an hour old %((%d+) seconds old%)$")
	if seconds then return ui.format("Conversion Rates are less than an hour old (%s seconds old)", seconds) end
	seconds = text:match("^Rate limited%. Retrying after (%d+) seconds%.%.%.$")
	if seconds then return ui.format("Rate limited. Retrying after %s seconds...", seconds) end
	local count = text:match("^%+ (%d+) Additional Stats$")
	if count then return ui.format("+ %s Additional Stats", count) end
	return text
end

function ui.prepareTradeTooltips(controls)
	for _, control in pairs(controls) do
		if type(control.tooltipText) == "string" then control.tooltipText = ui.translate(control.tooltipText) end
		if control.tooltip then control.tooltip.maxWidth = 600 end
	end
end

function ui.itemOrigin(origin, typeName)
	local format = ui.language == "ru" and itemDisplayCatalog().origins[origin]
	return format and (format:gsub("{0}", function() return typeName end)) or (origin .. " " .. typeName)
end

function ui.itemSource(text)
	if ui.language ~= "ru" then return text end
	if text == "No longer obtainable" then return "Больше нельзя получить" end
	local source, area = text:match("^Drops from (unique%b{}) in (normal%b{})$")
	source = source or text:match("^Drops from (unique%b{})$")
	if not source then return text end
	local names = itemDisplayCatalog().sources
	local tagged = area and (source .. " · " .. area) or source
	return (tagged:gsub("(%a+){([^}]+)}", function(kind, name)
		return kind .. "{" .. (names[name] or name) .. "}"
	end))
end

function ui.itemVariantCaption(label, item)
	if label == "Current" then return "Текущий" end
	local version = label:match("^Pre (%d[%d%.%a]+)$")
	if version then return "До " .. version end
	local name, oldVersion = label:match("^(.+) %(Pre (%d[%d%.%a]+)%)$")
	if name then return ui.itemVariantCaption(name, item) .. " (до " .. oldVersion .. ")" end
	local stat = ui.itemModifier(label, nil, item)
	if stat ~= label then return stat end
	if item and (item.title == "Prism of Belief" or item.title == "Cursecarver") then
		return ui.effectCaption(label)
	end
	return ui.translate(label)
end

function ui.itemVariantName(label, item)
	if not label or ui.language ~= "ru" then return label end
	if item then
		itemVariants = itemVariants or LoadModule("Data/Locale/item_variants_ru")
		local byTitle = itemVariants[item.title or ""]
		local variants = byTitle and byTitle[item.baseName]
		if variants and variants[label] then return variants[label] end
	end
	return ui.itemVariantCaption(label, item)
end

local function itemClientText(id, ...)
	itemStats = itemStats or LoadModule("Data/Locale/item_stats_ru")
	local args = { ... }
	return (itemStats.client[id]:gsub("{(%d+)}", function(index)
		return args[tonumber(index) + 1]
	end))
end

function ui.itemStatLabel(id, fallback)
	return ui.language == "ru" and itemClientText(id) or fallback
end

function ui.itemFlaskRecovery(resource, amount, duration, amountColor, timeColor)
	if ui.language ~= "ru" then return end
	local time = duration % 1 == 0 and tostring(duration) or (string.format("%.2f", duration):gsub("%.", ","))
	local key = "ItemDisplayFlask" .. resource .. "RecoveryNSeconds"
	return "^x7F7F7F" .. itemClientText(key,
		amountColor .. round(amount) .. "^x7F7F7F", timeColor .. time .. "^x7F7F7F")
end

function ui.itemCharges(used, maximum, usedColor, maximumColor)
	if ui.language ~= "ru" then return end
	return "^x7F7F7F" .. itemClientText("ItemDisplayChargesConsumptionOnUseNCharges",
		usedColor .. math.floor(used) .. "^x7F7F7F", maximumColor .. math.floor(maximum) .. "^x7F7F7F")
end

local function translateItemModifier(text, direction, itemTitle)
	itemStats = itemStats or LoadModule("Data/Locale/item_stats_ru")
	local catalog = itemStats[direction]
	if itemTitle then catalog = catalog[itemTitle] end
	if not catalog then return end
	local source = utf8.lower(text):gsub("%s+", " "):match("^%s*(.-)%s*$")
	local shape = source:gsub("%(%-?%d+[.,]?%d*%-%-?%d+[.,]?%d*%)", "#"):gsub("%d+[.,]?%d*", "#")
	local variants = catalog[shape]
	if not variants then return end
	for _, entry in ipairs(variants) do
		local values = { source:match(entry.pattern) }
		if values[1] then
			if not entry.text then return end
			return (entry.text:gsub("{(%d*)(:?[%+%-]?d?)}", function(index, format)
				local value = values[entry.positions[(tonumber(index) or 0) + 1]]
				if format == ":+d" and not value:match("^[+%-]") then value = "+" .. value end
				if format == ":-d" and not value:match("^[+%-]") then value = "-" .. value end
				return direction == "reverse" and value:gsub(",", ".") or value
			end))
		end
	end
end

local referenceNames
local function itemReferenceName(category, direction, name)
	if not referenceNames then
		referenceNames = {
			skill = { forward = {}, reverse = {} }, gem = { forward = {}, reverse = {} },
			passive = { forward = {}, reverse = {} },
		}
		local function record(collection, from, to)
			local key = utf8.lower(from:match("^%s*(.-)%s*$"))
			local saved = collection[key]
			collection[key] = (saved == nil or saved == to) and to or false
		end
		local function index(collection, entries)
			for _, entry in pairs(entries) do
				if entry.en and entry.name then
					record(collection.forward, entry.en, entry.name)
					record(collection.reverse, entry.name, entry.en)
				end
			end
		end
		index(referenceNames.skill, skills.active)
		for _, byEffect in pairs(skills.gems) do
			for _, variants in pairs(byEffect) do
				for english, russian in pairs(variants) do
					record(referenceNames.gem.forward, english, russian)
					record(referenceNames.gem.reverse, russian, english)
				end
			end
		end
		index(referenceNames.passive, tree.nodes)
	end
	return referenceNames[category][direction][utf8.lower(name)]
end

local itemPropertyPrefixes = {
	{ forward = "Small Passive Skills in Radius also grant ", reverse = "Малые пассивные умения в радиусе также даруют " },
	{ forward = "Notable Passive Skills in Radius also grant ", reverse = "Значимые пассивные умения в радиусе также даруют " },
}

local function compoundItemModifier(text, direction)
	for _, prefix in ipairs(itemPropertyPrefixes) do
		local source = prefix[direction]
		if text:sub(1, #source) == source then
			local stat = text:sub(#source + 1)
			local modifier = translateItemModifier(stat, direction)
				or (direction == "forward" and translateItemModifier(stat, "passive"))
			if modifier then
				return prefix[direction == "forward" and "reverse" or "forward"] .. modifier
			end
		end
	end
end

function ui.itemModifier(text, modifier, item)
	if ui.language ~= "ru" then return text end
	if item and item.title and (item.rarity == "UNIQUE" or item.rarity == "RELIC") then
		local reviewed = translateItemModifier(text, "reviewedItems", item.title)
		if reviewed then return reviewed end
		if item.title == "Flesh Crucible" then
			local passive = itemReferenceName("passive", "forward", text)
			if passive then return passive end
		end
	end
	local bonded = text:match("^Bonded: (.+)$")
	if bonded then
		local translated = ui.itemModifier(bonded, modifier, item)
		if translated ~= bonded then return itemClientText("ItemDisplayShamanOnly") .. " " .. translated end
		return text
	end
	if modifier and modifier.rune then
		-- SoulCoreStats links the Iron Rune armour property to the local defence stat.
		local runeText = translateItemModifier(text, "armourRune")
		if runeText then return runeText end
	end
	local level, name = text:match("^Grants Skill: Level (%S+) (.+)$")
	if level then
		local russian = itemReferenceName("skill", "forward", name)
		if russian then return string.format("Дарует умение: %s %s уровня", russian, level) end
	end
	name = text:match("^Grants Skill: (.+)$")
	local russian = name and itemReferenceName("skill", "forward", name)
	if russian then return "Дарует умение: " .. russian end
	level, name = text:match("^([+%-]%S+) to Level of all (.+) Skills$")
	russian = name and (itemReferenceName("gem", "forward", name) or itemReferenceName("skill", "forward", name))
	if russian then return string.format("%s к уровню всех умений %s", level, russian) end
	name = text:match("^Allocates (.+)$")
	russian = name and itemReferenceName("passive", "forward", name)
	if russian then return "Активирует " .. russian end
	name = text:match("^Passives in radius of (.+) can be Allocated without being connected to your tree$")
	russian = name and itemReferenceName("passive", "forward", name)
	if russian then
		return string.format("Пассивные умения в радиусе %s могут быть выбраны без связи с остальным деревом", russian)
	end
	local translated = translateItemModifier(text, "forward") or compoundItemModifier(text, "forward")
	if translated then return translated end
	if text:find("\n", 1, true) then
		local parts = {}
		for line in text:gmatch("[^\n]+") do
			local part = ui.itemModifier(line, modifier, item)
			if part == line then return text end
			parts[#parts + 1] = part
		end
		return table.concat(parts, "\n")
	end
	return text
end

function ui.englishItemModifier(text)
	local bondedPrefix = itemClientText("ItemDisplayShamanOnly") .. " "
	if text:sub(1, #bondedPrefix) == bondedPrefix then
		local translated = ui.englishItemModifier(text:sub(#bondedPrefix + 1))
		return translated and "Bonded: " .. translated
	end
	local name, level = text:match("^Дарует умение: (.-) (%S+) уровня$")
	if name then
		local english = itemReferenceName("skill", "reverse", name)
		if english then return string.format("Grants Skill: Level %s %s", level, english) end
	end
	name = text:match("^Дарует умение: (.+)$")
	local english = name and itemReferenceName("skill", "reverse", name)
	if english then return "Grants Skill: " .. english end
	level, name = text:match("^([+%-]%S+) к уровню всех умений (.+)$")
	english = name and (itemReferenceName("gem", "reverse", name) or itemReferenceName("skill", "reverse", name))
	if english then return string.format("%s to Level of all %s Skills", level, english) end
	name = text:match("^Активирует (.+)$")
	english = name and itemReferenceName("passive", "reverse", name)
	if english then return "Allocates " .. english end
	name = text:match("^Пассивные умения в радиусе (.+) могут быть выбраны без связи с остальным деревом$")
	english = name and itemReferenceName("passive", "reverse", name)
	if english then
		return string.format("Passives in radius of %s can be Allocated without being connected to your tree", english)
	end
	return translateItemModifier(text, "reverse") or compoundItemModifier(text, "reverse")
end

function ui.itemBaseLabel(base)
	local name = ui.itemBaseName(base.name)
	if ui.language == "ru" then
		local skillId = itemBaseSkills[base.name]
		if skillId then return name .. " (" .. skills.active[skillId].name .. ")" end
	end
	return name
end

function ui.itemType(base, original)
	local key = base.subType == "Warstaff" and "Warstaff" or base.type
	return (ui.language == "ru" and gemWeaponTypes[key]) or original
end

function ui.itemName(item)
	if ui.language ~= "ru" or not itemNames.bases[item.baseName] or item.name == "Unidentified item" then return item.name end
	local uniqueTitle = (item.rarity == "UNIQUE" or item.rarity == "RELIC") and item.title
	local base = ui.itemBaseName(item.baseName, uniqueTitle)
	if item.title then return ui.itemTitle(item) .. ", " .. base end
	return ui.itemNameWithoutTitle(item, base)
end

function ui.gemText(id, english, ...)
	local template = ui.language == "ru" and skills.clientText[id] or english
	local values = { ... }
	return (template:gsub("{(%d+)}", function(index) return values[tonumber(index) + 1] end))
end

function ui.gemWeaponRequirements(text)
	if ui.language ~= "ru" then return text end
	return (text:gsub("([^,%s][^,]*)", function(kind) return skills.clientText[kind] or gemWeaponTypes[kind] or kind end))
end

function ui.gemResourceNumber(text)
	return ui.language == "ru" and (text:gsub("(%d)%.(%d)", "%1,%2")) or text
end

function ui.gemTags(text)
	if ui.language ~= "ru" then return text end
	return (text:gsub("([^,%s][^,]*)", function(tag) return skills.tags[tag] or tag end))
end

function ui.gemFamily(text)
	return ui.language == "ru" and skills.families[text] or text
end

function ui.gemStatTemplate(scopeName, stats, desc)
	if ui.language ~= "ru" then return desc.text end
	gemStats = gemStats or LoadModule("Data/Locale/gem_stats_ru")
	local limits, directives = {}, {}
	for i, limit in ipairs(desc.limit) do
		limits[i] = limit[1] .. ":" .. limit[2]
	end
	for _, spec in ipairs(desc) do
		if spec.k ~= "reminderstring" and spec.k ~= "canonical_stat" and spec.k ~= "canonical_line" then
			table.insert(directives, spec.k .. ":" .. tostring(spec.v))
		end
	end
	local text = desc.text:gsub("\\n", " "):gsub("%%%%", "%%"):gsub("%s+", " "):match("^%s*(.-)%s*$")
	local statIds = table.concat(stats, ",")
	local key = table.concat({ statIds, table.concat(limits, ","), table.concat(directives, ","),
		desc.gem_quality and "1" or "0", text }, "\t")
	local name = scopeName:lower():gsub("^specific_skill_stat_descriptions/", "")
	local scope = gemStats.scopes[name]
	local official = (scope and scope[key]) or gemStats.common[key]
	if official and official ~= desc.text then return official end
	local supplemental = gemStats.supplemental[name]
	local manual = supplemental and supplemental[statIds .. "\t" .. text]
	return manual or desc.text, manual ~= nil
end

local function skillEntry(id, originalName)
	if ui.language ~= "ru" then return end
	local entry = skills.active[id]
	if entry and originalName and entry.en == originalName:match("^%s*(.-)%s*$") then return entry end
	local variants = skills.gemEffects[id]
	return variants and variants[originalName]
end

function ui.effectName(effect)
	local entry = skillEntry(effect.id, effect.name)
	return entry and entry.name or effect.name
end

function ui.effectDescription(effect)
	local entry = skillEntry(effect.id, effect.name) or (ui.language == "ru" and skills.active[effect.id])
	if entry and entry.enDescription and effect.description then
		local function normalized(text)
			return (text:gsub("%s+", " "):gsub(" +%.", "."):match("^%s*(.-)%s*$"):gsub("%.$", ""))
		end
		local source = normalized(effect.description)
		if entry.pobDescription and source == normalized(entry.pobDescription) then return entry.description, entry.comparisonNote end
		if effect.id == "SupportDoedresUndoingPlayer" then source = source:gsub("eneimes", "enemies") end
		if normalized(entry.enDescription) == source then return entry.description end
	end
	return effect.description
end

function ui.effectFlavourText(effect)
	local entry = skillEntry(effect.id, effect.name)
	return entry and entry.flavour and { entry.flavour } or effect.flavourText
end

function ui.gemName(gem)
	local variants = ui.language == "ru" and skills.gems[gem.gameId]
	local names = variants and variants[gem.grantedEffectId]
	if names and names[gem.name] then return names[gem.name] end
	local entry = skillEntry(gem.grantedEffectId, gem.name)
	return entry and entry.name or gem.name
end

function ui.gemInstanceName(instance)
	local gem = instance.gemData
	if gem and instance.nameSpec == gem.name then return ui.gemName(gem) end
	local effect = instance.grantedEffect
	if effect and instance.nameSpec == effect.name then return ui.effectName(effect) end
	return instance.nameSpec
end

function ui.minionName(id, originalName)
	if ui.language ~= "ru" then return originalName end
	return skills.minions[id] or ui.effectCaption(originalName)
end

function ui.skillDisplayName(effect, label, minionId)
	if ui.language ~= "ru" then return label end
	local entry = skills.active[effect.id]
	if entry and entry.selectionName then
		if label == effect.name then return entry.selectionName end
		local name = label:match("^Spectre: (.+)$") or label:match("^Companion: (.+)$")
		if name then
			return (entry.name:gsub("{0}", function() return ui.minionName(minionId, name) end))
		end
	end
	return label == effect.name and ui.effectName(effect) or label
end

function ui.gemDisplayName(instance)
	local label = ui.gemInstanceName(instance)
	local effect = instance.grantedEffect or (instance.gemData and instance.gemData.grantedEffect)
	return effect and ui.skillDisplayName(effect, label or effect.name, instance.skillMinion) or label
end

function ui.skillVariantLabel(label, effect)
	if ui.language ~= "ru" then return label end
	if effect and label == effect.name then return ui.skillDisplayName(effect, label) end
	return skills.statLabels[label] or ui.translate(label)
end

function ui.skillGroupName(group)
	if ui.language ~= "ru" then return group.displayLabel end
	if group.source == "Explode" and group.label == "On Kill Monster Explosion" then
		return ui.translate(group.displayLabel)
	end
	if group.label and group.label:match("%S") then return group.displayLabel end
	local names = {}
	for _, instance in ipairs(group.gemList) do
		local effect = instance.gemData and instance.gemData.grantedEffect or instance.grantedEffect
		if instance.enabled and effect and not effect.support then
			table.insert(names, ui.gemDisplayName(instance))
		end
	end
	return #names > 0 and table.concat(names, ", ") or group.displayLabel
end

function ui.effectCaption(name)
	if ui.language ~= "ru" then return name end
	local first, second = name:match("^([^:]+): (.+)$")
	if first then return ui.effectCaption(first) .. ": " .. ui.effectCaption(second) end
	return itemReferenceName("skill", "forward", name) or itemReferenceName("gem", "forward", name) or ui.translate(name)
end

function ui.effectList(text)
	if ui.language ~= "ru" then return text end
	local parts = {}
	for name in text:gmatch("[^,]+") do
		name = name:match("^%s*(.-)%s*$")
		parts[#parts + 1] = ui.effectCaption(name)
	end
	return table.concat(parts, ", ")
end

function ui.passive(version, id, originalName)
	if ui.language ~= "ru" then return end
	local catalog = tree
	if version == "0_4" then
		historicalTree = historicalTree or LoadModule("Data/Locale/tree_0_4_ru")
		catalog = historicalTree
	elseif version ~= "0_5" then
		return
	end
	local entry = catalog.nodes[id]
	if entry and entry.en == originalName then return entry end
end

function ui.passiveName(version, node)
	local entry = ui.passive(version, node.id, node.dn)
	return entry and entry.name or node.dn
end

function ui.emotionName(key, full)
	local emotion = ui.language == "ru" and tree.emotions[key]
	if emotion then return full and emotion.name or emotion.short end
	return full and "Distilled " .. key or (key:gsub("Oil$", ""))
end

function ui.passiveLine(entry, line)
	-- Radius jewel bonuses and scaled values are calculated after the tree data is loaded.
	if ui.language ~= "ru" then return line end
	return (entry and entry.stats[line]) or translateItemModifier(line, "passive") or ui.itemModifier(line)
end

function ui.passiveStat(entry, lines, index, combine)
	if entry then
		local group = combine and entry.groups and entry.groups[index]
		if group then
			local last = index + group.length - 1
			if last <= #lines and table.concat(lines, "\n", index, last) == group.source then
				return group.text, group.length
			end
		end
	end
	return ui.passiveLine(entry, lines[index]), 1
end

local function translateLine(text)
	local prefix = ""
	while text:sub(1, 1) == "^" do
		local escape = text:match("^%^x%x%x%x%x%x%x") or text:match("^%^%d")
		if not escape then break end
		prefix = prefix .. escape
		text = text:sub(#escape + 1)
	end

	local leading, body, trailing = text:match("^(%s*)(.-)(%s*)$")
	if not leading then return prefix .. text end
	local translated = messages[body] or tradeMessages[body] or tree.classes[body]
	if translated then return prefix .. leading .. translated .. trailing end
	local minionSort = body:match("^Sort by Minion (.+)$")
	if minionSort and messages["Sort by " .. minionSort] then
		return prefix .. leading .. messages["Sort by " .. minionSort] .. " (приспешник)" .. trailing
	end
	local label, value = body:match("^([^:^]+):(.*)$")
	if label then
		translated = messages[label .. ":"] or tradeMessages[label .. ":"]
			or ((messages[label] or tradeMessages[label]) and (messages[label] or tradeMessages[label]) .. ":")
		if translated then return prefix .. leading .. translated .. value .. trailing end
	end
	local hand, stat = body:match("^([MO]H) (.+)$")
	if hand then
		local key, colon = stat:match("^(.-)(:?)$")
		local statText = messages[key] or messages[key .. ":"]
		if statText then
			local handText = hand == "MH" and "осн. рука" or "втор. рука"
			return prefix .. leading .. statText:gsub(":$", "") .. " (" .. handText .. ")" .. colon .. trailing
		end
	end
	local shade = body:match("%^x%x%x%x%x%x%x") or body:match("%^%d")
	if shade then
		local plain = body:gsub("%^x%x%x%x%x%x%x", ""):gsub("%^%d", "")
		local exact = messages[plain]
		if exact then
			local closingShade = body:match("(%^x%x%x%x%x%x%x)$") or body:match("(%^%d)$") or ""
			return prefix .. leading .. (shade ~= closingShade and shade or "") .. exact .. closingShade .. trailing
		end
	end
	local act, index, area = body:match("^(%a+) (%d+): (.+)$")
	local areaName = area and (tree.areas[area:lower()] or tree.areas["the " .. area:lower()])
	if areaName and (act == "Act" or act == "Interlude") then
		local chapter = act == "Act" and "Акт" or "Интерлюдия"
		return prefix .. leading .. chapter .. " " .. index .. ": " .. areaName .. trailing
	end
	local warnings = body:match("^(%d+) Warnings?$")
	if warnings then return prefix .. leading .. "Предупреждений: " .. warnings .. trailing end
	local dps = body:match("^([%d.,]+) DPS$")
	if dps then return prefix .. leading .. dps .. " УВС" .. trailing end
	local low, high = body:match("^([%d.,]+) to ([%d.,]+)$")
	if low then return prefix .. leading .. low .. "–" .. high .. trailing end
	return prefix .. leading .. ui.tradeText(body) .. trailing
end

function ui.translate(text)
	if ui.language ~= "ru" or type(text) ~= "string" or text == "" then return text end
	return messages[text] or tradeMessages[text] or (text:gsub("[^\n]+", translateLine))
end

function ui.configText(text)
	if ui.language ~= "ru" or text == nil then return text end
	configMessages = configMessages or LoadModule("Data/Locale/config_ru")
	local plain = StripEscapes(text):match("^%s*(.-)%s*$")
	local translated = configMessages[plain]
	if not translated then return ui.translate(text) end
	local prefix = text:match("^%^x%x%x%x%x%x%x") or text:match("^%^%d") or ""
	return prefix .. translated
end

function ui.format(text, ...)
	return string.format(ui.translate(text), ...)
end

function ui.setLanguage(language)
	ui.language = language == "en" and "en" or "ru"
end

ui.drawRaw = DrawString
ui.measureRaw = DrawStringWidth

function ui.fitButton(button)
	local minimumWidth = button:GetProperty("width")
	button.width = function(control)
		local fontHeight = control:GetProperty("height") - 4 + (control.overSizeText or 0) * 2
		local label = ui.translate(control:GetProperty("label"))
		return math.max(minimumWidth, ui.measureRaw(fontHeight, "VAR", label) + 14)
	end
end

function ui.wrap(control, source, height, font, width)
	local text = ui.translate(source)
	local cached = control.wrappedText
	if cached and cached.text == text and cached.height == height and cached.font == font and cached.width == width then
		return cached.result, cached.lines
	end

	local lines = {}
	for paragraph in (text .. "\n"):gmatch("(.-)\n") do
		local line
		for word in paragraph:gmatch("%S+") do
			local candidate = line and line .. " " .. word or word
			if line and ui.measureRaw(height, font, candidate) > width then
				lines[#lines + 1] = line
				line = word
			else
				line = candidate
			end
			-- Break very long words only when the entire word is wider than the cell.
			if ui.measureRaw(height, font, line) > width then
				local tail = line
				line = ""
				while tail ~= "" do
					local token = tail:match("^%^x%x%x%x%x%x%x") or tail:match("^%^%d")
						or tail:match("^.[\128-\191]*")
					if line ~= "" and ui.measureRaw(height, font, line .. token) > width then
						lines[#lines + 1] = line
						line = ""
					end
					line = line .. token
					tail = tail:sub(#token + 1)
				end
			end
		end
		lines[#lines + 1] = line or ""
	end
	while #lines > 1 and lines[#lines] == "" do
		lines[#lines] = nil
	end

	local result = table.concat(lines, "\n")
	control.wrappedText = { text = text, height = height, font = font, width = width, result = result, lines = #lines }
	return result, #lines
end

function DrawString(left, top, align, height, font, text)
	return ui.drawRaw(left, top, align, height, font, ui.translate(text))
end

function DrawStringWidth(height, font, text)
	return ui.measureRaw(height, font, ui.translate(text))
end

return ui
