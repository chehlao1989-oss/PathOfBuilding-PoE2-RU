local work = os.getenv("POB_FIXTURE_ROOT")
dofile(work .. "/verify_pob.lua")

local utf8 = require("lua-utf8")
local treeTab = build.treeTab
local search = treeTab.controls.treeSearch
local ctrl = false
IsKeyDown = function(key) return key == "CTRL" and ctrl end

local function checkEdit(before, caret, selection, key, withCtrl, expected)
	search:SetText(before, true)
	search.caret = caret or search.caret
	search.sel = selection
	ctrl = withCtrl
	search:OnKeyDown(key)
	ctrl = false
	assert(search.buf == expected, "Unexpected result for " .. key .. ": " .. search.buf)
	assert(utf8.isvalid(search.buf) and treeTab.viewer.searchStr == expected)
	search:OnKeyDown("BACK") -- Exercise consecutive edits in the same field.
	assert(utf8.isvalid(search.buf))
end

checkEdit("плетёныш", nil, nil, "BACK", false, "плетёны")
checkEdit("плетёныш", #"плет" + 1, nil, "DELETE", false, "плетныш")
checkEdit("a🛡б", 2, nil, "DELETE", false, "aб")
checkEdit("a🛡б", #"a🛡" + 1, nil, "BACK", false, "aб")
checkEdit("искра сила  ", nil, nil, "BACK", true, "искра ")
checkEdit("искра  сила", #"искра" + 1, nil, "DELETE", true, "искра")
checkEdit("искра сила", #"искра " + 1, 1, "DELETE", false, "сила")
checkEdit("Spark", nil, nil, "BACK", false, "Spar")

search:SetText("плетёныш", true)
search:OnKeyDown("BACK")
search:Undo()
assert(search.buf == "плетёныш")
search:Redo()
assert(search.buf == "плетёны")

local viewport = { x = 312, y = 40, width = 1600, height = 740 }
search:SetText("СИЛАх", true)
search:OnKeyDown("BACK")
treeTab:Draw(viewport, {})
assert(treeTab.viewer.searchParams[1] == "сила")
search:SetText("СИЛА" .. string.char(0xD1), true)
treeTab:Draw(viewport, {})
assert(utf8.isvalid(treeTab.viewer.searchParams[1]))

local popupText, panelColor
DrawString = function(_, _, _, _, _, text) popupText = text end
SetDrawColor = function(r, g, b) panelColor = { r, g, b } end
local background
DrawImage = function() background = panelColor end
launch:DrawPopup(1, 0, 0, "^0%s", "Ошибка поиска")
assert(popupText == "^xEEEEEEОшибка поиска")
assert(background[1] < 0.2 and background[2] < 0.2 and background[3] < 0.2)
print("Tree search editing and error popup checks passed")
