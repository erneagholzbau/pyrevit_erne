# -*- coding: cp1252 -*-
"""
Exports all selected schedules in Project browser as
csv tables both in raw and formatted mode
"""
import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import ViewScheduleExportOptions, ExportTextQualifier, ExportColumnHeaders
from System.Diagnostics import Stopwatch
from rpw.ui.forms import select_folder
from rpw import doc, uidoc
import datetime


def get_sched_raw_options():
    sched_opt = ViewScheduleExportOptions()
    sched_opt.Title = False
    sched_opt.FieldDelimiter = ";"
    sched_opt.HeadersFootersBlanks = False
    sched_opt.TextQualifier = ExportTextQualifier.None
    ViewScheduleExportOptions.ColumnHeaders.SetValue(
        sched_opt,
        ExportColumnHeaders.None,
    )
    return sched_opt


def get_sched_formatted_options():
    sched_opt = ViewScheduleExportOptions()
    sched_opt.Title = True
    sched_opt.FieldDelimiter = ";"
    sched_opt.HeadersFootersBlanks = True
    sched_opt.TextQualifier = ExportTextQualifier.None
    ViewScheduleExportOptions.ColumnHeaders.SetValue(
        sched_opt,
        ExportColumnHeaders.MultipleRows,
    )
    return sched_opt


export_dir = select_folder()
export_modes = {
    "raw"      : get_sched_raw_options(),
    "formatted": get_sched_formatted_options(),
}

stopwatch = Stopwatch()
stopwatch.Start()

selection = [doc.GetElement(elId) for elId in uidoc.Selection.GetElementIds()]
today_date = str(datetime.datetime.now().date()).replace("-","")

for view in selection:
    if str(view.ViewType) != 'Schedule':
        continue

    sched_name = view.Name.replace(" ", "_")
    print("exporting: {}".format(sched_name))

    for mode, sched_opt in export_modes.items():
        view.Export(
            export_dir,
            "{}_{}_{}.csv".format(today_date, sched_name, mode),
            sched_opt,
        )

stopwatch.Stop()
print("{} exported in: ".format(__file__))
print(stopwatch.Elapsed)
