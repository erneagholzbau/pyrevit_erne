from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import ElementId
from System.Diagnostics import Stopwatch
from collections import defaultdict
from rpw import doc, db
from rph import param

def get_window_area(window):
    height = window.Symbol.LookupParameter("Height").AsDouble()
    width  = window.Symbol.LookupParameter("Width" ).AsDouble()
    print(window.Name, height * ft_m, width * ft_m)
    return height * width


stopwatch = Stopwatch()
stopwatch.Start()

window_area_param_name = "Fensterflaeche_Tag"
exclude_param_name     = "Fensterflaeche_Exklusion"
use = "FromRoom" #  "ToRoom"
ft_m = 0.304800609

windows = Fec(doc).OfCategory(Bic.OST_Windows).WhereElementIsNotElementType().ToElements()

window_area_by_room = defaultdict(float)

for phase in doc.Phases:
    last_phase = phase
print("using phase: {}".format(last_phase.Name))

for window in windows:
    window_id = window.Id
    print("________\nwindow_id: {}".format(window_id))
    if param.get_val(window, exclude_param_name):
        print("skipping window excluded by parameter")
        continue

    window_room = getattr(window, use)[last_phase]
    if window_room:
        print(window_room)
        window_area = get_window_area(window)
        window_area_by_room[window_room.Id.IntegerValue] += window_area

with db.Transaction("window area per room"):
    for room_id, area in window_area_by_room.items():
        room = doc.GetElement(ElementId(room_id))
        room_name = param.get_val(room, "Name")
        print("________\nroom: {} - {}".format(room_id, room_name))
        print(room, area)
        param.set_val(room, window_area_param_name, area)


#print("{} updated in: ".format(__file__))

stopwatch.Stop()
print(stopwatch.Elapsed)