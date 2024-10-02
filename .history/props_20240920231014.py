from math import pi
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
    update_target = target_class[update_target_name]
    scene_target = context.scene[scene_target_name]
    update_target = scene_target


def AmountCheck(
        target_class,
        check_value_name:str,
        target_value_name:str,
        context, 
        bCheckMax=True, # True for Max, false for min
        ):
    check_value = getattr(target_class, check_value_name)
    target_value = getattr(target_class, target_value_name)
    if bCheckMax:
        if check_value > target_value:
            setattr(target_class, check_value_name, )
            check_value = target_value
    else:
        if check_value < target_value:
            check_value = target_value


class BaseUIListStructure(PropertyGroup):
    Object: PointerProperty(type=bpy.types.Object)
    Collection: PointerProperty(type=bpy.types.Collection)


class General(PropertyGroup):
    bInPreview: BoolProperty(default=False)
    bRandomOrNot: BoolProperty(default=True)
    bNoneTrackBK: BoolProperty(default=False)
    RandomSeed: IntProperty(name="Random Seed", default=1, min=1, max=9999)
    VideoNumber: IntProperty(name='Video Amount', default=1, min=1, max=9999)
    VideoMaxFrame = IntProperty(name='Scene Max Frame', update=lambda self, context : context.scene.frame_end)
    StartVideoIndex: IntProperty(name='Start Video Index', default=1, min=1, max=9999,
                                 update=lambda self, context : AmountCheck(self, 'StartVideoIndex', 'VideoNumber', context, bCheckMax=True))
    StartFrameIndex: IntProperty(name='Start Frame Index', default=1, min=1, max=999999,
                                 update=lambda self, context : AmountCheck(self, 'StartFrameIndex', 'VideoMaxFrame', context, bCheckMax=True))
    HDRIRoot: StringProperty(name='HDRI Background path', default='/tmp\\', subtype='DIR_PATH')


class TrackCollectionListStructure(BaseUIListStructure):
    bTracked: BoolProperty(default=False)

class Objects(PropertyGroup): 
    Collections: CollectionProperty(type=TrackCollectionListStructure)
    Index: IntProperty(default=0, min=0)
    MaxAmount: IntProperty(name="Max", default=1, min=1, max=1024,
                           update=lambda self, context: AmountCheck(self, 'MaxAmount', 'MinAmount', context, bCheckMax=False))
    MinAmount: IntProperty(name="Min", default=1, min=1, max=1024,
                           update=lambda self, context : AmountCheck(self, 'MinAmount', 'MaxAmount', context, bCheckMax=True))
    AppearRange: FloatProperty(name="Max spawn range", default=2, min=0.01, max=50000.0, subtype='DISTANCE')
    RandomScale: FloatProperty(name="Random scale +-", min=0, max=0.9999)


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

class Material(PropertyGroup):
    SelectedMesh: CollectionProperty(type=MaterialMeshListStructure)
    Index: IntProperty(default=0, min=0)


class Light(PropertyGroup):
    PointMax: IntProperty(default=0, min=0, max=5)
    SunMax: IntProperty(default=0, min=0, max=5)
    SpotMax: IntProperty(default=0, min=0, max=5)
    AreaMax: IntProperty(default=0, min=0, max=5)
    bRandomSpec: BoolProperty(name='Random Light Specs?', default=True)
    Color: FloatVectorProperty(name="Light color", subtype='COLOR', default=[1,1,1], min=0, max=1)
    Power: FloatProperty(name='Light power', default=10.0, min=1.0, subtype='POWER')
    PointRadius: FloatProperty(name='Point Light Radius', default=0.25, min=0.0, max=100.0, subtype='DISTANCE')
    SunAngle: FloatProperty(name='Sun Light Angle', default=0.009180, min=0.0, max=pi, subtype='ANGLE')
    SpotRadius: FloatProperty(name='Spot Light Radius', default=1.0, min=0.0, max=100.0, subtype='DISTANCE')
    SpotSize: FloatProperty(name='Spot Light Size', default=pi/4, min=1.0, max=pi, subtype='ANGLE')
    SpotBlend: FloatProperty(name='Spot Light Blend', default=0.15, min=0, max=1)
    AreaSizeX: FloatProperty(name='Area Light SizeX', default=0.25, min=0.0, max=100.0, unit='LENGTH')
    AreaSizeY: FloatProperty(name='Area Light SizeY', default=0.25, min=0.0, max=100.0, unit='LENGTH')


class CameraCurvesListStructure(BaseUIListStructure):
    bCameraFocus: BoolProperty(name='Keep Focusing', default=True)
    FocusCenter: FloatVectorProperty(name="Focus Center", default=[0, 0, 0])
    bCameraRotate: BoolProperty(name='Rotation Follow Path', default=False)

class Camera(PropertyGroup):
    Curves: CollectionProperty(type=CameraCurvesListStructure)
    Index: IntProperty(default=0, min=0)
    LensFocalLength: FloatProperty(name="Focal Length", default=50, min=1, max=1000, subtype='DISTANCE_CAMERA')
    bUseDoF: BoolProperty(name='Use Depth of Field?', default=False)
    FocalDistance: FloatProperty(name='Focal Distance', default=10, min=0.1, subtype='DISTANCE')
    FStop: FloatProperty(name='F-Stop', default=2.8, min=0.1, max=22)
    Blades: IntProperty(name='Blades', default=0, min=0, max=16)
    ApertureRotation: FloatProperty(name='Aperture Rotation', default=0, min=-pi, max=pi, subtype='ANGLE')
    ApertureRatio: FloatProperty(name='Aperture Ratio', default=1, min=1, max=2)
    SensorFit: EnumProperty(
        name="Sensor Fit",
        items=[
        ('AUTO', 'Auto', ''),
        ('HORIZONTAL', 'Horizontal', ''),
        ('VERTICAL', 'Vertical', ''),
        ]
    )
    SensorSize: FloatProperty(name='Size', default=36, min=1, max=100, subtype='DISTANCE_CAMERA')
    CameraNumber: IntProperty(name='Camera Amount', default=1, min=1, max=100)
    CameraMotionRange: FloatProperty(name="Camera range", default=5, min=1.0, max=50000.0, subtype='DISTANCE')
    bRandomCameraFocus: BoolProperty(name='Random Keep Focusing', default=True)
    RandomFocusCenter: FloatVectorProperty(name="Random Focus Center", default=[0, 0, 0])
    bRandomCameraRotate: BoolProperty(name='Random Rotation Follow Path', default=False)
    ComplexRate: IntProperty(name='Camera Path Complex', default=2, min=1, max=10)


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

class Physics(PropertyGroup):
    SelectedObject: CollectionProperty(type=PhysicObjectsListStructure)
    Index: IntProperty(default=0, min=0)
    TimeScale: FloatProperty(name="Time scale", default=1.0, min=0.001, max=10.000)
    Substeps: IntProperty(name='Substeps Per Frame', default=10, min=1, max=1000)
    Iterations: IntProperty(name='Solver Iterations', default=10, min=10, max=100)


class VelocityCurvesStructure(BaseUIListStructure):
    bObjectRotate: BoolProperty(name='Rotation Follow Path', default=False)

class Movement(PropertyGroup):
    bRandomVelVal: BoolProperty(name='Random Initial Velocity Value?', default=True)
    MaxVel: FloatProperty(name="Max Velocity", default=1, min=1, max=1024, 
                          update=lambda self, context: AmountCheck(self, 'MaxVel', 'MinVel', context, bCheckMax=False), unit='VELOCITY')
    MinVel: FloatProperty(name="Min Velocity", default=1, min=1, max=1024,
                          update=lambda self, context : AmountCheck(self, 'MinVel', 'MaxVel', context, bCheckMax=True), unit='VELOCITY')
    InitialVelVal: FloatProperty(name="Initial Velocity", default=0.0, min=0.0, max=100.0, unit='VELOCITY')
    bRandomVelDir: BoolProperty(name='Random Initial Velocity Direction?', default=True)
    InitialVelDir: FloatVectorProperty(name="Random Initial Velocity Direction", default=[0, 0, 0])
    Curves: CollectionProperty(type=VelocityCurvesStructure)
    Index: IntProperty(default=0, min=0)


class Annotation(PropertyGroup):
    bTracking: BoolProperty(name="Track", default=True)
    bObjectsTrack2D: BoolProperty(name="2D bounding boxes", default=True)

    bDepth: BoolProperty(name="Depth", default=True)
    bDepth8bit: BoolProperty(name="8 bit depth", default=True)
    bDepthRaw: BoolProperty(name="raw depth", default=True)


class Props_All(PropertyGroup):
    General: PointerProperty(type=General)
    Obj: PointerProperty(type=Objects)
    Mat: PointerProperty(type=Material)
    Light: PointerProperty(type=Light)
    Camera: PointerProperty(type=Camera)
    Physics: PointerProperty(type=Physics)
    Movement: PointerProperty(type=Movement)
    Annotation: PointerProperty(type=Annotation)


AllPropClasses = [
    BaseUIListStructure, 
    TrackCollectionListStructure, 
    MaterialMeshListStructure, 
    PhysicObjectsListStructure, 
    CameraCurvesListStructure,
    VelocityCurvesStructure,
    General, Objects, Material, Light, Camera, Physics, Movement, Annotation, Props_All]
