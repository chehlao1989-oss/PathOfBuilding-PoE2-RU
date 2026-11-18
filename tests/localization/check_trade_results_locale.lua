local work = assert(os.getenv("POB_FIXTURE_ROOT"))
dofile(work .. "/verify_pob.lua")
local utf8 = require("lua-utf8")
UILocale.measureRaw = function(size, _, text)
	return utf8.len((StripEscapes(tostring(text or "")))) * size * 0.55
end
main.screenW,main.screenH = 1282,906
main.viewPort = {x=0,y=0,width=1282,height=906}
main.api = {authToken=nil}
launch.DownloadPage = function() error("Unexpected network call in trade results test") end

local raw = "Rarity: RARE\nGolem Core\nBombard Crossbow\n--------\nQuality: +20%\n--------\n104% increased Physical Damage\nAdds 2 to 6 Physical Damage\n+9 to Strength"
local originalItem = new("Item",raw)
assert(originalItem.baseName == "Bombard Crossbow")
local saved = build:SaveDB("code")
local rawPayload = {item_string=raw,amount=158,currency="divine",weight=10}
local function capture(fn)
	local original = UILocale.drawRaw
	local rendered = {}
	UILocale.drawRaw = function(x,y,align,size,font,text)
		rendered[#rendered+1] = {x=x,y=y,align=align,size=size,text=text}
	end
	fn()
	UILocale.drawRaw = original
	return rendered
end
for _, language in ipairs({"ru","en"}) do
	UILocale.setLanguage(language)
	local trade = new("TradeQuery",build.itemsTab)
	trade.pbRealm,trade.pbLeague = "poe2","Forbidden Rites"
	trade.realmDropList = {"PoE 2"}
	trade.allLeagues.poe2 = {"Forbidden Rites","Standard"}
	build.itemsTab.leagueDropList = {"Forbidden Rites","Standard"}
	trade.resultTbl[1] = {rawPayload,{item_string=raw,amount=0.5,currency="exalted",weight=9}}
	trade.sortedResultTbl[1] = {{index=1},{index=2}}
	trade.itemIndexTbl[1] = 1
	trade:PriceItem()
	local popup = main.popups[#main.popups]
	local c = trade.controls
	local list = c.resultDropdown1
	assert(c.league:GetSelValue() == "Forbidden Rites")
	local rendered = capture(function() c.league:Draw(main.viewPort,true) end)
	local output = ""
	for _, line in ipairs(rendered) do output=output..line.text end
	assert(output:find(language=="ru" and "Запретные ритуалы" or "Forbidden Rites",1,true),output)
	-- League lists are empty until the asynchronous API callback arrives.
	c.league:SetList({})
	capture(function() c.league:Draw(main.viewPort,true) end)
	c.league:SetList({"Forbidden Rites","Standard"})
	local result = list.displayLabelAccessor(list.list[1])
	assert(list.list[1].label:find("Golem Core, Bombard Crossbow",1,true))
	assert(result:find(language=="ru" and "Громадное чистилище, Самострел бомбардира" or "Golem Core, Bombard Crossbow",1,true),result)
	assert(result:find(language=="ru" and "158 Божественная сфера" or "158 divine",1,true),result)
	assert(list.displayLabelAccessor(list.list[2]):find("0.5",1,true))
	for _, query in ipairs(language=="ru" and {"ГРОМАДНОЕ","GOLEM","бомбардира"} or {"GOLEM"}) do
		list:OnSearchChar(query)
		assert(list.searchInfos[1].matches,query)
		list:ResetSearch()
	end
	rendered=capture(function() list:Draw(main.viewPort,true) end)
	for _, line in ipairs(rendered) do
		assert(line.size == 16)
		assert(UILocale.measureRaw(line.size,"VAR",line.text) <= list.width-list.height+2)
	end
	local tooltip = new("Tooltip")
	list.tooltipFunc(tooltip,"BODY",1,list.list[1])
	list:SetSel(2)
	assert(trade.itemIndexTbl[1]==2 and trade.totalPrice[1].amount==0.5 and trade.totalPrice[1].currency=="exalted")

	-- Many currencies and large prices must fit the footer, with the full text available on hover.
	for index,currency in ipairs({"divine","mirror","exalted","chaos","alch","transmute","aug","regal","vaal","annul"}) do
		trade.totalPrice[index]={amount=1234567.5,currency=currency}
	end
	c.fullPrice.label="^7Total Price: "..trade:GetTotalPriceString()
	local fullText=UILocale.translate(c.fullPrice.label)
	rendered=capture(function() c.fullPrice:Draw(main.viewPort) end)
	assert(#rendered==1 and UILocale.measureRaw(rendered[1].size,"VAR",rendered[1].text) <= c.fullPrice.width)
	local fx,fy=c.fullPrice:GetPos()
	local px,py=popup:GetPos()
	assert(fx >= px and fx+c.fullPrice.width <= px+popup.width)
	assert(rendered[1].align == "LEFT" and rendered[1].x >= fx
		and rendered[1].x+UILocale.measureRaw(rendered[1].size,"VAR",rendered[1].text) <= fx+c.fullPrice.width)
	local addLine,hoverText = tooltip.AddLine
	tooltip.AddLine=function(_,_,text) hoverText=text end
	c.fullPrice.fullPriceTooltip.tooltipFunc(tooltip)
	tooltip.AddLine=addLine
	assert(hoverText == fullText)
	assert(fullText:find(language=="ru" and "Общая цена:" or "Total Price:",1,true))
	assert(rawPayload.item_string==raw and rawPayload.amount==158 and rawPayload.currency=="divine")
	assert(build:SaveDB("code")==saved)
	main:ClosePopup()
end
print("TRADE", "rendered league, live-result names/currencies, fractional prices, bilingual result search, selection mapping, footer bounds and unchanged API payload/build")
