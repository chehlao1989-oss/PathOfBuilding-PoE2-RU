def patch_trade_locale(edit, build):
    edit("Classes/DropDownControl.lua", [
        ('while labelSize > 11 and DrawStringWidth(labelSize, "VAR", selLabel) > textWidth do',
         'while labelSize > (self.minimumLabelSize or 11) and DrawStringWidth(labelSize, "VAR", selLabel) > textWidth do'),
    ], source=build)
    edit("Classes/TradeQuery.lua", [
        ('nameColor..slotTbl.slotName)', 'nameColor..UILocale.tradeSlotName(slotTbl))'),
        ('self.controls.league:SetSel(self.pbLeagueIndex)\n\tself.controls.league.enabled',
         'self.controls.league.displayLabelAccessor = UILocale.itemLeague\n'
         '\tself.controls.league.displayStringLabelAccessor = UILocale.itemLeague\n'
         '\tself.controls.league.localizedSearchAccessor = UILocale.itemLeague\n'
         '\tself.controls.league.fitSelectedLabel = true\n'
         '\tself.controls.league.showFullLabelTooltip = true\n'
         '\tself.controls.league:SetSel(self.pbLeagueIndex)\n\tself.controls.league.enabled'),
        ('table.insert(dropdownLabels, colorCodes[item.rarity] .. item.name .. price)',
         'table.insert(dropdownLabels, { label = colorCodes[item.rarity] .. item.name .. price, item = item, amount = result.amount, currency = result.currency })'),
        ('\tself:UpdateDropdownList(row_idx)\n\tcontrols["resultDropdown"..row_idx].tooltipFunc',
         '\tcontrols["resultDropdown"..row_idx].displayLabelAccessor = UILocale.tradeResultLabel\n'
         '\tcontrols["resultDropdown"..row_idx].localizedSearchAccessor = UILocale.tradeResultLabel\n'
         '\tcontrols["resultDropdown"..row_idx].fitSelectedLabel = true\n'
         '\tcontrols["resultDropdown"..row_idx].minimumLabelSize = 16\n'
         '\tcontrols["resultDropdown"..row_idx].showFullLabelTooltip = true\n'
         '\tself:UpdateDropdownList(row_idx)\n\tcontrols["resultDropdown"..row_idx].tooltipFunc'),
        ('\tself.controls.close = new("ButtonControl", {"BOTTOM", nil, "BOTTOM"}',
         '\tUILocale.fitTradeTotal(self.controls.fullPrice, pane_width - 2 * pane_margins_horizontal)\n'
         '\tself.controls.close = new("ButtonControl", {"BOTTOM", nil, "BOTTOM"}'),
        ('s_format("%s: %.2f", stat.label, stat.weightMult)',
         's_format("%s: %.2f", UILocale.translate(stat.label), stat.weightMult)'),
        ('main:OpenPopup(pane_width, self.pane_height, "Trader",',
         'UILocale.prepareTradeTooltips(self.controls)\n\tmain:OpenPopup(pane_width, self.pane_height, "Trader",'),
        ('string.format("^7Price: %s %s", result.amount, result.currency)',
         'string.format("^7Price: %s %s", result.amount, UILocale.tradeCurrencyName(result.currency))'),
        ('.. " " .. self.totalPrice[row_idx].currency',
         '.. " " .. UILocale.tradeCurrencyName(self.totalPrice[row_idx].currency)'),
        (' .. " " .. currency .. ", "', ' .. " " .. UILocale.tradeCurrencyName(currency) .. ", "'),
        ('return price and "Whisper for " .. price or "Whisper"',
         'return UILocale.tradeActionLabel("Whisper", price)'),
        ('return price and "Search for " .. price or "Search"',
         'return UILocale.tradeActionLabel("Search", price)'),
        ('{135 + 8, 0, 80, row_height}',
         '{(UILocale.language == "ru" and 160 or 135) + 8, 0, 80, row_height}', 2),
        ('{8, 0, 514, row_height}', '{8, 0, UILocale.language == "ru" and 489 or 514, row_height}'),
        ('{8, 0, 351, row_height}', '{8, 0, UILocale.language == "ru" and 326 or 351, row_height}'),
        ('local popupHeight = 500', 'local popupHeight = 500\n\tlocal popupWidth = UILocale.language == "ru" and 600 or 500'),
        ('local listHeight = popupHeight - 45 - 30 - 10', 'local listHeight = popupHeight - 65 - 30 - 10'),
        ('{ -410, 45, 400, listHeight }', '{10 - popupWidth, 65, popupWidth - 20, listHeight}'),
        ('{-410, 20, 0, 16}', '{10 - popupWidth, 20, 0, 16}'),
        ('controls.Slider = new("SliderControl", { "TOPLEFT", controls.SliderLabel, "TOPRIGHT" }, {20, 0, 150, 16}',
         'controls.SliderLabel:SetWrapWidth(popupWidth - 280)\n'
         '\tcontrols.Slider = new("SliderControl", { "TOPLEFT", nil, "TOPRIGHT" }, {-250, 20, 140, 16}'),
        ('controls[stat.label.."Slider"].tooltip.realDraw(self, x - 8 - sliderOffsetX',
         'controls.Slider.tooltip.realDraw(self, x - 8 - sliderOffsetX'),
        ('main:OpenPopup(420, popupHeight, "Stat Weight Multipliers", controls)',
         'UILocale.prepareTradeTooltips(controls)\n'
         '\tmain:OpenPopup(popupWidth, popupHeight, "Stat Weight Multipliers", controls)'),
    ])
    edit("Classes/TradeQueryGenerator.lua", [
        ('local popupWidth = 400', 'local popupWidth = UILocale.language == "ru" and 560 or 400'),
        ('{5, 0, 150, 18}, currencyDropdownNames', '{5, 0, UILocale.language == "ru" and 230 or 150, 18}, currencyDropdownNames'),
        ('s_format("^7%.2f: %s", stat.weightMult, stat.label)',
         's_format("^7%.2f: %s", stat.weightMult, UILocale.translate(stat.label))'),
        ('lastItemAnchor = controls["sortStatType"..tostring(i)]\n\t\tpopupHeight = popupHeight + 19',
         'lastItemAnchor = controls["sortStatType"..tostring(i)]\n'
         '\t\tlastItemAnchor:SetWrapWidth(popupWidth / 2 + 20)\n'
         '\t\tpopupHeight = popupHeight + lastItemAnchor:GetProperty("height") + 3'),
        ('s_format("%s: %.2f", stat.label, stat.weightMult)',
         's_format("%s: %.2f", UILocale.translate(stat.label), stat.weightMult)'),
        ('main:OpenPopup(popupWidth, popupHeight, "Query Options", controls)',
         'UILocale.prepareTradeTooltips(controls)\n\tmain:OpenPopup(popupWidth, popupHeight, "Query Options", controls)', 2),
        ('local totalWidth = 340', 'local totalWidth = popupWidth - 60'),
        ('{-45, -10, 80, 20}', '{UILocale.language == "ru" and -55 or -45, -10, UILocale.language == "ru" and 100 or 80, 20}'),
        ('{45, -10, 80, 20}', '{UILocale.language == "ru" and 55 or 45, -10, UILocale.language == "ru" and 100 or 80, 20}'),
        ('\t\tdropdown.shown = function()',
         '\t\tdropdown.displayLabelAccessor = UILocale.tradeModLabel\n'
         '\t\tdropdown.localizedSearchAccessor = UILocale.tradeModLabel\n'
         '\t\tdropdown.fitSelectedLabel = true\n'
         '\t\tdropdown.showFullLabelTooltip = true\n'
         '\t\tdropdown.shown = function()'),
        ('controls.jewelSlotLabel = new("LabelControl"',
         'controls.jewelSlot.displayLabelAccessor = function(slot) return UILocale.itemSlotLabel(slot.label) end\n'
         '\t\tcontrols.jewelSlotLabel = new("LabelControl"'),
    ])
