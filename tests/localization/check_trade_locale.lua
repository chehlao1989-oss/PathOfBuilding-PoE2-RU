local work = assert(os.getenv("POB_FIXTURE_ROOT"))
dofile(work .. "/verify_pob.lua")
local utf8 = require("lua-utf8")
UILocale.measureRaw = function(size, _, text)
	local factor = UILocale.language == "ru" and 0.55 or 0.48
	return utf8.len((StripEscapes(tostring(text or "")))) * size * factor
end
main.screenW, main.screenH = 1282, 906
main.viewPort = { x = 0, y = 0, width = main.screenW, height = main.screenH }
main.api = { authToken = nil }
launch.DownloadPage = function() error("The UI check attempted a network request") end
local weapon = new("Item", "Rarity: RARE\nTrade QA\nConstruct Crossbow")
build.itemsTab:AddItem(weapon)
build.itemsTab:PopulateSlots()
local weaponSlot = build.itemsTab.slots["Weapon 1"]
weaponSlot:SetSelItemId(weapon.id)
local snapshots = {}

local function fits(control, popup, name)
	local x, y = control:GetPos()
	local width, height = control:GetSize()
	local px, py = popup:GetPos()
	local pw, ph = popup:GetSize()
	assert(x >= px and x + width <= px + pw,
		UILocale.language .. " " .. name .. " exceeds popup width " .. x .. "/" .. width .. " vs " .. px .. "/" .. pw)
	assert(y >= py and y + height <= py + ph, name .. " exceeds popup height")
end

for _, language in ipairs({ "en", "ru" }) do
	UILocale.setLanguage(language)
	local trade = new("TradeQuery", build.itemsTab)
	trade.pbRealm = "poe2"
	trade.pbLeague = "Forbidden Rites"
	trade.realmDropList = { "PoE 2" }
	trade.allLeagues.poe2 = { "Forbidden Rites", "Standard" }
	build.itemsTab.leagueDropList = { "Forbidden Rites", "Standard" }
	trade:PriceItem()
	local popup = assert(main.popups[#main.popups])
	for _, field in ipairs({ "setSelect", "poesessidButton", "fetchCountEdit", "StatWeightMultipliersButton",
		"itemSortSelection", "itemSortSelectionLabel", "realm", "realmLabel", "league", "leagueLabel",
		"bestButton1", "uri1", "priceButton1", "updateCurrencyConversion", "close" }) do
		fits(assert(trade.controls[field], field), popup, "Trader " .. field)
	end
	assert(trade.controls.tradeTypeSelection.list[1] == "Instant buyout")
	assert(trade.controls.league:GetSelValue() == "Forbidden Rites")
	if language == "ru" then
		assert(trade.controls.league.displayLabelAccessor("Forbidden Rites") == "Запретные ритуалы")
		for index, slot in ipairs(trade.slotTables) do
			local nameControl = trade.controls["name" .. index]
			local label = StripEscapes(nameControl.label)
			assert(not label:gsub("I", ""):gsub("V", ""):find("%a"), label)
			assert(nameControl:GetPos() + nameControl:GetProperty("width") + 4
				<= trade.controls["bestButton" .. index]:GetPos(), label .. " overlaps search button")
		end
	end
	local oldDraw = UILocale.drawRaw
	local rendered = {}
	UILocale.drawRaw = function(_, _, _, _, _, text) rendered[#rendered + 1] = text end
	popup:Draw(main.viewPort)
	UILocale.drawRaw = oldDraw
	if language == "ru" then
		local text = table.concat(rendered, "\n")
		assert(text:find("Торговля", 1, true))
		assert(text:find("Подбор", 1, true))
		assert(not text:find("Instant buyout", 1, true))
	end
	main:ClosePopup()

	local generator = trade.tradeQueryGenerator
	generator.StartQuery = function(self, slot, options)
		assert(slot == weaponSlot)
		snapshots[language] = options
	end
	local context = { slotTbl = { slotName = "Weapon 1" }, controls = trade.controls }
	generator:RequestQuery(weaponSlot, context, trade.statSortSelectionList, function() end)
	popup = assert(main.popups[#main.popups])
	local c = popup.controls
	for _, field in ipairs({ "includeCorrupted", "includeMirrored", "augmentBehaviour", "augmentBehaviourLabel",
		"maxPrice", "maxPriceType", "maxPriceLabel", "maxLevel", "maxLevelLabel", "sockets", "socketsLabel",
		"sortStatLabel", "sortStatType1", "sortStatType2", "modSelector1", "generateQuery", "cancel" }) do
		fits(assert(c[field], field), popup, "Query " .. field)
	end
	for _, name in ipairs(c.maxPriceType.list) do
		if language == "ru" then assert(not UILocale.translate(name):find("%a"), name) end
	end
	c.augmentBehaviour:SetSel(2)
	assert(c.augmentBehaviour:GetSelValue() == "Keep")
	c.maxPrice:SetText("15", true)
	c.maxPriceType:SetSel(4)
	c.maxLevel:SetText("82", true)
	c.sockets:SetText("2", true)
	assert(#c.modSelector1.list > 1)
	local accuracyIndex
	for index, mod in ipairs(c.modSelector1.list) do
		if mod.label:find("Accuracy Rating", 1, true) then accuracyIndex = index; break end
	end
	assert(accuracyIndex)
	if language == "ru" then
		for _, query in ipairs({ "МЕТКОСТ", "ACCURACY" }) do
			c.modSelector1:OnSearchChar(query)
			assert(c.modSelector1.searchInfos[accuracyIndex].matches, query)
			c.modSelector1:ResetSearch()
		end
	end
	c.modSelector1:SetSel(2)
	c.modSelectorMin1:SetText("7", true)
	c.generateQuery.onClick()
	assert(snapshots[language].maxPriceType == "divine")
	assert(snapshots[language].maxPrice == 15 and snapshots[language].maxLevel == 82)
	assert(snapshots[language].sockets == 2 and snapshots[language].includeRunes)
	assert(generator.lastAugmentBehaviour == "Keep")

	trade:SetStatWeights()
	popup = assert(main.popups[#main.popups])
	local weights = popup.controls
	for _, field in ipairs({ "ListControl", "SliderLabel", "Slider", "SliderValue", "finalise", "cancel", "reset" }) do
		fits(weights[field], popup, "Weights " .. field)
	end
	for index, entry in ipairs(weights.ListControl.list) do
		weights.ListControl:OnSelClick(index, entry)
		fits(weights.Slider, popup, "Weights selected slider " .. entry.stat.label)
		fits(weights.SliderValue, popup, "Weights selected value " .. entry.stat.label)
		if language == "ru" then
			assert(UILocale.translate(entry.label) ~= entry.label, entry.label)
		end
	end
	weights.Slider.tooltip:Draw(600, 200, 140, 16, main.viewPort)
	main:ClosePopup()
end
for _, field in ipairs({ "maxPrice", "maxPriceType", "maxLevel", "sockets", "includeCorrupted", "includeMirrored", "includeRunes" }) do
	assert(snapshots.ru[field] == snapshots.en[field], field)
end
assert(snapshots.ru.requiredMods[1].tradeId == snapshots.en.requiredMods[1].tradeId)
assert(snapshots.ru.requiredMods[1].value == snapshots.en.requiredMods[1].value)
assert(UILocale.tradeCurrencyName("divine") == "Божественная сфера")
assert(UILocale.tradeActionLabel("Whisper", "250 Божественная сфера") == "Сообщение")
print("TRADE", "both screenshot dialogs and weights, bilingual modes and popup bounds passed")
print("TRADE", "currency IDs, rune mode, trade types, required property IDs and numeric query options preserved")
