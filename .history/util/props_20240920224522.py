import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty,
                       )
from bpy.types import (PropertyGroup)

def CheckMaterialValue(self, context, name, action):
    if name == 'Metallic':
        Max = self.MetallicMax
        Min = self.MetallicMin
    elif name == 'Roughness':
        Max = self.RoughnessMin
        Min = self.RoughnessMax
    elif name == 'Specular':
        Max = self.SpecularMax
        Min = self.SpecularMin

    if Max < Min: 
        if action == 'Max':
            self[name+'Min'] = Max
        elif action == 'Min':
            self[name+'Max'] = Min

Register = []
