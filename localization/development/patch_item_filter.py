import json

from read_poe2_dat import read_rows


def write_item_filter_catalog(destination):
    # PoB's type keys match ItemClassCategories.Id, except for these two labels.
    category_ids = (
        "Amulet", "Belt", "Body Armour", "Boots", "Bow", "Buckler", "Charm",
        "Claw", "Crossbow", "Dagger", "FishingRod", "Flail", "Flask", "Focus",
        "Gloves", "Helmet", "IncursionLimb", "Jewel", "One Hand Axe",
        "One Hand Mace", "One Hand Sword", "Quiver", "Ring", "Sceptre",
        "Shield", "Spear", "Staff", "Talisman", "TrapTool", "Two Hand Axe",
        "Two Hand Mace", "Two Hand Sword", "Wand", "Warstaff",
    )
    aliases = {"FishingRod": "Fishing Rod", "IncursionLimb": "Transcendent Limb"}
    categories = {
        row["Id"]: row["Name"].removeprefix("[").removesuffix("]").rsplit("|", 1)[-1]
        for row in read_rows("itemclasscategories", ("Id", "Name"), "russian")
    }
    labels = {aliases.get(key, key): categories[key] for key in category_ids}
    client_strings = {
        row["Id"]: row["Text"] for row in read_rows("clientstrings", ("Id", "Text"), "russian")
        if row["Id"] in {"GambleTabNameArmour", "GambleTabNameJewellery"}
    }
    labels.update({
        "Armour": client_strings["GambleTabNameArmour"],
        "Jewellery": client_strings["GambleTabNameJewellery"],
        "One Handed Melee": "Одноручное оружие ближнего боя",
        "Two Handed Melee": "Двуручное оружие ближнего боя",
    })
    if any(not label for label in labels.values()):
        raise ValueError("A PoE 2 item filter category has no Russian label")
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    lines = [f"\t[{quote(kind)}] = {quote(label)}," for kind, label in sorted(labels.items())]
    destination.write_text(
        "-- PoE 2 ItemClassCategories and ClientStrings, Steam build 26650308.\n"
        "-- The two melee group labels describe filters defined by PoB.\n"
        "return {\n" + "\n".join(lines) + "\n}\n",
        encoding="utf-8",
    )


def patch_item_filter(edit):
    edit("Classes/ItemDBControl.lua", [
        ('local m_floor = math.floor', '''local m_floor = math.floor
local russianTypeLabels = LoadModule("Data/Locale/item_filter_ru")
local shortRussianTypeLabels = {
	["One Handed Melee"] = "Одноручн. (ближ. бой)",
	["Two Handed Melee"] = "Двуручн. (ближ. бой)",
}
local filterKeys = { "slot", "type", "sort", "league", "requirement", "obtainable", "searchMode" }
local function localizedOptionLabel(option)
	local label = type(option) == "table" and option.label or option
	return StripEscapes(UILocale.translate(label))
end'''),
        ('{2, 0, 179, 18}, self.typeList, function(index, value)',
         '{2, 0, 179, 18}, nil, function(index, value)'),
        ('\tself:BuildSortOrder()\n\tself.listBuildFlag = true\nend)',
         '''	for _, key in ipairs(filterKeys) do
		local dropdown = self.controls[key]
		if dropdown then
			dropdown.fitSelectedLabel = true
			dropdown.droppedLabelPadding = 28
			dropdown.maxDroppedWidth = 480
			dropdown.localizedSearchAccessor = localizedOptionLabel
		end
	end
	self:BuildSortOrder()
	self:UpdateTypeLabels()
	self.listBuildFlag = true
end)'''),
        ('function ItemDBClass:LoadLeaguesAndTypes()', '''function ItemDBClass:UpdateTypeLabels()
	local entries = {}
	local russian = UILocale.language == "ru"
	for index, typeKey in ipairs(self.typeList) do
		entries[index] = {
			label = russian and (russianTypeLabels[typeKey] or UILocale.translate(typeKey)) or typeKey,
			selectedLabel = russian and shortRussianTypeLabels[typeKey] or nil,
			searchFilter = typeKey,
		}
	end
	self.controls.type:SetList(entries)
	for _, key in ipairs(filterKeys) do
		local dropdown = self.controls[key]
		if dropdown then
			dropdown:CheckDroppedWidth(true)
			dropdown:UpdateSearch()
		end
	end
	self.typeLabelLanguage = UILocale.language
end

function ItemDBClass:LoadLeaguesAndTypes()'''),
        ('\tself.leaguesAndTypesLoaded = true\nend',
         '\tself.leaguesAndTypesLoaded = true\n\tself:UpdateTypeLabels()\nend'),
        ('"^7Sorting... ("..m_floor(itemIndex/#list*100).."%)"',
         '"^7"..UILocale.format("Sorting... (%d%%)", m_floor(itemIndex / #list * 100))'),
        ('function ItemDBClass:Draw(viewPort)\n', '''function ItemDBClass:Draw(viewPort)
	if self.typeLabelLanguage ~= UILocale.language then
		self:UpdateTypeLabels()
	end
'''),
    ])

    edit("Classes/DropDownControl.lua", [
        ('local ipairs = ipairs', "local utf8 = require('lua-utf8')\nlocal ipairs = ipairs"),
        ('selLabel = selItem.label', 'selLabel = selItem.selectedLabel or selItem.label'),
        ('\tlocal mOver\n\n\tif self.dropped then',
         '''	if self.fitSelectedLabel then
		if cursorX >= x and cursorX < x + width and cursorY >= y and cursorY < y + height then
			return true, "BODY"
		end
		if self.dropped and self.popupX and cursorX >= self.popupX and cursorX < self.popupX + self.popupWidth then
			if cursorY >= self.popupY and cursorY < self.popupY + self.dropHeight + 4 then
				return true, "DROP"
			end
		end
		return false
	end
	local mOver

	if self.dropped then'''),
        ('''	local mOver, mOverComp = self:IsMouseOver()
	local dropExtra = self.dropHeight + 4
	scrollBar:SetContentDimension(lineHeight * self:GetDropCount(), self.dropHeight)
	local dropY = self.dropUp and y - dropExtra or y + height''',
         '''	local dropExtra = self.dropHeight + 4
	scrollBar:SetContentDimension(lineHeight * self:GetDropCount(), self.dropHeight)
	local dropY = self.dropUp and y - dropExtra or y + height
	local dropX, dropWidth = x, self.droppedWidth
	if self.fitSelectedLabel then
		dropWidth = m_min(dropWidth, viewPort.width - 4)
		dropX = m_max(viewPort.x, m_min(x, viewPort.x + viewPort.width - dropWidth - 2))
		self.popupX, self.popupY, self.popupWidth = dropX, dropY, dropWidth
		scrollBar.x = dropX + dropWidth - (x + width) - 1
	end
	local mOver, mOverComp = self:IsMouseOver()'''),
        ('DrawImage(nil, x, dropY, self.droppedWidth, dropExtra)', 'DrawImage(nil, dropX, dropY, dropWidth, dropExtra)'),
        ('DrawImage(nil, x + 1, dropY + 1, self.droppedWidth - 2, dropExtra - 2)',
         'DrawImage(nil, dropX + 1, dropY + 1, dropWidth - 2, dropExtra - 2)'),
        ('\t\twidth = self.droppedWidth', '\t\twidth = dropWidth'),
        ('\t\t\t\tx, dropY + 2 + (self.hoverSelDrop',
         '\t\t\t\tdropX, dropY + 2 + (self.hoverSelDrop'),
        ('if (mOver or self.dropped) and mOverComp ~= "DROP" and not noTooltip then',
         'if (mOver or self.dropped) and mOverComp ~= "DROP" and not noTooltip and not (self.dropped and self.fitSelectedLabel) then'),
        ('if self.hoverSel and not noTooltip then',
         'if self.hoverSel and not noTooltip and not self.fitSelectedLabel then'),
        ('SetViewport(x + 2, dropY + 2, scrollBar.enabled',
         'SetViewport(dropX + 2, dropY + 2, scrollBar.enabled'),
        ('DrawString(0, 0, "LEFT", lineHeight, "VAR", selLabel or "")',
         '''local labelSize = lineHeight
	if self.fitSelectedLabel and selLabel and not selDetail and not self:IsSearchActive() then
		local textWidth = width - height - 2
		while labelSize > 11 and DrawStringWidth(labelSize, "VAR", selLabel) > textWidth do
			labelSize = labelSize - 1
		end
		if DrawStringWidth(labelSize, "VAR", selLabel) > textWidth then
			local visible = StripEscapes(UILocale.translate(selLabel))
			local length = utf8.len(visible)
			repeat
				length = length - 1
				selLabel = utf8.sub(visible, 1, length) .. "…"
			until length <= 0 or DrawStringWidth(labelSize, "VAR", selLabel) <= textWidth
		end
	end
	DrawString(0, m_floor((lineHeight - labelSize) / 2), "LEFT", labelSize, "VAR", selLabel or "")'''),
        ('dWidth = m_max(dWidth, DrawStringWidth(lineHeight, "VAR", line or "") + 10)',
         'dWidth = m_max(dWidth, DrawStringWidth(lineHeight, "VAR", line or "") + (self.droppedLabelPadding or 10))'),
        ('self:DrawSearchHighlights(label, searchInfo, 0, y, width - 4, lineHeight)',
         '''if searchInfo then
					local highlightLabel = self.localizedSearchAccessor and self.localizedSearchAccessor(listVal) or label
					self:DrawSearchHighlights(highlightLabel, searchInfo, 0, y, width - 4, lineHeight)
				end'''),
    ])

    edit("Classes/SearchHost.lua", [
        ('local SearchHostClass', "local utf8 = require('lua-utf8')\n\nlocal SearchHostClass"),
        ('self.searchTerm = self.searchTerm:sub(1, -2)', 'self.searchTerm = utf8.sub(self.searchTerm, 1, -2)'),
        ('''		self.searchInfos = matchTerm(self.searchTerm, self.searchListAccessor(), self.valueAccessor)
		self:UpdateMatchCount()''',
         '''		local list = self.searchListAccessor()
		self.searchInfos = matchTerm(self.searchTerm, list, self.valueAccessor)
		if self.localizedSearchAccessor and self:IsSearchActive() then
			local localized = matchTerm(utf8.lower(self.searchTerm), list, function(entry)
				return utf8.lower(self.localizedSearchAccessor(entry))
			end)
			for index, info in ipairs(localized) do
				-- English matches still select the same row, while highlight ranges follow the visible text.
				if not info.matches and self.searchInfos[index].matches then
					info.matches = true
					info.ranges = {}
				end
				self.searchInfos[index] = info
			end
		end
		self:UpdateMatchCount()'''),
    ])
