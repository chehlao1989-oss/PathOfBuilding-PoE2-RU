def patch_item_runes(edit):
    edit("Classes/Item.lua", [
        (
            '\t\t\tif specName then\n\t\t\t\tif specName == "Unique ID" then',
            '\t\t\tlocal isItemProperty = specName ~= nil\n'
            '\t\t\tif specName then\n\t\t\t\tif specName == "Unique ID" then',
        ),
        (
            '\t\t\t\telseif specName == "Sockets" then\n\t\t\t\t\tlocal group = 0',
            '\t\t\t\telseif specName == "Sockets" then\n'
            '\t\t\t\t\t-- A repeated socket header replaces the same kind of socket block.\n'
            '\t\t\t\t\t-- Older saves can contain a stale copy among the modifiers.\n'
            '\t\t\t\t\tif specVal:find("S", 1, true) then\n'
            '\t\t\t\t\t\tself.sockets = { }\n'
            '\t\t\t\t\t\tself.runes = { }\n'
            '\t\t\t\t\tend\n'
            '\t\t\t\t\tif specVal:find("J", 1, true) then\n'
            '\t\t\t\t\t\tself.jewelSocketCount = 0\n'
            '\t\t\t\t\tend\n'
            '\t\t\t\t\tlocal group = 0',
        ),
        (
            'elseif specName == "Armour" or specName == "Evasion Rating" or specName == "Evasion" or specName == "Energy Shield" or specName == "Ward" then',
            'elseif specName == "Armour" or specName == "Evasion Rating" or specName == "Evasion" or specName == "Energy Shield" or specName == "Ward" or specName == "Runic Ward" then',
        ),
        (
            '\t\t\t\t\tself.armourData = self.armourData or { }\n'
            '\t\t\t\t\tself.armourData[specName] = specToNumber(specVal)',
            '\t\t\t\t\tif specName == "Runic Ward" then\n'
            '\t\t\t\t\t\tspecName = "Ward"\n'
            '\t\t\t\t\tend\n'
            '\t\t\t\t\tself.armourData = self.armourData or { }\n'
            '\t\t\t\t\tself.armourData[specName] = specToNumber(specVal)',
        ),
        (
            '\t\t\t\telseif not lineIsBaseImplicit and not (self.name:match(specName) and self.name:match(specVal)) then\n'
            '\t\t\t\t\tfoundExplicit = true\n'
            '\t\t\t\t\tgameModeStage = "EXPLICIT"\n'
            '\t\t\t\tend\n'
            '\t\t\tend\n'
            '\t\t\tif line == "Prefixes:" then',
            '\t\t\t\telse\n'
            '\t\t\t\t\tisItemProperty = false\n'
            '\t\t\t\t\tif not lineIsBaseImplicit and not (self.name:match(specName) and self.name:match(specVal)) then\n'
            '\t\t\t\t\t\tfoundExplicit = true\n'
            '\t\t\t\t\t\tgameModeStage = "EXPLICIT"\n'
            '\t\t\t\t\tend\n'
            '\t\t\t\tend\n'
            '\t\t\tend\n'
            '\t\t\t-- Item properties have already been consumed, even after a modifier.\n'
            '\t\t\tif isItemProperty then\n'
            '\t\t\t\tgoto continue\n'
            '\t\t\tend\n'
            '\t\t\tif line == "Prefixes:" then',
        ),
    ])
