local json = require("dkjson")
local update = dofile("Modules/RuUpdate.lua")
local function release(version)
    local tag, name = "v" .. version, "PoB2-RU-" .. version .. "-Windows.zip"
    return {tag_name=tag, draft=false, assets={{name=name, digest="sha256:"..string.rep("a",64),
        browser_download_url="https://github.com/chehlao1989-oss/PathOfBuilding-PoE2-RU/releases/download/"..tag.."/"..name}}}
end
local old = release("0.23.1-ru.1-beta.2")
local nextBeta = release("0.23.1-ru.1-beta.10")
local stable = release("0.23.1-ru.1")
assert(update.selectRelease(old.tag_name, {old,nextBeta}).tag == nextBeta.tag_name)
assert(update.selectRelease(nextBeta.tag_name, {stable,nextBeta}).tag == stable.tag_name)
assert(not update.selectRelease(stable.tag_name, {old,nextBeta,stable}))
local staged = release("1.0.0-ru.1")
staged.draft=true
assert(not update.selectRelease(old.tag_name, {staged}))
staged.draft=false
staged.assets[1].browser_download_url="https://example.org/file"
assert(not update.selectRelease(old.tag_name, {staged}))
local launcher = {main={toastMessages={}}}
function GetTime() return 100 end
local callback
function launcher:DownloadPage(url, cb, options)
    assert(url:match("api.github.com/repos/chehlao1989%-oss/PathOfBuilding%-PoE2%-RU/releases"))
    assert(options.secureUpdate)
    callback = cb
    return 1
end
update.check(launcher, true)
assert(launcher.updateCheckRunning)
callback({body=json.encode({old,nextBeta})})
assert(not launcher.updateCheckRunning and launcher.ruRelease.tag == nextBeta.tag_name)
assert(#launcher.main.toastMessages == 1)
update.check(launcher, true)
callback(nil,"offline")
assert(not launcher.updateCheckRunning and #launcher.main.toastMessages==1)
function GetRuntimePath() return "." end
function SpawnProcess(path, args)
    assert(path == "./PoB2RUUpdater" and args:match("^v0%.23%.1%-ru%.1%-beta%.10 %x+ %d+$"))
end
update.install(launcher.ruRelease)
print("RU discovery, notification, offline handling and installer arguments passed.")
