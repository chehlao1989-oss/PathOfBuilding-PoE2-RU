def patch_item_clipboard(edit, build):
    edit("Modules/Common.lua", [
        (
            "function sanitiseText(text)",
            "function sanitiseText(text, preserveUnicode)",
        ),
        (
            '\treturn text:find("[\\128-\\255<]") and text',
            '\tif not text:find("[\\128-\\255<]") then return text end\n'
            '\tlocal preserveUtf8 = preserveUnicode and utf8.len(text)\n'
            '\ttext = text',
        ),
        (
            '\t\t-- single-byte: Windows-1252 and similar',
            '\t-- Keep valid item names and untranslated modifiers readable.\n'
            '\tif preserveUtf8 then return text end\n'
            '\treturn text\n'
            '\t\t-- single-byte: Windows-1252 and similar',
        ),
        (
            '\t\t:gsub("[\\128-\\255]", "?")\n\t\tor text',
            '\t\t:gsub("[\\128-\\255]", "?")',
        ),
    ])
    edit("Classes/Item.lua", [
        (
            "self:ParseRaw(sanitiseText(raw), rarity, highQuality)",
            "self:ParseRaw(sanitiseText(raw, true), rarity, highQuality)",
        ),
    ], source=build)
