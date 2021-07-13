"""
Redraws all model-in-place windows with windows of scripted window family
"""
import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import BuiltInParameter as Bip
from Autodesk.Revit.DB.Structure.StructuralType import NonStructural as non_struct
from Autodesk.Revit.DB import ElementId, XYZ, Outline, BoundingBoxIntersectsFilter
from System.Collections.Generic import List
from rpw import doc, db
from rph import bbx


def get_or_create_type(info, target_type_name):
    global check
    print("searching for: {}".format(target_type_name))
    existing_types = info["types"]
    if existing_types.get(target_type_name):
        print("found: {}".format(target_type_name))
        return existing_types[target_type_name]
    print("type not found! - creating: {}".format(target_type_name))
    first_symbol = None
    target_prefix = target_type_name.split("::")[0]
    target_suffix = target_type_name.split("::")[1]
    mm_width  = int(target_suffix.split("x")[0].strip())
    mm_heigth = int(target_suffix.split("x")[1].strip())
    for sym_name in info["types"]:
        sym_prefix = sym_name.split("::")[0]
        if sym_prefix == target_prefix:
            first_symbol = info["types"][sym_name]
            check = first_symbol
            print("found symbol to duplicate: {}".format(sym_name))
            break
    dup_symbol = first_symbol.Duplicate(target_suffix)
    existing_types[target_type_name] = dup_symbol
    ft_width  = mm_width  / FT_MM
    ft_height = mm_heigth / FT_MM
    dup_symbol.get_Parameter(Bip.CASEWORK_WIDTH ).Set(ft_width)
    dup_symbol.get_Parameter(Bip.CASEWORK_HEIGHT).Set(ft_height)
    dup_symbol.Activate()
    doc.Regenerate()
    return dup_symbol


def redraw_door_window_from_huell(huell, fam_type, wall, keep_original=None):
    print("attempt to redraw door/windows in wall", huell.Id.IntegerValue, wall.Id.IntegerValue)
    elem_bbox = huell.get_BoundingBox(None)
    bbox_centroid = bbx.bbox_centroid(elem_bbox)
    if not fam_type.IsActive:
        # print("activating symbol")
        fam_type.Activate()
        doc.Regenerate()
    if wall.LevelId.IntegerValue == -1:
        lvl_elevation = 0.0
        height_offset = elem_bbox.Min.Z - lvl_elevation
        elem = doc.Create.NewFamilyInstance(
            bbox_centroid,
            fam_type,
            wall,
            non_struct,
        )
    else:
        wall_level = doc.GetElement(wall.LevelId)
        lvl_elevation = wall_level.Elevation
        height_offset = elem_bbox.Min.Z - lvl_elevation
        elem = doc.Create.NewFamilyInstance(
            bbox_centroid,
            fam_type,
            wall,
            wall_level,
            non_struct,
        )
    elem.get_Parameter(Bip.INSTANCE_SILL_HEIGHT_PARAM).Set(height_offset)
    elem.flipFacing()
    if not keep_original:
        doc.Delete(huell.Id)
    return elem


FT_MM = 304.8
NON_STRUCTURAL = False

walls   = Fec(doc).OfCategory(Bic.OST_Walls  ).WhereElementIsNotElementType().ToElements()
windows = Fec(doc).OfCategory(Bic.OST_Windows).WhereElementIsNotElementType().ToElements()

wall_ids   = List[ElementId]([wall.Id   for wall   in walls  ])
window_ids = List[ElementId]([window.Id for window in windows])

window_bboxes_by_id = {wi.Id.IntegerValue:wi.get_BoundingBox(None) for wi in windows}

window_types = Fec(doc).OfCategory(Bic.OST_Windows).WhereElementIsElementType().ToElements()
window_types_by_fam_type_name = {
    "{}::{}".format(wt.FamilyName, wt.get_Parameter(Bip.ALL_MODEL_TYPE_NAME).AsString()):wt for wt in window_types
}

cx_cats = {
    "windows": {
        "bic"      : Bic.OST_Windows,
        "types"    : window_types_by_fam_type_name,
        "inst_ids" : window_ids,
        "drawn_ids": [],
    },
}

window_fam_name = "Scripted_FE"

with db.Transaction("redraw_mip_windows"):
    for window in windows:
        if not window.LevelId.IntegerValue == -1:
            print("{} skipped typed window".format(window.Id))
            continue

        mip_window = window

        window_bbx = mip_window.get_BoundingBox(None)

        outline = Outline(window_bbx.Min, window_bbx.Max)
        cx_filter = BoundingBoxIntersectsFilter(outline)
        cx_filter.Tolerance = -0.1
        cx_elems = Fec(doc, wall_ids).OfCategory(Bic.OST_Walls).WherePasses(cx_filter).ToElements()
        if not cx_elems:
            print("{} could not find an intersecting wall".format(window.Id))
            continue

        cx_wall = cx_elems[0]
        width = None
        if bbx.bbox_long_edge_is_x_vector(window_bbx):
            width = bbx.bbox_edge_length(window_bbx, "x")
        elif bbx.bbox_long_edge_is_y_vector(window_bbx):
            width = bbx.bbox_edge_length(window_bbx, "y")
        height = bbx.bbox_edge_length(window_bbx, "z")

        info = cx_cats["windows"]

        width_mm  = int(round(width  * FT_MM))
        height_mm = int(round(height * FT_MM))

        elem_type_name = "{}::{} x {}".format(
            window_fam_name, width_mm, height_mm
        )
        elem_type = info["types"].get(elem_type_name)
        if not elem_type:
            elem_type = get_or_create_type(info, elem_type_name)

        redraw_door_window_from_huell(mip_window, elem_type, cx_wall, keep_original=True)

