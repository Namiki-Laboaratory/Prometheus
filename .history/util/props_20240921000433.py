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

Register = []

class BaseUIListStructure(PropertyGroup):
    Object: PointerProperty(type=bpy.types.Object)
    Collection: PointerProperty(type=bpy.types.Collection)
    Target: PointerProperty(type=bpy.types.Collection)
