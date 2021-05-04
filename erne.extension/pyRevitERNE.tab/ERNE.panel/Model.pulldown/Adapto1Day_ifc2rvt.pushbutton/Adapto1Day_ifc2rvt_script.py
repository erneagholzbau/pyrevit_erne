"""
Prepares a Adapto1Day model
opened IFC from rh2bb2rvt for use in rvt.
Merges doubled walls, replaces doors,
replaces and flips windows,
joins floors and walls, creates rooms.
"""
import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import BuiltInParameter as Bip
from Autodesk.Revit.DB.Structure.StructuralType import NonStructural as non_struct
from Autodesk.Revit.DB import ElementId, XYZ, Outline, BoundingBoxIntersectsFilter
from Autodesk.Revit.DB import JoinGeometryUtils
from Autodesk.Revit.DB import Line, Wall
from System.Collections.Generic import List
from System.Diagnostics import Stopwatch
from collections import defaultdict
from rpw import doc, db
from rph import param, bbx


# TODO map floor type from reference
# DONE switch window external directions
# DONE dynamically create window/door size types
# DONE redraw split wall
# DONE join floors
# TODO write params to replaced elements
# TODO respect wall level offsets
# TODO derive wall type
# TODO derive door type
# TODO derive floor type


def get_bbox_info(wall_bbox, inner_offset=None, outer_offset=None):
    wall_info = {}
    wall_info["bbox_centroid"] = bbx.bbox_centroid(wall_bbox)
    bbox_x_dir = bbx.bbox_long_edge_is_x_vector(wall_bbox)
    bbox_y_dir = bbx.bbox_long_edge_is_y_vector(wall_bbox)
    inner_offset = inner_offset or 0.0
    outer_offset = outer_offset or 0.0
    if bbox_y_dir:
        mid_start_pt   = XYZ(
            wall_info["bbox_centroid"].X,
            wall_bbox.Min.Y,
            wall_bbox.Min.Z,
        )
        mid_end_pt     = XYZ(
            wall_info["bbox_centroid"].X,
            wall_bbox.Max.Y,
            wall_bbox.Min.Z,
        )
        outer_end_pt   = XYZ(
            wall_bbox.Max.X - outer_offset,
            wall_bbox.Min.Y,
            wall_bbox.Min.Z,
        )
        outer_start_pt = XYZ(
            wall_bbox.Max.X - outer_offset,
            wall_bbox.Max.Y,
            wall_bbox.Min.Z,
        )
        inner_start_pt = XYZ(
            wall_bbox.Min.X + inner_offset,
            wall_bbox.Min.Y,
            wall_bbox.Min.Z,
        )
        inner_end_pt   = XYZ(
            wall_bbox.Min.X + inner_offset,
            wall_bbox.Max.Y,
            wall_bbox.Min.Z,
        )
        wall_info["width"]  = bbx.bbox_edge_length(wall_bbox, "x")
        wall_info["length"] = bbx.bbox_edge_length(wall_bbox, "y")
        wall_info["dir"] = "y"
    elif bbox_x_dir:
        mid_start_pt   = XYZ(
            wall_bbox.Min.X,
            wall_info["bbox_centroid"].Y,
            wall_bbox.Min.Z,
        )
        mid_end_pt     = XYZ(
            wall_bbox.Max.X,
            wall_info["bbox_centroid"].Y,
            wall_bbox.Min.Z,
        )
        outer_end_pt   = XYZ(
            wall_bbox.Min.X,
            wall_bbox.Min.Y + outer_offset,
            wall_bbox.Min.Z,
        )
        outer_start_pt = XYZ(
            wall_bbox.Max.X,
            wall_bbox.Min.Y + outer_offset,
            wall_bbox.Min.Z,
        )
        inner_start_pt = XYZ(
            wall_bbox.Min.X,
            wall_bbox.Max.Y - inner_offset,
            wall_bbox.Min.Z,
        )
        inner_end_pt   = XYZ(
            wall_bbox.Max.X,
            wall_bbox.Max.Y - inner_offset,
            wall_bbox.Min.Z,
        )
        wall_info["width"]  = bbx.bbox_edge_length(wall_bbox, "y")
        wall_info["length"] = bbx.bbox_edge_length(wall_bbox, "x")
        wall_info["dir"] = "x"
    if bbox_x_dir or bbox_y_dir:
        wall_info["mid_line"]   = Line.CreateBound(mid_start_pt,   mid_end_pt)
        wall_info["outer_line"] = Line.CreateBound(outer_start_pt, outer_end_pt)
        wall_info["inner_line"] = Line.CreateBound(inner_start_pt, inner_end_pt)
        wall_info["height"] = bbx.bbox_edge_length(wall_bbox, "z")
        return wall_info


def redraw_doubled_wall_from_split_huells(wall_huell1, wall_huell2, wall_type_id):
    print("attempt to redraw wall from 2 split huells")
    print(wall_huell1.Id, wall_huell2.Id)
    # print(wall_huell1.LevelId, wall_huell2.LevelId)
    wall_lvl_id = wall_huell1.LevelId if not wall_huell1.LevelId.IntegerValue == -1 else wall_huell2.LevelId
    if wall_lvl_id.IntegerValue == -1:
        print("skipping walls {} and {} with lvl id: {}".format(
            wall_huell1.Id, wall_huell2.Id, wall_lvl_id
        ))
        return
    wall1_guid = param.get_val(wall_huell1, "IfcGUID")
    wall2_guid = param.get_val(wall_huell2, "IfcGUID")
    wall_guids = "{}::split::{}".format(wall1_guid, wall2_guid)
    wall1_bbox = wall_huell1.get_BoundingBox(None)
    wall2_bbox = wall_huell2.get_BoundingBox(None)
    bbox_bottom_offset = wall1_bbox.Min.Z - doc.GetElement(wall_lvl_id).Elevation
    combined_bbox = bbx.get_combined_bbox([wall1_bbox, wall2_bbox])
    combined_info = get_bbox_info(combined_bbox)
    wall_type = doc.GetElement(wall_type_id)
    print(wall_type.get_Parameter(Bip.WALL_ATTR_WIDTH_PARAM).AsDouble(), combined_info["width"])
    wall = Wall.Create(
        doc,
        combined_info["mid_line"],
        wall_type_id,
        wall_lvl_id,
        combined_info["height"],
        bbox_bottom_offset, # offset
        False, # flip
        False, # structural
    )
    wall.get_Parameter(Bip.ALL_MODEL_INSTANCE_COMMENTS).Set(wall_guids)
    doc.Delete(wall_huell1.Id)
    doc.Delete(wall_huell2.Id)
    return wall


def redraw_door_window_from_huell(huell, fam_type, wall, offset=0.0):
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
    doc.Delete(huell.Id)
    return elem


def get_wall_pairs(wall_bboxes_by_id):
    threshold = 0.65616 # ~200mm
    matches = {}
    for eid1, wall_bbx1 in wall_bboxes_by_id.items():
        for eid2, wall_bbx2 in wall_bboxes_by_id.items():
            if eid1 == eid2:
                continue
            if eid1 in matches.keys():
                continue
            if eid1 in matches.values():
                continue
            #print(35*"-")
            #print(eid1, eid2)
            wall_bbx1_info = get_bbox_info(wall_bbx1)
            wall_bbx2_info = get_bbox_info(wall_bbx2)
            # direction same
            if wall_bbx1_info["dir"] != wall_bbx2_info["dir"]:
                #print("NO: different direction: {}::{}".format(wall_bbx1_info["dir"], wall_bbx2_info["dir"]))
                continue
            # z height
            if abs(wall_bbx1.Min.Z - wall_bbx2.Min.Z) > threshold:
                #print("NO: low_to_far: {}".format(abs(wall_bbx1.Min.Z - wall_bbx2.Min.Z)))
                continue
            if abs(wall_bbx1.Max.Z - wall_bbx2.Max.Z) > threshold:
                #print("NO: high_to_far: {}".format(abs(wall_bbx1.Max.Z - wall_bbx2.Max.Z)))
                continue
            # x location
            if abs(wall_bbx1.Min.X - wall_bbx2.Min.X) > threshold:
                #print("NO: xmin_to_far: {}".format(abs(wall_bbx1.Min.X - wall_bbx2.Min.X)))
                continue
            if abs(wall_bbx1.Max.X - wall_bbx2.Max.X) > threshold:
                #print("NO: xmax_to_far: {}".format(abs(wall_bbx1.Max.X - wall_bbx2.Max.X)))
                continue
            # y location
            if abs(wall_bbx1.Min.Y - wall_bbx2.Min.Y) > threshold:
                #print("NO: ymin_to_far: {}".format(abs(wall_bbx1.Min.Y - wall_bbx2.Min.Y)))
                continue
            if abs(wall_bbx1.Max.Y - wall_bbx2.Max.Y) > threshold:
                #("NO: ymax_to_far: {}".format(abs(wall_bbx1.Max.Y - wall_bbx2.Max.Y)))
                continue
            #print(
            #    abs(wall_bbx1.Min.Z - wall_bbx2.Min.Z),
            #    abs(wall_bbx1.Max.Z - wall_bbx2.Max.Z),
            #    abs(wall_bbx1.Min.X - wall_bbx2.Min.X),
            #    abs(wall_bbx1.Max.X - wall_bbx2.Max.X),
            #    abs(wall_bbx1.Min.Y - wall_bbx2.Min.Y),
            #    abs(wall_bbx1.Max.Y - wall_bbx2.Max.Y),
            #)
            print(eid1, eid2)
            matches[eid1] = eid2
    matched_walls = [(doc.GetElement(ElementId(k)), doc.GetElement(ElementId(v))) for k, v in matches.items()]
    print("found {} matches".format(len(matches)))
    return matched_walls


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


def redraw_wall_huell_contained_elems(wall, wall_bbx):
    global cx_cats
    outline = Outline(wall_bbx.Min, wall_bbx.Max)
    cx_filter = BoundingBoxIntersectsFilter(outline)
    cx_filter.Tolerance = -0.1
    for cat, info in cx_cats.items():
        cx_elems = Fec(doc, info["inst_ids"]).OfCategory(info["bic"]).WherePasses(cx_filter).ToElements()
        print(cx_elems)
        if not cx_elems:
            print(35 * "-")
            print(cat, wall.Id.IntegerValue, wall)
            continue
        for cx_elem in cx_elems:
            cx_id = cx_elem.Id.IntegerValue
            print(25 * "-")
            print(cx_id, cx_elem, cx_elem.Name)
            elem_type_name = param.get_val(cx_elem.Symbol, "rvt_fam_type")
            if not elem_type_name:
                elem_type_name = param.get_val(cx_elem.Symbol, "FamType")
            elem_type = get_or_create_type(info, elem_type_name)
            elem_type = info["types"].get(elem_type_name)
            if not elem_type:
                print("could not find rvt {} type {}".format(cat, elem_type_name))
                continue
            if cx_id in info["drawn_ids"]:
                print("already redrawn {}".format(cx_id))
                continue
            redraw_door_window_from_huell(cx_elem, elem_type, wall)
            info["drawn_ids"].append(cx_id)


stopwatch = Stopwatch()
stopwatch.Start()

levels  = Fec(doc).OfCategory(Bic.OST_Levels ).WhereElementIsNotElementType().ToElements()
walls   = Fec(doc).OfCategory(Bic.OST_Walls  ).WhereElementIsNotElementType().ToElements()
doors   = Fec(doc).OfCategory(Bic.OST_Doors  ).WhereElementIsNotElementType().ToElements()
windows = Fec(doc).OfCategory(Bic.OST_Windows).WhereElementIsNotElementType().ToElements()
floors  = Fec(doc).OfCategory(Bic.OST_Floors ).WhereElementIsNotElementType().ToElements()

wall_bboxes_by_id   = {wa.Id.IntegerValue:wa.get_BoundingBox(None) for wa in walls}
door_bboxes_by_id   = {do.Id.IntegerValue:do.get_BoundingBox(None) for do in doors}
window_bboxes_by_id = {wi.Id.IntegerValue:wi.get_BoundingBox(None) for wi in windows}

door_ids   = List[ElementId]([ElementId(eid_int) for eid_int in door_bboxes_by_id  ])
window_ids = List[ElementId]([ElementId(eid_int) for eid_int in window_bboxes_by_id])

door_types = Fec(doc).OfCategory(Bic.OST_Doors).WhereElementIsElementType().ToElements()
door_types_by_fam_type_name = {
    "{}::{}".format(dt.FamilyName, dt.get_Parameter(Bip.ALL_MODEL_TYPE_NAME).AsString()):dt for dt in door_types
}

window_types = Fec(doc).OfCategory(Bic.OST_Windows).WhereElementIsElementType().ToElements()
window_types_by_fam_type_name = {
    "{}::{}".format(wt.FamilyName, wt.get_Parameter(Bip.ALL_MODEL_TYPE_NAME).AsString()):wt for wt in window_types
}

wall_types = Fec(doc).OfCategory(Bic.OST_Walls).WhereElementIsElementType().ToElements()
wall_types_by_type_name = {
    wt.get_Parameter(Bip.ALL_MODEL_TYPE_NAME).AsString():wt for wt in wall_types
}

FT_MM = 304.8
NON_STRUCTURAL = False

double_wall_type_id = wall_types_by_type_name["IW 240 FA AA CC Modultrennwand doppelt"].Id

cx_cats = {
    "doors"  : {
        "bic"      : Bic.OST_Doors,
        "types"    : door_types_by_fam_type_name,
        "inst_ids" : door_ids,
        "drawn_ids": [],
    },
    "windows": {
        "bic"      : Bic.OST_Windows,
        "types"    : window_types_by_fam_type_name,
        "inst_ids" : window_ids,
        "drawn_ids": [],
    },
}

print("found {} wall bboxes".format(len(wall_bboxes_by_id)))


with db.Transaction("redraw_paired_walls_doors_windows"):
    wall_pairs = get_wall_pairs(wall_bboxes_by_id)
    for wall1, wall2 in wall_pairs:
        redraw_doubled_wall_from_split_huells(wall1, wall2, double_wall_type_id)

    doc.Regenerate()

walls = Fec(doc).OfCategory(Bic.OST_Walls  ).WhereElementIsNotElementType().ToElements()
wall_bboxes_by_id = {wa.Id.IntegerValue:wa.get_BoundingBox(None) for wa in walls}


with db.Transaction("redraw_wall_and_door"):
    for eid, wall_bbx in wall_bboxes_by_id.items():
        wall = doc.GetElement(ElementId(eid))
        if wall.LevelId.IntegerValue == -1:
            print("{} skipped mip-ds-wall".format(eid))
            continue
        print(55*"=")
        print(eid)
        redraw_wall_huell_contained_elems(wall, wall_bbx)


with db.Transaction("add_rooms"):
    for lvl in levels:
        if lvl.Name == "zero":
            continue
        param.set_val(lvl, "level_compute_height", 3.0, bip=True)
        added_rooms = doc.Create.NewRooms2(lvl)
        print("added {} rooms on level: {}".format(
            len(added_rooms),
            lvl.Name
        ))


windows = Fec(doc).OfCategory(Bic.OST_Windows).WhereElementIsNotElementType().ToElements()
windows_direction = "ToRoom"  # "FromRoom"

with db.Transaction("correct window flip direction"):
    for window in windows:
        window_id = window.Id
        print("________\nwindow_id: {}".format(window_id))
        window_phase = doc.GetElement(window.CreatedPhaseId)
        window_room = getattr(window, windows_direction)[window_phase]
        if window_room:
            # print("window correct")
            pass
        else:
            print("window not correct yet flipping it.")
            window.flipFacing()


floors  = Fec(doc).OfCategory(Bic.OST_Floors ).WhereElementIsNotElementType().ToElements()

floors_by_lvl_offset = defaultdict(list)
for floor in floors:
    floor_id = floor.Id
    floor_lvl_id = floor.LevelId
    print("________\nfloor_id: {}".format(floor_id))
    floor_lvl_offset = floor.get_Parameter(Bip.FLOOR_HEIGHTABOVELEVEL_PARAM).AsDouble()
    key = "{}_{}".format(floor_lvl_id, floor_lvl_offset)
    floors_by_lvl_offset[key].append({
        "floor": floor,
        "id": floor_id,
        "bbox": floor.get_BoundingBox(None),
    })

with db.Transaction("join floors"):
    for k, lvl_floors_infos in floors_by_lvl_offset.items():
        print("________\nfloor_infos: {}".format(k))
        for info in lvl_floors_infos:
            floor = info["floor"]
            floor_id = info["id"]
            other_floor_ids = [i["id"] for i in lvl_floors_infos if not i["id"] == floor_id]
            other_lvl_floor_ids = List[ElementId](other_floor_ids)
            bbox = info["bbox"]
            floor_outline = Outline(bbox.Min, bbox.Max)
            bbox_filter = BoundingBoxIntersectsFilter(floor_outline, 0.03)
            cx_floors = Fec(doc, other_lvl_floor_ids).OfCategory(Bic.OST_Floors).WherePasses(bbox_filter).ToElements()
            print("cx_floors: {}".format(cx_floors))
            for cx_floor in cx_floors:
                already_joined = JoinGeometryUtils.AreElementsJoined(doc, floor, cx_floor)
                if not already_joined:
                    print("joining: {} with {}".format(floor.Id, cx_floor.Id))
                    JoinGeometryUtils.JoinGeometry(doc, floor, cx_floor)


print("{} run in: ".format(__file__))
stopwatch.Stop()
print(stopwatch.Elapsed)
