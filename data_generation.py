import bpy
import mathutils
import pathlib
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import bmesh
from math import radians,sqrt
import numpy as np
import os
from math import pi, acos
from io_mesh_ply import import_ply
from space_view3d_point_cloud_visualizer import PCVControl



    
def look_at(obj_camera, point):
    '''
    make the camera look at the object
    '''
    loc_camera = obj_camera.matrix_world.to_translation()
    
    direction = point - loc_camera
    
    # Y up, -Z to
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj_camera.rotation_euler = rot_quat.to_euler()

    
    bpy.context.view_layer.update()

#def remove_bounding_box():
    
    
def reset_all():
    '''
    delete all the object 
    reset frame
    '''
    
    objs = bpy.data.objects
    for o in bpy.data.objects:
        objs.remove(o, do_unlink=True)

    for o in bpy.context.scene.objects:
        print('o',o)
        if o.type == 'LIGHT' or o.type == 'CAMERA' or o.type == 'MESH':
            o.select_set(True)
        else:
            o.select_set(False)

    bpy.ops.object.delete()
    
    current_frame = bpy.context.scene.frame_current
    bpy.context.scene.frame_set(0)
    
    #change to metric system
    bpy.context.scene.unit_settings.system = 'METRIC'
    
    #change the measure system
    bpy.context.scene.unit_settings.length_unit = 'METERS'
    
    # create light datablock, set attributes
    light_data = bpy.data.lights.new(name="light_2.80", type='POINT')
    light_data.energy = 2500

    # create new object with our light datablock
    light_object = bpy.data.objects.new(name="light_2.80", object_data=light_data)

    # link light object
    bpy.context.collection.objects.link(light_object)

    scene = bpy.context.scene
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.render.image_settings.color_depth = '16'
    scene.view_settings.view_transform = 'Raw'
    scene.sequencer_colorspace_settings.name = 'Raw'

    #change location
    light_object.location = (4, 4, 10)

    # update scene, if needed
    dg = bpy.context.evaluated_depsgraph_get() 
    dg.update()
    

    
def add_mesh(shape,size,location,scale,path = None):
    '''
    add mesh to the scence, it can be primitive, or custom_stl
    '''
    if shape == 'Cube':
        bpy.ops.mesh.primitive_cube_add(size=size, enter_editmode=False, location=location)
        bpy.context.active_object.name = 'new_name'
    
    if shape == 'custom_stl':
        custom_mesh = bpy.ops.import_mesh.stl(filepath=path)
        bpy.context.object.scale[0] = scale[0]
        bpy.context.object.scale[1] = scale[1]
        bpy.context.object.scale[2] = scale[2]
#        bpy.context.collection.objects.link(custom_mesh)
        
    bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
    bpy.context.object.scale[0] = 40
    bpy.context.object.scale[1] = 40
    bpy.context.object.scale[2] = 40

        
    
def get_dir_file_path():
    BASE_DIR = pathlib.Path(__file__)
    BASE_DIR = BASE_DIR.parent

    #get base directory
    STL_DIR = BASE_DIR.joinpath('env').joinpath('mesh')
    all_STL = list(STL_DIR.glob('**/*.stl'))
    all_STL = [str(item) for item in all_STL]
    
    return BASE_DIR, STL_DIR, all_STL

def add_camera(location,rotation,align = 'VIEW'):
    bpy.ops.object.camera_add(enter_editmode=False, align=align, location=location, rotation=rotation)
#    cam = bpy.data.cameras['Camera']
    cam = bpy.context.object.data
    cam.clip_start = 0.5 
    cam.clip_end = 10
    cam.lens = 25
    cam.type = 'PERSP'
    cam.sensor_fit = 'HORIZONTAL'


#    cam.type = 'PERSP'
#    bpy.context.object.data.lens = 20

    
def generate_cam_x_y(radius,level = 2,center = (0,0,0),num_loc = 100):
    '''
    generate camera location 
    '''
    locs = np.zeros((num_loc,2))
    locs = np.concatenate((locs,np.ones((num_loc,1)) * level + center[2]),axis = 1)
    
    x_loc = np.random.uniform(-radius,radius,(num_loc,1))
    sign = np.random.choice([-1,1],(num_loc,1))
    y_loc = sign * (radius ** 2 - x_loc ** 2) ** 0.5
    
    for i in range(locs.shape[0]):
        locs[i,0] = x_loc[i] + center[0]
        locs[i,1] = y_loc[i] + center[1]
    
    return locs
        
def save_camera_intrinsics(path,camd):
    
    def get_sensor_size(sensor_fit, sensor_x, sensor_y):
        if sensor_fit == 'VERTICAL':
            return sensor_y
        return sensor_x

    def get_sensor_fit(sensor_fit, size_x, size_y):
        if sensor_fit == 'AUTO':
            if size_x >= size_y:
                return 'HORIZONTAL'
            else:
                return 'VERTICAL'
        return sensor_fit
    
    
    scene = bpy.context.scene
    f_in_mm = camd.lens
    
    scale = scene.render.resolution_percentage / 100
    resolution_x_in_px = scale * scene.render.resolution_x
    resolution_y_in_px = scale * scene.render.resolution_y
    sensor_size_in_mm = get_sensor_size(camd.sensor_fit, camd.sensor_width, camd.sensor_height)
    sensor_fit = get_sensor_fit(
        camd.sensor_fit,
        scene.render.pixel_aspect_x * resolution_x_in_px,
        scene.render.pixel_aspect_y * resolution_y_in_px
    )
    
    pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
    if sensor_fit == 'HORIZONTAL':
        view_fac_in_px = resolution_x_in_px
    else:
        view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px
    pixel_size_mm_per_px = sensor_size_in_mm / f_in_mm / view_fac_in_px
    
    s_u = 1 / pixel_size_mm_per_px
    s_v = 1 / pixel_size_mm_per_px / pixel_aspect_ratio

    # Parameters of intrinsic calibration matrix K
    u_0 = resolution_x_in_px / 2 - camd.shift_x * view_fac_in_px
    v_0 = resolution_y_in_px / 2 + camd.shift_y * view_fac_in_px / pixel_aspect_ratio
    skew = 0 # only use rectangular pixels

    intrinsics = np.array([[s_u,skew,u_0],
                  [0,  s_v, v_0],
                  [0,  0,   1]])
    
    intri_path = str(path.joinpath('data').joinpath('camera-intrinsics.npy'))
#    intri_path_txt = str(path.joinpath('data').joinpath('camera-intrinsics.txt'))
    np.save(intri_path, intrinsics)
#    np.savetxt(intri_path_txt , intrinsics)



def get_calibration_matrix_K_from_blender(cam):
    # get the relevant data
    scene = bpy.context.scene
    # assume image is not scaled
    assert scene.render.resolution_percentage == 100
    # assume angles describe the horizontal field of view
    assert cam.sensor_fit != 'VERTICAL'

    f_in_mm = cam.lens
    sensor_width_in_mm = cam.sensor_width

    w = scene.render.resolution_x
    h = scene.render.resolution_y

    pixel_aspect = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x

    f_x = f_in_mm / sensor_width_in_mm * w
    f_y = f_x * pixel_aspect

    # yes, shift_x is inverted. WTF blender?
    c_x = w * (0.5 - cam.shift_x)
    # and shift_y is still a percentage of width..
    c_y = h * 0.5 + w * cam.shift_y

    K = [[f_x, 0, c_x],
         [0, f_y, c_y],
         [0,   0,   1]]
    return K

def save_image(BASE_DIR,rgb = True, depth = True):
    
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links
    
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    #stop use extension
    bpy.context.scene.render.use_file_extension = True

    #create composite layer
    render_layer_node = tree.nodes.new('CompositorNodeRLayers')
    
    #depth node
    if depth:
        map_value_node = tree.nodes.new('CompositorNodeMapValue')
        depth_file_output_node = tree.nodes.new('CompositorNodeOutputFile')
        
        g_depth_clip_start = 0.5
        g_depth_clip_end = 30
        
        g_depth_color_mode = 'BW'
        g_depth_color_depth = '16'
        g_depth_file_format = 'PNG'

        map_value_node.size[0] = 1/ bpy.context.object.data.clip_end
        
        depth_file_output_node.format.color_mode = g_depth_color_mode
        depth_file_output_node.format.color_depth = g_depth_color_depth
        depth_file_output_node.format.file_format = g_depth_file_format 
        depth_file_output_node.base_path = str(BASE_DIR.joinpath('data'))

        #normalized by far cliping
        links.new(render_layer_node.outputs[2], map_value_node.inputs[0])
        links.new(map_value_node.outputs[0], depth_file_output_node.inputs[0])
        
#        links.new(render_layer_node.outputs[2], depth_file_output_node.inputs[0])
        depth_file_output_node.file_slots[0].path = 'frame-######.depth'

    #color node
    if rgb:
        scale_node = tree.nodes.new('CompositorNodeScale')
        alpha_over_node = tree.nodes.new('CompositorNodeAlphaOver')
        color_file_output_node = tree.nodes.new('CompositorNodeOutputFile')

        g_scale_space = 'RENDER_SIZE'
        scale_node.space = g_scale_space
        color_file_output_node.base_path = str(BASE_DIR.joinpath('data'))

        links.new(render_layer_node.outputs[0], scale_node.inputs[0])
        links.new(scale_node.outputs[0], alpha_over_node.inputs[1])
        links.new(render_layer_node.outputs[0], alpha_over_node.inputs[2])
        links.new(alpha_over_node.outputs[0], color_file_output_node.inputs[0])
        
        color_file_output_node.file_slots[0].path = 'frame-######.color'
    

    bpy.ops.render.render(write_still=False)
    current_frame = bpy.context.scene.frame_current
    bpy.context.scene.frame_set(current_frame + 1)
    
    
def duplicate_obj(obj):
    obj_copy = obj.copy()
    obj_copy.data = obj_copy.data.copy()
    bpy.context.collection.objects.link(obj_copy)
    
    return obj_copy
    
def create_rect(obj,translation):
    
    bound_box = np.array(obj.bound_box)
    bounding_points = (np.array(obj.matrix_world)[:3,:3] @ bound_box.T).T
    
    min_x,min_y,min_z = np.min(bounding_points[:,0]),np.min(bounding_points[:,1]),np.min(bounding_points[:,2])
    max_x,max_y,max_z = np.max(bounding_points[:,0]),np.max(bounding_points[:,1]),np.max(bounding_points[:,2])
    
    min_x = min_x + translation[0] - 1.2
    max_x = max_x + translation[0] + 0.2
    
    min_y = min_y + translation[1] - 0.6
    max_y = max_y + translation[1] + 0.6
    
    min_z = min_z + translation[2] - 0.3
    max_z = max_z + translation[2] - 0.001
    
#    print('-' * 50)
#    print(min_x,max_x)
#    print(min_y,max_y)
#    print(min_z,max_z)
    
    verts = [
    (max_x, max_y, min_z),
    (max_x, min_y, min_z),
    (min_x, min_y, min_z),
    (min_x, max_y, min_z),
    (max_x, max_y, max_z),
    (max_x, min_y, max_z),
    (min_x, min_y, max_z),
    (min_x, max_y, max_z)
    ]

    faces = [
    (0, 1, 2, 3),
    (4, 7, 6, 5),
    (0, 4, 5, 1),
    (1, 5, 6, 2),
    (2, 6, 7, 3),
    (4, 0, 3, 7)
    ]
    
    mesh_data = bpy.data.meshes.new("cube_mesh_data")
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()

    Bounding_Mesh = bpy.data.objects.new("Bounding_Mesh", mesh_data)

#    scene = bpy.context.scene
#    scene.collection.objects.link(rect)
    bpy.context.collection.objects.link(Bounding_Mesh)
    
    return Bounding_Mesh
    

def transform_and_save(path,num,obj,angle,translation = (3,0,0)):
    
    #select context
    context = bpy.context
    obj_placeholder = duplicate_obj(obj)
    
    #transformation
    rot_mat = Matrix.Rotation(radians(angle), 4, 'Z')         
    trans_mat = Matrix.Translation(translation)
    mat = trans_mat @ rot_mat
    
    #record vertices
#    vertics = np.zeros((len(obj.data.vertices),3))
#    for i,vert in enumerate(obj.data.vertices):
#        vertics[i,:] = obj_placeholder.matrix_world @ vert.co
    obj_placeholder.matrix_world = mat @ obj_placeholder.matrix_world
    
    Bounding_Mesh = create_rect(obj,translation)
    
    large_cube = context.object

    mod = Bounding_Mesh.modifiers.new("Boolean", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = obj_placeholder

    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)  
    
    print('before',obj_placeholder.matrix_world @ list(obj.data.vertices)[0].co)
    print('after',obj.matrix_world @ list(obj.data.vertices)[0].co)
    
    context.collection.objects.unlink(obj_placeholder)    
     
    save_path_npy = str(path.joinpath('data').joinpath('frame-object-{:06}.pose.npy'.format(num)))
#    save_path_npy_vertices = str(path.joinpath('data').joinpath('frame-object-{:06}.vertices.npy'.format(num)))
    
    #scale with trans and rot
    np.save(save_path_npy,np.array(mat))
#    np.save(save_path_npy_vertices,vertics)
    
    return mat

def get_sensor_size(sensor_fit, sensor_x, sensor_y):
    if sensor_fit == 'VERTICAL':
        return sensor_y
    return sensor_x


def get_sensor_fit(sensor_fit, size_x, size_y):
    if sensor_fit == 'AUTO':
        if size_x >= size_y:
            return 'HORIZONTAL'
        else:
            return 'VERTICAL'
    return sensor_fit

def get_3x4_RT_matrix(path,cam,iteration):    
    """
    get the pose of camera
    """
    
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed() 
    T_world2bcam = -1*R_world2bcam @ location

    R_world2cv = R_bcam2cv @ R_world2bcam
    T_world2cv = R_bcam2cv @ T_world2bcam

    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
         ))
    
    print(RT)
    RT_path = str(path.joinpath('data').joinpath('frame-camera-{:06}.RT.npy'.format(iteration)))
    np.save(RT_path ,RT)
        
def save_load_ply_file(path,points, in_side_px,load_ply = False):
    
    TEST_DIR = path.joinpath('test')
    grid = str(TEST_DIR.joinpath('grid.ply'))
    ply_file = open(grid,'w')
    ply_file.write("ply\n")
    ply_file.write("format ascii 1.0\n")
    ply_file.write("element vertex %d\n"%(points.shape[0]))
    ply_file.write("property float x\n")
    ply_file.write("property float y\n")
    ply_file.write("property float z\n")
    ply_file.write("property float nx\n")
    ply_file.write("property float ny\n")
    ply_file.write("property float nz\n")
    ply_file.write("property uchar red\n")
    ply_file.write("property uchar green\n")
    ply_file.write("property uchar blue\n")
    ply_file.write("end_header\n")

    for i in range(points.shape[0]):
        if in_side_px[i] == True:
            ply_file.write("%f %f %f %f %f %f %d %d %d\n"%(points[i,0],points[i,1],points[i,2],0,0,0,0,0,0))
        else:
            ply_file.write("%f %f %f %f %f %f %d %d %d\n"%(points[i,0],points[i,1],points[i,2],0,0,0,255,0,0))

    ply_file.close()
    if load_ply:
        import_ply.load_ply(grid)
    


def point_cloud_inside(path ,obj, grid_size, scale,tolerance=0.05):
    
    c = PCVControl(obj)

    TEST_DIR = path.joinpath('test')
    CUR_PLT_DIR = path.joinpath('env').joinpath('tsdf_projected_ply')
    ply_list = [str(item) for item in CUR_PLT_DIR.glob('**/*.ply')]
    
    if not os.path.exists(str(TEST_DIR)):
        os.mkdir(TEST_DIR)

    bound_box = np.array(obj.bound_box)
    bounding_points = (np.array(obj.matrix_world)[:3,:3] @ bound_box.T).T
    
    shift = 0.01
    
    min_x,min_y,min_z = np.min(bounding_points[:,0]) - shift,np.min(bounding_points[:,1]) - shift,np.min(bounding_points[:,2]) - shift 
    max_x,max_y,max_z = np.max(bounding_points[:,0]) - shift,np.max(bounding_points[:,1]) - shift,np.max(bounding_points[:,2]) - shift
        
    xyz = np.mgrid[min_x:max_x:grid_size, min_y:max_y:grid_size, min_z:max_z:grid_size]  
    points = np.reshape(xyz,[3,-1],order = 'C').T
    
    in_side_px = np.zeros((points.shape[0],), dtype=bool)
    for idx,point in enumerate(points):
        
        target_pt_local = obj.matrix_world.inverted() @ Vector(point)
        _, pt_closest, face_normal, _ = obj.closest_point_on_mesh(point / 0.1)
        target_closest_pt_vec = (pt_closest - target_pt_local).normalized()
        dot_prod = target_closest_pt_vec.dot(face_normal)
        in_side_px[idx] = not(dot_prod < 0)
        
    save_load_ply_file(path,points / scale,in_side_px)
    print('total_points_inside', np.sum(in_side_px))
    return points[in_side_px,:]

def save_vertices_inside_pts(path,obj,inside_pts):
    
    #record the vertices
    vertics = np.zeros((len(obj.data.vertices),3))
    for i,vert in enumerate(obj.data.vertices):
        vertics[i,:] = obj.matrix_world @ vert.co
    
    save_path_npy_inside_pts = str(path.joinpath('data').joinpath('frame-object.inside_pts.npy'))
    save_path_npy_vertices = str(path.joinpath('data').joinpath('frame-object.vertices.npy'))
    
    np.save(save_path_npy_inside_pts,inside_pts)
    np.save(save_path_npy_vertices,vertics)
    
    


if __name__ == '__main__':
    
    num_image = 200
    print(list(bpy.data.objects))
    print('\n' * 20 + 'start' + '-' * 30)
    reset_all()
    
    #get the working directory
    BASE_DIR, STL_DIR, all_STL = get_dir_file_path()
    
    print(all_STL)
    if not os.path.exists(BASE_DIR.joinpath('data')):
        os.chdir(BASE_DIR)
        os.mkdir('data')
    
    #add custom stl file
    add_mesh('custom_stl',1,(0,0,0),(0.1,0.1,0.1),all_STL[3])
    add_camera(location = (15,0,0),rotation = (0,0,0))
    scale = np.array((0.1,0.1,0.1))

    #save intrinsics
    cam = bpy.data.cameras["Camera"]
    cam = bpy.context.object.data
    save_camera_intrinsics(BASE_DIR,cam)
    
    #selet object
    obj = bpy.data.objects['small B']
    cam_locs = generate_cam_x_y(radius = 2,level = 6,center = (2,0,0),num_loc = num_image)
    
    #duplicate
    obj_copy = duplicate_obj(obj)
    obj_camera = bpy.data.objects["Camera"]
    bpy.context.view_layer.update()

    #calculate points inside a mesh
    pts_inside = point_cloud_inside(BASE_DIR,obj_copy,grid_size = 0.05,scale = scale)
    
    #save vertices and points inside mesh
    save_vertices_inside_pts(BASE_DIR,obj,pts_inside)
        
    
    for num in range(num_image):
        
        #rotate object and save object pose
        angle = np.random.uniform(0,1) * 360
        mat = transform_and_save(BASE_DIR,num,obj,angle = angle,translation = (3.5,0,0.3))
        
        #change camera location
        obj_camera.location = cam_locs[num,:]
        bpy.context.view_layer.update()
        
        #make the camera look at the object
        look_at(obj_camera, mathutils.Vector([1.5,0,0]))              
        get_3x4_RT_matrix(BASE_DIR,obj_camera,num)
        
        #select the camera
        bpy.context.scene.camera = bpy.context.object
        
        #save image
        save_image(BASE_DIR,rgb = True, depth = True)
        
        #delete unnecessary objects
        o = bpy.data.objects['Bounding_Mesh']
        bpy.data.objects.remove(o, do_unlink=True)
        o = bpy.data.objects['small B.002']
        bpy.data.objects.remove(o, do_unlink=True)
        

        
        
        

        


