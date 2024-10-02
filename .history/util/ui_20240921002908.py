import bpy

UIListIDname = "AD_UL_"

class UL_SelectedTarget(bpy.types.UIList):
    bl_idname = UIListIDname + "SelectedTarget"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene

        if item:
            item_name = ''
            try:
                item_name = item.Target.name
            except KeyError:
                
            layout.label(text=item.name, translate=False)

Reigster = [UL_SelectedTarget]