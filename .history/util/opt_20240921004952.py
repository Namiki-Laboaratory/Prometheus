import bpy
from bpy.types import Operator as Opt

from . import props

OptIDName = "ad_util."

def ListCheck(self, context, structure, idx, dic_to_find:dict):
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

class OP_UI_SyncSelectedCollectionsToProp(Opt):
    bl_idname = OptIDName + "sync_collecetions"
    bl_label = "Sync Selected Collections to Prop"
    previous_collection = set()

    def execute(self, context):
        scene = context.scene
        AllCollections = list(bpy.data.collections)

        # print(scene.P_S.Obj.Collections.keys())

        for i, (k, col) in enumerate(scene.P_S.Obj.Collections.items()):
            if col.Collection not in AllCollections:
                scene.P_S.Obj.Collections.remove(i)
            else:
                AllCollections.remove(col.Collection)
                col.name = col.Collection.name

        for col in AllCollections:
            Add_Col = scene.P_S.Obj.Collections.add()
            Add_Col.name = col.name
            Add_Col.Collection = col

        return {'FINISHED'}

class OP_UI_List_actions_Object(Opt):
    """Move items up and down, add and remove"""
    bl_idname = OptIDName + "list_action_object"
    bl_label = "List Actions"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}

    action : bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", "")
            )
        )

    panel_name: bpy.props.StringProperty()
    structure_name: bpy.props.StringProperty()
    idx_name: bpy.props.StringProperty()
    type: bpy.props.StringProperty()

    def invoke(self, context, event):
        self.scn = context.scene

        Prop_Gropu = getattr(self.scn.P_S, self.panel_name)
        self.structure = getattr(Prop_Gropu, self.structure_name)
        self.idx = getattr(Prop_Gropu, self.idx_name)

        return self.execute(context)

    def execute(self, context):
        Type = 'MESH'
        Type = self.type
        # if self.panel_name == 'Mat' or self.panel_name == 'Physics':
        #     Type = 'MESH'
        # elif self.panel_name == 'Camera':
        #     Type = 'CURVE'

        scn = self.scn
        structure = self.structure
        idx = self.idx

        try:
            item = structure[idx]
        except IndexError:
            pass

        if self.action == 'DOWN' and idx < len(structure) - 1:
            item_next = structure[idx+1].Target.name
            structure.move(idx, idx+1)
            idx += 1
            info = 'Item "%s" moved to position %d' % (item.Target.name, idx + 1)
            self.report({'INFO'}, info)

        elif self.action == 'UP' and idx >= 1:
            item_next = structure[idx-1].Target.name
            structure.move(idx, idx-1)
            idx -= 1
            info = 'Item "%s" moved to position %d' % (item.Target.name, idx + 1)
            self.report({'INFO'}, info)

        elif self.action == 'REMOVE':
            if len(structure) > 0:
                info = 'Item "%s" removed from list' % (structure[idx].Target.name)
                structure.remove(idx)
                idx -= 1
                self.report({'INFO'}, info)
            else:
                info = 'No item to be removed'
                self.report({'INFO'}, info)

        elif self.action == 'ADD':
            selected_objects = []
            objects_holder = []

            if context.selected_objects:
                for each_obj in context.selected_objects:
                    if each_obj.type == Type:
                        selected_objects.append(each_obj)
            else:
                self.report({'INFO'}, "No objects selected in the Viewport")

            if not selected_objects:
                self.report({'INFO'}, "No %s objects selected in the Viewport" % Type)
            else:
                for stored_objects in structure:
                    objects_holder.append(stored_objects.Target)

                difference = set(selected_objects).difference(set(objects_holder))

                if difference:
                    for obj in difference:
                        idx += 1
                        item = structure.add()
                        item.Target = obj
                        scn.P_S.Mat.Index = len(structure)-1
                        info = '"%s" added to list %s' % (item.Target.name, self.panel_name)
                        self.report({'INFO'}, info)
                else:
                    self.report({'INFO'}, "All selected MESH objects have been selected!")
        return {"FINISHED"}

class OP_UI_clearList(Opt):
    """Clear all items of the list"""
    bl_idname = OptIDName + "clear_list"
    bl_label = "Clear List"
    bl_description = "Clear all items of the list"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.P_S)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if bool(context.scene.P_S.Mat.SelectedMesh):
            context.scene.P_S.Mat.SelectedMesh.clear()
            self.report({'INFO'}, "All items removed")
        else:
            self.report({'INFO'}, "Nothing to remove")
        return{'FINISHED'}

Register = [OP_UI_ListCheck, OP_UI_SyncSelectedCollectionsToProp, OP_UI_List_actions_Object, OP_UI_clearList]