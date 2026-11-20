local json = require("dkjson")
local update = {}
local repository = "chehlao1989-oss/PathOfBuilding-PoE2-RU"
local base = "https://github.com/" .. repository .. "/releases/download/"

local function parts(tag)
	if type(tag) ~= "string" then return end
	local major, minor, patch, revision, suffix = tag:match("^v(%d+)%.(%d+)%.(%d+)%-ru%.(%d+)(.*)$")
	if not major then return end
	local beta = suffix:match("^%-beta%.(%d+)$")
	if suffix ~= "" and not beta then return end
	return {tonumber(major), tonumber(minor), tonumber(patch), tonumber(revision), beta and tonumber(beta) or math.huge}
end

local function newer(a, b)
	for i = 1, #a do
		if a[i] ~= b[i] then return a[i] > b[i] end
	end
	return false
end

function update.selectRelease(current, releases)
	local best = parts(current)
	if not best or type(releases) ~= "table" then return nil, "Неверный формат версии." end
	local selected
	for _, release in ipairs(releases) do
		local tag = release.tag_name
		local candidate = parts(tag)
		if candidate and not release.draft and newer(candidate, best) then
			local name = "PoB2-RU-" .. tag:sub(2) .. "-Windows.zip"
			for _, asset in ipairs(release.assets or {}) do
				local sha = (asset.digest or ""):match("^sha256:([0-9a-f]+)$")
				if asset.name == name and asset.browser_download_url == base .. tag .. "/" .. name and sha and #sha == 64 then
					selected, best = {tag = tag, sha = sha}, candidate
				end
			end
		end
	end
	return selected
end

function update.check(launcher, background)
	if launcher.updateCheckRunning then return end
	launcher.lastUpdateCheck = GetTime()
	local function report(message)
		if not background then table.insert(launcher.main.toastMessages, message) end
	end
	local versionFile = io.open("RU-VERSION.json", "rb")
	if not versionFile then return report("Не найден файл версии русской сборки.") end
	local version = json.decode(versionFile:read("*a"))
	versionFile:close()
	if not version or not parts(version.tag) then return report("Не удалось прочитать версию сборки.") end
	launcher.updateCheckRunning = true
	local id = launcher:DownloadPage("https://api.github.com/repos/" .. repository .. "/releases?per_page=30", function(response, err)
		launcher.updateCheckRunning = false
		if err then return report("Не удалось проверить обновления. Попробуйте позже.") end
		local release, problem = update.selectRelease(version.tag, json.decode(response.body))
		if problem then return report(problem) end
		local previous = launcher.ruRelease
		launcher.ruRelease = release
		if release then
			if not background or not previous or previous.tag ~= release.tag then
				table.insert(launcher.main.toastMessages, "Доступна русская PoB " .. release.tag:sub(2) .. "\nДля установки нажмите «Обновить PoB».")
			end
		else
			report("Установлена актуальная русская сборка.")
		end
	end, {secureUpdate = true})
	if not id then
		launcher.updateCheckRunning = false
		report("Не удалось запустить проверку обновлений.")
	end
end

function update.install(release)
	local ffi = require("ffi")
	ffi.cdef "unsigned long __stdcall GetCurrentProcessId(void);"
	SpawnProcess(GetRuntimePath() .. "/PoB2RUUpdater", release.tag .. " " .. release.sha .. " " .. tostring(tonumber(ffi.C.GetCurrentProcessId())))
end

return update
