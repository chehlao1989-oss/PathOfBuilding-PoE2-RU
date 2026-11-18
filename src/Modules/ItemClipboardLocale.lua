local names = LoadModule("Data/Locale/item_names_ru")
local affixes = LoadModule("Data/Locale/item_affixes_ru")
local types = LoadModule("Data/Locale/item_filter_ru")

local rarityNames = {
	["Обычный"] = "NORMAL", ["Обычная"] = "NORMAL",
	["Волшебный"] = "MAGIC", ["Волшебная"] = "MAGIC",
	["Редкий"] = "RARE", ["Редкая"] = "RARE",
	["Уникальный"] = "UNIQUE", ["Уникальная"] = "UNIQUE",
}
local labels = {
	["Уровень предмета"] = "Item Level",
	["Качество"] = "Quality",
	["Гнёзда"] = "Sockets", ["Гнезда"] = "Sockets",
	["Дух"] = "Spirit",
	["Гнёзда для оберегов"] = "Charm Slots", ["Гнезда для оберегов"] = "Charm Slots",
	["Броня"] = "Armour", ["Уклонение"] = "Evasion Rating",
	["Энергетический щит"] = "Energy Shield", ["Рунический барьер"] = "Ward",
	["Физический урон"] = "Physical Damage", ["Урон от стихий"] = "Elemental Damage",
	["Урон от хаоса"] = "Chaos Damage", ["Урон от огня"] = "Fire Damage",
	["Урон от холода"] = "Cold Damage", ["Урон от молнии"] = "Lightning Damage",
	["Шанс критического удара"] = "Critical Hit Chance",
	["Шанс крит. попадания"] = "Critical Hit Chance",
	["Атак в секунду"] = "Attacks per Second", ["Атаки в секунду"] = "Attacks per Second",
	["Шанс блока"] = "Chance to Block", ["Время перезарядки"] = "Reload Time",
	["Дальность оружия"] = "Weapon Range", ["Лимит"] = "Limited to",
}
local flags = {
	["Осквернено"] = "Corrupted", ["Осквернённый"] = "Corrupted", ["Оскверненный"] = "Corrupted",
	["Неопознанный"] = "Unidentified", ["Отражённый"] = "Mirrored", ["Отраженный"] = "Mirrored",
}
local modifierKinds = {
	["встроенное"] = "implicit", ["встроенное свойство"] = "implicit",
	["зачарование"] = "enchant", ["созданное"] = "crafted", ["расколотое"] = "fractured",
	["rune"] = "rune",
}

local function trim(text)
	return (text:match("^%s*(.-)%s*$"))
end

local function readAffix(entries, title, inflection)
	if title == "" then return "" end
	local result
	for english, entry in pairs(entries) do
		local russian = type(entry.name) == "table" and entry.name[inflection] or entry.name
		if russian == title then
			if result and result ~= english then return end
			result = english
		end
	end
	return result
end

local function chooseBase(title, class, magic)
	local matches = {}
	for english, entry in pairs(names.bases) do
		local base = data.itemBases[english]
		if base and (not class or base.type == class or base.subType == class) then
			if title == entry.name or magic and not english:match("^Shrine Sceptre %(") then
				local from, to = title:find(entry.name, 1, true)
				if from then
					local prefix, suffix = trim(title:sub(1, from - 1)), trim(title:sub(to + 1))
					if (prefix == "" or title:sub(from - 1, from - 1) == " ")
						and (suffix == "" or title:sub(to + 1, to + 1) == " ") then
						matches[#matches + 1] = { en = english, entry = entry, prefix = prefix, suffix = suffix }
					end
				end
			end
		end
	end
	table.sort(matches, function(a, b) return #a.entry.name > #b.entry.name end)
	if #matches == 0 or matches[2] and #matches[1].entry.name == #matches[2].entry.name then return end
	return matches[1]
end

local function englishUnique(title, baseName)
	local matchTitle, matchBase
	for english, variants in pairs(names.uniques) do
		for base, entry in pairs(variants) do
			if title == entry.name and baseName == (entry.baseName or names.bases[base].name) then
				if matchTitle and (matchTitle ~= english or matchBase ~= base) then return end
				matchTitle, matchBase = english, base
			end
		end
	end
	return matchTitle, matchBase
end

local function englishRareTitle(title)
	local result
	for english, entry in pairs(affixes.rareNouns) do
		local suffix = " " .. entry.name.noun
		if title:sub(-#suffix) == suffix then
			local prefix = readAffix(affixes.rarePrefixes, title:sub(1, -#suffix - 1), entry.name.inflection)
			if prefix then
				local name = prefix .. " " .. english
				if result and result ~= name then return title end
				result = name
			end
		end
	end
	return result or title
end

local function normalize(raw)
	if not raw:find("Редкость:", 1, true) then return raw end
	local lines, issues = {}, {}
	for line in raw:gmatch("[^\r\n]+") do lines[#lines + 1] = trim(line) end
	local index, class = 1
	local russianClass = lines[index] and lines[index]:match("^Класс предмета:%s*(.+)$")
	if russianClass then
		for en, ru in pairs(types) do
			if russianClass == ru then class = en; break end
		end
		index = index + 1
	end
	local rarityLabel = lines[index] and lines[index]:match("^Редкость:%s*(.+)$")
	if not rarityLabel then return raw end
	local rarity = rarityNames[rarityLabel]
	if not rarity then return nil, { "Неизвестная редкость: " .. rarityLabel } end
	local output = { "Rarity: " .. rarity }
	local title = lines[index + 1]
	local base = lines[index + 2]
	if not title then return nil, { "Отсутствует название предмета." } end
	local propertiesStart
	if rarity == "UNIQUE" then
		local englishTitle, englishBase = englishUnique(title, base)
		if not englishTitle then return nil, { "Не удалось определить уникальный предмет: " .. title } end
		output[#output + 1], output[#output + 2] = englishTitle, englishBase
		propertiesStart = index + 3
	elseif rarity == "RARE" then
		local match = base and chooseBase(base, class)
		if not match then return nil, { "Не удалось определить базу: " .. (base or title) } end
		output[#output + 1], output[#output + 2] = englishRareTitle(title), match.en
		propertiesStart = index + 3
	else
		local match = chooseBase(title, class, rarity == "MAGIC")
		if not match then return nil, { "Не удалось определить базу: " .. title } end
		local prefix = readAffix(affixes.magicPrefixes, match.prefix, match.entry.inflection)
		local suffix = readAffix(affixes.magicSuffixes, match.suffix, match.entry.inflection)
		if not prefix or not suffix then issues[#issues + 1] = "Части имени: " .. title end
		output[#output + 1] = trim((prefix or match.prefix) .. " " .. match.en .. " " .. (suffix or match.suffix))
		propertiesStart = index + 2
	end

	for i = propertiesStart, #lines do
		local line = lines[i]
		-- Advanced-copy headers describe affixes. The following lines contain their actual rolls.
		if line:match("^%{%s") then goto nextLine end
		line = line:gsub("([+%-]?%d+[.,]?%d*)%(%-?%d+[.,]?%d*%-%-?%d+[.,]?%d*%)", "%1")
		local label, value = line:match("^(.-):%s*(.*)$")
		local converted = flags[line]
		if labels[label] then
			converted = labels[label] .. ": " .. value:gsub(" %([%a ]+%)", ""):gsub("(%d),(%d)", "%1.%2")
		elseif label == "Требуется" or label == "Требует" or label == "Требования" then
			converted = "Requires: " .. value:gsub(" %([%a ]+%)", ""):gsub("Уровень", "Level"):gsub("Сила", "Str")
				:gsub("Ловк", "Dex"):gsub("Инт", "Int")
		elseif line == "--------" then
			converted = line
		elseif not converted then
			local body, modifierKind = line:match("^(.-)%s+%(([^()]+)%)$")
			local kind = modifierKinds[modifierKind] or
				((modifierKind == "implicit" or modifierKind == "enchant" or modifierKind == "crafted" or
					modifierKind == "fractured") and modifierKind)
			converted = UILocale.englishItemModifier(kind and body or line)
			if converted and kind then converted = converted .. " (" .. kind .. ")" end
		end
		if not converted then
			issues[#issues + 1] = line
		end
		output[#output + 1] = converted or line
		::nextLine::
	end
	return table.concat(output, "\n"), issues
end

return normalize
