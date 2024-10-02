import os
import shutil
import random
from mathutils import Matrix

import bpy
from bpy.types import Operator as Opt

OptIDName = "ad_util."

def util_mkdir(path: str):
    # Make a dir or clear it if it exists #
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        # delete all files in this dir
        del_list = os.listdir(path)
        for f in del_list:
            file_path = os.path.join(path, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    return path


def util_Random_iterable(seed: str, name: str, target, min, max):
    seed_tmp = seed + name
    for i in range(len(target)):
        seed_tmp += str(i)
        random.seed(seed_tmp)
        if isinstance(target[i], int):
            target[i] = random.randint(min,max)
        else:
            target[i] = random.uniform(min,max)
    return target

def util_Random(seed: str, name: str, min, max):
    seed_tmp = seed + name
    random.seed(seed_tmp)
    if isinstance(max, int):
        target = random.randint(min,max)
    else:
        target = random.uniform(min,max)
    return target

def util_ApplyTransform(object: bpy.types.Object):
    mw = object.matrix_world
    mb = object.matrix_basis

    loc, rot, scale = mb.decompose()

    T = Matrix.Translation(loc)
    R = rot.to_matrix().to_4x4()
    S = Matrix.Diagonal(scale).to_4x4()

    if hasattr(object.data, "transform"):
        object.data.transform(R @ S)
    for c in object.children:
        c.matrix_local = (R @ S) @ c.matrix_local

    object.matrix_basis.identity
    bpy.context.view_layer.update()


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
                    self.report({'INFO'}, "All selected %s objects have been added!" % Type)
        return {"FINISHED"}


Register = [OP_UI_List_actions_Object]