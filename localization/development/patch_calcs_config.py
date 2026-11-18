def replace_region(source, start, end, replacement):
    first = source.index(start)
    last = source.index(end, first)
    return source[first:last], replacement


def patch_calcs_config(edit, baseline):
    edit("Modules/ConfigOptions.lua", [
        ('tooltip:AddLine(14, [[', 'tooltip.maxWidth = 560\n\t\ttooltip:AddLine(14, UILocale.configText([['),
        ('needed]])', 'needed]]))'),
        ('..value.val..": "..data.bossSkills[value.val].tooltip',
         '..UILocale.configText(value.label)..": "..UILocale.configText(data.bossSkills[value.val].tooltip)'),
        ('''	local out = 'You will automatically be considered to be on Low ^xE05030Life ^7if you have at least '..100 - build.calcsTab.mainOutput.LowLifePercentage..'% ^xE05030Life ^7reserved'
	out = out..'\\nbut you can use this option to force it if necessary.'
	return out''',
         '''	return UILocale.format("You will automatically be considered to be on Low Life if you have at least %s%% Life reserved. You can force it here.",
		100 - build.calcsTab.mainOutput.LowLifePercentage)'''),
        ('''	local out = 'You can be considered to be on Full ^xE05030Life ^7if you have at least '..build.calcsTab.mainOutput.FullLifePercentage..'% ^xE05030Life ^7left.'
	out = out..'\\nYou will automatically be considered to be on Full ^xE05030Life ^7if you have Chaos Inoculation,'
	out = out..'\\nbut you can use this option to force it if necessary.'
	return out''',
         '''	return UILocale.format("PoB can use the Full Life condition when at least %s%% Life remains. Chaos Inoculation enables it automatically. You can also force it here.",
		build.calcsTab.mainOutput.FullLifePercentage)'''),
        ('table.insert(listOptions, { label = option, val = option })',
         '''local firstLine = option:match("^[^\\r\\n]+") or option
				table.insert(listOptions, { label = firstLine, val = option })'''),
    ])

    edit("Classes/CheckBoxControl.lua", [
        ('\t-- move x left by label width, increase width by label width',
         '''	if self.configLabel and self.configLabel:IsMouseInBounds() then
		return true
	end
	-- move x left by label width, increase width by label width'''),
    ])

    control_path = "Classes/CalcSectionControl.lua"
    control = (baseline / control_path).read_text(encoding="utf-8")
    edit(control_path, [
        replace_region(control, "function CalcSectionClass:UpdateSize()", "function CalcSectionClass:UpdatePos()", '''local function layoutHeading(subSec, actor, width, top)
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

'''),
        ('colData.control.y = colData.y + 9 - colData.control.height/2',
         'colData.control.y = colData.y + math.floor((colData.height - colData.control:GetProperty("height")) / 2)'),
        replace_region(control, "function CalcSectionClass:Draw(", "function CalcSectionClass:OnKeyDown(", '''function CalcSectionClass:Draw(viewPort, noTooltip)
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

'''),
    ])

    calcs_path = "Classes/CalcsTab.lua"
    calcs = (baseline / calcs_path).read_text(encoding="utf-8")
    edit(calcs_path, [
        ('local m_max = math.max', "local utf8 = require('lua-utf8')\nlocal m_max = math.max"),
        ('{0, 0, 100, 16}, buffModeDropList', '{0, 0, 170, 16}, buffModeDropList'),
        replace_region(calcs, "\t-- Arrange the sections\n", "\tself.controls.scrollBar.height", '''	-- Keep offense and defense in separate columns when there is room.
	local baseX = viewPort.x + 4
	local baseY = viewPort.y + 30
	local available = viewPort.width - 26
	local gap = 8
	local columns = m_max(1, math.min(5, m_floor((available + gap) / (256 + gap))))
	local columnWidth = m_floor((available - (columns - 1) * gap) / columns)
	local bottoms = {}
	for column = 1, columns do
		bottoms[column] = baseY
	end
	local maxY = baseY
	for _, section in ipairs(self.sectionList) do
		local first, last = 1, columns
		if columns >= 4 then
			if section.group == 1 then
				last = columns - 2
			else
				first = columns - 4 + section.group + 1
				last = first
			end
		end
		local span = math.min(section.widthCols, last - first + 1)
		section.width = span * columnWidth + (span - 1) * gap
		section:UpdateSize()
		if section.enabled then
			local column, top = first, math.huge
			for start = first, last - span + 1 do
				local candidate = bottoms[start]
				for occupied = start + 1, start + span - 1 do
					candidate = m_max(candidate, bottoms[occupied])
				end
				if candidate < top then
					column, top = start, candidate
				end
			end
			section.x = baseX + (column - 1) * (columnWidth + gap)
			section.y = top
			local bottom = top + section.height + gap
			for occupied = column, column + span - 1 do
				bottoms[occupied] = bottom
			end
			maxY = m_max(maxY, bottom)
		end
	end
'''),
        ('section.y = section.y - self.controls.scrollBar.offset\n\t\tsection:UpdatePos()',
         'if section.enabled then\n\t\t\tsection.y = section.y - self.controls.scrollBar.offset\n\t\t\tsection:UpdatePos()\n\t\tend'),
        ('local searchStr = self.controls.search.buf:lower()\n\treturn string.len(searchStr) > 0 and txt:lower():find(searchStr)',
         '''local search = utf8.lower(self.controls.search.buf)
	return search ~= "" and (utf8.lower(txt):find(search, 1, true)
		or utf8.lower(StripEscapes(UILocale.translate(txt .. ":"))):find(search, 1, true))'''),
    ])

    config_path = "Classes/ConfigTab.lua"
    config = (baseline / config_path).read_text(encoding="utf-8")
    edit(config_path, [
        ('local s_upper = string.upper', "local s_upper = string.upper\nlocal utf8 = require('lua-utf8')"),
        ('\n\tlocal function searchMatch(varData)', '\n\tUILocale.fitButton(self.controls.setManage)\n\tUILocale.fitButton(self.controls.toggleConfigs)\n\n\tlocal function searchMatch(varData)'),
        ('self.controls.search.buf:lower():gsub', 'utf8.lower(self.controls.search.buf):gsub'),
        ('''local label = StripEscapes(varData.label or ""):lower()
			local err, match = PCall(string.matchOrPattern, label, searchStr)''',
         '''local source = varData.label or ""
			local label = utf8.lower(StripEscapes(source))
			local localized = utf8.lower(StripEscapes(UILocale.configText(source)))
			local err, match = PCall(function()
				return string.matchOrPattern(label, searchStr) or string.matchOrPattern(localized, searchStr)
			end)'''),
        replace_region(config, '\t\t\tlastSection.height = function(self)', '\t\t\tt_insert(self.sectionList, lastSection)', ''),
        ('''			if varData.inactiveText then''', '''			if varData.type == "list" then
				control.displayLabelAccessor = function(option) return UILocale.configText(option.label) end
				control.localizedSearchAccessor = control.displayLabelAccessor
			end

			if varData.inactiveText then'''),
        ('out = (out and out .. "\\n" or "") .. curTooltipText',
         'out = (out and out .. "\\n" or "") .. UILocale.configText(curTooltipText)'),
        ('''return "This option is specific to '"..self.build.spec.nodes[ifOption].dn.."'."''',
         '''local node = self.build.spec.nodes[ifOption]
					local name = node and UILocale.passiveName(self.build.spec.treeVersion, node) or tostring(ifOption)
					return UILocale.format("This option is specific to '%s'.", name)'''),
        ('labelControl.label = function()\n', 'labelControl.label = function()\n\t\t\t\t\tlocal text = type(innerLabel) == "function" and innerLabel() or innerLabel\n'),
        ('return colorCodes.NEGATIVE..StripEscapes(innerLabel)', 'return colorCodes.NEGATIVE..StripEscapes(text)'),
        ('\t\t\t\t\treturn innerLabel\n', '\t\t\t\t\treturn text\n'),
        ('tooltip:AddLine(14, tooltipText)', 'tooltip.maxWidth = 560\n\t\t\t\t\t\t\ttooltip:AddLine(14, tooltipText)'),
        ('{234, 0, 18}, varData.label, function(state)', '{234, 0, 18}, nil, function(state)'),
        ('''if varData.label and varData.type ~= "check" then
				labelControl = new("LabelControl", {"RIGHT",control,"LEFT"}, {-4, 0, 0, DrawStringWidth(14, "VAR", varData.label) > 228 and 12 or 14}, "^7"..varData.label)
				t_insert(self.controls, labelControl)
			end''',
         '''if varData.label then
				labelControl = new("LabelControl", {"TOPLEFT",lastSection,"TOPLEFT"}, {8, 0, 0, 14},
					function() return "^7" .. UILocale.configText(varData.label) end)
				labelControl:SetWrapWidth(220)
				labelControl.wrapAlign = "RIGHT_X"
				labelControl.shown = function()
					return control:IsShown()
				end
				control.configLabel = labelControl
				t_insert(self.controls, labelControl)
			end
			control.configType = varData.type'''),
        replace_region(config, "\tlocal maxCol = m_floor((viewPort.width", "\tlocal newSetList", '''	local inset, gap = 10, 10
	local available = viewPort.width - 38
	local columns = m_max(1, math.min(3, m_floor((available + gap) / 370)))
	local sectionWidth = math.min(480, m_floor((available - (columns - 1) * gap) / columns))
	local bottoms = { 0, 0, 0 }
	local maxColY = 0
	local controls = self.controls
	controls.setSelect.x = m_max(76, controls.setLabel:GetProperty("width") + 12)
	controls.setSelect.width = m_min(210, available - controls.setSelect.x - controls.setManage:GetProperty("width"))
	controls.search.width = m_min(sectionWidth, available - inset - gap - controls.toggleConfigs:GetProperty("width"))

	for _, section in ipairs(self.sectionList) do
		section.shown = true
		local y = 15
		local fieldWidth = math.max(118, m_floor(sectionWidth * 0.34))
		local fieldX = sectionWidth - fieldWidth - 8
		for _, control in ipairs(section.varControlList) do
			if control:IsShown() then
				local label = control.configLabel
				local fullWidth = control.configType == "text"
				control.x = fullWidth and 8 or fieldX
				if fullWidth then
					control.width = sectionWidth - 16
					if control.minWidth then
						control.minWidth = control.width
						control.maxWidth = control.width
					end
				elseif control.configType == "list" then
					if control.width ~= fieldWidth or control.layoutLanguage ~= UILocale.language then
						control.width = fieldWidth
						control.layoutLanguage = UILocale.language
						control.droppedLabelPadding = 24
						control.fitSelectedLabel = true
						control.maxDroppedWidth = 480
						control:CheckDroppedWidth(true)
					end
				end
				local height = control:GetProperty("height")
				if label then
					label.wrapWidth = (fullWidth and sectionWidth or fieldX) - 16
					label.width = label.wrapWidth
					local labelHeight = label:GetProperty("height")
					if fullWidth then
						label.y = y
						y = y + labelHeight + 4
					else
						local rowHeight = m_max(height, labelHeight)
						label.y = y + m_floor((rowHeight - labelHeight) / 2)
						control.y = y + m_floor((rowHeight - height) / 2)
						y = y + rowHeight + 4
					end
				end
				if fullWidth or not label then
					control.y = y
					y = y + height + 4
				end
			end
		end
		section.shown = y > 15
		if section.shown then
			section.width = sectionWidth
			section.height = y + 3
			local column = section.col
			if not column or column > columns or bottoms[column] + section.height + 78 > viewPort.height then
				column = 1
				for candidate = 2, columns do
					if bottoms[candidate] < bottoms[column] then
						column = candidate
					end
				end
			end
			section.x = inset + (column - 1) * (sectionWidth + gap)
			section.y = bottoms[column] + 18
			bottoms[column] = section.y + section.height
			maxColY = m_max(maxColY, bottoms[column])
		end
	end

'''),
    ])
