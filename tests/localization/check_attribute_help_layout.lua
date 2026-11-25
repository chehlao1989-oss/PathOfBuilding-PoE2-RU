local work = assert(os.getenv("POB_FIXTURE_ROOT"))
dofile(work .. "/verify_pob.lua")
local utf8 = require("lua-utf8")
local rawMeasure, rawDraw = UILocale.measureRaw, UILocale.drawRaw
UILocale.measureRaw = function(height, _, text)
	local width = 0
	for line in (tostring(text or "") .. "\n"):gmatch("(.-)\n") do
		width = math.max(width, utf8.len((StripEscapes(line))) * height * 0.55)
	end
	return width
end
local function fits(text, height, width)
	assert(utf8.isvalid(text))
	for line in (text .. "\n"):gmatch("(.-)\n") do
		assert(UILocale.measureRaw(height, "VAR", line) <= width, "Text exceeds available width: " .. line)
	end
end
local function attributeNode()
	local best
	for _, node in pairs(build.spec.nodes) do
		if node.isAttribute and not node.alloc and node.path and (not best or #node.path < #best.path) then best = node end
	end
	return assert(best, "Missing reachable attribute node")
end

local savedW, savedH = main.screenW, main.screenH
for _, language in ipairs({"ru", "en"}) do
	UILocale.setLanguage(language)
	for _, size in ipairs({{1920,1080},{1280,720},{970,600},{660,480},{480,400}}) do
		main.screenW, main.screenH = unpack(size)
		build.treeTab:ModifyAttributePopup(attributeNode())
		local popup = assert(main.popups[1])
		local label = popup.controls.hotkeyTooltip
		local text = label:GetWrappedLabel()
		local plain = StripEscapes(text):gsub("\n", " ")
		if language == "ru" then
			assert(plain:find("ЛКМ", 1, true) and plain:find("ПКМ", 1, true))
			assert(plain:find("последней использованной характеристикой", 1, true))
			assert(not plain:find("Right-click", 1, true) and not plain:find("Intelligence", 1, true))
		else
			assert(plain:find("left mouse button", 1, true) and plain:find("Right-click", 1, true))
		end
		for _, value in ipairs({colorCodes.INTELLIGENCE .. '"1"', colorCodes.STRENGTH .. '"2"', colorCodes.DEXTERITY .. '"3"', colorCodes.RARE}) do
			assert(text:find(value, 1, true), "Missing original attribute color/key")
		end
		for _, key in ipairs({'"I"', '"S"', '"D"'}) do assert(text:find(key, 1, true)) end
		fits(text, 16, label:GetProperty("wrapWidth"))
		local px, py = popup:GetPos()
		local lx, ly = label:GetPos()
		assert(px >= 0 and py - 10 >= 0 and px + popup.width <= main.screenW and py + popup.height <= main.screenH)
		assert(lx >= px + 16 and lx + label:GetProperty("width") <= px + popup.width - 16)
		assert(ly >= select(2, popup.controls.save:GetPos()) + popup.controls.save.height + 15)
		assert(ly + label:GetProperty("height") <= py + popup.height - 16)
		local dx = popup.controls.attrSelect:GetPos()
		assert(dx + popup.controls.attrSelect.width / 2 == px + popup.width / 2)
		print("ATTRIBUTE_POPUP", language, size[1], size[2], popup.width, popup.height)
		main:ClosePopup()
	end
end

local getScreen, getTime = GetVirtualScreenSize, GetTime
local clock, width, height = 10000, 1920, 1080
GetVirtualScreenSize = function() return width, height end
GetTime = function() return clock end
for _, language in ipairs({"ru", "en"}) do
	UILocale.setLanguage(language)
	for _, size in ipairs({{1920,1080},{1280,720},{970,600},{660,480}}) do
		width, height = unpack(size)
		for _, message in ipairs({
			"Доступна русская PoB 0.23.1-ru.1-beta.4\nДля установки нажмите «Обновить PoB».",
			"No update available\nYou are running the latest version.",
			"^xFF7700" .. ("Ж"):rep(65) .. "\nСтрока 1\n\nСтрока 2",
		}) do
			main.toastMessages = { message }
			main.toastMode = nil
			local drawn = {}
			UILocale.drawRaw = function(x,y,align,size,font,text)
				if text == main.toastTitle then drawn.title = {x=x,y=y,text=text} end
				if text == main.toastBody then drawn.body = {x=x,y=y,text=text} end
			end
			main:OnFrame()
			clock = clock + 300
			main:OnFrame()
			assert(main.toastMode == "SHOWN")
			fits(main.toastTitle, 20, 300)
			fits(main.toastBody, 16, 300)
			assert(drawn.title and drawn.body, "Toast layout not used by OnFrame drawing")
			local _, bodyLines = main.toastBody:gsub("\n", "")
			local bodyBottom = drawn.body.y + (bodyLines + 1) * 16
			local buttonY = select(2, main.controls.dismissToast:GetPos())
			assert(drawn.body.y >= drawn.title.y + main.toastTitleHeight)
			assert(bodyBottom + 8 <= buttonY and buttonY + 20 <= height - 58)
			assert(drawn.title.x + 300 <= 308 and height - main.mainBarHeight >= 0)
			print("TOAST_LAYOUT", language, width, main.toastTitleHeight, main.toastHeight)
		end
	end
end
UILocale.drawRaw = rawDraw
GetVirtualScreenSize, GetTime = getScreen, getTime
main.toastMessages, main.toastMode, main.mainBarHeight = {}, nil, 58
main.screenW, main.screenH = savedW, savedH

-- Exercise the actual viewer click path and its real attribute allocation methods.
local reference = assert(io.open(work .. "/reference-build.xml", "rb"))
local xml = reference:read("*a"); reference:close()
local cursor, keyDown = GetCursorPos, IsKeyDown
local viewport = {x=312, y=40, width=1000, height=680}
local held
GetCursorPos = function() return viewport.x + viewport.width / 2, viewport.y + viewport.height / 2 end
IsKeyDown = function(key) return key == held end
local function reset()
	loadBuildFromXML(xml, "Attribute QA")
	runCallback("OnFrame")
	local node = attributeNode()
	local viewer = build.treeTab.viewer
	viewer.zoom = 1
	local scale = math.min(viewport.width, viewport.height) / build.spec.tree.size
	viewer.zoomX, viewer.zoomY = -node.x * scale, -node.y * scale
	return node, viewer
end
local function click(viewer, node, button)
	local events = button == "LEFT" and {{type="KeyDown",key="LEFTBUTTON"},{type="KeyUp",key="LEFTBUTTON"}} or {{type="KeyUp",key="RIGHTBUTTON"}}
	viewer:Draw(build, viewport, events)
	assert(viewer.hoverNode.id == node.id, "Click missed attribute node")
end
for _, case in ipairs({{"1",3,"Intelligence"},{"I",3,"Intelligence"},{"2",1,"Strength"},{"S",1,"Strength"},{"3",2,"Dexterity"},{"D",2,"Dexterity"}}) do
	local node, viewer = reset()
	held = case[1]
	click(viewer, node, "LEFT")
	assert(not main.popups[1] and build.spec.attributeIndex == case[2])
	assert(build.spec.nodes[node.id].alloc and build.spec.nodes[node.id].dn == case[3])
	print("ATTRIBUTE_HOTKEY", case[1], case[3])
end
held = nil
local node, viewer = reset()
click(viewer, node, "LEFT")
assert(main.popups[1] and main.popups[1].title == "Choose Attribute")
main:ClosePopup()
build.spec.attributeIndex = 2
click(viewer, node, "RIGHT")
assert(build.spec.nodes[node.id].alloc and build.spec.nodes[node.id].dn == "Dexterity")
for _, expected in ipairs({"Intelligence", "Strength", "Dexterity"}) do
	click(viewer, build.spec.nodes[node.id], "RIGHT")
	assert(build.spec.nodes[node.id].dn == expected)
end
GetCursorPos, IsKeyDown = cursor, keyDown
UILocale.measureRaw = rawMeasure
print("Attribute help RU/EN, popup/toast geometry and real LMB/RMB/hotkey behavior passed")
