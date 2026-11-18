-- Path of Building
--
-- Module: Gem Tooltip
-- Shared renderer for gem-style tooltips.

local m_max = math.max
local m_min = math.min

local GemTooltip = { }

local function getFontSizes()
	return main.showFlavourText and 18 or 16, main.showFlavourText and 24 or 20
end

local function addDescriptionLine(tooltip, build, statSet, line, stat, index, colorCode)
	local fontSizeBig = getFontSizes()
	local source = statSet.statMap[stat] or build.data.skillStatMap[stat]
	local bg = (index % 2 == 0) and "GemHoverModBg" or nil
	if source then
		if launch.devModeAlt then
			local devText = stat
			if source[1] then
				if not source[1].value then
					source[1].value = stat
				end
				devText = modLib.formatMod(source[1])
			end
			line = line .. " ^2" .. devText
		end
		tooltip:AddLine(fontSizeBig, (colorCode or colorCodes.MAGIC) .. line, "FONTIN SC", bg)
	else
		if launch.devModeAlt then
			line = line .. " ^1" .. stat
		end
		line = colorCodes.UNSUPPORTED .. line
		line = main.notSupportedModTooltips and (line .. main.notSupportedTooltipText) or line
		tooltip:AddLine(fontSizeBig, line, "FONTIN SC", bg)
	end
end

local function getDisplayInstance(gemInstance)
	return gemInstance.displayEffect or gemInstance
end

local function addGrantedEffectInfo(tooltip, build, gemInstance, grantedEffect, addReq, levelRange)
	local fontSizeBig = getFontSizes()
	local displayInstance = getDisplayInstance(gemInstance)
	local levelStats = grantedEffect.levels[levelRange and 1 or displayInstance.level] or { }
	local maxStats = levelRange and (grantedEffect.levels[20] or levelStats) or levelStats

	-- Passive tree tooltips need level 1-20 ranges; normal gem tooltips keep the current level value.
	local function valueOrRange(keyName, formatter, add, div, mul)
		local firstValue = levelStats[keyName]
		if not firstValue then
			return nil
		end
		local lastValue = levelRange and ((maxStats and maxStats[keyName]) or firstValue) or firstValue
		local numFormat = formatter or "%d"
		local first = (mul or 1) * (firstValue + (add or 0)) / (div or 1)
		local last = (mul or 1) * (lastValue + (add or 0)) / (div or 1)
		if first == last then
			return string.format(numFormat, first)
		end
		return string.format("(" .. numFormat .. "-" .. numFormat .. ")", first, last)
	end

	if not levelRange and gemInstance.gemData.Tier and gemInstance.gemData.Tier > 0 and not grantedEffect.isLineage and not grantedEffect.hidden then
		tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("Tier", "Tier") .. ": ^7%d", gemInstance.gemData.Tier), "FONTIN SC")
	end
	if not levelRange and addReq and not grantedEffect.support then
		local totalGlobalLevels = 0
		if displayInstance.gemPropertyInfo then
			for i, prop in ipairs(displayInstance.gemPropertyInfo) do
				if prop.value and prop.value.key == "level" and prop.value.value then
					totalGlobalLevels = totalGlobalLevels + prop.value.value
				end
			end
		end
		local totalLevel
		local corruptLevel = displayInstance.corruptLevel or 0
		totalLevel = m_max(displayInstance.level, (gemInstance.level + corruptLevel)) -- Needed for tooltip comparison for dropdown gems. Otherwise they only show level 20 when corrupted.
		if corruptLevel ~= 0 or
		totalGlobalLevels > 0 or
		(displayInstance.level - gemInstance.level - corruptLevel > 0)
		then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("Level", "Level") .. ": ^7" .. colorCodes.MAGIC .. totalLevel), "FONTIN SC")
			tooltip:AddLine(fontSizeBig, "   ^7" .. (gemInstance.level >= gemInstance.gemData.naturalMaxLevel
				and UILocale.gemText("ItemDisplaySkillGemLevelsFromGemMaxLevel", "{0} Levels from Gem (Max)", gemInstance.level)
				or UILocale.gemText("ItemDisplaySkillGemLevelsFromGem", "{0} Levels from Gem", gemInstance.level)), "FONTIN SC")
		else
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("Level", "Level") .. ": ^7" .. (gemInstance.level >= gemInstance.gemData.naturalMaxLevel and UILocale.gemText("ItemDisplaySkillGemMaxLevel", "{0} (Max)", totalLevel) or totalLevel)), "FONTIN SC")
		end
		if corruptLevel > 0 then
			tooltip:AddLine(fontSizeBig, colorCodes.MAGIC .. "   " .. UILocale.gemText("ItemDisplaySkillGemPlusLevelFromCorruption", "+{0} Level from Corruption", corruptLevel), "FONTIN SC")
		elseif corruptLevel < 0 then
			tooltip:AddLine(fontSizeBig, colorCodes.MAGIC .. "   " .. UILocale.gemText("ItemDisplaySkillGemMinusLevelFromCorruption", "-{0} Level from Corruption", -corruptLevel), "FONTIN SC")
		end
		if totalGlobalLevels > 0 then
			tooltip:AddLine(fontSizeBig, colorCodes.MAGIC .. "   " .. UILocale.gemText("ItemDisplaySkillGemPlusLevelsFromGlobalStats", "+{0} Levels from Global Modifiers", totalGlobalLevels), "FONTIN SC")
			if totalLevel - gemInstance.level - corruptLevel - totalGlobalLevels > 0 then
				tooltip:AddLine(fontSizeBig, colorCodes.MAGIC .. "   " .. UILocale.gemText("ItemDisplaySkillGemPlusLevelsFromSupport", "+{0} Levels from Supports", totalLevel - gemInstance.level - corruptLevel - totalGlobalLevels), "FONTIN SC")
			end
		elseif totalLevel - gemInstance.level - corruptLevel > 0 then
			tooltip:AddLine(fontSizeBig, colorCodes.MAGIC .. "   " .. UILocale.gemText("ItemDisplaySkillGemPlusLevelsFromSupport", "+{0} Levels from Supports", totalLevel - gemInstance.level - corruptLevel), "FONTIN SC")
		end
	end
	if not levelRange and addReq and displayInstance.quality > 0 then
		tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("Quality", "Quality") .. ": " .. colorCodes.MAGIC .. "+%d%%^7%s",
			gemInstance.quality,
			(displayInstance.quality > gemInstance.quality) and " (" .. colorCodes.MAGIC .. "+" .. (displayInstance.quality - gemInstance.quality) .. "^7)" or ""
		), "FONTIN SC")
	end
	if not levelRange and grantedEffect.support then
		if levelStats.manaMultiplier and levelStats.reservationMultiplier and levelStats.manaMultiplier == levelStats.reservationMultiplier then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemCostAndReservationMultiplier", "Cost & Reservation Multiplier") .. ": ^7%d%%", levelStats.manaMultiplier + 100), "FONTIN SC")
		elseif levelStats.reservationMultiplier then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemReservationMultiplier", "Reservation Multiplier") .. ": ^7%d%%", levelStats.reservationMultiplier + 100), "FONTIN SC")
		elseif levelStats.manaMultiplier then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemCostMultiplier", "Cost Multiplier") .. ": ^7%d%%", levelStats.manaMultiplier + 100), "FONTIN SC")
		end
		if levelStats.spiritReservationFlat then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemReservationFromSupport", "Additional Reservation") .. ": ^7%s", UILocale.gemText("SkillPopupCostValueSpirit", "{0} Spirit", levelStats.spiritReservationFlat)), "FONTIN SC")
		end
	else
		if gemInstance.skillMinion and not levelRange then
			if gemInstance.nameSpec:match("^Spectre:") then
				levelStats.spiritReservationFlat = data.spectres[gemInstance.skillMinion].spectreReservation
			elseif gemInstance.nameSpec:match("^Companion:") then
				levelStats.spiritReservationPercent = data.spectres[gemInstance.skillMinion].companionReservation
			end
		end
		if levelStats.spiritReservationFlat then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemManaReserved", "Reservation") .. ": ^7%s %s", valueOrRange("spiritReservationFlat"), UILocale.gemText("ItemDisplayGemReservationSpirit", "Spirit")), "FONTIN SC")
		end
		if levelStats.spiritReservationPercent then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemManaReserved", "Reservation") .. ": ^7%s%% %s", UILocale.gemResourceNumber(valueOrRange("spiritReservationPercent", "%.1f")), UILocale.gemText("ItemDisplayGemReservationSpirit", "Spirit")), "FONTIN SC")
		end
		local cost
		for _, res in ipairs(data.costs) do
			if levelStats.cost and levelStats.cost[res.Resource] then
				local first = round(levelStats.cost[res.Resource] / res.Divisor, 2)
				local last = first
				if levelRange and maxStats.cost and maxStats.cost[res.Resource] then
					last = round(maxStats.cost[res.Resource] / res.Divisor, 2)
				end
				local value = first == last and string.format("%g", first) or string.format("(%g-%g)", first, last)
				cost = (cost and (cost .. ", ") or "") .. UILocale.gemText(res.ResourceString, res.ResourceString, UILocale.gemResourceNumber(value))
			end
		end
		if cost then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. "   " .. UILocale.gemText("ItemDisplaySkillGemManaCost", "Cost") .. ": ^7" .. cost, "FONTIN SC")
		end
	end

	if levelStats.cooldown then
		local line = colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemCooldownTime", "Cooldown Time") .. ": ^7%s", UILocale.gemText("ItemDisplaySkillGemCastTimeValue", "{0} sec", valueOrRange("cooldown", "%.2f")))
		if levelStats.storedUses and levelStats.storedUses > 1 then
			line = line .. UILocale.format(" (%s uses)", valueOrRange("storedUses"))
		end
		tooltip:AddLine(fontSizeBig, line, "FONTIN SC")
	end
	if levelStats.vaalStoredUses then
		tooltip:AddLine(fontSizeBig, string.format("^x7F7F7FCan Store ^7%d ^x7F7F7FUse (%d Souls)", levelStats.vaalStoredUses, levelStats.vaalStoredUses * levelStats.cost.Soul), "FONTIN SC")
	end
	if levelStats.soulPreventionDuration then
		tooltip:AddLine(fontSizeBig, string.format("^x7F7F7FSoul Gain Prevention: ^7%s sec", valueOrRange("soulPreventionDuration")), "FONTIN SC")
	end
	if gemInstance.gemData.tags.attack then
		if levelStats.attackSpeedMultiplier then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemAttackSpeedMultiplier", "Attack Speed") .. ": ^7%s%% %s", valueOrRange("attackSpeedMultiplier", nil, 100), UILocale.translate("of base")), "FONTIN SC")
		end
		if levelStats.attackTime then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemAttackTimeOverride", "Attack Time") .. ": ^7%s", UILocale.gemText("ItemDisplaySkillGemCastTimeValue", "{0} sec", valueOrRange("attackTime", "%.2f", nil, 1000))), "FONTIN SC")
		end
		if levelStats.baseMultiplier then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemAttackDamageEffectiveness", "Attack Damage") .. ": ^7%s", UILocale.format("%s%% of base", valueOrRange("baseMultiplier", "%g", nil, nil, 100))), "FONTIN SC")
		end
	elseif not grantedEffect.hidden then
		if (grantedEffect.castTime or 0) > 0 then
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemCastTime", "Cast Time") .. ": ^7%s", UILocale.gemText("ItemDisplaySkillGemCastTimeValue", "{0} sec", string.format("%.2f", grantedEffect.castTime))), "FONTIN SC")
		else
			tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. "   " .. UILocale.gemText("ItemDisplaySkillGemCastTime", "Cast Time") .. ": ^7" .. UILocale.gemText("SkillIsInstant", "Instant"), "FONTIN SC")
		end
	end
	if levelStats.critChance then
		tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format("   " .. UILocale.gemText("ItemDisplaySkillGemCriticalStrikeChance", "Critical Hit Chance") .. ": ^7%s%%", valueOrRange("critChance", "%.2f")), "FONTIN SC")
	end
	if not levelRange and addReq then
		local reqLevel = grantedEffect.levels[gemInstance.level] and grantedEffect.levels[gemInstance.level].levelRequirement or 1
		build:AddRequirementsToTooltip(tooltip, reqLevel,
			calcLib.getGemStatRequirement(reqLevel, gemInstance.gemData.reqStr, grantedEffect.support),
			calcLib.getGemStatRequirement(reqLevel, gemInstance.gemData.reqDex, grantedEffect.support),
			calcLib.getGemStatRequirement(reqLevel, gemInstance.gemData.reqInt, grantedEffect.support))
	end
	if gemInstance.gemData.weaponRequirements and not grantedEffect.hidden then
		tooltip:AddLine(fontSizeBig, "   ^x7F7F7F" .. UILocale.gemText("HeistRequiresText", "Requires") .. ": ^7" .. UILocale.gemWeaponRequirements(gemInstance.gemData.weaponRequirements), "FONTIN SC")
	end
	tooltip.center = true
	if grantedEffect.description then
		tooltip:AddSeparator(10)
		local description, comparisonNote = UILocale.effectDescription(grantedEffect)
		tooltip:AddLine(fontSizeBig, colorCodes.GEMDESCRIPTION .. description, "FONTIN ITALIC")
		if comparisonNote then
			tooltip:AddLine(14, colorCodes.WARNING .. comparisonNote)
		end
	end
	if displayInstance.corrupted == true then
		tooltip:AddSeparator(10)
		tooltip:AddLine(fontSizeBig, colorCodes.NEGATIVE .. UILocale.gemText("MonsterCorrupted", "Corrupted"), "FONTIN SC")
	end
end

local function addStatSetInfo(tooltip, build, gemInstance, grantedEffect, statSet, noLabel, index, levelRange)
	local fontSizeBig, fontSizeTitle = getFontSizes()
	local displayInstance = getDisplayInstance(gemInstance)
	local includeAltQualityStats = build.calcsTab.mainEnv.modDB:Flag(nil, "GemlingQuality")
	local statSetLevel = statSet.levels[levelRange and gemInstance.level or displayInstance.level] or statSet.levels[1] or { }
	if not (index == 1 and statSet.label == grantedEffect.name) and statSet.label ~= "" and not noLabel then
		tooltip:AddSeparator(10)
		tooltip:AddLine(fontSizeTitle, colorCodes.GEM .. UILocale.skillVariantLabel(statSet.label, grantedEffect), "FONTIN SC")
		tooltip:AddSeparator(10)
	end
	if statSetLevel.critChance then
		tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format(UILocale.gemText("ItemDisplaySkillGemCriticalStrikeChance", "Critical Hit Chance") .. ": ^7%.2f%%", statSetLevel.critChance), "FONTIN SC")
	end
	if statSetLevel.baseMultiplier then
		tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. string.format(UILocale.gemText("ItemDisplaySkillGemAttackDamageEffectiveness", "Attack Damage") .. ": ^7%d%%", statSetLevel.baseMultiplier * 100), "FONTIN SC")
	end
	if build.data.describeStats then
		if not noLabel then tooltip:AddSeparator(10) end
		local stats
		if levelRange then
			-- Passive tree granted skills are not real gem instances, so show how their stats scale from level 1 to 20.
			local copiedInstance = copyTable(gemInstance, true)
			copiedInstance.quality = 0
			copiedInstance.level = 20
			local statsLevel20 = calcLib.buildSkillInstanceStats(copiedInstance, grantedEffect, statSet, includeAltQualityStats)
			copiedInstance.level = 1
			stats = calcLib.buildSkillInstanceStats(copiedInstance, grantedEffect, statSet, includeAltQualityStats)
			for statName, min in pairs(stats) do
				stats[statName] = { min = min, max = statsLevel20[statName] or min }
			end
		else
			stats = calcLib.buildSkillInstanceStats(displayInstance, grantedEffect, statSet, includeAltQualityStats)
		end
		local descriptions, lineMap = build.data.describeStats(stats, statSet.statDescriptionScope, false, UILocale.gemStatTemplate)
		local altQualityStatColor = { }
		if includeAltQualityStats then
			for _, stat in ipairs(grantedEffect.altQualityStats or { }) do
				altQualityStatColor[stat[1]] = colorCodes.ENCHANTED
			end
		end
		for i, line in ipairs(descriptions) do
			local stat = lineMap[line]
			addDescriptionLine(tooltip, build, statSet, line, stat, i, stat and altQualityStatColor[stat])
		end
	end
end

local function addEffectStats(tooltip, build, gemInstance, grantedEffect, noLabel, levelRange)
	for idx, statSet in ipairs(grantedEffect.statSets) do
		addStatSetInfo(tooltip, build, gemInstance, grantedEffect, statSet, noLabel, idx, levelRange)
	end
end

local function addQualityRangeInfo(tooltip, build, grantedEffect, addedHeader, includeAltQualityStats)
	-- Quality ranges are tree-only. SkillsTab shows the 20 quality value separately, but tree nodes need the 0-20 range inline.
	local qualityStats = { }
	for _, stat in ipairs(grantedEffect.qualityStats or { }) do
		qualityStats[#qualityStats + 1] = { stat = stat[1], value = stat[2], statSetIndexes = stat[3], color = colorCodes.MAGIC }
	end
	if includeAltQualityStats then
		for _, stat in ipairs(grantedEffect.altQualityStats or { }) do
			qualityStats[#qualityStats + 1] = { stat = stat[1], value = stat[2], statSetIndexes = stat[3], color = colorCodes.ENCHANTED }
		end
	end
	if #qualityStats == 0 then
		return addedHeader
	end
	local fontSizeBig = getFontSizes()
	local lineIndex = 1
	for _, stat in ipairs(qualityStats) do
		if stat.stat and stat.value then
			local stats = { [stat.stat] = 20 * stat.value }
			local statSet = grantedEffect.statSets[(stat.statSetIndexes[1] or 0) + 1] or grantedEffect.statSets[1]
			local descriptions, lineMap = build.data.describeStats(stats, statSet.statDescriptionScope, true, UILocale.gemStatTemplate, stat.stat)
			for _, line in ipairs(descriptions) do
				local statName = lineMap[line] or stat.stat
				if not addedHeader then
					tooltip:AddLine(fontSizeBig, "\n^7" .. UILocale.gemText("ItemDescriptionGemQualityStatDivider", "Additional Effects From Quality:"), "FONTIN SC")
					addedHeader = true
				end
				addDescriptionLine(tooltip, build, statSet, line, statName, lineIndex, stat.color)
				lineIndex = lineIndex + 1
			end
		end
	end
	return addedHeader
end

function GemTooltip.AddGemTooltip(tooltip, build, gemInstance, options)
	options = options or { }
	local fontSizeBig, fontSizeTitle = getFontSizes()
	local levelRange = options.levelRange
	tooltip.center = false
	tooltip.color = colorCodes.GEM
	tooltip.minWidth = 600
	tooltip.maxWidth = m_min(tooltip.maxWidth or 600, 600)
	tooltip.tooltipHeader = "GEM"
	tooltip.gemIcon = gemInstance.gemData.grantedEffect.icon
	tooltip.gemBackground = gemInstance.gemData.grantedEffect.id

	local grantedEffect = gemInstance.gemData.grantedEffect
	local additionalEffects = gemInstance.gemData.additionalGrantedEffects

	if grantedEffect.isLineage then
		tooltip.isUniqueGem = true
	end

	local iconNameIndent = "            "
	local iconTagIndent = "                  "
	if grantedEffect.support then
		iconNameIndent = "    "
	 	iconTagIndent = "      "
	end

	if grantedEffect.name:match("^Spectre:") or grantedEffect.name:match("^Companion:") then
		tooltip:AddLine(fontSizeTitle, colorCodes.GEM .. iconNameIndent .. UILocale.skillDisplayName(grantedEffect, (gemInstance.displayEffect and gemInstance.displayEffect.nameSpec) or UILocale.gemName(gemInstance.gemData), gemInstance.skillMinion), "FONTIN SC")
	else
		tooltip:AddLine(fontSizeTitle, colorCodes.GEM .. iconNameIndent .. UILocale.gemName(gemInstance.gemData), "FONTIN SC")
	end
	tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. iconTagIndent .. (grantedEffect.support and UILocale.gemText("GemStashFilterGreen", gemInstance.gemData.gemType) or UILocale.gemTags(gemInstance.gemData.gemType)), "FONTIN SC")
	tooltip:AddSeparator(8)
	if grantedEffect.legacy then
		tooltip:AddLine(fontSizeBig, colorCodes.WARNING .. "   Legacy Gem", "FONTIN SC")
		tooltip:AddLine(fontSizeBig, colorCodes.WARNING .. "   Gem only exists in Standard League", "FONTIN SC")
	end
	if gemInstance.gemData.tagString ~= "" then
		tooltip:AddLine(fontSizeBig, "   ^x7F7F7F" .. UILocale.gemTags(gemInstance.gemData.tagString), "FONTIN")
	end
	if gemInstance.gemData.gemFamily then
		tooltip:AddLine(fontSizeBig, colorCodes.GEMINFO .. "   " .. UILocale.translate("Category:") .. " ^7" .. UILocale.gemFamily(gemInstance.gemData.gemFamily), "FONTIN SC")
	end
	-- Default mode preserves the old GemSelectControl tooltip. levelRange is only for passive-tree granted skills.
	addGrantedEffectInfo(tooltip, build, gemInstance, grantedEffect, true, levelRange)
	addEffectStats(tooltip, build, gemInstance, grantedEffect, nil, levelRange)

	for _, additional in ipairs(additionalEffects or { }) do
		if not additional.support then
			if additional.name ~= "" then
				tooltip:AddSeparator(10)
				tooltip:AddLine(fontSizeTitle, colorCodes.GEM .. UILocale.effectName(additional), "FONTIN SC")
			end
			tooltip:AddSeparator(10)
			addGrantedEffectInfo(tooltip, build, gemInstance, additional, nil, levelRange)
			addEffectStats(tooltip, build, gemInstance, additional, nil, levelRange)
		else
			addEffectStats(tooltip, build, gemInstance, additional, true, levelRange)
		end
	end

	if options.includeQualityRange then
		local addedHeader
		local includeAltQualityStats = build.calcsTab.mainEnv.modDB:Flag(nil, "GemlingQuality")
		addedHeader = addQualityRangeInfo(tooltip, build, grantedEffect, addedHeader, includeAltQualityStats)
		for _, effect in ipairs(additionalEffects or { }) do
			addedHeader = addQualityRangeInfo(tooltip, build, effect, addedHeader, includeAltQualityStats)
		end
	end

	if grantedEffect.flavourText and main.showFlavourText then
		tooltip:AddSeparator(10)
		for _, line in ipairs(UILocale.effectFlavourText(grantedEffect)) do
			tooltip:AddLine(fontSizeBig, colorCodes.UNIQUE .. line, "FONTIN SC ITALIC")
		end
	end
end

return GemTooltip
