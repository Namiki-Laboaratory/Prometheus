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


def UpdateGetSceneData(
        target_class,
        context,
        update_target_name:str,
        scene_target_name:str,
        ):
    update_target = getattr(target_class, update_target_name)
    scene_target = getattr(context.scene, scene_target_name)
    setattr(target_class, update_target_name, scene_target)


def AmountCheck(
        target_class,
        context, 
        check_value_name:str,
        target_value_name:str,
        bCheckMax=True, # True for Max, false for min
        bTargetSceneValue=False,
        ):
    check_value = getattr(target_class, check_value_name)
    target_value = getattr(context.scene, target_value_name) if bTargetSceneValue else getattr(target_class, target_value_name)
    if bCheckMax:
        if check_value > target_value:
            setattr(target_class, check_value_name, target_value)
            check_value = target_value
    else:
        if check_value < target_value:
            setattr(target_class, check_value_name, target_value)


class BaseUIListStructure(PropertyGroup):
    Target: PointerProperty(type=bpy.types.ID)


Register = [BaseUIListStructure]
