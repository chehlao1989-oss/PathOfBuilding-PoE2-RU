local work = os.getenv("POB_FIXTURE_ROOT")
dofile(work .. "/verify_pob.lua")

local utf8 = require("lua-utf8")
UILocale.measureRaw = function(height, _, text)
	local width = 0
	for line in (tostring(text or "") .. "\n"):gmatch("(.-)\n") do
		width = math.max(width, utf8.len((StripEscapes(line))) * height * 0.55)
	end
	return width
end

local function right(control)
	return control:GetPos() + control:GetProperty("width")
end

local function bottom(control)
	return select(2, control:GetPos()) + control:GetProperty("height")
end

local function textFits(text, size, font, width)
	for line in (text .. "\n"):gmatch("(.-)\n") do
		local actual = UILocale.measureRaw(size, font, line)
		assert(actual <= width, line .. ": " .. actual .. " > " .. width)
	end
end

local items = build.itemsTab
local skills = build.skillsTab
local calcs = build.calcsTab
local config = build.configTab
local viewport = { x = 312, y = 40, width = 1600, height = 740 }

local savedName, savedFile, savedWidth = build.buildName, build.dbFileName, main.screenW
local drawRaw = UILocale.drawRaw
local captured
UILocale.drawRaw = function(_, _, _, _, _, text)
	captured[#captured + 1] = text
end
for _, language in ipairs({ "ru", "en" }) do
	UILocale.setLanguage(language)
	for _, width in ipairs({ 1920, 1282 }) do
		main.screenW = width
		for _, name in ipairs({ "Unnamed build", "Save", ("Длинное имя билда "):rep(8) }) do
			build.buildName = name
			build.dbFileName = name ~= "Unnamed build" and "test-fixture.xml"
			local header = build.controls.buildName
			local x, y = header:GetPos()
			if width == 1920 then
				assert(y == 4 and x >= right(build.controls.saveAs) + 8)
				assert(right(header) <= build.controls.pointDisplay:GetPos() - 8)
			else
				assert(x >= 4 and right(header) <= 304 and bottom(header) <= select(2, build.anchorSideBar:GetPos()))
			end
			captured = {}
			header:Draw()
			assert(captured[1] == (language == "ru" and "Текущий билд:" or "Current build:"))
			assert(captured[2] == (name == "Unnamed build" and language == "ru" and "Безымянный билд" or name))
		end
	end
end
UILocale.drawRaw = drawRaw
build.buildName, build.dbFileName, main.screenW = savedName, savedFile, savedWidth

for _, language in ipairs({ "ru", "en" }) do
	UILocale.setLanguage(language)
	for _, width in ipairs({ 1600, 970, 660 }) do
		viewport.width = width
		items:Draw(viewport, {})
		local c = items.controls
		assert(c.setLabel:GetPos() >= viewport.x)
		assert(c.specLabel:GetPos() >= viewport.x)
		assert(right(c.itemList.controls.delete) <= right(c.itemList))
		assert(c.displayItemTip:GetPos() >= viewport.x)
		local _, panelY = c.craftDisplayItem:GetPos()
		local _, setY = c.setSelect:GetPos()
		if width == 1600 then
			assert(panelY == setY)
		else
			assert(panelY >= bottom(c.specSelect) + 15)
			assert(right(c.craftDisplayItem) <= viewport.x + width)
		end
		assert(select(2, c.sharedItemList:GetPos()) >= bottom(c.displayItemTip) + 20)

		calcs:Draw(viewport, {})
		local visible = {}
		for _, section in ipairs(calcs.sectionList) do
			if section.enabled then
				local x, y = section:GetPos()
				assert(x >= viewport.x and right(section) < viewport.x + width)
				for _, other in ipairs(visible) do
					local ox, oy = other:GetPos()
					assert(right(section) <= ox or right(other) <= x or bottom(section) <= oy or bottom(other) <= y, section.id .. " overlaps " .. other.id)
				end
				table.insert(visible, section)
				for _, sub in ipairs(section.subSection) do
					local h = sub.heading
					local headingWidth = section.width - 29
					textFits(h.title, 16, "VAR BOLD", headingWidth)
					if h.summary then
						textFits(h.summary, 14, "VAR", headingWidth - h.summaryX + 4)
						if h.summaryY == h.y + 4 then
							assert(h.summaryX > UILocale.measureRaw(16, "VAR BOLD", h.title) + 4)
						end
					end
					for _, row in ipairs(sub.data) do
						if row.enabled then
							if row.label then
								textFits(row.labelText, 14, "VAR", sub.labelWidth - 10)
							end
							for _, cell in ipairs(row) do
								assert(cell.x + cell.width <= right(section))
								if cell.displayText then
									textFits(cell.displayText, row.textSize or 14, "VAR", cell.width - 8)
								elseif cell.control then
									assert(right(cell.control) <= cell.x + cell.width)
									assert(bottom(cell.control) <= cell.y + cell.height)
								end
							end
						end
					end
					if section.subSection[1].collapsed then break end
				end
			end
		end
		assert(#visible > 10)

		config:Draw(viewport, {})
		for _, section in ipairs(config.sectionList) do
			if section:IsShown() then
				assert(section:GetPos() >= viewport.x and right(section) <= viewport.x + width)
				for _, control in ipairs(section.varControlList) do
					if control:IsShown() then
						assert(right(control) <= right(section) and bottom(control) <= bottom(section))
						local label = control.configLabel
						if label then
							local labelText = label:GetWrappedLabel()
							textFits(labelText, 14, "VAR", label.wrapWidth)
							assert(label:GetPos() >= section:GetPos() + 8)
							assert(right(label) <= control:GetPos() or bottom(label) <= select(2, control:GetPos()))
						end
					end
				end
			end
		end
	end

	skills:Draw(viewport, {})
	local c = skills.controls
	assert(c.setLabel:GetPos() >= viewport.x)
	assert(c.defaultQualityLabel:GetPos() >= c.optionSection:GetPos() + 8)
	assert(right(c.defaultLevel) <= right(c.optionSection) - 8)
	assert(select(2, c.optionSection:GetPos()) >= bottom(c.groupTip) + 8)
	assert(right(c.groupSlotLabel) + 7 <= c.groupSlot:GetPos())
	assert(right(c.gemLevelHeader) < c.gemQualityHeader:GetPos())
	for _, drop in ipairs({ c.sortGemsByDPSFieldControl, c.defaultLevel, c.showSupportGemTypes }) do
		assert(right(drop) <= right(c.optionSection) - 8)
		for _, opt in ipairs(drop.list) do
			local localized = UILocale.translate(opt.label)
			textFits(localized, drop.height - 4, "VAR", drop.width - drop.height - 2)
			if language == "ru" then
				assert(localized ~= opt.label, "Untranslated gem dropdown option " .. opt.label)
			end
		end
	end
end

UILocale.setLanguage("ru")
assert(UILocale.translate("Lineage") == "Династические")
assert(UILocale.translate("MH Total Increased:") == "Общее повышение (осн. рука):")
assert(UILocale.translate("OH Chance to Hit:") == "Шанс попадания (втор. рука):")
assert(UILocale.translate("Act 2: Spires of Deshar") == "Акт 2: Шпили Дешара")
assert(UILocale.translate("Act 3: Azak Bog") == "Акт 3: Болото Азак")
assert(UILocale.translate("Act 3: Venom Crypts") == "Акт 3: Ядовитые крипты")
assert(UILocale.translate("Interlude 2: Khari Crossing") == "Интерлюдия 2: Кхарийский перевал")

config.controls.search:SetText("ЗАРЯДЫ ВЫНОСЛИВОСТИ", true)
config:Draw(viewport, {})
assert(config.varControls.useEnduranceCharges:IsShown())
config.controls.search:SetText("", true)

local rewards = config.varControls["questAct 2Valley of the TitansMedallion"]
assert(not rewards.list[2].label:find("\n"))
assert(rewards.list[2].val:find("\n", 1, true))
rewards:SetSel(2)
assert(config.input["questAct 2Valley of the TitansMedallion"] == rewards.list[2].val)

print("CHECK", "wide and narrow layouts, Russian search and saved dropdown values", "ru/en")
