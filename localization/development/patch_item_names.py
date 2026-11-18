ITEM_TOOLTIP_LABELS = (
    ("Charm Slots", "ItemDisplayBeltCharmSlots"),
    ("Spirit", "ItemDisplaySpiritValue"),
    ("Physical Damage", "ItemDisplayWeaponPhysicalDamage"),
    ("Elemental Damage", "ItemDisplayWeaponElementalDamage"),
    ("Chaos Damage", "ItemDisplayWeaponChaosDamage"),
    ("Critical Hit Chance", "ItemDisplayWeaponCriticalStrikeChance"),
    ("Attacks per Second", "ItemDisplayWeaponAttacksPerSecond"),
    ("Reload Time", "ItemDisplayWeaponReloadTime"),
    ("Weapon Range", "ItemDisplayWeaponRange"),
    ("Chance to Block", "ItemDisplayShieldBlockChance"),
    ("Armour", "ItemDisplayArmourArmour"),
    ("Evasion Rating", "ItemDisplayArmourEvasionRating"),
    ("Energy Shield", "ItemDisplayArmourEnergyShield"),
    ("Runic Ward", "ItemDisplayArmourWard"),
    ("Sockets", "ItemDisplayStringSockets"),
    ("Limited to", "JewelItemLimit"),
    ("Radius", "ItemDisplayHarvestEffectRadius"),
)


def patch_item_names(edit):
    edit("Classes/ItemDBControl.lua", [
        ("local pairs = pairs", 'local utf8 = require("lua-utf8")\nlocal pairs = pairs'),
        ("local searchStr = self.controls.search.buf:lower():gsub", "local searchStr = utf8.lower(self.controls.search.buf):gsub"),
        ('''			if not err and match then
				found = true
			end
		end
		if mode == 1 or mode == 3 then''', '''			found = not err and match
			local label = UILocale.itemName(item)
			if not found and label ~= item.name then
				err, match = PCall(string.matchOrPattern, utf8.lower(label), searchStr)
				found = not err and match
			end
		end
		if mode == 1 or mode == 3 then'''),
        ("		self:UpdateTypeLabels()\n	end\n	if self.itemsTab.build.outputRevision",
         "		self:UpdateTypeLabels()\n		self.listBuildFlag = true\n	end\n	if self.itemsTab.build.outputRevision"),
        ("return colorCodes[item.rarity] .. item.name", "return colorCodes[item.rarity] .. UILocale.itemName(item)"),
        ("		if mode == 1 or mode == 3 then\n", '''		if mode == 1 or mode == 3 then
			local function matchesModifier(line)
				local err, match = PCall(string.matchOrPattern, line.line:lower(), searchStr)
				if not err and match then return true end
				local localized = UILocale.itemModifier(line.line, line, item)
				if localized == line.line then return false end
				err, match = PCall(string.matchOrPattern, utf8.lower(localized), searchStr)
				return not err and match
			end
'''),
        ('''				local err, match = PCall(string.matchOrPattern, line.line:lower(), searchStr)
				if not err and match then
					found = true''',
         '''				if matchesModifier(line) then
					found = true''', 4),
    ])
    edit("Classes/DropDownControl.lua", [
        ('if self.hoverSel and not noTooltip and not self.fitSelectedLabel then',
         'if self.hoverSel and not noTooltip and (self.showFullLabelTooltip or not self.fitSelectedLabel) then'),
        ("\t\t\tselLabel = selItem\n",
         "\t\t\tselLabel = self.displayStringLabelAccessor and self.displayStringLabelAccessor(selItem) or selItem\n"),
        ("\t\t\t\t\tlabel = listVal\n",
         "\t\t\t\t\tlabel = self.displayStringLabelAccessor and self.displayStringLabelAccessor(listVal) or listVal\n"),
        ('\t\t\tend\n\t\t\t  -- +10 to stop clipping',
         '\t\t\telseif self.displayStringLabelAccessor then\n\t\t\t\tline = self.displayStringLabelAccessor(line)\n\t\t\tend\n\t\t\t  -- +10 to stop clipping'),
        ('\t\t\tend\n\t\t\t-- add 20 to account for the',
         '\t\t\telseif line and self.displayStringLabelAccessor then\n\t\t\t\tline = self.displayStringLabelAccessor(line)\n\t\t\tend\n\t\t\t-- add 20 to account for the'),
        ("selLabel = selItem.selectedLabel or selItem.label",
         "selLabel = self.displayLabelAccessor and self.displayLabelAccessor(selItem) or selItem.selectedLabel or selItem.label"),
        ("					label = listVal.label",
         "					label = self.displayLabelAccessor and self.displayLabelAccessor(listVal) or listVal.label"),
        ('line = line.label or ""', 'line = self.displayLabelAccessor and self.displayLabelAccessor(line) or line.label or ""'),
        ("				line = line.label",
         "				line = self.displayLabelAccessor and self.displayLabelAccessor(line) or line.label"),
    ])
    edit("Classes/ItemsTab.lua", [
        ('            text = entry.text,', '            id = entry.id,\n            text = entry.text,'),
        ('flavourText = flavour.text or flavour', 'flavourText = UILocale.itemFlavourText(flavour)'),
        ('function ItemsTabClass:FormatItemSource(text)\n',
         'function ItemsTabClass:FormatItemSource(text)\n\ttext = UILocale.itemSource(text)\n'),
        ('typeStr = itemOrigin .. " " .. typeStr', 'typeStr = UILocale.itemOrigin(itemOrigin, typeStr)'),
        ('"^xFFFF30Variant: "..item.variantList[1]',
         '"^xFFFF30" .. UILocale.format("Variant: %s", UILocale.itemVariantName(item.variantList[1], item))'),
        ('"^xFFFF30Variant: "..item.variantList[item.variant].." ("..#item.variantList.." variants)"',
         '"^xFFFF30" .. UILocale.format("Variant: %s (%d variants)", UILocale.itemVariantName(item.variantList[item.variant], item), #item.variantList)'),
        ('"^xFF5555Exclusive to: "..item.league',
         '"^xFF5555" .. UILocale.format("Exclusive to: %s", UILocale.itemLeague(item.league))'),
        ('colorCodes.NEGATIVE.."Not yet available"', 'colorCodes.NEGATIVE .. UILocale.translate("Not yet available")'),
        ('colorCodes.SOURCE.."Source: "..self:FormatItemSource(item.source)',
         'colorCodes.SOURCE .. UILocale.format("Source: %s", self:FormatItemSource(item.source))'),
        ('"%d-%d (%.1f DPS)", weaponData.PhysicalMin, weaponData.PhysicalMax, weaponData.PhysicalDPS',
         '"%d-%d (%.1f %s)", weaponData.PhysicalMin, weaponData.PhysicalMax, weaponData.PhysicalDPS, UILocale.translate("DPS")'),
        ('"(%.1f DPS)", weaponData.ChaosMin, weaponData.ChaosMax, weaponData.ChaosDPS',
         '"(%.1f %s)", weaponData.ChaosMin, weaponData.ChaosMax, weaponData.ChaosDPS, UILocale.translate("DPS")'),
        ('^x7F7F7Fmetres", main:StatColor(weaponData.range, base.weapon.Range), weaponData.range / 10)',
         '^x7F7F7F%s", main:StatColor(weaponData.range, base.weapon.Range), weaponData.range / 10, UILocale.translate("metres"))'),
        ('"^x7F7F7FElemental DPS: "', '"^x7F7F7F" .. UILocale.translate("Elemental DPS:") .. " "'),
        ('"^x7F7F7FTotal DPS: "', '"^x7F7F7F" .. UILocale.translate("Total DPS:") .. " "'),
        *[(f'.."{label}", "FONTIN SC")', f' .. UILocale.translate("{label}"), "FONTIN SC")')
          for label in ("Mirrored", "Sanctified", "Twice Corrupted", "Item base is not supported by the current version.")],
        ('\t-- Section: Sockets and Links', '''\tlocal function variantLabel(label)
\t\treturn UILocale.itemVariantName(label, self.displayItem)
\tend
\tfor _, name in ipairs({ "displayItemVariant", "displayItemAltVariant", "displayItemAltVariant2",
\t\t"displayItemAltVariant3", "displayItemAltVariant4", "displayItemAltVariant5" }) do
\t\tlocal control = self.controls[name]
\t\tcontrol.displayStringLabelAccessor = variantLabel
\t\tcontrol.localizedSearchAccessor = variantLabel
\t\tcontrol.fitSelectedLabel = true
\t\tcontrol.showFullLabelTooltip = true
\t\tcontrol.tooltipFunc = function(tooltip, mode, _, label)
\t\t\ttooltip:Clear()
\t\t\tif label and (mode == "BODY" or mode == "HOVER") then
\t\t\t\ttooltip.maxWidth = 500
\t\t\t\ttooltip:AddLine(14, variantLabel(label))
\t\t\tend
\t\tend
\tend

\t-- Section: Sockets and Links'''),
        ('''				local newItem = Paste()
				if newItem then
					self:CreateDisplayItemFromRaw(newItem, true)
				end
				if self.displayItem and IsKeyDown("SHIFT") then''',
         '''				local newItem = Paste()
				local imported = newItem and self:CreateDisplayItemFromRaw(newItem, true)
				if imported and self.displayItem and IsKeyDown("SHIFT") then'''),
        ('''function ItemsTabClass:CreateDisplayItemFromRaw(itemRaw, normalise)
	local newItem = new("Item", itemRaw)
	if newItem.base then''',
         '''local normalizeRussianItem = LoadModule("Modules/ItemClipboardLocale")

function ItemsTabClass:CreateDisplayItemFromRaw(itemRaw, normalise)
	local source, issues = normalizeRussianItem(itemRaw)
	if not source then
		main:OpenMessagePopup("Импорт предмета", table.concat(issues, "\\n"))
		return false
	end
	local newItem = new("Item", source)
	if newItem.base then
		if issues and #issues == 0 then
			newItem:BuildAndParseRaw()
		end'''),
        ('\t\tif normalise then\n\t\t\tnewItem:NormaliseQuality()',
         '\t\tif normalise then\n\t\t\tif not issues then newItem:NormaliseQuality() end'),
        ('''		self:SetDisplayItem(newItem)
	end
end

-- Sets the display item''',
         '''		self:SetDisplayItem(newItem)
		if issues then
			local added = {}
			for _, issue in ipairs(issues) do added[issue] = true end
			for _, list in ipairs({ newItem.enchantModLines, newItem.runeModLines, newItem.implicitModLines, newItem.explicitModLines }) do
				for _, mod in ipairs(list) do
					if mod.extra and not added[mod.line] then
						issues[#issues + 1] = mod.line
						added[mod.line] = true
					end
				end
			end
			if #issues > 0 then
				main:OpenMessagePopup("Импорт предмета", "Проверьте строки, которые PoB не сопоставила:\\n" .. table.concat(issues, "\\n"))
				return false
			end
		end
		return true
	end
	return false
end

-- Sets the display item'''),
        ("		controls.base.list = self.build.data.itemBaseLists[self.build.data.itemBaseTypeList[index]]\n		controls.base.selIndex = 1",
         "		controls.base:SetList(copyTable(self.build.data.itemBaseLists[value], true))\n		controls.base.selIndex = 1\n		controls.base:ResetSearch()"),
        ('''	controls.base = new("DropDownControl", {"TOPLEFT",nil,"TOPLEFT"}, {55, 70, 200, 18}, self.build.data.itemBaseLists[self.build.data.itemBaseTypeList[controls.type.selIndex]])''',
         '''	controls.base = new("DropDownControl", {"TOPLEFT",nil,"TOPLEFT"}, {55, 70, 295, 18},
		copyTable(self.build.data.itemBaseLists[self.build.data.itemBaseTypeList[controls.type.selIndex]], true))
	controls.base.displayLabelAccessor = UILocale.itemBaseLabel
	controls.base.localizedSearchAccessor = UILocale.itemBaseLabel'''),
        ('''	if item.title then
		tooltip:AddLine(fontSizeTitle, rarityCode..item.title, "FONTIN SC")
		tooltip:AddLine(fontSizeTitle, rarityCode..item.baseName:gsub(" %(.+%)",""), "FONTIN SC")
	else
		tooltip:AddLine(fontSizeTitle, rarityCode..item.namePrefix..item.baseName:gsub(" %(.+%)","")..item.nameSuffix, "FONTIN SC")
	end''',
         '''	local uniqueTitle = (item.rarity == "UNIQUE" or item.rarity == "RELIC") and item.title
	local baseName = UILocale.itemBaseName(item.baseName, uniqueTitle)
	if item.title then
		tooltip:AddLine(fontSizeTitle, rarityCode..UILocale.itemTitle(item), "FONTIN SC")
		tooltip:AddLine(fontSizeTitle, rarityCode..baseName, "FONTIN SC")
	else
		tooltip:AddLine(fontSizeTitle, rarityCode..UILocale.itemNameWithoutTitle(item, baseName), "FONTIN SC")
	end'''),
        ("slot.slotName, colorCodes[item.rarity], item.name)", "slot.slotName, colorCodes[item.rarity], UILocale.itemName(item))"),
        ("local typeStr = base.weapon and self.build.data.weaponTypeInfo[base.type].label or base.type",
         "local typeStr = UILocale.itemType(base, base.weapon and self.build.data.weaponTypeInfo[base.type].label or base.type)"),
        *[
            (f'"^x7F7F7F{label}: ', f'("^x7F7F7F" .. UILocale.itemStatLabel("{key}", "{label}") .. ": ") .. "',
             2 if label == "Sockets" else 1)
            for label, key in ITEM_TOOLTIP_LABELS
        ],
        ('"^x7F7F7FQuality: "', '"^x7F7F7F" .. UILocale.translate("Quality:") .. " "'),
        ('"Tip: Press Ctrl+D to enable the display of stat differences."',
         'UILocale.translate("Tip: Press Ctrl+D to enable the display of stat differences.")'),
        ('''		drop.y = function()
			return i == 1 and 0 or 24
		end
		drop.tooltipFunc = function(tooltip, mode, index, value)''',
         '''		drop.y = function()
			return i == 1 and 0 or 24
		end
		local runeModifier = { rune = true }
		drop.displayLabelAccessor = function(value)
			return UILocale.itemModifier(value.label, runeModifier)
		end
		drop.localizedSearchAccessor = drop.displayLabelAccessor
		drop.tooltipFunc = function(tooltip, mode, index, value)'''),
        ('''			if value.lines and value.lines[1] ~= "None" then
				tooltip:AddLine(14, "^7"..value.name)
				for _, line in ipairs(value.lines) do
					tooltip:AddLine(14, "^7"..line)''',
         '''			if value and value.lines and value.lines[1] ~= "None" then
				tooltip:AddLine(14, "^7" .. UILocale.itemRuneName(value.name))
				for _, line in ipairs(value.lines) do
					tooltip:AddLine(14, "^7" .. UILocale.itemModifier(line, runeModifier))
'''.rstrip()),
        ('"^7Rune #"..i)', '"^7" .. UILocale.format("Rune #%s", i))'),
        ('s_format("^x7F7F7FRecovers %s%d ^x7F7F7FLife over %s%.1f0 ^x7F7F7FSeconds",',
         '''UILocale.itemFlaskRecovery("Life", flaskData.lifeGradual, flaskData.duration,
					main:StatColor(flaskData.lifeTotal, base.flask.life), main:StatColor(flaskData.duration, base.flask.duration))
					or s_format("^x7F7F7FRecovers %s%d ^x7F7F7FLife over %s%.1f0 ^x7F7F7FSeconds",'''),
        ('s_format("^x7F7F7FRecovers %s%d ^x7F7F7FMana over %s%.1f0 ^x7F7F7FSeconds",',
         '''UILocale.itemFlaskRecovery("Mana", flaskData.manaGradual, flaskData.duration,
					main:StatColor(flaskData.manaTotal, base.flask.mana), main:StatColor(flaskData.duration, base.flask.duration))
					or s_format("^x7F7F7FRecovers %s%d ^x7F7F7FMana over %s%.1f0 ^x7F7F7FSeconds",'''),
        ('''s_format("^x7F7F7FConsumes %s%d ^x7F7F7Fof %s%d ^x7F7F7FCharges on use",
			main:StatColor(flaskData.chargesUsed''',
         '''UILocale.itemCharges(flaskData.chargesUsed, flaskData.chargesMax,
			main:StatColor(flaskData.chargesUsed, base.flask.chargesUsed), main:StatColor(flaskData.chargesMax, base.flask.chargesMax))
			or s_format("^x7F7F7FConsumes %s%d ^x7F7F7Fof %s%d ^x7F7F7FCharges on use",
			main:StatColor(flaskData.chargesUsed'''),
        ('''s_format("^x7F7F7FConsumes %s%d ^x7F7F7Fof %s%d ^x7F7F7FCharges on use",
			main:StatColor(charmData.chargesUsed''',
         '''UILocale.itemCharges(charmData.chargesUsed, charmData.chargesMax,
			main:StatColor(charmData.chargesUsed, base.charm.chargesUsed), main:StatColor(charmData.chargesMax, base.charm.chargesMax))
			or s_format("^x7F7F7FConsumes %s%d ^x7F7F7Fof %s%d ^x7F7F7FCharges on use",
			main:StatColor(charmData.chargesUsed'''),
        ('colorCodes.MAGIC..modLine.line, "FONTIN SC")',
         'colorCodes.MAGIC .. UILocale.itemModifier(modLine.line), "FONTIN SC")', 2),
        ('colorCodes.NEGATIVE.."Corrupted", "FONTIN SC")',
         'colorCodes.NEGATIVE .. UILocale.gemText("MonsterCorrupted", "Corrupted"), "FONTIN SC")'),
        ("itemLib.formatModLine(copyModLine, dbMode)", "itemLib.formatModLine(copyModLine, dbMode, UILocale.itemModifier, item)"),
        ("itemLib.formatModLine(modLine, dbMode)", "itemLib.formatModLine(modLine, dbMode, UILocale.itemModifier, item)"),
        ('''				header = "^7Removing this item from " .. compareSlot.label .. " will give you:"
			else
				header = string.format("^7Equipping this item in %s will give you:%s",
					compareSlot.label or compareSlot.slotName,
					selItem and "\\n(replacing " .. colorCodes[selItem.rarity] .. selItem.name .. "^7)" or "")
			end''', '''				header = "^7" .. UILocale.format("Removing this item from %s will give you:",
					UILocale.itemSlotLabel(compareSlot.label or compareSlot.slotName))
			else
				header = "^7" .. UILocale.format("Equipping this item in %s will give you:",
					UILocale.itemSlotLabel(compareSlot.label or compareSlot.slotName))
				if selItem then
					header = header .. "\\n" .. UILocale.format("(replacing %s)",
						colorCodes[selItem.rarity] .. UILocale.itemName(selItem) .. "^7")
				end
			end'''),
    ])
    edit("Classes/ItemSlotControl.lua", [
        ("	self.anchor.collapse = true", '''	self.displayLabelAccessor = function(entry)
		return colorCodes[entry.item.rarity] .. UILocale.itemName(entry.item)
	end
	self.localizedSearchAccessor = function(entry)
		return type(entry) == "table" and UILocale.itemName(entry.item) or UILocale.translate(entry)
	end
	self.anchor.collapse = true'''),
        ("t_insert(self.list, colorCodes[item.rarity]..item.name)",
         "t_insert(self.list, { label = colorCodes[item.rarity]..item.name, item = item })"),
        ("	-- Update Jewel Sockets", "	self:UpdateSearch()\n\n	-- Update Jewel Sockets"),
        ('"^7"..self.label..":"', '"^7"..UILocale.itemSlotLabel(self.label)..":"'),
    ])
    for path in ("ItemListControl", "SharedItemListControl", "CompareCalcsHelpers"):
        replacements = [
            ("return colorCodes[item.rarity] .. item.name", "return colorCodes[item.rarity] .. UILocale.itemName(item)"),
        ]
        if path == "ItemListControl":
            replacements.append(('"  ^9(Unused)"', '"  ^9" .. UILocale.translate("(Unused)")'))
        edit(f"Classes/{path}.lua", replacements)
    edit("Classes/SharedItemSetListControl.lua", [
        ("colorCodes[item.rarity], item.name)", "colorCodes[item.rarity], UILocale.itemName(item))"),
    ])
    edit("Classes/CompareTab.lua", [
        ("rarityColor .. item.name)", "rarityColor .. UILocale.itemName(item))"),
    ])
    edit("Classes/SkillsTab.lua", [
        (".. self.displayGroup.sourceItem.name", ".. UILocale.itemName(self.displayGroup.sourceItem)"),
    ])
    edit("Modules/ItemTools.lua", [
        ("function itemLib.formatModLine(modLine, dbMode)", "function itemLib.formatModLine(modLine, dbMode, displayFormatter, item)"),
        ("	local colorCode\n	if modLine.extra then",
         "	if displayFormatter then line = displayFormatter(line, modLine, item) end\n	local colorCode\n	if modLine.extra then"),
    ])
