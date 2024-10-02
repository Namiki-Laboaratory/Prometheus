import bpy

from . import props


UIListIDname = "AD_UL_"


def ListCheck(structure, idx, dic_to_find:dict):
    try: 
        item = structure[idx]
    except IndexError:
        pass
    else:
        if not item.Target:
            structure.remove(idx)
            idx -= 1
        else:
                if not dic_to_find.find(item.Target.name) + 1:
                    structure.remove(idx)
                    idx -= 1

def SyncListToProp(target: list, structure:props.BaseUIListStructure):
    AllTargets = target

    for i, (k, col) in enumerate(structure.items()):
        if col.Target not in AllTargets:
            structure.remove(i)
        else:
            AllTargets.remove(col.Target)
            col.name = col.Target.name

    for col in AllTargets:
        Add_Col = structure.add()
        Add_Col.name = col.name
        Add_Col.Target = col

class UL_SelectedTarget(bpy.types.UIList):
    bl_idname = UIListIDname + "SelectedTarget"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item:
            item_name = ''
            try:
                item_name = item.Target.name
            except AttributeError:
                item_name = item.name

            split = layout.split(factor=0.05, align=True)
            split.label(icon_value=icon)
            layout.label(text=item_name, translate=False)

class UL_SelectCollectionForTrack(bpy.types.UIList):
    bl_idname = UIListIDname + "SelectedCollectionForTrack"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        
        layout.use_property_split = False
        split = layout.split(factor=0.05, align=True)
        split.prop(scene.P_S.Obj.Collections[item.name], "bTracked", text="")
        split = layout.split(factor=0.05, align=True)
        split.label(text=item.name, translate=False, icon_value=icon)
        layout.label(text=item.name, translate=False)

Reigster = [UL_SelectedTarget, UL_SelectCollectionForTrack]