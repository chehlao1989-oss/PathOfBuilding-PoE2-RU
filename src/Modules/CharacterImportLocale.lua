-- Display-only character import text and layout. API identifiers remain unchanged.
local locale = {}

function locale.statusText(text)
	if UILocale.language ~= "ru" or type(text) ~= "string" then return text end
	local prefix, body = "", text
	while body:sub(1, 1) == "^" do
		local escape = body:match("^%^x%x%x%x%x%x%x") or body:match("^%^%d")
		if not escape then break end
		prefix, body = prefix .. escape, body:sub(#escape + 1)
	end
	local seconds = body:match("^Logging in%.%.%. %((%d+)%)$")
	if seconds then return prefix .. UILocale.format("Logging in... (%s)", seconds) end
	seconds = body:match("^Requests are being sent too fast, try again in (%d+) seconds%.$")
	if seconds then return prefix .. UILocale.format("Requests are being sent too fast, try again in %s seconds.", seconds) end
	local errorCode = body:match("^Authentication failed: (.+)$")
	if errorCode then return prefix .. UILocale.format("Authentication failed: %s", errorCode) end
	for _, subject in ipairs({ "character list", "character data" }) do
		local detail = body:match("^Error " .. (subject == "character list" and "retrieving " or "importing ") .. subject .. ", try again %((.*)%)$")
		if detail then
			local key = subject == "character list" and "Error retrieving character list, try again (%s)" or "Error importing character data, try again (%s)"
			return prefix .. UILocale.format(key, detail)
		end
	end
	return prefix .. UILocale.translate(body)
end

function locale.characterDetail(color, class, level, league)
	local text = color .. UILocale.translate(class) .. " ^x808080" .. UILocale.format("lvl %d", level)
	if league then text = text .. " " .. UILocale.format("in %s", UILocale.itemLeague(league)) end
	return text
end

local function width(control)
	return control:GetProperty("width")
end

function locale.prepare(tab)
	local c = tab.controls
	c.sectionCharImport.width = function() return math.min(650, math.max(300, width(tab) - 20)) end
	c.charImportStatusLabel:SetWrapWidth(function() return width(c.sectionCharImport) - 12 end)
	c.logoutApiButton:SetAnchor("TOPLEFT", c.charImportStatusLabel, "BOTTOMLEFT", 0, 8)
	c.logoutApiButton.height = 20
	UILocale.fitButton(c.logoutApiButton)
	c.characterImportAnchor:SetAnchor("TOPLEFT", c.logoutApiButton, "BOTTOMLEFT", 0, 12, true)
	c.authenticateButton.height = 22
	UILocale.fitButton(c.authenticateButton)
	c.accountNameHeader:SetWrapWidth(function() return width(c.sectionCharImport) - 12 end)
	c.accountNameGo:SetAnchor("LEFT", c.accountRealm, "RIGHT", 12, 0)
	UILocale.fitButton(c.accountNameGo)
	c.charSelectHeader:SetAnchor("TOPLEFT", c.characterImportAnchor, "TOPLEFT", 0, 0)
	c.charSelectLeague.displayLabelAccessor = function(entry) return UILocale.itemLeague(entry.label) end
	c.charSelectLeague.localizedSearchAccessor = c.charSelectLeague.displayLabelAccessor
	c.charSelectLeague.fitSelectedLabel = true
	c.charSelectLeague.showFullLabelTooltip = true
	for _, button in ipairs({ c.charImportTree, c.charImportItems }) do
		button.width = 200
		button.height = 22
		UILocale.fitButton(button)
	end
	c.charImportItems:SetAnchor("TOPLEFT", c.charImportTree, "BOTTOMLEFT", 0, 10)
	c.charImportTreeClearJewels.x = function()
		return UILocale.measureRaw(14, "VAR", UILocale.translate(c.charImportTreeClearJewels.label)) + 16
	end
	c.charImportItemsClearSkills:SetAnchor("TOPLEFT", c.charImportItems, "BOTTOMLEFT", 0, 10)
	c.charImportItemsClearItems:SetAnchor("TOPLEFT", c.charImportItemsClearSkills, "BOTTOMLEFT", 0, 8)
	c.charImportItemsIgnoreWeaponSwap:SetAnchor("TOPLEFT", c.charImportItemsClearItems, "BOTTOMLEFT", 0, 8)
	c.sectionCharImport.height = function()
		local last = c.characterImportAnchor
		if tab.charImportMode == "AUTHENTICATION" then
			last = c.authenticateButton
		elseif tab.charImportMode == "GETACCOUNTNAME" then
			last = c.accountNameGo
		elseif tab.charImportMode == "SELECTCHAR" or tab.charImportMode == "IMPORTING" then
			last = c.charImportItemsIgnoreWeaponSwap
		end
		return select(2, last:GetPos()) + last:GetProperty("height") - select(2, c.sectionCharImport:GetPos()) + 16
	end
end

function locale.layout(tab)
	local c = tab.controls
	c.charSelect.width = width(c.sectionCharImport) - 12
	c.charSelectLeague.width = math.min(320, width(c.sectionCharImport) - 70)
	local labels = { c.charImportItemsClearSkills, c.charImportItemsClearItems, c.charImportItemsIgnoreWeaponSwap }
	local labelWidth = 0
	for _, control in ipairs(labels) do
		control.labelWidth = UILocale.measureRaw(14, "VAR", UILocale.translate(control.label)) + 5
		labelWidth = math.max(labelWidth, control.labelWidth)
	end
	c.charImportItemsClearSkills.x = labelWidth
	c.charImportItemsClearItems.x = 0
	c.charImportItemsIgnoreWeaponSwap.x = 0
	c.charImportTreeClearJewels.labelWidth = UILocale.measureRaw(14, "VAR", UILocale.translate(c.charImportTreeClearJewels.label)) + 5
end

return locale
