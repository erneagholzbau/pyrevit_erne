﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import ImportInstance, WorksharingUtils
from collections import defaultdict
from rpw import doc

dwgs = Fec(doc).OfClass(ImportInstance).WhereElementIsNotElementType().ToElements()
dwg_insts = defaultdict(list)
ws_table = doc.GetWorksetTable()

for d in dwgs:
    if d.IsLinked:
        dwg_insts["linked"].append(d)
    else:
        dwg_insts["imported"].append(d)

for link_mode in dwg_insts:
    print("{}{}\n".format(len(dwg_insts[link_mode]), link_mode.upper()))
    for dwg in dwg_insts[link_mode]:
        dwg_workset = ws_table.GetWorkset(dwg.WorksetId).Name

        print("DWG created by:{0} Id: {1} DWGName:{2} on Workset: {3}".format(
                    WorksharingUtils.GetWorksharingTooltipInfo(doc, dwg.Id).Creator.ljust(12),
                    str(dwg.Id.IntegerValue).rjust(8),
                    dwg.LookupParameter("Name").AsString().rjust(6),
                    dwg_workset.ljust(110)))
