import bpy, bmesh
from bpy.types import Operator as Opt

import time
import os, stat
import json
import random
import shutil
import math
from mathutils.bvhtree import BVHTree
from mathutils import Matrix
import numpy as np

from . import util, props

Blender_version = bpy.app.version
OptIDName = 'ad.'
scene_name = 'AD'
Flag = 'AD_Generated'

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

class object_by_cryptomatte:
    def __init__(
        self,
        path: str,
        scene: bpy.types.Scene, 
        view: bpy.types.ViewLayer, 
        objects: list
                ):
        
        self.scene = scene
        self.view = view
        self.objects_dic = {}
        self.object_segment_list = []
        self.path = path
        self.path_crypto = util_mkdir(path + 'cryptomatte\\')
        self.image = []

        self.cryptomatte_node_list = []
        self.output_node = scene.node_tree.nodes.new('CompositorNodeOutputFile')
        self.output_node.base_path = self.path_crypto
        self.output_node.file_slots.clear()

        for each_obj in objects:
            self.objects_dic[each_obj.name] = each_obj

            cryptomatte = scene.node_tree.nodes.new('CompositorNodeCryptomatteV2')
            cryptomatte.source = 'RENDER'
            cryptomatte.scene = scene
            cryptomatte.layer_name = view.name + '.CryptoAsset'
            cryptomatte.matte_id = each_obj.name
            self.cryptomatte_node_list.append(cryptomatte)
            
            output_slot = self.output_node.file_slots.new(each_obj.name + '_')  # Only work with .file_slots or .layer_slots, .inputs not working
            scene.node_tree.links.new(cryptomatte.outputs['Matte'], output_slot)

    def clear(self, path: str):
        for cryptomatte_node in self.cryptomatte_node_list:
            self.scene.node_tree.nodes.remove(cryptomatte_node)
        self.scene.node_tree.nodes.remove(self.output_node)

        for image in self.image:
            bpy.data.images.remove(image)
        self.image = []
        
        for each_file in os.listdir(path):
            os.remove(os.path.join(path, each_file))

        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWRITE)
        os.rmdir(path)

    def Find_bbox(self, file_name, path):
        print('Finding bbox start')
        files = os.listdir(self.path_crypto)
        track_data_list = []

        min_area_ratio = 1024

        for each_file in files:
            print('Finding bbox in %s'%each_file)
            image = bpy.data.images.load(os.path.join(self.path_crypto, each_file))
            self.image.append(image)
            size_x = image.size[0]
            size_y = image.size[1]
            max = [0, 0]
            min = [0, 0]

            arr = np.array(image.pixels)
            arr.shape = (size_y, size_x,4)
            arr = np.delete(arr, np.s_[0:3], 2)
            arr = np.squeeze(arr)
            segment = np.where(arr > 0)

            name: str
            ext: str
            name, ext = os.path.splitext(each_file)
            delimiter = name.rfind('_')
            name = name[:delimiter]

            if not segment[0].size <= (size_x * size_y) // min_area_ratio:
                class_id = self.objects_dic[name]['class_id']
                track_id = self.objects_dic[name]['track_id']

                max[0] = segment[1].max()
                max[1] = segment[0].max()
                min[0] = segment[1].min()
                min[1] = segment[0].min()

                w = max[0] - min[0]
                h = max[1] - min[1]
                x = round(min[0] + (w / 2))
                y = round(min[1] + (h / 2))

                xywh = {
                    'class_id': class_id,
                    'track_id': track_id,
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h
                }      

                track_data_list.append(xywh)
        print(track_data_list)

        with open(path + file_name + '.txt', mode='w') as trak_file:
            for track_data in track_data_list:
                trak_file.write(
                    f'{track_data["class_id"]} {track_data["track_id"]} {round(track_data["x"] / size_x, 6)} {round((size_y - track_data["y"]) / size_y, 6)} {round(track_data["w"] / size_x, 6)} {round(track_data["h"] / size_y, 6)}' + '\n'
                )
        self.clear(self.path_crypto)

class OP_Action(Opt):
    bl_idname = OptIDName + "action"
    bl_label = "Overall action"

    action : bpy.props.EnumProperty(
        items=(
            ('RENDER', 'Render', ''),
            ('PREVIEW', 'Preview', ''),
            ('BACK', 'Back From Preview', '')
        )
    )

    Props = bpy.props.PointerProperty(type=props.Props_All)

    # # Testing, maybe a bug in blender
    # def invoke(self, context, event):
    #     # bpy.ops.scene.new(type='FULL_COPY')
    #     self.scene = bpy.data.scenes[-1]
    #     self.path = self.scene.render.filepath
    #     self.view_layer = self.scene.view_layers.new('Test')

    #     # Do something here #

    #     return self.execute(context)

    # def execute(self, context):
    #     for i in range(self.scene.frame_start, self.scene.frame_end + 1):

    #         # Do something here #

    #         self.scene.frame_set(i)
    #         self.scene.render.filepath = (self.path + str(self.scene.frame_current).zfill(4))  # Set save path with frame
    #         bpy.ops.render.render(
    #             scene= self.scene.name, layer= self.view_layer.name, animation=False, write_still=True
    #             )

    #     return {'FINISHED'}

    def invoke(self, context, event):
        context.scene.render.use_lock_interface = True
        self.video_num = 0
        self.non_track_source = []
        self.class_list_source = []
        self.track_list_source = []
        self.bRandom = True
        self.scene_origin = context.scene
        self.Props = self.scene_origin.P_S

        if self.action == 'BACK':
            self.BackFromPreview(context)
            return {'FINISHED'}
            
        else:
            for col_strc in self.Props.Obj.Collections:
                if col_strc.bTracked:
                    print(col_strc.Collection)
                    self.class_list_source += [col_strc.Collection]
            if not self.class_list_source:
                info = 'No Tracking Class!'
                self.report({'ERROR'}, info)
                return {'CANCELLED'}

            for i_c, col in enumerate(self.class_list_source):
                self.track_list_source += []
                bHaveMesh = False
                if col.objects:
                    for obj in col.objects:
                        if obj.type == 'MESH':
                            bHaveMesh = True
                            self.util_ApplyTransform(obj)
                            self.track_list_source += [obj]
                            obj['class_id'] = i_c
                    
                else:
                    info = 'No Objcets in %s Class!' % (col.name)
                    self.report({'ERROR'}, info)
                    return {'CANCELLED'}
                
                if not bHaveMesh:
                    info = 'No Mesh in %s Class!' % (col.name)
                    self.report({'ERROR'}, info)
                    return {'CANCELLED'}
            
            if not self.RangeCheck():
                info = 'Object Appear Range is Too Small!'
                self.report({'ERROR'}, info)
                return {'CANCELLED'}
            
            if self.Props.General.bNoneTrackBK:
                obj_set = set(self.scene_origin.objects)
                print(obj_set)
                track_set = set(self.track_list_source)
                print(track_set)
                non_track_set = obj_set.difference(track_set)
                print(non_track_set)
                self.non_track_source = list(non_track_set)

            self.path_origin = self.scene_origin.render.filepath  # Get the default save path in panel
            self.bRandom = self.Props.General.bRandomOrNot

            self.create_scene()

            self.create_composite_node_tree()

            bpy.context.window.scene = self.scene_track
            bpy.context.window.view_layer = self.ViewLayer

            # return {'CANCELLED'}
            return self.execute(context)

    def execute(self, context):
        General = self.Props.General
        self.seed = General.RandomSeed
        self.VideoMax = General.VideoNumber
        self.StartVideoIndex = General.StartVideoIndex
        self.StartFrameIndex = General.StartFrameIndex
        self.HDRIRoot = General.HDRIRoot

        if self.bRandom:
            for video_num in range(self.StartVideoIndex, self.VideoMax+1):
                self.video_num = video_num
                video_name = str(video_num).zfill(4)
                if self.path_origin[0:4] == '/tmp':
                    self.path = r'C:\tmp' + self.path_origin[5:-1]
                else:
                    self.path = self.path_origin

                self.seed_video_str = str(self.seed * 10000 + video_num)

                self.clear_scene(self.scene_track)

                self.BackgroundObjectGenerate()

                self.RandomObjectsGenerate()

                self.RandomLightGenerate()

                self.RandomCameraGenerate()

                self.SetHdri(self.HDRIRoot)

                if self.action == 'RENDER':

                    self.image_path = util_mkdir(self.path + 'images\\' + video_name + '\\')
                    self.segement_path = util_mkdir(self.path + 'labels_with_ids\\' + video_name + '\\')

                    if self.properties.General.bDepth8bit
                    self.depth_path = util_mkdir(self.path + 'depth_8bit\\' + video_name + '\\')
                    self.create_annotation_depth_output_8bit()
                    
                    self.Animation()

                    self.RenderAction()

                    self.write_id_into_json(self.class_list_source, self.Objects, (self.path + 'labels_with_ids\\' + video_name + '\\'))
                    
                    info = 'Video No.%d render finished, %d/%d!' % (video_num, video_num, self.VideoMax)
                    print(info)
                    print('\n')

                elif self.action == 'PREVIEW':
                    self.scene_track.P_S.General.bInPreview = True
                    self.scene_origin.P_S.General.bInPreview = True
                    
                    self.scene_track.camera = self.Cameras[0]

                    self.scene_track.frame_current = self.StartFrameIndex

                    self.Animation()

                    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
                    space = next(space for space in area.spaces if space.type == 'VIEW_3D')
                    space.shading.type = 'RENDERED'  # set the viewport shading
                    space.overlay.show_overlays = False
                    
                    info = 'Into preview'
                    self.report({'INFO'}, info)
                    
                    return {'FINISHED'}
                    
            self.BackFromPreview(context)

        info = 'All render finished'
        self.report({'INFO'}, info)
        print(info)

        if Blender_version[0] < 3 or (Blender_version[0] == 3 and Blender_version[1] < 4):
            self.report({'INFO'}, "Can't remove action lower than version 3.4, please manually delete them.")

        return {'FINISHED'}
    
    def RangeCheck(self) -> bool:
        Range = self.Props.Obj.AppearRange ** 3
        MaxAmount = self.Props.Obj.MaxAmount
        Scale = 1 + self.Props.Obj.RandomScale

        max_size = 0.0
        for each in self.track_list_source:
            each: bpy.types.Object
            p = each.bound_box
            size = (p[6][0] - p[0][0]) * (p[6][1] - p[0][1]) * (p[6][2] - p[0][2])
            if size > max_size:
                max_size = size
        max_size = max_size * Scale

        return Range > max_size*MaxAmount*2
    
    def create_scene(self):
        bpy.ops.scene.new(type='EMPTY')
        self.scene_track = bpy.data.scenes[-1]
        self.scene_track.name = scene_name
        self.scene_track.render.use_lock_interface = True
        bpy.context.window.scene = self.scene_track

        self.ViewLayer = self.scene_track.view_layers.new('MultiTrack')
        self.ViewLayer.use_pass_cryptomatte_accurate = True
        self.ViewLayer.use_pass_cryptomatte_asset = True
        self.ViewLayer.use_pass_z = True
        self.ViewLayer.use_pass_normal = True

    def clear_scene(self, scene: bpy.types.Scene):
        info = 'Clear Scene START'
        # self.report({'INFO'}, info)
        print(info)

        for type in (
                bpy.data.materials,
                bpy.data.meshes,
                bpy.data.cameras,
                bpy.data.lights,
                bpy.data.curves,
                bpy.data.objects,
        ):
            for target in type:
                if Flag in target.keys():
                    # if target.animation_data:
                    #     if target.animation_data.action:
                    #         action = target.animation_data.action
                    #         fcs = [fc for fc in action.fcurves]
                    #         for fc in fcs:
                    #             action.fcurves.remove(fc)
                    #         # Maybe a bug, can't remove action in operator lower than 3.4.
                    #         if not (Blender_version[0]<3 or (Blender_version[0]==3 and Blender_version[1]<4)):
                    #             bpy.data.actions.remove(action)
                    #     target.animation_data_clear()
                    type.remove(target)

        for image in bpy.data.images:
            if Flag in image.keys():
                bpy.data.images.remove(image)

        for col in scene.collection.children:
            bpy.data.collections.remove(col)

        if scene.world:
            bpy.data.worlds.remove(scene.world)

        try:
            if self.rigidbody_collection:
                bpy.data.collections.remove(self.rigidbody_collection)
        except:
            ...

        info = 'Clear Scene DONE'
        # self.report({'INFO'}, info)
        print(info)

    def create_composite_node_tree(self):
        self.scene_track.use_nodes = True  # Use node in compositing
        self.node_tree = self.scene_track.node_tree
        self.node_tree.nodes.clear()

        self.compositornode_renderlayer = self.node_tree.nodes.new(type='CompositorNodeRLayers')
        self.compositornode_renderlayer.scene = self.scene_track
        self.compositornode_renderlayer.layer = self.ViewLayer.name
        self.compositornode_composite = self.node_tree.nodes.new(type='CompositorNodeComposite')
        
        links = self.node_tree.links
        link = links.new(self.compositornode_renderlayer.outputs['Image'], self.compositornode_composite.inputs['Image'])
        link = links.new(self.compositornode_renderlayer.outputs['Alpha'], self.compositornode_composite.inputs['Alpha'])

    def create_annotation_depth_output_8bit(self):
        output_node = self.node_tree.nodes.new(type='CompositorNodeOutputFile')
        output_node.format.compression = 0
        output_node.base_path = self.depth_path
        links = self.node_tree.links
        link = links.new(self.compositornode_renderlayer.outputs['Z'], output_node.inputs['Image'])

    def write_id_into_json(self, class_list, track_list, path):
        dic = {}
        class_name = []
        track_name = [[] for _ in range(len(class_list))]

        for each in class_list:
            class_name += [each.name]
        for each in track_list:
            track_name[each['class_id']].insert(each['track_id'], each.name)

        dic['classes'] = class_name
        dic['tracks'] = track_name
        json_name = 'IDs.json'

        with open(os.path.join(path, json_name), 'w') as json_file:
            json.dump(dic, json_file, indent=4)

    def BackgroundObjectGenerate(self):
        self.non_track_col = bpy.data.collections.new('AD_Background')
        self.scene_track.collection.children.link(self.non_track_col)
        self.Non_tracks = []
        self.Non_tracks_withPhysics = []
        for i, each in enumerate(self.non_track_source):
            Back_object : bpy.types.Object = each.copy()
            Back_object.data = each.data.copy()
            Back_object.user_clear()
            Back_object[Flag] = True
            self.Non_tracks.append(Back_object)
            self.non_track_col.objects.link(Back_object)

            if self.scene_origin.rigidbody_world:
                if each in self.scene_origin.rigidbody_world.collection.objects.values():
                    self.Non_tracks_withPhysics.append(Back_object)

    def RandomObjectsGenerate(self):
        info = 'Objects Generation START'
        # self.report({'INFO'}, info)
        print(info)

        seed_object = self.seed_video_str + 'Object'
        random.seed(seed_object)

        self.track_col = bpy.data.collections.new('AD_Track')
        self.scene_track.collection.children.link(self.track_col)

        Obj_props = self.Props.Obj
        Range = Obj_props.AppearRange
        Scale = Obj_props.RandomScale
        MaxAmount = Obj_props.MaxAmount
        MinAmount = Obj_props.MinAmount

        Amount = random.randint(MinAmount, MaxAmount)
        choices = random.choices(self.track_list_source, k=Amount)

        self.Objects = []
        for i, each in enumerate(choices):
            seed = seed_object + '%d' % i
            obj_new: bpy.types.Object = each.copy()
            obj_new.data = each.data.copy()
            obj_new.user_clear()
            obj_new[Flag] = True
            obj_new.data[Flag] = True
            obj_new['track_id'] = i

            self.util_Random_iterable(seed, 'location', obj_new.location, -Range/2, Range/2)
            self.util_Random_iterable(seed, 'scale', obj_new.scale, 1-Scale, 1+Scale)
            self.util_Random_iterable(seed, 'rotation', obj_new.rotation_euler, 0.0, 2*math.pi)
            self.ViewLayer.update()
            
            self.RandomMaterial(seed, each, obj_new)

            self.RandomPhysics(seed, each, obj_new)

            self.RandomMovement(seed, each, obj_new)

            bCheckOverlap = True
            loop_count = 0
            if self.Objects:
                while bCheckOverlap:
                    loop_count += 1

                    if loop_count >= 256:

                        info = 'Objects %s is removed due to overlap' % (obj_new.name)
                        # self.report({'INFO'}, info)
                        print(info)

                        bpy.data.objects.remove(obj_new, do_unlink=True)
                        obj_new = None
                        break

                    else:
                        info = 'Checking Objects %s Overlap in loop %d' % (obj_new.name, loop_count)
                        # self.report({'INFO'}, info)
                        print(info)
                        for obj in self.Objects:
                            obj: bpy.types.Object

                            #create bmesh objects
                            bm1 = bmesh.new()
                            bm2 = bmesh.new()

                            #fill bmesh data from objects
                            bm1.from_mesh(obj_new.data)
                            bm2.from_mesh(obj.data)

                            #fixed it here:
                            bm1.transform(obj_new.matrix_basis)
                            bm2.transform(obj.matrix_basis)

                            #make BVH tree from BMesh of objects
                            bvh1 = BVHTree.FromBMesh(bm1)
                            bvh2 = BVHTree.FromBMesh(bm2)

                            bCheckOverlap = bool(bvh1.overlap(bvh2))

                            bm1.free()
                            bm2.free()

                            if bCheckOverlap:
                                self.util_Random_iterable(seed, 're_location_%d' % loop_count, obj_new.location, -Range/2, Range/2)
                                self.util_Random_iterable(seed, 're_scale_%d' % loop_count, obj_new.scale, 1-Scale, 1+Scale)
                                self.util_Random_iterable(seed, 're_rotation_%d' % loop_count, obj_new.rotation_euler, 0.0, 2*math.pi)
                                self.ViewLayer.update()
                                break
                            else:
                                ...

            if obj_new:
                self.Objects.append(obj_new)
                self.track_col.objects.link(obj_new)

        info = 'Objects Generation OVER'
        # self.report({'INFO'}, info)
        print(info)

    def RandomMaterial(self, seed: str, obj_ori: bpy.types.Object, obj_new: bpy.types.Object):
        info = 'Random Material START'
        # self.report({'INFO'}, info)
        print(info)

        seed_material = seed + 'Material'
        random.seed(seed_material)

        props = self.Props.Mat
        strc = props.SelectedMesh

        self.Materials=[]

        if strc:
            for each_strc in strc:
                Object = each_strc.Object

                # BaseColor = each_strc.BaseColor
                MetallicMax = each_strc.MetallicMax
                MetallicMin = each_strc.MetallicMin
                RoughnessMax = each_strc.RoughnessMax
                RoughnessMin = each_strc.RoughnessMin
                SpecularMax = each_strc.SpecularMax
                SpecularMin = each_strc.SpecularMin

                if obj_ori == Object:
                    obj_new['bAD_RandomMaterial'] = True
                    mat_new = bpy.data.materials.new(name= obj_new.name + '_' + 'AD_Random')
                    mat_new[Flag] = True
                    self.Materials.append(mat_new)
                    if not obj_new.material_slots:
                        obj_new.data.materials.append(mat_new)
                    for MatSlot in obj_new.material_slots:
                        self.util_Random_iterable(
                            seed_material, 'BaseColor', mat_new.diffuse_color,0.0, 1.0
                            )
                        mat_new.metallic = self.util_Random(
                            seed_material, 'Metallic', MetallicMin, MetallicMax
                            )
                        mat_new.roughness = self.util_Random(
                            seed_material, 'Roughness', RoughnessMin, RoughnessMax
                            )
                        mat_new.specular_intensity = self.util_Random(
                            seed_material, 'Specular', SpecularMin, SpecularMax
                            )
                        MatSlot.material = mat_new

        info = 'Random Material OVER'
        # self.report({'INFO'}, info)
        print(info)

    def RandomLightGenerate(self):
        info = 'Random Light START'
        # self.report({'INFO'}, info)
        print(info)

        seed_light = self.seed_video_str + 'Light'
        random.seed(seed_light)

        props = self.Props.Light

        Range = self.Props.Obj.AppearRange

        PointMax = props.PointMax
        SunMax = props.SunMax
        SpotMax = props.SpotMax
        AreaMax = props.AreaMax

        bRandomSpec = props.bRandomSpec

        Color = props.Color
        Power = props.Power

        PointRadius = props.PointRadius

        SunAngle = props.SunAngle

        SpotRadius = props.SpotRadius
        SpotSize = props.SpotSize
        SpotBlend = props.SpotBlend

        AreaSizeX = props.AreaSizeX
        AreaSizeY = props.AreaSizeY

        self.light_col = bpy.data.collections.new('AD_Lights')
        self.scene_track.collection.children.link(self.light_col)

        light_type = ['POINT', 'SUN', 'SPOT', 'AREA']
        Amount = [0,0,0,0]
        Amount[0] = self.util_Random(seed_light, 'Point', 0, PointMax)
        Amount[1] = self.util_Random(seed_light, 'Sun', 0, SunMax)
        Amount[2] = self.util_Random(seed_light, 'Spot', 0, SpotMax)
        Amount[3] = self.util_Random(seed_light, 'Area', 0, AreaMax)

        self.Lights = [[],[],[],[]]
        for i, light in enumerate(self.Lights):
            if Amount[i]:
                for light_index in range(Amount[i]):
                    light_data = bpy.data.lights.new(name=light_type[i] + '_DATA', type=light_type[i])
                    light_data.color = Color
                    light_data.energy = Power

                    if i == 0:
                        light_data: bpy.types.PointLight
                        light_data.shadow_soft_size = self.util_Random(
                            seed_light, 'PointSize', 0, PointRadius
                            ) if bRandomSpec else PointRadius
                    if i == 1:
                        light_data: bpy.types.SunLight
                        light_data.angle = self.util_Random(
                            seed_light, 'SunAngle', 0, SunAngle
                            ) if bRandomSpec else SunAngle
                    if i == 2:
                        light_data: bpy.types.SpotLight
                        light_data.shadow_soft_size = self.util_Random(
                            seed_light, 'SpotRadius', 0, SpotRadius
                            ) if bRandomSpec else SpotRadius
                        light_data.spot_size = self.util_Random(
                            seed_light, 'SpotSize', 0, SpotSize
                            ) if bRandomSpec else SpotSize
                        light_data.spot_blend = self.util_Random(
                            seed_light, 'SpotBlend', 0, SpotBlend
                            ) if bRandomSpec else SpotBlend
                    if i == 3:
                        light_data: bpy.types.AreaLight
                        light_data.size = self.util_Random(
                            seed_light, 'AreaSizeX', 0, AreaSizeX
                            ) if bRandomSpec else AreaSizeX
                        light_data.size_y = self.util_Random(
                            seed_light, 'AreaSizeY', 0, AreaSizeY
                            ) if bRandomSpec else AreaSizeY

                    light_object = bpy.data.objects.new(name=light_type[i], object_data=light_data)
                    light_object[Flag] = True
                    self.Lights[i].append(light_object)
                    self.light_col.objects.link(light_object)
                    
                    self.util_Random_iterable(
                        seed_light, light_type[i] + 'Location' + str(light_index),
                        light_object.location,
                        -Range/2, Range/2
                        )
                    self.util_Random_iterable(
                        seed_light, light_type[i] + 'Rotation' + str(light_index),
                        light_object.rotation_euler,
                        0, 2*math.pi
                        )

        info = 'Random Light OVER'
        # self.report({'INFO'}, info)
        print(info)

    def RandomCameraGenerate(self):
        info = 'Random Camera START'
        # self.report({'INFO'}, info)
        print(info)

        seed_camera = self.seed_video_str + 'Camera'
        random.seed(seed_camera)

        props = self.Props.Camera
        strc = props.Curves
        CameraNumber = props.CameraNumber
        CameraMotionRange = props.CameraMotionRange
        bRandomCameraFocus = props.bRandomCameraFocus
        RandomFocusCenter = props.RandomFocusCenter
        bRandomCameraRotate = props.bRandomCameraRotate
        ComplexRate = props.ComplexRate

        LensFocalLength = props.LensFocalLength

        bUseDoF = props.bUseDoF
        FocalDistance = props.FocalDistance
        FStop = props.FStop
        Blades = props.Blades
        ApertureRotation = props.ApertureRotation
        ApertureRatio = props.ApertureRatio

        SensorFit = props.SensorFit
        SensorSize = props.SensorSize

        self.camera_col = bpy.data.collections.new('AD_Cameras')
        self.scene_track.collection.children.link(self.camera_col)
        empty_origin = bpy.data.objects.new('Empty_Origin', None)
        empty_origin.empty_display_type = 'PLAIN_AXES'
        self.camera_col.objects.link(empty_origin)

        self.Cameras = []
        self.Curves = []

        if strc:
            choice = random.choices(strc, k=CameraNumber)
            for col in choice:
                each_curve = col.Object
                curve_new : bpy.types.Object = each_curve.copy()
                curve_new.data = each_curve.data.copy()
                curve_new.user_clear()
                curve_new['bCameraFocus'] = col.bCameraFocus
                curve_new['FocusCenter'] = col.FocusCenter
                curve_new['bCameraRotate'] = col.bCameraRotate
                curve_new[Flag] = True
                self.Curves.append(curve_new)
                self.camera_col.objects.link(curve_new)
        else:
            for _ in range(CameraNumber):
                curve_data = bpy.data.curves.new('Curve', type='CURVE')    
                curve_data.dimensions = '3D'

                polyline = curve_data.splines.new('BEZIER')
                polyline.bezier_points.add(ComplexRate-1)
                for i, each_point in enumerate(polyline.bezier_points):
                    each_point: bpy.types.BezierSplinePoint
                    self.util_Random_iterable(
                        seed_camera, 'BezierPoint%s'%str(i), each_point.co, -CameraMotionRange, CameraMotionRange
                        )
                    each_point.handle_left_type = 'ALIGNED'
                    self.util_Random_iterable(
                        seed_camera, '%s_HandleLeft'%str(i), each_point.handle_left, 0.9, 1.1
                        )
                    each_point.handle_left = each_point.handle_left + each_point.co
                    each_point.handle_right_type = 'ALIGNED'
                    self.util_Random_iterable(
                        seed_camera, '%s_HandleRight'%str(i), each_point.handle_right, 0.9, 1.1
                        )
                    each_point.handle_right = each_point.handle_right + each_point.co

                curve_object = bpy.data.objects.new('Bezier', curve_data)
                curve_object['bCameraFocus'] = bRandomCameraFocus
                curve_object['FocusCenter'] = RandomFocusCenter
                curve_object['bCameraRotate'] = bRandomCameraRotate
                curve_object[Flag] = True
                self.Curves.append(curve_object)
                self.camera_col.objects.link(curve_object)

        for curve_object in self.Curves:
            camera_data = bpy.data.cameras.new(name='Camera')
            camera_data.clip_start = 0.001
            camera_data.lens = LensFocalLength
            if bUseDoF:
                dof = camera_data.dof
                dof.focus_distance = FocalDistance
                dof.aperture_fstop = FStop
                dof.aperture_blades = Blades
                dof.aperture_rotation = ApertureRotation
                dof.aperture_ratio = ApertureRatio
            camera_data.sensor_fit = SensorFit
            camera_data.sensor_width = SensorSize
            camera_data.sensor_height = SensorSize

            camera_object = bpy.data.objects.new('Camera', camera_data)
            camera_object.rotation_euler = (math.pi/2, 0, 0)
            follow_path = camera_object.constraints.new(type='FOLLOW_PATH')
            follow_path: bpy.types.FollowPathConstraint
            follow_path.target = curve_object
            follow_path.use_fixed_location = True
            if curve_object['bCameraFocus']:
                empty_origin.location = curve_object['FocusCenter']
                con = camera_object.constraints.new(type='TRACK_TO')
                con: bpy.types.TrackToConstraint
                con.target = empty_origin
            else:
                if curve_object['bCameraRotate']:
                    follow_path.use_curve_follow = True
            camera_object[Flag] = True

            self.Cameras.append(camera_object)
            self.camera_col.objects.link(camera_object)

        info = 'Random Camera OVER'
        # self.report({'INFO'}, info)
        print(info)

    def RandomPhysics(self, seed: str, obj_ori: bpy.types.Object, obj_new: bpy.types.Object):
        info = 'Random Physics START'
        # self.report({'INFO'}, info)
        print(info)

        seed_phy = seed + 'Physics'
        random.seed(seed_phy)

        props = self.Props.Physics
        strc = props.SelectedObject

        if strc:
            for each_strc in strc:
                Object = each_strc.Object
                Shape = each_strc.Shape
                Source = each_strc.Source
                Mass = each_strc.Mass
                Friction = each_strc.Friction
                Bounciness = each_strc.Bounciness
                Damping = each_strc.Damping
                Rotation = each_strc.Rotation

                self.util_AddRigidBodyWorld()

                if obj_ori == Object:
                    self.scene_track.rigidbody_world.collection.objects.link(obj_new)
                    obj_new.rigid_body.mass = self.util_Random(
                        seed_phy, 'Mass', Mass * 0.5, Mass
                        )
                    obj_new.rigid_body.collision_shape = Shape
                    obj_new.rigid_body.mesh_source = Source
                    obj_new.rigid_body.friction = self.util_Random(
                        seed_phy, 'Friction', 0.001, Friction
                        )
                    obj_new.rigid_body.restitution = self.util_Random(
                        seed_phy, 'Bounciness', 0.001, Bounciness
                        )
                    obj_new.rigid_body.linear_damping = self.util_Random(
                        seed_phy, 'Damping', 0.001, Damping
                        )
                    obj_new.rigid_body.angular_damping = self.util_Random(
                        seed_phy, 'Rotation', 0.001, Rotation
                        )
            try:
                if self.Non_tracks_withPhysics:
                    for each in self.Non_tracks_withPhysics:
                        self.scene_track.rigidbody_world.collection.objects.link(each)

            except:
                ...

        info = 'Random Physics OVER'
        # self.report({'INFO'}, info)
        print(info)

    def RandomMovement(self, seed: str, obj_ori: bpy.types.Object, obj_new: bpy.types.Object):
        info = 'Random Movement START'
        # self.report({'INFO'}, info)
        print(info)

        seed_mov = seed + 'Movement'
        random.seed(seed_mov)

        value = 0.0
        direction = [0,0,0]

        props = self.Props.Movement

        if props.bRandomVelVal:
            Max = props.MaxVel
            Min = props.MinVel
            value = self.util_Random(seed_mov, 'VelocityValue', Min, Max)
        else:
            value = props.InitialVelVal

        if props.bRandomVelDir:
            direction = self.util_Random_iterable(seed_mov, 'VelocityDirection', direction, -1.0, 1.0)
        else:
            direction = props.InitialVelDir
        direction = np.array(direction)
        length = np.linalg.norm(direction)
        if length <= 0:
            direction = direction
        else:
            direction = direction / length

        velocity = direction * value
        obj_new['initial_velocity'] = velocity

        info = 'Random Movement OVER'
        # self.report({'INFO'}, info)
        print(info)
        ...

    def SetHdri(self, dir: str):
        info = 'Set Hdri START'
        # self.report({'INFO'}, info)
        print(info)

        seed_hdri = self.seed_video_str + 'Hdri'
        random.seed(seed_hdri)
        world = bpy.data.worlds.new('AD_Wolrd')
        world.use_nodes = True
        self.scene_track.world = world

        node_tree = world.node_tree
        tree_nodes = node_tree.nodes

        tree_nodes.clear()

        # Add Background node
        node_background = tree_nodes.new(type='ShaderNodeBackground')

        # Add Environment Texture node
        node_environment = tree_nodes.new(type='ShaderNodeTexEnvironment')

        # Add Output node
        node_output = tree_nodes.new(type='ShaderNodeOutputWorld')

        self.HDRI = []
        Hdri_list = []
        for files in os.listdir(dir):
            if files.endswith('.exr'):
                Hdri_list.append(os.path.join(dir, files))

        try:
            image = bpy.data.images.load(random.choice(Hdri_list))
            image[Flag] = True
            node_environment.image = image
            self.HDRI.append(image)

            # Link all nodes
            links = node_tree.links
            link = links.new(node_environment.outputs["Color"], node_background.inputs["Color"])
            link = links.new(node_background.outputs["Background"], node_output.inputs["Surface"])
        
        except IndexError:
            info = 'No Hdri files found, will use default gray background'
            # self.report({'WARNING'}, info)
            print(info)

            node_background.color = (0.05, 0.05, 0.05)
            tree_nodes.remove(node_environment)

            links = node_tree.links
            link = links.new(node_background.outputs["Background"], node_output.inputs["Surface"])
        ...

        info = 'Set Hdri OVER'
        # self.report({'INFO'}, info)
        print(info)

    def Animation(self):
        info = 'Create Animation START'
        # self.report({'INFO'}, info)
        print(info)

        seed_animation = self.seed_video_str + 'Animation'
        random.seed(seed_animation)

        fps = self.scene_track.render.fps
        velocity_time = 3 / fps

        self.AnimationAction = []
        for each in self.Cameras:
            each: bpy.types.Camera
            each.animation_data_create()
            each.animation_data.action = bpy.data.actions.new(name='AD_CameraAction')
            each.animation_data.action[Flag] = True
            fcurve = each.animation_data.action.fcurves.new(
                data_path='constraints["Follow Path"].offset_factor'
            )

            k1 = fcurve.keyframe_points.insert(frame=self.scene_track.frame_start, value=0)
            k2 = fcurve.keyframe_points.insert(frame=self.scene_track.frame_end, value=1)
            k1.interpolation = 'LINEAR'
            k2.interpolation = 'LINEAR'
            self.AnimationAction.append(each.animation_data.action)

        total_curves = min(len(self.Props.Movement.Curves), len(self.Objects))
        choice_objects = random.sample(list(set(self.Objects)), k=total_curves)
        choice_curves = random.sample(list(set(self.Props.Movement.Curves)), k=total_curves)

        self.util_AddRigidBodyWorld()
        for each in self.Objects:
            each: bpy.types.Object
            each.animation_data_create()
            each.animation_data.action = bpy.data.actions.new(name='AD_ObjectAction')
            each.animation_data.action[Flag] = True

            if each in choice_objects:
                self.rigidbody_collection.objects.unlink(each)
                i = choice_objects.index(each)
                curve_object = choice_curves[i].Object
                follow_path = each.constraints.new(type='FOLLOW_PATH')
                follow_path: bpy.types.FollowPathConstraint
                follow_path.target = curve_object
                follow_path.use_fixed_location = True
                if choice_curves[i].bObjectRotate:
                    follow_path.use_curve_follow = True
                fcurve = each.animation_data.action.fcurves.new(
                    data_path='constraints["Follow Path"].offset_factor'
                )

                k1 = fcurve.keyframe_points.insert(frame=self.scene_track.frame_start, value=0)
                k2 = fcurve.keyframe_points.insert(frame=self.scene_track.frame_end, value=1)
                k1.interpolation = 'LINEAR'
                k2.interpolation = 'LINEAR'
                self.AnimationAction.append(each.animation_data.action)
                each.location = [0,0,0]

            else:
                ini_vel: [float] = each['initial_velocity']

                fcurve_x = each.animation_data.action.fcurves.new(data_path='location', index=0)
                fcurve_y = each.animation_data.action.fcurves.new(data_path='location', index=1)
                fcurve_z = each.animation_data.action.fcurves.new(data_path='location', index=2)
                fcurve_phy_animate = each.animation_data.action.fcurves.new(data_path='rigid_body.kinematic')

                k_x_1 = fcurve_x.keyframe_points.insert(frame=1, value=each.location[0])
                k_y_1 = fcurve_y.keyframe_points.insert(frame=1, value=each.location[1])
                k_z_1 = fcurve_z.keyframe_points.insert(frame=1, value=each.location[2])
                k_phy_animate_1 = fcurve_phy_animate.keyframe_points.insert(frame=1, value=True)
                k_x_1.interpolation = 'LINEAR'
                k_y_1.interpolation = 'LINEAR'
                k_z_1.interpolation = 'LINEAR'
                k_phy_animate_1.interpolation = 'CONSTANT'

                k_x_2 = fcurve_x.keyframe_points.insert(frame=4, value=each.location[0] + (ini_vel[1] * velocity_time))
                k_y_2 = fcurve_y.keyframe_points.insert(frame=4, value=each.location[1] + (ini_vel[1] * velocity_time))
                k_z_2 = fcurve_z.keyframe_points.insert(frame=4, value=each.location[2] + (ini_vel[2] * velocity_time))
                k_phy_animate_2 = fcurve_phy_animate.keyframe_points.insert(frame=4, value=False)
                k_x_2.interpolation = 'LINEAR'
                k_y_2.interpolation = 'LINEAR'
                k_z_2.interpolation = 'LINEAR'
                k_phy_animate_2.interpolation = 'CONSTANT'

                self.AnimationAction.append(each.animation_data.action)

        info = 'Create Animation OVER'
        # self.report({'INFO'}, info)
        print(info)

    def RenderAction(self):
        scene= self.scene_track

        info = 'Rendering START'
        # self.report({'INFO'}, info)
        print(info)

        for i_camera, each_camera in enumerate(self.Cameras):
            scene.camera = each_camera
            
            for i in range(self.StartFrameIndex, scene.frame_end + 1):
                scene.frame_set(i)
                image_name = str(i_camera).zfill(4) + '_' + str(scene.frame_current).zfill(4)
                scene.render.filepath = (self.image_path + image_name)  # Set save path with frame

                Output_cryptmatte = object_by_cryptomatte(
                    self.segement_path,
                    self.scene_track, 
                    self.ViewLayer, 
                    self.Objects
                    )

                bpy.ops.render.render({"scene": scene},
                    scene= scene.name, layer= self.ViewLayer.name, animation=False, write_still=True
                    )
                
                Output_cryptmatte.Find_bbox(image_name, self.segement_path)

            info = 'Camera %d in video No.%d render finished' % (i_camera+1, self.video_num)
            print('\n')
            print(info)

            time.sleep(0.01)

    def BackFromPreview(self,context):
        scene_delete = bpy.data.scenes[scene_name]

        self.clear_scene(scene_delete)

        bpy.data.scenes.remove(scene_delete)

        context.scene.P_S.General.bInPreview = False

        area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        space = next(space for space in area.spaces if space.type == 'VIEW_3D')
        space.shading.type = 'SOLID'  # set the viewport shading
        space.overlay.show_overlays = True
        
        info = 'Back form preview'
        # self.report({'INFO'}, info)
        print(info)

    def util_Random_iterable(self, seed: str, name: str, target, min, max):
        seed_tmp = seed + name
        for i in range(len(target)):
            seed_tmp += str(i)
            random.seed(seed_tmp)
            if isinstance(target[i], int):
                target[i] = random.randint(min,max)
            else:
                target[i] = random.uniform(min,max)
        return target

    def util_Random(self, seed: str, name: str, min, max):
        seed_tmp = seed + name
        random.seed(seed_tmp)
        if isinstance(max, int):
            target = random.randint(min,max)
        else:
            target = random.uniform(min,max)
        return target

    def util_ApplyTransform(self, object: bpy.types.Object):
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
        # bpy.context.view_layer.update()

        info = 'Object %s has been applied Rotation and Scale' % (object.name)
        # self.report({'WARNING'}, info)
        print(info)

    def util_AddRigidBodyWorld(self):
        if not self.scene_track.rigidbody_world:
            bpy.ops.rigidbody.world_add({"scene": self.scene_track})
        if not self.scene_track.rigidbody_world.collection:
            rigidbody_collection = bpy.data.collections.new("AD_RigidBodyWorld")
            self.rigidbody_collection = rigidbody_collection
            self.scene_track.rigidbody_world.collection = rigidbody_collection
        self.scene_track.rigidbody_world.enabled = True
        self.scene_track.rigidbody_world.point_cache.frame_start = 1
        self.scene_track.rigidbody_world.point_cache.frame_end = self.scene_track.frame_end

AllOperators = [OP_Action]