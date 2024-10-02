import bpy

UIListIDname = "AD_UL_"

class UL_SelectedTarget(bpy.types.UIList):
    bl_idname = UIListIDname + "SelectedObjects"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene

        if item:
            layout.label(text=item.Target.name, translate=False)

Reigster = [UL_SelectedTarget]