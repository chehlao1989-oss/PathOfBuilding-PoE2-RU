local attributes = {
	Strength = "силы",
	Dexterity = "ловкости",
	Intelligence = "интеллекта",
}

local resources = {
	Life = "здоровья",
	Mana = "маны",
	Rage = "ярости",
	["Energy Shield"] = "энергетического щита",
	["Energy Shield and Mana"] = "энергетического щита и маны",
	["Unreserved life%"] = "свободного здоровья",
	["Unreserved Mana%"] = "свободной маны",
}

local function subjectName(name, build)
	for _, item in pairs(build.itemsTab.items) do
		if item.name == name then return UILocale.itemName(item) end
	end
	for _, group in ipairs(build.skillsTab.socketGroupList) do
		if group.displayLabel == name then return UILocale.skillGroupName(group) end
	end
	return UILocale.effectCaption(name)
end

local function groupNames(text, build)
	local names = {}
	for name in text:gmatch("[^,]+") do
		names[#names + 1] = subjectName(name:match("^%s*(.-)%s*$"), build)
	end
	return table.concat(names, ", ")
end

return function(text, build)
	if UILocale.language ~= "ru" then return text end
	local attribute, source = text:match("^You do not meet the (%a+) requirement of (.+)$")
	if attributes[attribute] then
		if source == "your total " .. attribute .. " support gems." then
			return UILocale.format("You do not meet the %s requirement of your support gems.", attributes[attribute])
		end
		return UILocale.format("You do not meet the %s requirement of %s", attributes[attribute], subjectName(source, build))
	end
	local resource, skills = text:match("^You do not have enough (.-) to use: (.+)$")
	if resources[resource] then
		return UILocale.format("You do not have enough %s to use: %s", resources[resource], UILocale.effectList(skills))
	end
	local count, weaponSet = text:match("^You have allocated (%d+) too many weapon set ([12]) passives$")
	if count then
		return UILocale.format("You have allocated %s too many weapon set %s passives", count, weaponSet)
	end
	count = text:match("^You have (%d+) Weapon set 2 passives available$")
	if count then return UILocale.format("You have %s Weapon set 2 passives available", count) end
	source = text:match("^You are exceeding jewel limit with the jewel (.+)$")
	if source then
		local name = subjectName(source, build)
		for _, item in pairs(build.itemsTab.items) do
			if item.title == source then name = UILocale.itemTitle(item); break end
		end
		return UILocale.format("You are exceeding jewel limit with the jewel %s", name)
	end
	source = text:match("^You have too many gems in your (.+) socket group$")
	if source then return UILocale.format("You have too many gems in your %s socket group", subjectName(source, build)) end
	local gem, maximum, locations = text:match("^You have too many (.-) lineage support gems allocated%. Max allowed is (%d+)%.(.*)$")
	if gem then
		local warning = UILocale.format("You have too many %s lineage support gems allocated. Max allowed is %s.",
			UILocale.effectCaption(gem), maximum)
		locations = locations:match("^ Locations: (.+)$")
		return locations and warning .. " " .. UILocale.format("Locations: %s", groupNames(locations, build)) or warning
	end
	local allowed, allocated = text:match("^You have too many gem groups allocated%. Max allowed is (%d+)%. You have (%d+) non%-item/non%-granted gem groups allocated%.$")
	if allowed then
		return UILocale.format("You have too many gem groups allocated. Max allowed is %s. You have %s non-item/non-granted gem groups allocated.",
			allowed, allocated)
	end
	return UILocale.translate(text)
end
