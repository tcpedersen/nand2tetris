class SymbolTable:
    def __init__(self):
        self.classTable = dict()

        self.scope = {
            "static": "class",
            "field": "class",
            "arg": "subroutine",
            "var": "subroutine",
        }

    def startSubroutine(self):
        self.subroutineTable = dict()

    def define(self, varName, varType, varKind):
        entry = {
            "type": varType,
            "kind": varKind,
            "index": self.varCount(varKind),
        }

        if self.scope[varKind] == "class":
            self.classTable[varName] = entry
        elif self.scope[varKind] == "subroutine":
            self.subroutineTable[varName] = entry
        else:
            raise ValueError("something went wrong.")

    def varCount(self, kind):
        varCount = 0
        for table in [self.classTable, self.subroutineTable]:
            for key, values in table.items():
                if values["kind"] == kind:
                    varCount += 1

        return varCount

    def _getEntry(self, varName):
        if varName in self.subroutineTable:
            return self.subroutineTable[varName]
        elif varName in self.classTable:
            return self.classTable[varName]
        else:
            return None

    def kindOf(self, name):
        entry = self._getEntry(name)
        if entry is not None:
            return entry["kind"]
        return None

    def typeOf(self, name):
        return self._getEntry(name)["type"]

    def indexOf(self, name):
        return self._getEntry(name)["index"]
