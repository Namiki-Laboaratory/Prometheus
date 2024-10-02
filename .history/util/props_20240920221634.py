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

class BaseUIListStructure(PropertyGroup):
    Object: PointerProperty(type=bpy.types.Object)
    Collection: PointerProperty(type=bpy.types.Collection)


class TrackCollectionListStructure(BaseUIListStructure):
    bTracked: BoolProperty(default=False)


class MaterialMeshListStructure(BaseUIListStructure):
    # BaseColor : FloatVectorProperty(name="Base color", subtype='COLOR', default=(1,1,1), min=0, max=1)
    MetallicMax: FloatProperty(name='Metallic Max', default=1, min=0, max=1,
                                update= lambda self, context : CheckMaterialValue(self, context, 'Metallic', 'Max'))
    MetallicMin: FloatProperty(name='Metallic Min', default=0, min=0, max=1,
                                update= lambda self, context : CheckMaterialValue(self, context, 'Metallic', 'Min'))
    RoughnessMax: FloatProperty(name='Roughness Max', default=1, min=0, max=1,
                                 update= lambda self, context : CheckMaterialValue(self, context, 'Roughness', 'Max'))
    RoughnessMin: FloatProperty(name='Roughness Min', default=0.4, min=0, max=1,
                                 update= lambda self, context : CheckMaterialValue(self, context, 'Roughness', 'Min'))
    SpecularMax: FloatProperty(name='Specular Max', default=1, min=0, max=1,
                                update= lambda self, context : CheckMaterialValue(self, context, 'Specular', 'Max'))
    SpecularMin: FloatProperty(name='Specular Min', default=0.5, min=0, max=1,
                                update= lambda self, context : CheckMaterialValue(self, context, 'Specular', 'Min'))


class PhysicObjectsListStructure(BaseUIListStructure):
    Shape_Enu = [
        ('BOX', 'Box', "Box-like shapes (i.e. cubes), including planes (i.e. ground planes).", 'MESH_CUBE', 0),
        ('SPHERE', 'Sphere', "Sphere.", 'MESH_UVSPHERE', 1),
        ('CAPSULE', 'Capsule', "Capsule.", 'MESH_CAPSULE', 2),
        ('CYLINDER', 'Cylinder', "Cylinder.", 'MESH_CYLINDER', 3),
        ('CONE', 'Cone', "Cone.", 'MESH_CONE', 4),
        ('CONVEX_HULL', 'Convex Hull',
         "A mesh-like surface encompassing (i.e. shrinkwrap over) all vertices (best results with fewer vertices).",
         'MESH_ICOSPHERE', 5),
        ('MESH', 'Mesh',
         "Mesh consisting of triangles only, allowing for more detailed interactions than convex hulls.",
         'MESH_MONKEY', 6),
        ('COMPOUND', 'Compound Parent',
         "Combines all of its direct rigid body children into one rigid object.",
        'MESH_DATA', 7)
    ]
    Source_Enu = [
        ('BASE', 'Base', "Base mesh."),
        ('DEFORM', 'Deform', "Deformations (shape keys, deform modifiers)."),
        ('FINAL', 'Final', "All modifiers.")
    ]
    Mass: FloatProperty(name='Mass', default=1, min=0.001, max=4096)
    Shape: EnumProperty(name='Collision Shape', items=Shape_Enu, default='MESH')
    Source: EnumProperty(name='Collision Source', items=Source_Enu,default='BASE')
    Friction: FloatProperty(name='Friction', default=0.5, min=0.001, max=1)
    Bounciness: FloatProperty(name='Bounciness', default=0.5, min=0.001, max=1)
    Damping: FloatProperty(name='Damping', default=0.04, min=0.001, max=1)
    Rotation: FloatProperty(name='Rotation', default=0.1, min=0.001, max=1)


class CameraCurvesListStructure(BaseUIListStructure):
    bCameraFocus: BoolProperty(name='Keep Focusing', default=True)
    FocusCenter: FloatVectorProperty(name="Focus Center", default=[0, 0, 0])
    bCameraRotate: BoolProperty(name='Rotation Follow Path', default=False)


class VelocityCurvesStructure(BaseUIListStructure):
    bObjectRotate: BoolProperty(name='Rotation Follow Path', default=False)


Register = [
    BaseUIListStructure, 
    TrackCollectionListStructure, 
    MaterialMeshListStructure, 
    PhysicObjectsListStructure, 
    CameraCurvesListStructure,
    VelocityCurvesStructure,
    ]
