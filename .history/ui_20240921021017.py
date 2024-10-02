from typing import List
import bpy
from bpy.types import Context, Panel
from . import util
import opt

bDebug = True

PanelIDPrefix = "AD_UI_Panel_"
Space_Type = "PROPERTIES"
Region_Type = "WINDOW"
Panel_Context = "output"

# All panels
# 0.AutoData: Main panel contains all sub-panels
# 1.Object: Handle the objects for categories
# 2.Material: Handle the material option for each individual object
# 3.Light: Handle the light for all sences
# 4.Camera: Handle the camera for all sences
# 5.General: All other config and final render button in here
# 6.Physics: Physics setting based on blender riged body system
# 7.Movement: Manual set objects movement
# 8.Annotation: Select annotation data to output

def ButtonProps(
    button, 
    action: str,
    panel_name: str,
    structure_name: str,
    idx_name: str,
    type: str,
    ):

    button.action = action
    button.panel_name = panel_name
    button.structure_name = structure_name
    button.idx_name = idx_name
    button.type = type

def SubPropsShow(
    SelectedSturcture, 
    SelectedIndex, 
    layout:bpy.types.UILayout, 
    props_list: List[str],
    ):

    try: 
        item = SelectedSturcture[SelectedIndex]
    except IndexError:
        pass
    else:
        column = layout.column(align=True)
        for each_attribute in props_list:
            column.prop(item, each_attribute)

# Base Class
class P_Master(Panel):
    bl_space_type = Space_Type
    bl_region_type = Region_Type
    bl_context = Panel_Context

    @classmethod
    def poll(self, context):
        return context.mode == "OBJECT"
    
    def __init__(self) -> None:
        super().__init__()
        self.context = bpy.context
        self.scene = self.context.scene
        self.render = self.scene.render
        self.Props_All = self.scene.P_S

        self.props_general = self.Props_All.General 
        self.props_obj = self.Props_All.Obj
        self.props_mat = self.Props_All.Mat
        self.props_light = self.Props_All.Light
        self.props_camera = self.Props_All.Camera
        self.props_physics = self.Props_All.Physics
        self.props_movement = self.Props_All.Movement
        self.props_annotation = self.Props_All.Annotation

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.enabled = not self.props_general.bInPreview

        if bDebug:
            layout.label(text="! DEBUGING !")


# Main Panel
class P_General(P_Master):

# This is the main panel, all other panels in this panel

# Props:
# Random or not (boolean)
# Random seed (int)
# HDRI files (path)
# Number of videos (int)
# Output and render seting will direcly use the blender seting. 
# If you want to do some changes you should change them in those panels.

    bl_idname = PanelIDPrefix + "AutoDataset"
    bl_label = "AutoDataset"

    def __init__(self) -> None:
        super().__init__()

    def draw(self, context):
        super().draw(context)

        layout = self.layout
        layout.enabled = True

        if self.props_general.bInPreview:
            column_back = layout.column()
            column_back.operator(opt.OP_MainAction.bl_idname, icon='SCREEN_BACK', text='Back From Preview').action = 'BACK'

        column = layout.column()
        column.enabled = not self.props_general.bInPreview
        row = column.row(align=True)
        row.operator_context = 'INVOKE_DEFAULT'
        row.operator(opt.OP_MainAction.bl_idname, icon='OUTPUT', text='Render').action = 'RENDER'
        row.operator(opt.OP_MainAction.bl_idname, icon='VIEWZOOM', text='Preview').action = 'PREVIEW'

        column.prop(self.props_general, "RandomSeed")
        column.prop(self.props_general, 'VideoNumber')

        column.prop(self.props_general, 'StartVideoIndex')
        column.prop(self.props_general, 'StartFrameIndex')

        row = column.row(align=True)
        row.label(icon='WORLD')
        row.prop(self.props_general, 'HDRIRoot')

        column.prop(self.props_general, "bRandomOrNot", text="Random generation?")
        column.prop(self.props_general, "bNoneTrackBK", text="Non-track as background?")

        column.label(text=
        "Output and render seting will direcly use the blender seting."
        )


# Object Panel
class P_Object(P_Master):

# Props:
# Define which objects to track (collection select)
# Objects max and min number (int)
# Objects appear range (float)
# Object scale random (float)
# Physical or not (boolean)
# Initial speed (float)

    bl_idname = PanelIDPrefix + "Object"
    bl_label = "Object"
    bl_parent_id = P_General.bl_idname

    def __init__(self) -> None:
        super().__init__()
        util.ui.SyncListToProp(list(bpy.data.collections), self.props_obj.Collections)

    def draw(self, context):
        super().draw(context)

        layout = self.layout

        layout.label(text="Select collection as class to Track")
        collection_list = layout.template_list(util.ui.UL_ShowAllTargetsWithProperty.bl_idname, "UL_OBJ", 
                                               bpy.data, "collections", 
                                               self.props_obj, "Index",  
                            )
        
        column = layout.column(align=True)
        column.prop(self.props_obj, "MaxAmount", text='Amount Max')
        column.prop(self.props_obj, "MinAmount", text='Min')

        layout.separator_spacer()
        layout.prop(self.props_obj, "AppearRange")
        layout.prop(self.props_obj, "RandomScale")


# Material Panel
class P_Material(P_Master):

# Props:
# Random material selelct (object select)
# Random base PBR material (material parameter)

    bl_idname = PanelIDPrefix + "Material"
    bl_label = "Material"
    bl_parent_id = P_General.bl_idname

    def __init__(self) -> None:
        super().__init__()
        util.ui.ListCheck(self.props_mat.SelectedMesh, self.props_mat.Index, self.context.scene.objects)
        

    def draw(self, context):
        super().draw(context)

        layout = self.layout
        self.bFound = True

        row = layout.row()
        row.template_list(util.ui.UL_SelectedTarget.bl_idname,
                          'UL_Mat',
                          self.props_mat, 'SelectedMesh',
                          self.props_mat, 'Index')

        col = row.column(align=True)
        button = col.operator(util.opt.OP_UI_List_actions_Object.bl_idname, icon='ADD', text='')
        ButtonProps(button, 'ADD', 'Mat', 'SelectedMesh', 'Index', 'MESH')
        button = col.operator(util.opt.OP_UI_List_actions_Object.bl_idname, icon='REMOVE', text='')
        ButtonProps(button, 'REMOVE', 'Mat', 'SelectedMesh', 'Index', 'MESH')

        self.bFound = SubPropsShow(
                                self.props_mat.SelectedMesh, 
                                self.props_mat.Index, 
                                layout, 
                                ['MetallicMax', 'MetallicMin', 
                                'RoughnessMax', 'RoughnessMin', 
                                'SpecularMax', 'SpecularMin',],
                                )


# Light Panel
class P_Light(P_Master): 

# Props:
# Lights max min number for each type (int)
# Lights power, transform, special parmaters (float, vector, float)
## maybe move lights?

    bl_idname = PanelIDPrefix + "Light"
    bl_label = "Light"
    bl_parent_id = P_General.bl_idname

    def __init__(self) -> None:
        super().__init__()

    def draw(self, context):
        super().draw(context)

        layout = self.layout

        layout.label(text='Max number for each light type, 0 for none')
        column = layout.column(align=True)
        row = column.row(align=True)
        row.label(icon='LIGHT_POINT')
        row.prop(self.props_light, 'PointMax', text='Point')
        row = column.row(align=True)
        row.label(icon='LIGHT_SUN')
        row.prop(self.props_light, 'SunMax', text='Sun')
        row = column.row(align=True)
        row.label(icon='LIGHT_SPOT')
        row.prop(self.props_light, 'SpotMax', text='Spot')
        row = column.row(align=True)
        row.label(icon='LIGHT_AREA')
        row.prop(self.props_light, 'AreaMax', text='Area')

        layout.separator_spacer()
        layout.prop(self.props_light, 'bRandomSpec')
        layout.prop(self.props_light, 'Color')
        layout.prop(self.props_light, 'Power')
        layout.prop(self.props_light, 'PointRadius')
        layout.prop(self.props_light, 'SunAngle')
        column = layout.column(align=True)
        column.prop(self.props_light, 'SpotRadius')
        column.prop(self.props_light, 'SpotSize')
        column.prop(self.props_light, 'SpotBlend')
        column = layout.column(align=True)
        column.prop(self.props_light, 'AreaSizeX')
        column.prop(self.props_light, 'AreaSizeY')


# Camera Panel
class P_Camera(P_Master):

# Props:
# Lens (lens setting)
# Depth of field (dof setting)
# Sensor (enum, int)
# Camera numbers (int)
# Camera motion range (float)
# Foucus or not (boolean)
# Rotate or not (boolean)
# Complex rate (int)

    bl_idname = PanelIDPrefix + "Camera"
    bl_label = "Camera"
    bl_parent_id = P_General.bl_idname

    def __init__(self) -> None:
        super().__init__()
        util.ui.ListCheck(self.props_camera.Curves, self.props_camera.Index, self.context.scene.objects)

    def draw(self, context):
        super().draw(context)

        layout = self.layout

        layout.label(text=
        'WARNNING! If you selected curves, will not random generate but choice from this list.'
        )
        row = layout.row()
        row.template_list(util.ui.UL_SelectedTarget.bl_idname,'UL_Camera',
                            self.props_camera, 'Curves',
                            self.props_camera, 'Index')

        col = row.column(align=True)
        button = col.operator(util.opt.OP_UI_List_actions_Object.bl_idname, icon='ADD', text='')
        ButtonProps(button, 'ADD', 'Camera', 'Curves', 'Index', 'CURVE')
        button = col.operator(util.opt.OP_UI_List_actions_Object.bl_idname, icon='REMOVE', text='')
        ButtonProps(button, 'REMOVE', 'Camera', 'Curves', 'Index', 'CURVE')

        layout.prop(self.props_camera, 'LensFocalLength')
        
        layout.separator_spacer()
        layout.prop(self.props_camera, 'bUseDoF')
        column = layout.column(align=True)
        column.enabled = self.props_camera.bUseDoF
        column.prop(self.props_camera, 'FocalDistance')
        column.prop(self.props_camera, 'FStop')
        column.prop(self.props_camera, 'Blades')
        column.prop(self.props_camera, 'ApertureRotation')
        column.prop(self.props_camera, 'ApertureRatio')

        layout.separator_spacer()
        layout.prop(self.props_camera, 'SensorFit')
        layout.prop(self.props_camera, 'SensorSize')

        layout.separator_spacer()
        layout.prop(self.props_camera, 'ComplexRate')
        layout.prop(self.props_camera, 'CameraNumber')
        layout.prop(self.props_camera, 'CameraMotionRange')

        selected_curve = None
        if self.props_camera.Curves:
            try:
                selected_curve = self.props_camera.Curves[self.props_camera.Index]
            except:
                pass
            if selected_curve:
                column = layout.column(align=True)
                column.enabled = not selected_curve.bCameraRotate
                column.prop(selected_curve, 'bCameraFocus')
                column = layout.column(align=True)
                column.enabled = selected_curve.bCameraFocus
                column.prop(selected_curve, 'FocusCenter')
                column = layout.column(align=True)
                column.enabled = not selected_curve.bCameraFocus
                column.prop(selected_curve, 'bCameraRotate')
        else:
            column = layout.column(align=True)
            column.enabled = not self.props_camera.bRandomCameraRotate
            column.prop(self.props_camera, 'bRandomCameraFocus')
            column = layout.column(align=True)
            column.enabled = self.props_camera.bRandomCameraFocus
            column.prop(self.props_camera, 'RandomFocusCenter')
            column = layout.column(align=True)
            column.enabled = not self.props_camera.bRandomCameraFocus
            column.prop(self.props_camera, 'bRandomCameraRotate')


# Physics Panel
class P_Physics(P_Master):

# Props:
# Objects (List)
# Mass, Surface response, Dynamics setting
# Initial Speed (float)
# Time scale (float)
# Substeps (int)
# Solver Iterations (int)

    bl_idname = PanelIDPrefix + "Physics"
    bl_label = "Physics"
    bl_parent_id = P_General.bl_idname

    def __init__(self) -> None:
        super().__init__()
        util.ui.ListCheck(self.props_physics.SelectedObject, self.props_physics.Index, self.context.scene.objects)

    def draw(self, context):
        super().draw(context)

        layout = self.layout

        row = layout.row()
        row.template_list(util.ui.UL_SelectedTarget.bl_idname,'UL_Phy',
                            self.props_physics, 'SelectedObject',
                            self.props_physics, 'Index')
        col = row.column(align=True)
        button = col.operator(util.opt.OP_UI_List_actions_Object.bl_idname, icon='ADD', text='')
        ButtonProps(button, 'ADD', 'Physics', 'SelectedObject', 'Index', 'MESH')

        button = col.operator(util.opt.OP_UI_List_actions_Object.bl_idname, icon='REMOVE', text='')
        ButtonProps(button, 'REMOVE', 'Physics', 'SelectedObject', 'Index', 'MESH')
        
        SubPropsShow(
            self.props_physics.SelectedObject, 
            self.props_physics.Index, 
            layout, 
            ['Shape', 'Source', 'Mass', 'Friction', 'Bounciness'],
            )

        layout.prop(self.props_physics, "TimeScale")
        column = layout.column(align=True)
        column.prop(self.props_physics, "Substeps")
        column.prop(self.props_physics, "Iterations")


# Movement Panel
class P_Movement(P_Master):
    # Props:
    # InitialVelVal (Initial Velocity Value)
    # InitialVelDir (Initial Velocity Direction)

    bl_idname = PanelIDPrefix + "Movement"
    bl_label = "Movement"
    bl_parent_id = P_General.bl_idname

    def __init__(self) -> None:
        super().__init__()
        util.ui.ListCheck(self.props_movement.Curves, self.props_movement.Index, self.context.scene.objects)

    def draw(self, context):
        super().draw(context)

        layout = self.layout

        layout.label(text=
                     'WARNNING! If you selected curves, will not random generate but choice from this list.'
                     )
        row = layout.row()
        row.template_list(util.ui.UL_SelectedTarget.bl_idname, 'UL_Movement',
                          self.props_movement, 'Curves',
                          self.props_movement, 'Index')

        col = row.column(align=True)
        button = col.operator(util.opt.OP_UI_List_actions_Object.bl_idname, icon='ADD', text='')
        ButtonProps(button, 'ADD', 'Movement', 'Curves', 'Index', 'CURVE')
        button = col.operator(util.opt.OP_UI_List_actions_Object.bl_idname, icon='REMOVE', text='')
        ButtonProps(button, 'REMOVE', 'Movement', 'Curves', 'Index', 'CURVE')

        layout.separator_spacer()
        layout.prop(self.props_movement, 'bRandomVelVal')
        column = layout.column(align=True)
        column.enabled = self.props_movement.bRandomVelVal
        column.prop(self.props_movement, 'MaxVel', text='Max Random Velocity')
        column.prop(self.props_movement, 'MinVel', text='Min Random Velocity')
        column = layout.column(align=True)
        column.enabled = not self.props_movement.bRandomVelVal
        column.prop(self.props_movement, 'InitialVelVal', text='Initial Velocity Value')

        layout.separator_spacer()
        layout.prop(self.props_movement, 'bRandomVelDir')
        column = layout.column(align=True)
        column.enabled = not self.props_movement.bRandomVelDir
        column.prop(self.props_movement, 'InitialVelDir')


# Annotation Panel
class P_Annotation(P_Master):
    bl_idname = PanelIDPrefix + "Annotation"
    bl_label = 'Annotation'
    bl_parent_id = P_General.bl_idname
    
    def __init__(self) -> None:
        super().__init__()

    def draw(self, context: Context):
        super().draw(context)

class P_Annotation_Track(P_Master):
    bl_idname = P_Annotation.bl_idname + '_Track'
    bl_label = 'Track'
    bl_parent_id = P_Annotation.bl_idname

    def draw_header(self, context: Context):
        self.layout.prop(self.props_annotation, 'bTracking', text='')

    def draw(self, context):
        super().draw(context)
        self.layout.prop(self.props_annotation, 'bObjectsTrack2D')

class P_Annotation_Depth(P_Master):
    bl_idname = P_Annotation.bl_idname + '_Depth'
    bl_label = 'Depth'
    bl_parent_id = P_Annotation.bl_idname

    def draw_header(self, context: Context):
        self.layout.prop(self.props_annotation, 'bDepth', text='')

    def draw(self, context):
        super().draw(context)
        self.layout.prop(self.props_annotation, 'bDepth8bit')
        self.layout.prop(self.props_annotation, 'bDepthRaw')


AllPanelClasses = [
    P_General, 
    P_Object,
    P_Material, 
    P_Light, 
    P_Camera, 
    P_Physics, 
    P_Movement, 
    P_Annotation, 
    P_Annotation_Track, 
    P_Annotation_Depth,
    ]
