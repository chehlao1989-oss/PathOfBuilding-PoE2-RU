local work = assert(os.getenv("POB_FIXTURE_ROOT"))
dofile(work .. "/verify_pob.lua")
local utf8 = require("lua-utf8")
local locale = LoadModule("Modules/CharacterImportLocale")
UILocale.measureRaw = function(size, _, text)
	local max = 0
	for line in (tostring(text or "") .. "\n"):gmatch("(.-)\n") do
		max = math.max(max, utf8.len((StripEscapes(line))) * size * 0.55)
	end
	return max
end
launch.DownloadPage = function() error("Unexpected network request in character import layout test") end
local tab = build.importTab
local c = tab.controls
main.api = { authToken = "test-only" }
local character = { name = "Персонаж для проверки", class = "Witchhunter", level = 43, league = "Forbidden Rites" }
tab.lastCharList = { character }
c.charSelectLeague:SetList({ { label = character.league, league = character.league }, { label = "All" } })
local function rect(control, checkbox)
	local x,y = control:GetPos()
	local w,h = control:GetSize()
	if checkbox then x,w = x-control.labelWidth,w+control.labelWidth end
	return {x=x,y=y,w=w,h=h}
end
local function inside(control, container, checkbox)
	local r,p = rect(control, checkbox),rect(container)
	assert(r.x >= p.x and r.x+r.w <= p.x+p.w and r.y >= p.y and r.y+r.h <= p.y+p.h,
		"Control outside section: " .. tostring(control.label))
end
local function separate(a,b, checkboxA,checkboxB)
	local x,y = rect(a,checkboxA),rect(b,checkboxB)
	assert(x.x+x.w <= y.x or y.x+y.w <= x.x or x.y+x.h <= y.y or y.y+y.h <= x.y,
		"Overlapping controls: " .. tostring(a.label) .. " / " .. tostring(b.label))
end
local statuses = {
	"Not authenticated", "Authenticated", "Retrieving character list...", "Character list successfully retrieved.",
	"Retrieving character data...", "Passive tree and jewels successfully imported.", "Items and skills successfully imported.",
	"Sign-in is required.", "Account profile is private.", "Account name is incorrect.",
	"Requests are being sent too fast, try again in 12 seconds.", "Error retrieving character list, try again (Response code: 500)",
	"Error importing character data, try again (Response code: 503)", "Error processing character list, try again later",
	"The account has no characters to import.", "Failed to retrieve character data, try again.",
	"Error processing character data, try again later.", "Logging in... (27)", "Authentication failed: 401",
}
local saved = build:SaveDB("code")
for _, language in ipairs({"ru","en"}) do
	UILocale.setLanguage(language)
	tab:BuildCharacterList(character.league)
	assert(c.charSelect.list[1].char == character)
	assert(c.charSelectLeague:GetSelValueByKey("league") == "Forbidden Rites")
	assert(c.accountRealm:GetSelValueByKey("realmCode") == "poe2")
	assert(c.charSelect.list[1].label == character.name)
	if language == "ru" then
		assert(c.charSelect.list[1].detail:find("Охотник на ведьм",1,true))
		assert(c.charSelect.list[1].detail:find("ур. 43",1,true))
		assert(c.charSelectLeague.displayLabelAccessor(c.charSelectLeague.list[1]) == "Запретные ритуалы")
	end
	for _, status in ipairs(statuses) do
		local text = locale.statusText("^1"..status)
		assert(text:sub(1,2) == "^1")
		if language == "ru" then assert(text ~= "^1"..status,"Untranslated status: "..status)
		else assert(text == "^1"..status) end
		for _, mode in ipairs({"AUTHENTICATION","GETACCOUNTNAME","DOWNLOADCHARLIST","SELECTCHAR","IMPORTING"}) do
			for _, width in ipairs({970,660,500}) do
				tab.charImportMode,tab.charImportStatus = mode,status
				tab:Draw({x=312,y=40,width=width,height=850},{})
				inside(c.charImportStatusLabel,c.sectionCharImport)
				for _, key in ipairs({"logoutApiButton","authenticateButton","accountNameHeader","accountRealm","accountNameGo","charSelectHeader","charSelectLeague","charSelect","charImportHeader","charImportTree","charImportItems"}) do
					local control = c[key]
					if control:IsShown() then inside(control,c.sectionCharImport) end
				end
				separate(c.sectionCharImport,c.sectionBuild)
				if c.logoutApiButton:IsShown() then separate(c.logoutApiButton,c.charImportStatusLabel) end
				if mode == "SELECTCHAR" or mode == "IMPORTING" then
					local keys = {"charImportTree","charImportItems","charImportTreeClearJewels","charImportItemsClearSkills","charImportItemsClearItems","charImportItemsIgnoreWeaponSwap"}
					for i,key in ipairs(keys) do
						inside(c[key],c.sectionCharImport,i>2)
						for j=1,i-1 do separate(c[key],c[keys[j]],i>2,j>2) end
					end
				end
			end
		end
	end
	-- Display changes must not rewrite the selected character, league or build.
	assert(character.name == "Персонаж для проверки" and character.class == "Witchhunter")
	assert(build:SaveDB("code") == saved)
end
print("CHECK", "character import status, non-overlapping controls in five stages and three widths, ru/en, raw identifiers and saved build stable")
