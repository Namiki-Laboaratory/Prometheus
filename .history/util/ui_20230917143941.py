import bpy

UIListIDname = "AD_UL_"

class UL_SelectedCollections(bpy.types.UIList):
    bl_idname = UIListIDname + "SelectedCollections"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        
        layout.use_property_split = False
        split = layout.split(factor=0.05, align=True)
        split.prop(scene.P_S.Obj.Collections[item.name], "bTracked", text="")
        split.label(text=item.name, translate=False, icon_value=icon)

class UL_SelectedObjects(bpy.types.UIList):
    bl_idname = UIListIDname + "SelectedObjects"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene

        if item:
            layout.label(text=item.Object.name, translate=False)

Reigster = [UL_SelectedCollections, UL_SelectedObjects]