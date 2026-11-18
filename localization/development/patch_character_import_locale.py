def patch_character_import_locale(edit, build):
    edit("Classes/ImportTab.lua", [
        ('local tradeHelpers = LoadModule("Classes/TradeHelpers")',
         'local tradeHelpers = LoadModule("Classes/TradeHelpers")\nlocal importLocale = LoadModule("Modules/CharacterImportLocale")'),
        ('return "^7Character import status: "..UILocale.translate(type(self.charImportStatus) == "function" and self.charImportStatus() or self.charImportStatus)',
         'return "^7"..UILocale.translate("Character import status:").." "..importLocale.statusText(type(self.charImportStatus) == "function" and self.charImportStatus() or self.charImportStatus)'),
        ('\t-- validate the status of the api the first time',
         '\timportLocale.prepare(self)\n\n\t-- validate the status of the api the first time'),
        ('\tself:ProcessControlsInput(inputEvents, viewPort)',
         '\timportLocale.layout(self)\n\n\tself:ProcessControlsInput(inputEvents, viewPort)'),
        ('string.format("%s%s ^x808080lvl %d in %s", classColor, charClass, charLvl, charLeague)',
         'importLocale.characterDetail(classColor, charClass, charLvl, charLeague)'),
        ('string.format("%s%s ^x808080lvl %d", classColor, charClass, charLvl)',
         'importLocale.characterDetail(classColor, charClass, charLvl)'),
        ('searchFilter = charName.." "..charClass,',
         'searchFilter = charName.." "..charClass.." "..UILocale.translate(charClass),'),
    ], source=build)
