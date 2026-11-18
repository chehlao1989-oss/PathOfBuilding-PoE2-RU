-- Path of Building
--
-- Class: Calc Section Control
-- Section control used in the Calcs tab
--
local t_insert = table.insert

local CalcSectionClass = newClass("CalcSectionControl", "Control", "ControlHost", function(self, calcsTab, width, id, group, colour, subSection, updateFunc)
	self.Control(calcsTab, {0, 0, width, 0})
	self.ControlHost()
	self.calcsTab = calcsTab
	self.id = id
	self.group = group
	self.colour = colour
	self.width = width
	self.subSection = subSection
	self.flag = subSection[1].data.flag
	self.notFlag = subSection[1].data.notFlag
	self.updateFunc = updateFunc

	for i, subSec in ipairs(self.subSection) do
		subSec.id = subSec.label:gsub("%W", "")

		for _, data in ipairs(subSec.data) do
			for _, colData in ipairs(data) do
				if colData.control then
					-- Add control to the section's control list and set show/hide function
					self.controls[colData.controlName] = colData.control
					colData.control.shown = function()
						return self.enabled and not self.subSection[1].collapsed and not subSec.collapsed and data.enabled
					end
				end
			end
		end
		subSec.collapsed = subSec.defaultCollapsed
		self.controls["toggle"..i] = new("ButtonControl", {"TOPRIGHT",self,"TOPRIGHT"}, {-3, -13 + (16 * i), 16, 16}, function()
			return subSec.collapsed and "+" or "-"
		end, function()
			subSec.collapsed = not subSec.collapsed
			self.calcsTab.modFlag = true
		end)
		if i == 1 then
			self.controls["toggle"..i].shown = function()
				return self.enabled
			end
		else
			self.controls["toggle"..i].shown = function()
				return self.enabled and not self.subSection[1].collapsed
			end
		end
	end
	self.shown = function()
		return self.enabled
	end
end)

function CalcSectionClass:IsMouseOver()
	if not self:IsShown() then
		return
	end
	if self:GetMouseOverControl() then
		return true
	end
	local mOver = self:IsMouseInBounds()
	for _, subSec in ipairs(self.subSection) do
		if mOver and not subSec.collapsed and self.enabled then
			-- Check if mouse is over one of the cells
			local cursorX, cursorY = GetCursorPos()
			for _, data in ipairs(subSec.data) do
				if data.enabled then
					for _, colData in ipairs(data) do
						if colData.control then
						if colData.control:IsMouseOver() then
							return mOver, colData
						end
					elseif cursorX >= colData.x and cursorY >= colData.y and cursorX < colData.x + colData.width and cursorY < colData.y + colData.height then
						return mOver, colData
					end
				end
				end
			end
		end
	end
	return mOver
end

local function layoutHeading(subSec, actor, width, top)
	local title = UILocale.translate(subSec.label .. ":")
	local titleWidth = UILocale.measureRaw(16, "VAR BOLD", title)
	local titleText, titleLines = UILocale.wrap(subSec, title, 16, "VAR BOLD", width)
	local heading = { title = titleText, y = top, height = titleLines * 16 + 6 }
	if subSec.data.extra then
		local summary = "^7"..formatCalcStr(UILocale.translate(subSec.data.extra), actor)
		local summaryWidth = DrawStringWidth(14, "VAR", summary)
		if titleLines == 1 and titleWidth + 6 + summaryWidth <= width then
			heading.summaryX = 4 + titleWidth + 6
			heading.summaryY = top + 4
			heading.summary = UILocale.translate(summary)
		else
			local text, lines = UILocale.wrap(subSec.data, summary, 14, "VAR", width)
			heading.summaryX = 4
			heading.summaryY = top + titleLines * 16 + 3
			heading.summary = text
			heading.height = heading.height + lines * 14
		end
	end
	return heading
end

function CalcSectionClass:UpdateSize()
	self.enabled = false
	self.height = 0
	if not self.calcsTab:CheckFlag(self) then
		return
	end

	for _, subSec in ipairs(self.subSection) do
		for _, row in ipairs(subSec.data) do
			local eligible = self.calcsTab:CheckFlag(row)
			self.enabled = self.enabled or eligible
			row.enabled = eligible and not self.subSection[1].collapsed and not subSec.collapsed
		end
	end
	if not self.enabled then
		return
	end
	if self.updateFunc and not self.subSection[1].collapsed then
		self:updateFunc()
	end

	local actor = self.calcsTab.input.showMinion and self.calcsTab.calcsEnv.minion or self.calcsTab.calcsEnv.player
	local top = 0
	for index, subSec in ipairs(self.subSection) do
		subSec.heading = layoutHeading(subSec, actor, self.width - 29, top)
		self.controls["toggle"..index].y = top + 3
		top = top + subSec.heading.height

		local columns, labelWidth = 1, 0
		for _, row in ipairs(subSec.data) do
			if row.enabled then
				columns = math.max(columns, #row)
				if row.label then
					labelWidth = math.max(labelWidth, DrawStringWidth(14, "VAR", row.label .. ":") + 12)
				end
			end
		end
		labelWidth = math.min(labelWidth, math.floor(self.width * (columns == 1 and 0.61 or 0.34)))
		subSec.labelWidth = labelWidth

		for _, row in ipairs(subSec.data) do
			if row.enabled then
				row.y = top
				row.height = 18
				if row.label then
					local text, lines = UILocale.wrap(row, row.label .. ":", 14, "VAR", labelWidth - 10)
					row.labelText = text
					row.height = math.max(row.height, lines * 14 + 4)
				end

				for column, cell in ipairs(row) do
					local valueWidth = self.width - labelWidth - 4
					local left = math.floor(valueWidth * (column - 1) / columns)
					local right = math.floor(valueWidth * column / columns)
					cell.xOffset = 2 + labelWidth + left
					cell.yOffset = top
					cell.width = right - left
					if cell.control then
						local control = cell.control
						cell.controlWidth = cell.controlWidth or control:GetProperty("width")
						local width = math.min(cell.controlWidth, cell.width - 8)
						if control.width ~= width then
							control.width = width
							if control.CheckDroppedWidth then
								control:CheckDroppedWidth(control.enableDroppedWidth)
							end
						end
						row.height = math.max(row.height, control:GetProperty("height") + 4)
					elseif cell.format and self.calcsTab:CheckFlag(cell) then
						local size = row.textSize or 14
						local text = formatCalcStr(cell.format, actor, cell)
						if cell.format == "{output:BuffList}" then text = UILocale.effectList(text) end
						local wrapped, lines = UILocale.wrap(cell, text, size, "VAR", cell.width - 8)
						cell.displayText = wrapped
						row.height = math.max(row.height, lines * size + 4)
					else
						cell.displayText = nil
					end
				end
				for _, cell in ipairs(row) do
					cell.height = row.height
				end
				top = top + row.height
			end
		end
		if self.subSection[1].collapsed then
			break
		end
	end
	self.height = top + 2
end

function CalcSectionClass:UpdatePos()
	if not self.enabled then
		return
	end
	local x, y = self:GetPos()
	for _, subSec in ipairs(self.subSection) do
		for _, rowData in ipairs(subSec.data) do
			if rowData.enabled then
				for colour, colData in ipairs(rowData) do
					-- Update the real coordinates of this cell
					colData.x = x + colData.xOffset
					colData.y = y + colData.yOffset
				if colData.control then
					colData.control.x = colData.x + 4
					colData.control.y = colData.y + math.floor((colData.height - colData.control:GetProperty("height")) / 2)
				end
			end
			end
		end
	end
end

function CalcSectionClass:FormatVal(val, p)
	return formatNumSep(tostring(round(val, p)))
end

function CalcSectionClass:FormatStr(str, actor, colData)
	str = str:gsub("{output:([%a%.:]+)}", function(c) 
		local ns, var = c:match("^(%a+)%.(%a+)$")
		if ns then
			return actor.output[ns] and actor.output[ns][var] or ""
		else
			return actor.output[c] or ""
		end
	end)
	str = str:gsub("{(%d+):output:([%a%.:]+)}", function(p, c) 
		local ns, var = c:match("^(%a+)%.(%a+)$")
		if ns then
			return self:FormatVal(actor.output[ns] and actor.output[ns][var] or 0, tonumber(p))
		else
			return self:FormatVal(actor.output[c] or 0, tonumber(p))
		end
	end)
	str = str:gsub("{(%d+):mod:([%d,]+)}", function(p, n)
		local numList = { }
		for num in n:gmatch("%d+") do
			t_insert(numList, tonumber(num))
		end
		local modType = colData[numList[1]].modType
		local modTotal = modType == "MORE" and 1 or 0
		for _, num in ipairs(numList) do
			local sectionData = colData[num]
			local modCfg = (sectionData.cfg and actor.mainSkill[sectionData.cfg.."Cfg"]) or { }
			if sectionData.modSource then
				modCfg.source = sectionData.modSource
				modCfg.ignoreSourceInCheckConditions = true
			end
			if sectionData.actor then
				modCfg.actor = sectionData.actor
			end
			local modVal
			local modStore = (sectionData.enemy and actor.enemy.modDB) or (sectionData.cfg and actor.mainSkill.skillModList) or actor.modDB
			if type(sectionData.modName) == "table" then
				modVal = modStore:Combine(sectionData.modType, modCfg, unpack(sectionData.modName))
			else
				modVal = modStore:Combine(sectionData.modType, modCfg, sectionData.modName)
			end
			if modType == "MORE" then
				modTotal = modTotal * modVal
			else
				modTotal = modTotal + modVal
			end
		end
		if modType == "MORE" then
			modTotal = (modTotal - 1) * 100
		end
		return self:FormatVal(modTotal, tonumber(p)) 
	end)
	return str
end

function CalcSectionClass:Draw(viewPort, noTooltip)
	local x, y = self:GetPos()
	local width, height = self:GetSize()
	if y + height <= viewPort.y or y >= viewPort.y + viewPort.height then
		return
	end
	local cursorX, cursorY = GetCursorPos()
	SetDrawLayer(nil, -10)
	SetDrawColor(self.colour)
	DrawImage(nil, x, y, width, height)
	SetDrawColor(0.10, 0.10, 0.10)
	DrawImage(nil, x + 2, y + 2, width - 4, height - 4)

	for _, subSec in ipairs(self.subSection) do
		local heading = subSec.heading
		local top = y + heading.y
		SetDrawColor(self.colour)
		DrawImage(nil, x + 2, top, width - 4, 2)
		DrawImage(nil, x + 2, top + heading.height - 2, width - 4, 2)
		local titleColor = self.calcsTab:SearchMatch(subSec.label) and colorCodes.HIGHLIGHT or "^7"
		UILocale.drawRaw(x + 4, top + 3, "LEFT", 16, "VAR BOLD", titleColor..heading.title)
		if heading.summary then
			UILocale.drawRaw(x + heading.summaryX, y + heading.summaryY, "LEFT", 14, "VAR", heading.summary)
		end
		for _, row in ipairs(subSec.data) do
			local rowY = row.enabled and y + row.y
			if rowY and rowY + row.height > viewPort.y and rowY < viewPort.y + viewPort.height then
				if row.label then
					SetDrawColor(row.bgCol or "^0")
					DrawImage(nil, x + 2, rowY, subSec.labelWidth, row.height)
					local color = self.calcsTab:SearchMatch(row.label) and colorCodes.HIGHLIGHT or row.color or "^7"
					UILocale.drawRaw(x + subSec.labelWidth - 3, rowY + 2, "RIGHT_X", 14, "VAR", color..row.labelText)
				end
				for _, cell in ipairs(row) do
					SetDrawColor(self.colour)
					DrawImage(nil, cell.x, rowY, 2, row.height)
					if cell.displayText then
						if cursorY >= viewPort.y and cursorY < viewPort.y + viewPort.height
							and cursorX >= cell.x and cursorY >= cell.y
							and cursorX < cell.x + cell.width and cursorY < cell.y + cell.height then
							self.calcsTab:SetDisplayStat(cell)
						end
						SetDrawColor(row.bgCol or "^0")
						DrawImage(nil, cell.x + 2, rowY, cell.width - 2, row.height)
						if self.calcsTab.displayData == cell then
							SetDrawColor(0.25, 1, 0.25)
							DrawImage(nil, cell.x + 2, rowY, cell.width - 2, row.height)
							SetDrawColor(row.bgCol or "^0")
							DrawImage(nil, cell.x + 3, rowY + 1, cell.width - 4, row.height - 2)
						end
						UILocale.drawRaw(cell.x + 4, rowY + 2, "LEFT", row.textSize or 14, "VAR", "^7"..cell.displayText)
					end
				end
			end
		end
		if self.subSection[1].collapsed then
			break
		end
	end
	SetDrawLayer(nil, 0)
	self:DrawControls(viewPort, noTooltip and self.calcsTab.selControl)
end

function CalcSectionClass:OnKeyDown(key, doubleClick)
	if not self:IsShown() or not self:IsEnabled() then
		return
	end
	local mOverControl = self:GetMouseOverControl()
	if mOverControl and mOverControl.OnKeyDown then
		return mOverControl:OnKeyDown(key)
	end
	local mOver, mOverComp = self:IsMouseOver()
	if key:match("BUTTON") then
		if not mOver then
			return
		end
		if mOverComp then
			-- Pin the stat breakdown
			self.calcsTab:SetDisplayStat(mOverComp, true)
			return self.calcsTab.controls.breakdown
		end
	end
	return
end

function CalcSectionClass:OnKeyUp(key)
	if not self:IsShown() or not self:IsEnabled() then
		return
	end
	local mOverControl = self:GetMouseOverControl()
	if mOverControl and mOverControl.OnKeyUp then
		return mOverControl:OnKeyUp(key)
	end
	return
end