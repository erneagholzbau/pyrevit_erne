
# List of available pyRevit erne scripts:

## Data


### Data_Dump_Chosen

Collects data of selected category elements into csv.


### Data_Dump_Doors

Collects door data into csv.


### Data_Dump_Full

Collects floor data into csv.


### Data_Dump_Furniture

Collects furniture data into csv.


### Data_Dump_Rooms

Collects rooms data into csv.


### Data_Dump_Str_Columns

Collects structural columns data into csv.


## Doors


### Doors_Aufschlag_DIN_Wall_Info

set Aufschlagrichtung_DIN parameter on all appropriate doors


###### required parameters:

` Name: Opening_side_DIN` <br>
`Categories: Doors` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: GENERAL` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>

` Name: Revit_Id` <br>
`Categories: Floors,Walls,Rooms,Doors,Windows` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: GENERAL` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>


## ERNE


### Build_Sandbox

Builds a sandboxed / git-ignored script file to experiment with python and pyRevit


### Ensure_Shared_Parameters

Ensures all shared parameters for pyRevit ERNE scripts are
available in current model - created if necessary


###### required parameters:

` Name: db_project_name` <br>
`Categories: ProjectInformation` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: GENERAL` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>

` Name: Planart` <br>
`Categories: Sheets` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: VIEWS` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>

` Name: Planinfo` <br>
`Categories: Sheets` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: VIEWS` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>


### reload

Reload pyRevit into new session.


## git


## Inspect


### Detail_Items_Listing

Lists Detail Items placed on Legend Views


### Detail_Line_Coordinates

Shows coordinates of one Line element and X / Y / Z deltas to check for skew
Typical candidate: Detail line, Grid, Wall


### Elements_Of_Selected_Level

Lists elements for selected level


### Family_Formula_Overview

Select Family Instances like doors and get
a listing of formula parameters.


### Find_Current_View_Orphaned_Tags

Find orphaned tags showing ? in current view


### Find_Orphaned_Tags

Find orphaned tags showing ? in project


### Groups_Overview

Lists groups in project


### Lines_Per_View_Counter

Lists lines per view in project


### List_Constraints

Lists constraints in current model


### List_DWGs

Lists linked and imported DWGs in project


### List_Raster_Images

Lists raster images in project


### List_Scopeboxes

Lists scope boxes in project


### Materials_Overview

Lists materials in project


### Non_Sheet_Views_Creators

Lists views not on sheets


### Skewed_View_Directions

Lists skewed view directions


### Sqm_Of_Selected_Rooms

Square meters of selected rooms


## Model


### Adapto1Day_ifc2rvt

Prepares a Adapto1Day model
opened IFC from rh2bb2rvt for use in rvt.
Merges doubled walls, replaces doors,
replaces and flips windows,
joins floors and walls, creates rooms.


### Create_Free_Form_Element

Converts selected ACIS solid in family into
DirectShape with shape handles and material


### Create_Room_Floors

Creates a floor for each selected room or all rooms.
FloorType is selected from room parameter "Floor Finish" or first FloorType.


###### required parameters:

` Name: Exclude_from_floor_creation` <br>
`Categories: Doors, Rooms` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: GENERAL` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: YesNo` <br>

` Name: Floor_create_with_target_floor_type` <br>
`Categories: Rooms` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: GENERAL` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>

` Name: Belongs_to_room` <br>
`Categories: Floors` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: GENERAL` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>


### Get_Joined_To_Selected

Lists elements joined to selected element


### Redraw_MIP_Windows

Redraws all model-in-place windows with windows of scripted window family


### Void_Cutter

Select a nested RVT link. The script will search through this linked model.
It will create accordingly sized void instances, based on the bounding box size of
found "WD - RECH" generic models in that link, and will mirror a set of parameters.
The Voids are set to the closest "Building Story" level.
It will cut intersecting walls, floors, roofs and structural framings of predefined
types (see white lists and black lists) with these voids.
Furthermore will it check existing voids if they need to be recut, based on current
conditions in the model.
Rotation of void is currently not yet implemented!!
prerequisite: GEN_Void_Box.rfa
source: GEN_Void_Box.rfa
source updated 20210907


## Rooms


### Rooms_Window_Area

Writes sum of window area of appropriate windows into
room parameter Fensterflaeche, except for explicitly
excluded windows by parameter Fensterflaeche_Exklusion


###### required parameters:

` Name: Window_area` <br>
`Categories: Rooms` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: ROOMS` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Area` <br>

` Name: Window_area_exclusion` <br>
`Categories: Windows` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: WINDOWS` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: YesNo` <br>

` Name: Revit_Id` <br>
`Categories: Rooms` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: GENERAL` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>

` Name: Ratio_Room_area_Window_area` <br>
`Categories: Rooms` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: ROOMS` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Number` <br>


### Tag_Rooms_In_Views

Creates a tag for each selected room or all rooms in view or all rooms in all selected views.
Tag type is chosen in dialog.


## Schedules


### Schedules_CSV_Export

Exports all selected schedules in Project browser as
csv tables both in raw and formatted mode


## Sheets


### Duplicate_Sheets_With_Views

Your active Sheet View with placed views will be duplicated.
If multiple sheets are selected in project browser, all of those get duplicated.
If view with name collision exist, this will not work - please clean them up first


### Set_Sheet_Data

Collects sheet data into parameter "Projektname Zusatz 1" in pattern:
"{Planausgabedatum}_{Phase?}_{Projektnummer}_{Planart}_{Plannummer}_{Planinfo}_{Index}"


###### required parameters:

` Name: Projekt_Phase` <br>
`Categories: ProjectInformation` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: GENERAL` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>

` Name: Planart` <br>
`Categories: Sheets` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: VIEWS` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>

` Name: Planinfo` <br>
`Categories: Sheets` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: VIEWS` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>

` Name: Planbenennung` <br>
`Categories: Sheets` <br>
`Group_parameter_under: Data` <br>
`Shared_Parameter_Group: VIEWS` <br>
`Type_Instance: Instance` <br>
`Type_of_parameter: Text` <br>


## Walls


### Wall_Allow_Join_Ends

Allow join at both wall ends for selected walls.


### Wall_Disallow_Join_Ends

Disallow join at both wall ends for selected walls.

