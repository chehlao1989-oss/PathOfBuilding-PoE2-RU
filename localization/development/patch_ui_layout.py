def patch_layout(edit):
    edit("Classes/LabelControl.lua", [
        ('function LabelClass:Draw()\n\tlocal x, y = self:GetPos()\n\tDrawString(x, y, "LEFT", self:GetProperty("height"), "VAR", self:GetProperty("label"))\nend',
         '''function LabelClass:SetWrapWidth(width)
	self.wrapWidth = width
	self.lineHeight = self:GetProperty("height")
	self.width = width
	self.height = function(control)
		local _, lines = control:GetWrappedLabel()
		return control.lineHeight * lines
	end
end

function LabelClass:GetWrappedLabel()
	return UILocale.wrap(self, self:GetProperty("label"), self.lineHeight, "VAR", self:GetProperty("wrapWidth"))
end

function LabelClass:Draw()
	local x, y = self:GetPos()
	if self.wrapWidth then
		local text = self:GetWrappedLabel()
		if self.wrapAlign == "RIGHT_X" then
			for line in (text .. "\\n"):gmatch("(.-)\\n") do
				UILocale.drawRaw(x + self:GetProperty("width"), y, "RIGHT_X", self.lineHeight, "VAR", line)
				y = y + self.lineHeight
			end
		else
			UILocale.drawRaw(x, y, "LEFT", self.lineHeight, "VAR", text)
		end
	else
		DrawString(x, y, "LEFT", self:GetProperty("height"), "VAR", self:GetProperty("label"))
	end
end'''),
    ])

    edit("Classes/SkillsTab.lua", [
        ('nameSpec:SetText(gemInstance.nameSpec)', 'nameSpec:SetText(UILocale.gemInstanceName(gemInstance))', 2),
        ('\tslot.nameSpec:AddToTabGroup(self.controls.groupLabel)', '''	slot.nameSpec.inactiveText = function(text)
		local gem = self.displayGroup and self.displayGroup.gemList[index]
		return (gem and text == gem.nameSpec and UILocale.gemDisplayName(gem)) or text
	end
	slot.nameSpec:AddToTabGroup(self.controls.groupLabel)'''),
        ('tooltip:AddLine(16, "^7Active Skill #"..index..":")',
         'tooltip:AddLine(16, "^7" .. UILocale.format("Active Skill #%d:", index))'),
        ('tooltip:AddLine(16, "^7Active Skill #" .. index .. "\'s Main Minion Skill:")',
         'tooltip:AddLine(16, "^7" .. UILocale.format("Active Skill #%d\'s Main Minion Skill:", index))'),
        ('skillEffect.srcInstance.nameSpec or skillEffect.grantedEffect.name,',
         'UILocale.gemDisplayName(skillEffect.srcInstance) or UILocale.effectName(skillEffect.grantedEffect),'),
        ('activeEffect.grantedEffect.name,\n\t\t\t\tactiveEffect.level,',
         'UILocale.effectName(activeEffect.grantedEffect),\n\t\t\t\tactiveEffect.level,'),
        ('(gemInstance.grantedEffect and gemInstance.grantedEffect.name) or (gemInstance.gemData and gemInstance.gemData.name) or gemInstance.nameSpec,',
         'UILocale.gemDisplayName(gemInstance),'),
        ('\t\t\t\treason\n\t\t\t))', '\t\t\t\tUILocale.translate(reason)\n\t\t\t))'),
        ('colorCodes.GEM..grantedEffect.name)', 'colorCodes.GEM..UILocale.effectName(grantedEffect))'),
        ('colorCodes.NORMAL.."At +20% Quality:"', 'colorCodes.NORMAL..UILocale.translate("At +20% Quality:")'),
        ('self.build.data.describeStats(stats, statSet.statDescriptionScope, true)',
         'self.build.data.describeStats(stats, statSet.statDescriptionScope, true, UILocale.gemStatTemplate)'),
        ('\t-- Socket group list', '\tUILocale.fitButton(self.controls.setManage)\n\n\t-- Socket group list'),
        ('\t-- Gem options\n\tlocal optionInputsX = 170\n\tlocal optionInputsY = 45', '''	self.controls.groupTip:SetWrapWidth(function() return self.controls.groupList:GetProperty("width") end)

	-- Gem options
	local optionInputsX = 170'''),
        ('{ "TOPLEFT", self.controls.groupList, "BOTTOMLEFT" }, { 0, optionInputsY + 50, 360, 150 }',
         '{ "TOPLEFT", self.controls.groupTip, "BOTTOMLEFT" }, { 0, 14, 360, 150 }'),
        *[
            (
                '{ "TOPLEFT", self.controls.groupList, "BOTTOMLEFT" }, { optionInputsX, optionInputsY + ' + str(old) + ',',
                '{ "TOPLEFT", self.controls.optionSection, "TOPLEFT" }, { optionInputsX, ' + str(new) + ',',
            )
            for old, new in ((70, 20), (94, 44), (118, 68), (142, 92), (166, 116))
        ],
        ('{ "TOPLEFT", self.anchorGroupDetail, "TOPLEFT" }, { 85, 28, 130, 20 }',
         '{ "LEFT", self.controls.groupSlotLabel, "RIGHT" }, { 8, 0, 130, 20 }'),
        ('{ "LEFT", self.controls.groupSlot, "RIGHT" }, { 70, 0, 20 }, "Enabled:"',
         '{ "LEFT", self.controls.groupSlot, "RIGHT" }, { function() return m_max(70, DrawStringWidth(16, "VAR", "Enabled:") + 14) end, 0, 20 }, "Enabled:"'),
        ('{ "LEFT", self.controls.groupEnabled, "RIGHT" }, { 145, 0, 20 }, "Include in Full DPS:"',
         '{ "LEFT", self.controls.groupEnabled, "RIGHT" }, { function() return m_max(145, DrawStringWidth(16, "VAR", "Include in Full DPS:") + 14) end, 0, 20 }, "Include in Full DPS:"'),
        ('{"BOTTOMLEFT", self.gemSlots[1].level, "TOPLEFT"}, {0, -2, 0, 16}, "^7Level:"',
         '{"BOTTOM", self.gemSlots[1].level, "TOP"}, {0, -2, 0, 16}, "^7Level:"'),
        ('{"BOTTOMLEFT", self.gemSlots[1].quality, "TOPLEFT"}, {0, -2, 0, 16}, "^7Quality:"',
         '{"BOTTOM", self.gemSlots[1].quality, "TOP"}, {0, -2, 0, 16}, "^7Quality:"'),
        ('{"BOTTOMLEFT", self.gemSlots[1].enabled, "TOPLEFT"}, {-16, -2, 0, 16}, "^7Enabled:"',
         '{"BOTTOM", self.gemSlots[1].enabled, "TOP"}, {0, -2, 0, 16}, "^7On"'),
        ('{"BOTTOMLEFT", self.gemSlots[1].count, "TOPLEFT"}, {18, -2, 0, 16}, "^7Count:"',
         '{"BOTTOM", self.gemSlots[1].count, "TOP"}, {0, -2, 0, 16}, "^7Count:"'),
        ('{ "LEFT", slot.nameSpec, "RIGHT" }, { 2, 0, 60, 20 }',
         '{ "LEFT", slot.nameSpec, "RIGHT" }, { 6, 0, function() return m_max(60, DrawStringWidth(16, "VAR", "Level:") + 10) end, 20 }'),
        ('{"LEFT",slot.level,"RIGHT"}, {2, 0, 60, 20}',
         '{"LEFT",slot.level,"RIGHT"}, {6, 0, function() return m_max(60, DrawStringWidth(16, "VAR", "Quality:") + 10) end, 20}'),
        ('\t\tlocal maxX = self.controls.gemCountHeader:GetPos() + self.controls.gemCountHeader:GetSize() + 25',
         '''		local maxX = m_max(
			self.controls.groupList:GetPos() + self.controls.groupList:GetProperty("width"),
			self.controls.setManage:GetPos() + self.controls.setManage:GetProperty("width"))
		if self.displayGroup then
			maxX = m_max(maxX, self.controls.gemCountHeader:GetPos() + self.controls.gemCountHeader:GetProperty("width") + 25)
		end'''),
        ('function SkillsTabClass:Draw(viewPort, inputEvents)',
         '''function SkillsTabClass:LayoutLocalizedControls()
	if self.layoutLanguage == UILocale.language then
		return
	end
	self.layoutLanguage = UILocale.language
	local controls = self.controls
	controls.setSelect.x = m_max(76, controls.setLabel:GetProperty("width") + 16)

	local inputX = m_max(170,
		controls.defaultLevelLabel:GetProperty("width") + 16,
		controls.defaultQualityLabel:GetProperty("width") + 16,
		controls.showSupportGemTypesLabel:GetProperty("width") + 16,
		DrawStringWidth(16, "VAR", controls.sortGemsByDPS.label) + 16,
		DrawStringWidth(16, "VAR", controls.showLegacyGems.label) + 16)
	for _, control in ipairs({ controls.sortGemsByDPS, controls.defaultLevel, controls.defaultQuality,
		controls.showSupportGemTypes, controls.showLegacyGems }) do
		control.x = inputX
	end
	local right = inputX
	for _, dropdown in ipairs({ controls.sortGemsByDPSFieldControl, controls.defaultLevel, controls.showSupportGemTypes }) do
		local width = 170
		for _, option in ipairs(dropdown.list) do
			width = m_max(width, DrawStringWidth(dropdown.height - 4, "VAR", option.label) + dropdown.height + 8)
		end
		dropdown.width = width
		dropdown.droppedLabelPadding = 24
		dropdown:CheckDroppedWidth(true)
		local offset = dropdown == controls.sortGemsByDPSFieldControl and controls.sortGemsByDPS.width + 10 or 0
		right = m_max(right, inputX + offset + width)
	end
	controls.groupList.width = m_max(360, right + 12)
	controls.optionSection.width = controls.groupList.width
end

function SkillsTabClass:Draw(viewPort, inputEvents)
	self:LayoutLocalizedControls()'''),
    ])

    edit("Classes/SkillListControl.lua", [
        ('{-4, 0, 70, 18}, "Delete All"', '{-4, 0, 82, 18}, "Delete All"'),
        ('local label = socketGroup.displayLabel or "?"',
         'local label = UILocale.skillGroupName(socketGroup) or "?"\n\t\tif label == "<No active skills>" then label = UILocale.translate(label) end'),
        ('label = colour .. label .. " (Disabled)"',
         'label = colour .. label .. " (" .. UILocale.translate("Disabled") .. ")"'),
        ('local activeLabel = disabled and " (Forced Active)" or " (Active)"',
         'local activeLabel = " (" .. UILocale.translate(disabled and "Forced Active" or "Active") .. ")"'),
        ('label = label .. colorCodes.CUSTOM .. " (FullDPS)"',
         'label = label .. colorCodes.CUSTOM .. " (" .. UILocale.translate("FullDPS") .. ")"'),
    ])

    edit("Classes/ItemsTab.lua", [
        ('local m_max = math.max', 'local m_max = math.max\nlocal itemListTopOffset = 42'),
        ('{20, 20, 360, 308}, self, true)', '{20, itemListTopOffset, 360, 308}, self, true)'),
        ('{20, main.portraitMode and 0 or -20, 120, 20}', '{20, main.portraitMode and 0 or -itemListTopOffset, 120, 20}'),
        ('\t-- Price Items', '\tUILocale.fitButton(self.controls.setManage)\n\n\t-- Price Items'),
        ('\n\tself.sockets = { }', '\n\tUILocale.fitButton(self.controls.specButton)\n\n\tself.sockets = { }'),
        ('\tself.controls.displayItemTip = new("LabelControl",', '\tUILocale.fitButton(self.controls.craftDisplayItem)\n\tUILocale.fitButton(self.controls.newDisplayItem)\n\tself.controls.displayItemTip = new("LabelControl",'),
        ('''		tooltip:AddLine(16, "^7Contains searches from the official trading site to help find")
		tooltip:AddLine(16, "^7similar or better items for this build")''',
         '''		tooltip:AddLine(16, "^7Find similar or better items for this build on the official trade site.")'''),
        ('''	self.controls.displayItemTip = new("LabelControl", {"TOPLEFT",self.controls.craftDisplayItem,"BOTTOMLEFT"}, {0, 8, 100, 16},
[[^7Double-click an item from one of the lists,
or copy and paste an item from in game
(hover over the item and Ctrl+C) to view or edit
the item and add it to your build. You can
also clone an item within Path of Building by
copying and pasting it with Ctrl+C and Ctrl+V.

You can Control + Click an item to equip it, or
drag it onto the slot.  This will also add it to
your build if it's from the unique/template list.
If there's 2 slots an item can go in,
holding Shift will put it in the second.]])
	self.controls.sharedItemList = new("SharedItemListControl", {"TOPLEFT",self.controls.craftDisplayItem, "BOTTOMLEFT"}, {0, 232, 340, 308}, self, true)''',
         '''	self.controls.displayItemTip = new("LabelControl", {"TOPLEFT",self.controls.craftDisplayItem,"BOTTOMLEFT"}, {0, 8, 340, 16},
[[^7Double-click an item to open it. To copy a game item, hover over it in Path of Exile and press Ctrl+C, then paste it here with Ctrl+V. The same shortcuts can duplicate an item within PoB.

Ctrl+click an item or drag it onto a slot to equip it. Hold Shift to use the second compatible slot.]])
	self.controls.displayItemTip:SetWrapWidth(340)
	self.controls.sharedItemList = new("SharedItemListControl", {"TOPLEFT",self.controls.displayItemTip,"BOTTOMLEFT"}, {0, 30, 340, 308}, self, true)'''),
        ('''	if main.portraitMode then
		self.controls.itemList:SetAnchor("TOPRIGHT", self.lastSlot, "BOTTOMRIGHT", 0, 40)
	else
		self.controls.itemList:SetAnchor("TOPLEFT", self.controls.setManage, "TOPRIGHT", 20, 20)
	end
	self.controls.craftDisplayItem:SetAnchor("TOPLEFT", main.portraitMode and self.controls.setManage or self.controls.itemList, "TOPRIGHT", 20, main.portraitMode and 0 or -20)
	self.anchorDisplayItem:SetAnchor("TOPLEFT", main.portraitMode and self.controls.setManage or self.controls.itemList, "TOPRIGHT", 20, main.portraitMode and 0)

''', ''),
        ('function ItemsTabClass:Draw(viewPort, inputEvents)',
         '''function ItemsTabClass:LayoutLocalizedControls(viewPort)
	local controls = self.controls
	if self.layoutLanguage ~= UILocale.language then
		self.layoutLanguage = UILocale.language
		local labelWidth = m_max(84, controls.setLabel:GetProperty("width"), controls.specLabel:GetProperty("width"))
		for _, slot in ipairs(self.orderedSlots) do
			local textWidth = DrawStringWidth(16, "VAR", "^7"..slot.label..":")
			labelWidth = m_max(labelWidth, textWidth - slot.labelOffset)
		end
		local inset = labelWidth + 12
		controls.setSelect.x = inset
		controls.priceDisplayItem.x = inset
		self.slotAnchor.x = inset
	end

	local gap = 20
	local equipmentRight = controls.setManage:GetPos() - self.x + controls.setManage:GetProperty("width")
	local listRight = equipmentRight + gap + controls.itemList:GetProperty("width")
	local sideWidth = self.displayItem and 462 or controls.sharedItemList:GetProperty("width")
	local equipmentBottom = select(2, self.lastSlot:GetPos()) > select(2, controls.specSelect:GetPos())
		and self.lastSlot or controls.specSelect
	local sideAnchor, sidePoint, sideX, sideY

	self.stackItemColumns = main.portraitMode or listRight + gap > viewPort.width
	if self.stackItemColumns then
		controls.itemList:SetAnchor("TOPLEFT", equipmentBottom, "BOTTOMLEFT", 12 - self.slotAnchor.x, 54)
		local databaseHeight = controls.selectDBLabel:IsShown() and 362 or 670
		sideAnchor, sidePoint, sideX, sideY = controls.itemList, "BOTTOMLEFT", 0, databaseHeight + gap
	else
		controls.itemList:SetAnchor("TOPLEFT", controls.setManage, "TOPRIGHT", gap, itemListTopOffset)
		if listRight + gap + sideWidth + gap > viewPort.width then
			sideAnchor, sidePoint, sideX, sideY = equipmentBottom, "BOTTOMLEFT", 12 - self.slotAnchor.x, gap
		else
			sideAnchor, sidePoint, sideX, sideY = controls.itemList, "TOPRIGHT", gap, -itemListTopOffset
		end
	end
	controls.craftDisplayItem:SetAnchor("TOPLEFT", sideAnchor, sidePoint, sideX, sideY)
	self.anchorDisplayItem:SetAnchor("TOPLEFT", sideAnchor, sidePoint, sideX, sideY)
end

function ItemsTabClass:Draw(viewPort, inputEvents)'''),
        ('\tself.height = viewPort.height\n\tself.controls.scrollBarH.width',
         '\tself.height = viewPort.height\n\tself:LayoutLocalizedControls(viewPort)\n\tself.controls.scrollBarH.width'),
        ('\t\tlocal maxX = self.anchorDisplayItem:GetPos() + 462',
         '''		local maxX = m_max(
			self.anchorDisplayItem:GetPos() + (self.displayItem and 462 or 340),
			self.controls.setManage:GetPos() + self.controls.setManage:GetProperty("width") + 4,
			self.controls.itemList:GetPos() + self.controls.itemList:GetProperty("width") + 4)
		if self.controls.sharedItemList:IsShown() then
			local _, listY = self.controls.sharedItemList:GetPos()
			maxY = m_max(maxY, listY + self.controls.sharedItemList:GetProperty("height") + 4)
		end'''),
        ('\t\tself.maxY = h and self.controls.scrollBarH.y or viewPort.y + viewPort.height',
         '\t\tself.maxY = self.stackItemColumns and maxY or (h and self.controls.scrollBarH.y or viewPort.y + viewPort.height)'),
        ('return "Anoint " .. node.dn',
         'return UILocale.format("Anoint %s", UILocale.passiveName(self.build.spec.treeVersion, node))'),
        ('return "Remove "..curAnoints[self.anointEnchantSlot]',
         'return UILocale.format("Remove %s", curAnoints[self.anointEnchantSlot])'),
        ('function ItemsTabClass:AppendAnointTooltip(tooltip, node, actionText)',
         'function ItemsTabClass:AppendAnointTooltip(tooltip, node, actionText)\n\tlocal name = node and UILocale.passiveName(self.build.spec.treeVersion, node)'),
        ('"^7"..actionText.." "..node.dn.." changes nothing because this node is already allocated on the tree."',
         '"^7"..UILocale.format("%s %s changes nothing because this node is already allocated on the tree.", UILocale.translate(actionText), name)'),
        ('"^7"..actionText.." "..node.dn.." changes nothing because this node is already anointed."',
         '"^7"..UILocale.format("%s %s changes nothing because this node is already anointed.", UILocale.translate(actionText), name)'),
        ('"^7"..actionText.." "..node.dn.." will give you: "',
         '"^7"..UILocale.format("%s %s will give you: ", UILocale.translate(actionText), name)'),
        ('"^7"..actionText.." nothing will give you: "',
         '"^7"..UILocale.format("%s nothing will give you: ", UILocale.translate(actionText))'),
        ('"^7"..actionText.." "..node.dn.." changes nothing."',
         '"^7"..UILocale.format("%s %s changes nothing.", UILocale.translate(actionText), name)'),
    ])

    edit("Classes/ItemListControl.lua", [
        ('\tself.label = "^7All items:"', '\tself.label = "^7All items:"\n\tself.labelPositionOffset[2] = -22\n\tself.wrapDefaultText = true'),
        (r"""This is the list of items that have been added to this build.\nYou can add items to this list by dragging them from\none of the other lists, or by clicking 'Add to build' when\nviewing an item.""",
         "Drag an item here from another list or choose Add to Build when viewing it."),
        ('{-4, 0, 70, 18}, "Delete All"', '{-4, 0, 82, 18}, "Delete All"'),
        ('{-4, 0, 100, 18}, "Delete Unused"', '{-4, 0, 108, 18}, "Delete Unused"'),
        ('{-4, 0, 60, 18}, "Sort"', '{-4, 0, 84, 18}, "Sort"'),
        ('\tself.controls.deleteUnused.enabled = function()', '\tself.controls.deleteUnused.tooltipText = "Remove items that are not equipped or socketed."\n\tself.controls.deleteUnused.enabled = function()'),
    ])

    edit("Classes/TreeTab.lua", [
        ('..(spec.title or "Default"))', '..(spec.title or UILocale.translate("Default")))'),
        ('colorCodes.POSITIVE.."Convert to "..treeVersions[getLatestTreeVersion()].display',
         'colorCodes.POSITIVE .. UILocale.format("Convert to %s", treeVersions[getLatestTreeVersion()].display)'),
        ('colorCodes.POSITIVE.."Convert all trees to "..treeVersions[getLatestTreeVersion()].display',
         'colorCodes.POSITIVE .. UILocale.format("Convert all trees to %s", treeVersions[getLatestTreeVersion()].display)'),
        ('{ 74, 0, 20 }, "Compare:"', '{ function() return m_max(74, DrawStringWidth(16, "VAR", "Compare:") + 14) end, 0, 20 }, "Compare:"'),
        ('\t-- Tree Version Dropdown', '\tUILocale.fitButton(self.controls.reset)\n\n\t-- Tree Version Dropdown'),
        ('self.controls.compareCheck.width + self.controls.compareCheck.x',
         'self.controls.compareCheck.width + self.controls.compareCheck:GetProperty("x")'),
        ('self.controls.reset.width + self.controls.reset.x',
         'self.controls.reset:GetProperty("width") + self.controls.reset.x'),
    ])

    edit("Classes/SharedItemListControl.lua", [
        ('\tself.defaultText = ', '\tself.wrapDefaultText = true\n\tself.defaultText = '),
        (r"""This is a list of items that will be shared between all of\nyour builds.\nYou can add items to this list by dragging them from\none of the other lists.""",
         "Items in this list are available in all your builds. Drag items here from another list."),
    ])

    edit("Classes/ListControl.lua", [
        ('\t\tDrawString(2, 2, "LEFT", 14, self.font, self.defaultText)',
         '''		if self.wrapDefaultText then
			local text = UILocale.wrap(self, self.defaultText, 14, self.font, width - (self.scroll and 26 or 8))
			UILocale.drawRaw(2, 2, "LEFT", 14, self.font, text)
		else
			DrawString(2, 2, "LEFT", 14, self.font, self.defaultText)
		end'''),
    ])
