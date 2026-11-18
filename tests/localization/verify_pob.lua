local fixtureRoot = os.getenv("POB_FIXTURE_ROOT")
arg = {}
local wrapper = fixtureRoot .. "/upstream-downloads/HeadlessWrapper.lua"
local oldLoad = loadfile
function loadfile(filename)
	if filename == "Launch.lua" then
		function GetScriptPath() return "." end
		function GetRuntimePath() return "." end
		local file = assert(io.open(filename, "rb"))
		local source = file:read("*a")
		file:close()
		return loadstring((source:gsub("^#[^\n]*\n", "\n")), "@Launch.lua")
	end
	return oldLoad(filename)
end
local oldDoFile = dofile
function dofile(filename)
	if filename == "Launch.lua" then
		return assert(loadfile(filename))()
	end
	return oldDoFile(filename)
end

dofile(wrapper)
assert(build and launch.main, "PoB failed to load")

local ffi = require("ffi")
ffi.cdef([[
unsigned long compressBound(unsigned long sourceLen);
int compress2(unsigned char *dest, unsigned long *destLen, const char *source, unsigned long sourceLen, int level);
int uncompress(unsigned char *dest, unsigned long *destLen, const char *source, unsigned long sourceLen);
]])
local zlib = ffi.load("zlib1")
function Deflate(data)
	local capacity = zlib.compressBound(#data)
	local buffer = ffi.new("unsigned char[?]", capacity)
	local count = ffi.new("unsigned long[1]", capacity)
	assert(zlib.compress2(buffer, count, data, #data, 6) == 0)
	return ffi.string(buffer, count[0])
end
function Inflate(data)
	local capacity = 4096
	while capacity <= 16000000 do
		local buffer = ffi.new("unsigned char[?]", capacity)
		local count = ffi.new("unsigned long[1]", capacity)
		local status = zlib.uncompress(buffer, count, data, #data)
		if status == 0 then return ffi.string(buffer, count[0]) end
		if status ~= -5 then return nil end
		capacity = capacity * 2
	end
end

newBuild()
assert(not launch.promptMsg, launch.promptMsg)

local source = fixtureRoot .. "/reference-build.xml"
local fixture = io.open(source, "rb")
if fixture then
	local state = fixture:read("*a")
	fixture:close()
	loadBuildFromXML(state, "QA Spark")
else
	assert(not UILocale, "Fixture must be generated in the baseline")
	build.skillsTab.socketGroupList[1] = {
		gemList = {{
			gemId = "Metadata/Items/Gems/SkillGemSpark",
			level = 12, quality = 10, enabled = true,
		}},
		enabled = true,
		includeInFullDPS = true,
	}
	build.skillsTab:ProcessSocketGroup(build.skillsTab.socketGroupList[1])
	build.calcsTab:BuildOutput()
	fixture = assert(io.open(source, "wb"))
	fixture:write(build:SaveDB("code"))
	fixture:close()
end

assert(not launch.promptMsg, launch.promptMsg)
local startNode = build.spec.nodes[build.spec.curClass.startNodeId]
local allocated
for _, node in ipairs(startNode.linked) do
	if node.type == "Normal" and node.path then
		build.spec:AllocNode(node)
		allocated = node.id
		break
	end
end
assert(allocated and build.spec.allocNodes[allocated], "No control passive allocated")
build.calcsTab:BuildOutput()
print("CHECK", "allocated passive", allocated)
local output = build.calcsTab.mainOutput
local statKeys = { "TotalDPS", "CombinedDPS", "AverageDamage", "Life", "FireResist", "ColdResist", "LightningResist", "ChaosResist" }
for _, key in ipairs(statKeys) do
	print("CHECK", key, output[key])
end
assert(output.TotalDPS > 1, "Expected the fixture to use Spark")

if UILocale then
	local expectedLanguage = os.getenv("POB_EXPECTED_LANGUAGE") or "ru"
	assert(UILocale.language == expectedLanguage, "Wrong saved language loaded")
	print("CHECK", "saved language", UILocale.language)
	UILocale.setLanguage("ru")
	assert(UILocale.translate("^7Options") == "^7Настройки")
	assert(UILocale.translate("1. Item") == "1. Item")
	UILocale.setLanguage("en")
	assert(UILocale.translate("Options") == "Options")
	UILocale.setLanguage("ru")
	local entry = assert(UILocale.passive("0_5", 39567, "Ingenuity"))
	assert(entry.name == "Изобретательность")
	assert(entry.stats["+25 to Intelligence"] == "+25 к интеллекту")
	assert(not UILocale.passive("0_3", 39567, "Ingenuity"))
	assert(not UILocale.passive("0_5", 39567, "Changed name"))
	local viewer = build.treeTab.viewer
	local search = build.treeTab.controls.treeSearch
	local utf8 = require("lua-utf8")
	search:Insert("ИЗОБРЕТАТЕЛЬНОСТЬ")
	assert(search.buf == "ИЗОБРЕТАТЕЛЬНОСТЬ")
	runCallback("OnFrame")
	assert(viewer.searchStrResults[39567], "Russian tree search missed Ingenuity")
	search:SetText("INGENUITY", true)
	runCallback("OnFrame")
	assert(viewer.searchStrResults[39567], "English tree search missed Ingenuity")
	print("CHECK", "tree search", "ru/en")
	local tooltip = new("Tooltip")
	viewer:AddNodeTooltip(tooltip, build.spec.nodes[39567], build, 0)
	local russianTitle, russianStat
	for _, line in ipairs(tooltip.lines) do
		if type(line.text) == "string" then
			russianTitle = russianTitle or line.text:find("Изобретательность", 1, true)
			russianStat = russianStat or line.text:find("+25 к интеллекту", 1, true)
		end
	end
	assert(russianTitle and russianStat, "The tree tooltip misses the localized name or stat")
	print("CHECK", "tree tooltip", "ok")
end

local exportPath = fixtureRoot .. "/verify-share-code.txt"
if UILocale then
	build.importTab.controls.generateCode.onClick()
	local code = build.importTab.controls.generateCodeOut.buf
	assert(#code > 200, "Build export did not generate a share code")
	local codeFile = assert(io.open(exportPath, "wb"))
	codeFile:write(code)
	codeFile:close()
else
	local codeFile = io.open(exportPath, "rb")
	if codeFile then
		local code = codeFile:read("*a")
		codeFile:close()
		build.importTab.controls.importCodeIn:SetText(code, true)
		assert(build.importTab.importCodeValid, "Source PoB did not recognize exported code")
		build.importTab.controls.importCodeGo.onClick()
		runCallback("OnFrame")
		assert(build.spec.allocNodes[allocated], "Allocated passive was lost on import")
		assert(build.calcsTab.mainOutput.TotalDPS == output.TotalDPS)
		print("CHECK", "stock round-trip", "ok")
	end
end

if UILocale then
	local xml = build:SaveDB("code")
	loadBuildFromXML(xml, "QA round trip")
	assert(not launch.promptMsg, launch.promptMsg)
	assert(build.spec.allocNodes[allocated], "Allocated passive was lost on load")
	assert(build.calcsTab.mainOutput.TotalDPS == output.TotalDPS)
	print("CHECK", "round-trip", "ok")
end

if os.getenv("POB_UI_AUDIT") == "1" then
	local json = require("dkjson")
	local file = assert(io.open(fixtureRoot .. "/ui-audit.json", "wb"))
	local strings = {}
	local tab = ""
	local function record(_, _, _, _, _, label)
		if type(label) == "string" then strings[tab][label] = true end
	end
	if UILocale then
		UILocale.drawRaw = record
	else
		DrawString = record
	end
	for _, mode in ipairs({ "TREE", "SKILLS", "ITEMS", "CALCS", "CONFIG", "NOTES", "PARTY", "COMPARE", "IMPORT" }) do
		tab = mode
		strings[tab] = {}
		build.viewMode = mode
		runCallback("OnFrame")
		assert(not launch.promptMsg, launch.promptMsg)
	end
	file:write(json.encode(strings))
	file:close()
end
