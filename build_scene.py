import bpy
import bmesh
import math
import mathutils
import os

base_dir = "/Users/roshanpreetsinghdhiman/roshan/blender_models"

def clean_entire_blend_file():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)

# ----------------- Mesh Helpers (Direct bmesh creation) -----------------
def make_box(name, size, loc, mat=None, rot=(0,0,0), smooth=False):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    if smooth:
        for f in bm.faces:
            f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    obj.location = mathutils.Vector(loc)
    obj.rotation_euler = rot
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj

def make_cylinder(name, radius, depth, loc, mat=None, rot=(0,0,0), segments=32, smooth=True):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=depth)
    if smooth:
        for f in bm.faces:
            f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    obj.location = mathutils.Vector(loc)
    obj.rotation_euler = rot
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj

def make_cone(name, radius1, depth, loc, mat=None, rot=(0,0,0), segments=32, smooth=True):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius1, radius2=0.0, depth=depth)
    if smooth:
        for f in bm.faces:
            f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    obj.location = mathutils.Vector(loc)
    obj.rotation_euler = rot
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj

# ----------------- PBR Materials -----------------
def create_pbr_mat(name, base_color, roughness=0.5, metallic=0.0, specular=0.5, emission=None, emission_strength=1.0, is_glass=False):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new(type="ShaderNodeOutputMaterial")
    out.location = (300, 0)
    mat.diffuse_color = base_color
    
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    
    if is_glass:
        bsdf.inputs['Base Color'].default_value = (0.95, 0.98, 1.0, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.02
        bsdf.inputs['Transmission Weight'].default_value = 0.95
        bsdf.inputs['IOR'].default_value = 1.52
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'
    else:
        bsdf.inputs['Base Color'].default_value = base_color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if 'Specular IOR Level' in bsdf.inputs:
            bsdf.inputs['Specular IOR Level'].default_value = specular
        elif 'Specular' in bsdf.inputs:
            bsdf.inputs['Specular'].default_value = specular
            
        if emission:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = emission
                bsdf.inputs['Emission Strength'].default_value = emission_strength
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = emission
                
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_luxury_walnut_floor():
    mat = bpy.data.materials.new(name="RichWalnutPlankFloor")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    mat.diffuse_color = (0.24, 0.13, 0.07, 1.0)
    
    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.38
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.4
    
    coord = nodes.new(type="ShaderNodeTexCoord")
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.inputs['Scale'].default_value[0] = 0.6
    mapping.inputs['Scale'].default_value[1] = 2.2
    
    wave = nodes.new(type="ShaderNodeTexWave")
    wave.inputs['Scale'].default_value = 0.45
    wave.inputs['Distortion'].default_value = 0.7
    
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.2
    ramp.color_ramp.elements[0].color = (0.16, 0.08, 0.04, 1.0) # Deep dark walnut
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (0.32, 0.18, 0.09, 1.0) # Warm cognac wood
    
    links.new(coord.outputs['Object'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], wave.inputs['Vector'])
    links.new(wave.outputs['Color'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_cyberpunk_screen_mat():
    mat = bpy.data.materials.new(name="OLEDWallpaperPro")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.05
    
    # Create gradient wallpaper
    coord = nodes.new(type="ShaderNodeTexCoord")
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.inputs['Rotation'].default_value[2] = math.radians(45.0)
    
    grad = nodes.new(type="ShaderNodeTexGradient")
    grad.gradient_type = 'LINEAR'
    
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.1
    ramp.color_ramp.elements[0].color = (0.02, 0.05, 0.20, 1.0) # Deep midnight navy
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.0, 0.85, 0.95, 1.0) # Cyberpunk cyan glow
    e2 = ramp.color_ramp.elements.new(0.9)
    e2.color = (0.95, 0.15, 0.65, 1.0) # Synthwave magenta
    
    links.new(coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], grad.inputs['Vector'])
    links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    if 'Emission Color' in bsdf.inputs:
        links.new(ramp.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 2.5
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def append_objects(filepath, obj_names):
    full_path = os.path.join(base_dir, filepath)
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return []
    with bpy.data.libraries.load(full_path, link=False) as (data_from, data_to):
        if obj_names:
            data_to.objects = [name for name in data_from.objects if name in obj_names]
        else:
            data_to.objects = [name for name in data_from.objects if name not in ['Camera', 'Light', 'Lamp', 'Sun', 'Area']]
    appended = []
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            appended.append(obj)
    return appended

# ----------------- Lush Organic Conifer Tree Generator -----------------
def make_lush_pine_tree(name, loc, scale=1.0):
    bm = bmesh.new()
    mat_leaves = bpy.data.materials.get("DeepForestPineMat")
    if not mat_leaves:
        mat_leaves = create_pbr_mat("DeepForestPineMat", (0.025, 0.12, 0.04, 1.0), roughness=0.85, specular=0.2)

    # Trunk
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.18*scale, radius2=0.08*scale, depth=3.2*scale)
    for v in bm.verts:
        v.co.z += 1.6 * scale
    
    # 6 tiered rounded canopy layers
    tiers = [
        (1.5*scale, 1.3*scale, 1.5*scale, 0.0),
        (1.3*scale, 1.25*scale, 2.2*scale, 0.4),
        (1.05*scale, 1.2*scale, 2.9*scale, 0.8),
        (0.80*scale, 1.1*scale, 3.6*scale, 0.2),
        (0.55*scale, 0.9*scale, 4.3*scale, 0.6),
        (0.30*scale, 0.7*scale, 4.9*scale, 0.1)
    ]
    for r, h, z_base, rot_z in tiers:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=0.04*scale, depth=h)
        ca = math.cos(rot_z)
        sa = math.sin(rot_z)
        for v in bm.verts[-26:]:
            vx, vy = v.co.x, v.co.y
            v.co.x = vx * ca - vy * sa
            v.co.y = vx * sa + vy * ca
            v.co.z += z_base + h/2.0

    for f in bm.faces:
        f.smooth = True

    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    obj.location = mathutils.Vector(loc)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_leaves)
    return obj

# ----------------- Background Alpine Mountain Range -----------------
def create_panoramic_landscape():
    bm = bmesh.new()
    segments_x = 45
    segments_y = 55
    min_x, max_x = -75.0, -18.0
    min_y, max_y = -55.0, 55.0
    
    for i in range(segments_y + 1):
        y = min_y + (i / segments_y) * (max_y - min_y)
        for j in range(segments_x + 1):
            x = min_x + (j / segments_x) * (max_x - min_x)
            dist_w = max_x - x
            h1 = math.sin(x * 0.11) * math.cos(y * 0.09) * 9.5
            h2 = math.cos(x * 0.20 + y * 0.16) * 4.2
            h3 = math.sin(x * 0.35 - y * 0.28) * 1.8
            ramp_factor = (dist_w / (max_x - min_x)) ** 1.35
            z = max(0.0, (h1 + h2 + h3 + 6.0) * ramp_factor * 1.5) - 0.2
            bm.verts.new((x, y, z))
            
    bm.verts.ensure_lookup_table()
    for i in range(segments_y):
        for j in range(segments_x):
            v1 = bm.verts[i * (segments_x + 1) + j]
            v2 = bm.verts[i * (segments_x + 1) + j + 1]
            v3 = bm.verts[(i + 1) * (segments_x + 1) + j + 1]
            v4 = bm.verts[(i + 1) * (segments_x + 1) + j]
            bm.faces.new((v1, v2, v3, v4))
            
    mesh = bpy.data.meshes.new("AlpineMountainsMesh")
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
        
    terrain_obj = bpy.data.objects.new("AlpineMountains", mesh)
    bpy.context.collection.objects.link(terrain_obj)
    
    mat = bpy.data.materials.new(name="ScenicAlpineMountains")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    mat.diffuse_color = (0.12, 0.32, 0.10, 1.0)
    
    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.9
    
    coord = nodes.new(type="ShaderNodeTexCoord")
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.inputs['Scale'].default_value = 0.5
    noise.inputs['Detail'].default_value = 5.0
    
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[0].color = (0.10, 0.28, 0.08, 1.0)
    
    e1 = ramp.color_ramp.elements[1]
    e1.position = 0.60
    e1.color = (0.30, 0.28, 0.26, 1.0)
    
    e2 = ramp.color_ramp.elements.new(0.85)
    e2.color = (0.92, 0.95, 0.99, 1.0)
    
    links.new(coord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    terrain_obj.data.materials.append(mat)
    
    make_cylinder("InfiniteHorizonGround", 150.0, 0.1, (-30.0, 0.0, -0.15), mat, segments=48)
    return terrain_obj

# ----------------- Master 4K Scene Builder -----------------
def build_master_scene():
    clean_entire_blend_file()
    scene = bpy.context.scene
    
    # 1. Physical Atmosphere & Color Grading
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = -0.3
    
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()
    
    w_out = wnodes.new(type="ShaderNodeOutputWorld")
    w_bg = wnodes.new(type="ShaderNodeBackground")
    w_sky = wnodes.new(type="ShaderNodeTexSky")
    w_sky.sky_type = 'MULTIPLE_SCATTERING'
    w_sky.sun_elevation = math.radians(30.0)
    w_sky.sun_rotation = math.radians(110.0)
    w_bg.inputs['Strength'].default_value = 0.9
    wlinks.new(w_sky.outputs['Color'], w_bg.inputs['Color'])
    wlinks.new(w_bg.outputs['Background'], w_out.inputs['Surface'])

    # 2. Materials
    mat_floor = create_luxury_walnut_floor()
    mat_wall_slat = create_pbr_mat("AcousticWoodSlat", (0.12, 0.07, 0.04, 1.0), roughness=0.35)
    mat_wall_plaster = create_pbr_mat("DesignerPlaster", (0.92, 0.92, 0.90, 1.0), roughness=0.85)
    mat_ceiling = create_pbr_mat("CeilingMat", (0.96, 0.96, 0.96, 1.0), roughness=0.8)
    mat_glass = create_pbr_mat("ArchitecturalGlass", (0.95, 0.98, 1.0, 0.1), roughness=0.01, is_glass=True)
    mat_dark_aluminum = create_pbr_mat("AnodizedBlackAluminum", (0.05, 0.05, 0.06, 1.0), roughness=0.25, metallic=0.92)
    mat_gold_accent = create_pbr_mat("BrushedBrass", (0.85, 0.65, 0.25, 1.0), roughness=0.25, metallic=0.95)
    
    mat_warm_led = create_pbr_mat("WarmCoveLED", (1.0, 0.88, 0.72, 1.0), emission=(1.0, 0.88, 0.72, 1.0), emission_strength=4.5)
    mat_rgb_cyan = create_pbr_mat("RGBCyanGlow", (0.0, 0.9, 1.0, 1.0), emission=(0.0, 0.88, 1.0, 1.0), emission_strength=5.5)
    mat_rgb_magenta = create_pbr_mat("RGBMagentaGlow", (1.0, 0.05, 0.55, 1.0), emission=(1.0, 0.05, 0.55, 1.0), emission_strength=4.5)
    mat_screen_wallpaper = create_cyberpunk_screen_mat()
    
    mat_lawn = create_pbr_mat("LushGardenLawn", (0.14, 0.38, 0.12, 1.0), roughness=0.88)
    mat_patio_stone = create_pbr_mat("TravertinePatio", (0.82, 0.79, 0.75, 1.0), roughness=0.45)
    mat_court_blue = create_pbr_mat("CourtBluePro", (0.08, 0.24, 0.62, 1.0), roughness=0.55)
    mat_court_green = create_pbr_mat("CourtGreenPro", (0.12, 0.35, 0.20, 1.0), roughness=0.55)
    mat_court_line = create_pbr_mat("CourtLinePro", (0.98, 0.98, 0.98, 1.0), roughness=0.3)
    mat_rim_orange = create_pbr_mat("RimOrangePro", (0.95, 0.28, 0.04, 1.0), roughness=0.3, metallic=0.2)

    # 3. Room Architecture (X from -2.6 to 3.2, Y from -2.4 to 2.4, height 3.2m)
    room_w, room_d, room_h = 5.8, 4.8, 3.2
    floor_cx = 0.3
    floor_cy = 0.0
    make_box("RoomFloor", (room_w, room_d, 0.1), (floor_cx, floor_cy, -0.05), mat_floor)
    
    # Ceiling with Cove
    make_box("RoomCeiling", (room_w, room_d, 0.1), (floor_cx, floor_cy, room_h + 0.05), mat_ceiling)
    make_box("CoveLightingBack", (room_w - 0.4, 0.03, 0.02), (floor_cx, room_d/2 - 0.25, room_h - 0.03), mat_warm_led)
    make_box("CoveLightingRight", (0.03, room_d - 0.4, 0.02), (floor_cx + room_w/2 - 0.25, floor_cy, room_h - 0.03), mat_warm_led)

    # Back Wall with Designer Acoustic Wood Slats
    make_box("BackWallBase", (room_w, 0.15, room_h), (floor_cx, room_d/2, room_h/2), mat_wall_plaster)
    slat_spacing = 0.08
    for sx in [-2.4 + i * slat_spacing for i in range(35)]:
        make_box(f"WoodSlat_{sx:.2f}", (0.045, 0.03, room_h), (sx, room_d/2 - 0.09, room_h/2), mat_wall_slat)

    # Right Wall with Floor-to-Ceiling Picture Windows
    win_w, win_h = 2.0, 2.3
    right_wall_x = floor_cx + room_w/2
    for y_pos in [0.8, -1.3]:
        make_box(f"WinFrameOuter_{y_pos}", (0.16, win_w + 0.12, win_h + 0.12), (right_wall_x, y_pos, 1.5), mat_dark_aluminum)
        make_box(f"WinGlassPane_{y_pos}", (0.02, win_w, win_h), (right_wall_x, y_pos, 1.5), mat_glass)
        make_box(f"WinMullionH_{y_pos}", (0.06, win_w, 0.04), (right_wall_x, y_pos, 1.5), mat_dark_aluminum)
        make_box(f"WinMullionV_{y_pos}", (0.06, 0.04, win_h), (right_wall_x, y_pos, 1.5), mat_dark_aluminum)
        make_box(f"WinOakSill_{y_pos}", (0.35, win_w + 0.2, 0.04), (right_wall_x - 0.1, y_pos, 0.33), mat_wall_slat)
    
    make_box("RightPillarBack", (0.2, 0.8, room_h), (right_wall_x, 2.0, room_h/2), mat_wall_plaster)
    make_box("RightPillarCenter", (0.2, 0.6, room_h), (right_wall_x, -0.25, room_h/2), mat_wall_plaster)
    make_box("RightPillarFront", (0.2, 0.8, room_h), (right_wall_x, -2.0, room_h/2), mat_wall_plaster)

    # Left Terrace & Patio
    left_threshold_x = floor_cx - room_w/2 # X = -2.6
    make_box("OpenTerraceHeader", (0.18, room_d, 0.25), (left_threshold_x, floor_cy, room_h - 0.125), mat_dark_aluminum)
    make_box("OpenTerraceFloorTrack", (0.06, room_d, 0.015), (left_threshold_x, floor_cy, 0.005), mat_dark_aluminum)
    
    terrace_w = 2.6
    terrace_cx = left_threshold_x - terrace_w/2
    make_box("TerraceSlab", (terrace_w, room_d, 0.1), (terrace_cx, floor_cy, -0.05), mat_patio_stone)
    make_box("TerraceEdgeBorder", (0.08, room_d, 0.06), (left_threshold_x - terrace_w, floor_cy, -0.02), mat_dark_aluminum)

    # 4. Surroundings & Mountains
    create_panoramic_landscape()
    make_box("LushGardenLawn", (13.0, 24.0, 0.1), (-11.7, 0.0, -0.06), mat_lawn)
    
    # Stepping stones connecting terrace to court
    for i, py in enumerate([-1.8, -1.0, -0.2, 0.6, 1.4]):
        make_box(f"StepStone_{i}", (0.75, 0.5, 0.025), (left_threshold_x - terrace_w - 0.5 - (i%2)*0.15, py, 0.01), mat_patio_stone)

    # Organic lush pine trees framing the landscape
    tree_positions = [
        (-14.0, 6.5, 1.3),
        (-16.0, 3.5, 1.5),
        (-15.5, -4.5, 1.2),
        (-13.8, -7.5, 1.4),
        (-6.5, 6.8, 1.0),
        (-5.8, -6.5, 0.95),
        (-22.0, 9.5, 2.2),
        (-25.0, 0.0, 2.5),
        (-23.0, -8.0, 2.3)
    ]
    for idx, (tx, ty, tscale) in enumerate(tree_positions):
        make_lush_pine_tree(f"ScenicPineTree_{idx}", (tx, ty, 0.0), scale=tscale)

    # 5. Basketball Court directly visible outside the open wall
    court_x = -7.8
    court_y = 0.4
    court_w, court_l = 4.8, 5.8
    
    # Half-court flooring
    make_box("CourtBorder", (court_w + 0.6, court_l + 0.6, 0.03), (court_x, court_y, -0.025), mat_court_green)
    make_box("CourtSurface", (court_w, court_l, 0.035), (court_x, court_y, -0.015), mat_court_blue)
    make_box("CourtKeyArea", (1.8, 2.6, 0.038), (court_x, court_y + court_l/2 - 1.3, -0.01), mat_court_green)
    make_box("CourtFTLine", (1.8, 0.08, 0.04), (court_x, court_y + court_l/2 - 2.6, -0.005), mat_court_line)
    make_cylinder("CourtFTCircle", 0.85, 0.04, (court_x, court_y + court_l/2 - 2.6, -0.005), mat_court_line)

    # Complete Basketball Hoop System (Angled 32 degrees towards camera and patio for maximum visibility)
    hoop_rot = math.radians(32.0)
    hoop_sys_x = court_x - 0.3
    hoop_sys_y = court_y + court_l/2 - 0.2
    
    # Support Pole
    pole_h = 3.8
    pole_offset = 0.8
    pole_x = hoop_sys_x - pole_offset * math.sin(hoop_rot)
    pole_y = hoop_sys_y + pole_offset * math.cos(hoop_rot)
    
    make_box("HoopSupportPole", (0.18, 0.18, pole_h), (pole_x, pole_y, pole_h/2), mat_dark_aluminum, rot=(0, 0, hoop_rot))
    make_box("HoopBaseplate", (0.42, 0.42, 0.03), (pole_x, pole_y, 0.015), mat_dark_aluminum, rot=(0, 0, hoop_rot))
    make_box("HoopPolePad", (0.28, 0.28, 1.8), (pole_x, pole_y, 0.9), mat_dark_aluminum, rot=(0, 0, hoop_rot))
    make_box("HoopPadAccentTop", (0.285, 0.285, 0.05), (pole_x, pole_y, 1.7), mat_rim_orange, rot=(0, 0, hoop_rot))
    make_box("HoopPadAccentMid", (0.285, 0.285, 0.05), (pole_x, pole_y, 1.0), mat_rim_orange, rot=(0, 0, hoop_rot))

    # Overhang Arms
    arm_mid_x = (pole_x + hoop_sys_x) / 2.0
    arm_mid_y = (pole_y + hoop_sys_y) / 2.0
    make_box("HoopOverhangArm", (0.14, 0.85, 0.06), (arm_mid_x, arm_mid_y, 3.0), mat_dark_aluminum, rot=(0, 0, hoop_rot))

    # Regulation Glass Backboard facing towards room & camera
    bb_x = hoop_sys_x
    bb_y = hoop_sys_y
    bb_z = 3.25
    make_box("BackboardGlass", (1.83, 0.03, 1.07), (bb_x, bb_y, bb_z), mat_glass, rot=(0, 0, hoop_rot))
    make_box("BackboardFrameOuter", (1.87, 0.05, 1.11), (bb_x, bb_y, bb_z), mat_dark_aluminum, rot=(0, 0, hoop_rot))
    make_box("BackboardCrashPadBottom", (1.87, 0.08, 0.08), (bb_x, bb_y, bb_z - 0.54), mat_dark_aluminum, rot=(0, 0, hoop_rot))

    # Inner Target Rectangle
    target_w, target_h = 0.61, 0.46
    target_z = 3.12
    norm_x = math.sin(hoop_rot) * 0.025
    norm_y = -math.cos(hoop_rot) * 0.025
    make_box("TargetLineTop", (target_w, 0.02, 0.04), (bb_x + norm_x, bb_y + norm_y, target_z + target_h/2), mat_rim_orange, rot=(0, 0, hoop_rot))
    make_box("TargetLineBottom", (target_w, 0.02, 0.04), (bb_x + norm_x, bb_y + norm_y, target_z - target_h/2), mat_rim_orange, rot=(0, 0, hoop_rot))
    make_box("TargetLineLeft", (0.04, 0.02, target_h), (bb_x + norm_x - (target_w/2)*math.cos(hoop_rot), bb_y + norm_y - (target_w/2)*math.sin(hoop_rot), target_z), mat_rim_orange, rot=(0, 0, hoop_rot))
    make_box("TargetLineRight", (0.04, 0.02, target_h), (bb_x + norm_x + (target_w/2)*math.cos(hoop_rot), bb_y + norm_y + (target_w/2)*math.sin(hoop_rot), target_z), mat_rim_orange, rot=(0, 0, hoop_rot))

    # User Hoop & Net from Basketball Hoop.blend
    hoop_objs = append_objects("Basketball Hoop.blend", ["Hoop"])
    if hoop_objs:
        hoop = hoop_objs[0]
        hoop.name = "BasketballRimAndNet"
        hoop.scale = (0.28, 0.28, 0.28)
        rim_offset = 0.42
        hoop.location = (bb_x + rim_offset * math.sin(hoop_rot), bb_y - rim_offset * math.cos(hoop_rot), 2.95)
        hoop.rotation_euler = (0, 0, hoop_rot)

    # User Basketball
    ball_objs = append_objects("low-poly basketball ball.blend", ["BasketBall_Low"])
    if ball_objs:
        ball = ball_objs[0]
        ball.name = "InteractiveBasketball"
        ball.location = (court_x + 0.4, court_y - 0.7, 0.13)
        ball.scale = (1.0, 1.0, 1.0)

    # 6. Luxury Master Bed (Proper Queen Bed Orientation: Sedha / Headboard at Back Wall)
    bed_objs = append_objects("bed.blend", ["Plane.001"])
    if bed_objs:
        bed = bed_objs[0]
        bed.name = "MasterBed"
        bed.scale = (0.92, 0.92, 0.92)
        bed.rotation_euler = (0.0, math.radians(-53.05), math.radians(-90.0))
        bpy.context.view_layer.update()
        
        # Ground lowest vertex at Z = 0.0
        verts_world = [bed.matrix_world @ v.co for v in bed.data.vertices]
        min_z = min(v.z for v in verts_world)
        
        # Position bed with headboard against back wall and pillows elevated
        bed.location = (1.80, 0.70, -min_z)

    # Nightstand & Designer Lamp
    make_box("Nightstand", (0.5, 0.5, 0.54), (2.80, 1.85, 0.27), mat_wall_slat)
    make_box("NightstandDrawer", (0.51, 0.46, 0.2), (2.80, 1.83, 0.35), mat_dark_aluminum)
    make_box("DrawerBrassPull", (0.02, 0.14, 0.02), (2.80, 1.59, 0.35), mat_gold_accent)
    make_cylinder("LampBase", 0.09, 0.02, (2.80, 1.85, 0.55), mat_gold_accent)
    make_cylinder("LampStem", 0.012, 0.32, (2.80, 1.85, 0.71), mat_gold_accent)
    make_cone("LampFabricShade", 0.16, 0.22, (2.80, 1.85, 0.92), mat_warm_led)
    
    bed_light = bpy.data.lights.new(name="BedsideWarmLight", type='POINT')
    bed_light.energy = 22.0
    bed_light.color = (1.0, 0.88, 0.68)
    bed_light_obj = bpy.data.objects.new(name="BedsideWarmLight", object_data=bed_light)
    bpy.context.collection.objects.link(bed_light_obj)
    bed_light_obj.location = (2.80, 1.85, 0.90)

    # 7. Modern Battlestation Desk & Peripherals
    desk_x = -0.6
    desk_y = 1.85
    desk_w, desk_d, desk_h = 2.0, 0.85, 0.75
    
    make_box("BattlestationDeskTop", (desk_w, desk_d, 0.038), (desk_x, desk_y, desk_h), mat_wall_slat)
    make_box("DeskAmbientRGB", (desk_w - 0.1, 0.02, 0.015), (desk_x, desk_y + desk_d/2 - 0.02, desk_h - 0.02), mat_rgb_cyan)
    
    for side in [-1, 1]:
        lx = desk_x + side * (desk_w / 2 - 0.15)
        make_box(f"DeskLegPillar_{side}", (0.08, 0.08, desk_h - 0.08), (lx, desk_y, (desk_h - 0.08)/2), mat_dark_aluminum)
        make_box(f"DeskLegFoot_{side}", (0.09, desk_d - 0.1, 0.04), (lx, desk_y, 0.02), mat_dark_aluminum)
    make_box("DeskCableChannel", (desk_w - 0.4, 0.06, 0.08), (desk_x, desk_y + 0.2, desk_h - 0.18), mat_dark_aluminum)

    # Stitched Desk Mat
    make_box("ProDeskMat", (0.92, 0.42, 0.005), (desk_x - 0.1, desk_y - 0.08, desk_h + 0.0215), mat_dark_aluminum)

    # 49" Curved OLED Ultrawide Monitor
    mon_w, mon_h = 1.15, 0.38
    mon_z = desk_h + 0.25
    make_box("MonArmBase", (0.16, 0.16, 0.02), (desk_x, desk_y + 0.30, desk_h + 0.025), mat_dark_aluminum)
    make_cylinder("MonArmPillar", 0.03, 0.38, (desk_x, desk_y + 0.30, desk_h + 0.20), mat_dark_aluminum)
    make_box("MonArmElbow", (0.08, 0.20, 0.05), (desk_x, desk_y + 0.22, mon_z), mat_dark_aluminum)
    make_box("MonChassis", (mon_w, 0.03, mon_h), (desk_x, desk_y + 0.12, mon_z), mat_dark_aluminum)
    make_box("MonScreenOLED", (mon_w - 0.02, 0.004, mon_h - 0.02), (desk_x, desk_y + 0.102, mon_z), mat_screen_wallpaper)
    make_box("MonRearAmbientGlow", (mon_w * 0.85, 0.015, 0.02), (desk_x, desk_y + 0.14, mon_z), mat_rgb_cyan)

    # Custom Mechanical Keyboard
    kb_x = desk_x - 0.12
    kb_y = desk_y - 0.12
    kb_z = desk_h + 0.022
    make_box("CustomKB_Case", (0.36, 0.14, 0.018), (kb_x, kb_y, kb_z + 0.009), mat_dark_aluminum)
    make_box("CustomKB_BrassWeight", (0.32, 0.10, 0.003), (kb_x, kb_y, kb_z + 0.001), mat_gold_accent)
    for r_idx, (ry, rmat) in enumerate([
        (0.045, mat_rgb_cyan),
        (0.025, mat_wall_plaster),
        (0.005, mat_wall_plaster),
        (-0.015, mat_wall_plaster),
        (-0.035, mat_wall_plaster)
    ]):
        make_box(f"KeycapCluster_{r_idx}", (0.34, 0.017, 0.008), (kb_x, kb_y + ry, kb_z + 0.023), rmat)
    make_box("KeycapSpacebar", (0.14, 0.017, 0.008), (kb_x, kb_y - 0.052, kb_z + 0.023), mat_rgb_magenta)

    # Wireless Gaming Mouse
    mx = desk_x + 0.22
    my = desk_y - 0.12
    mz = desk_h + 0.022
    make_box("ProMouseChassis", (0.072, 0.124, 0.032), (mx, my, mz + 0.016), mat_dark_aluminum)
    make_box("ProMouseLClick", (0.032, 0.045, 0.005), (mx - 0.017, my - 0.035, mz + 0.034), mat_wall_slat)
    make_box("ProMouseRClick", (0.032, 0.045, 0.005), (mx + 0.017, my - 0.035, mz + 0.034), mat_wall_slat)
    make_cylinder("ProMouseWheel", 0.01, 0.01, (mx, my - 0.028, mz + 0.035), mat_rgb_cyan, rot=(0, math.radians(90), 0))

    # Studio Monitor Speakers
    for s, sx in [("L", desk_x - 0.65), ("R", desk_x + 0.65)]:
        make_box(f"StudioSpeaker_{s}", (0.13, 0.16, 0.24), (sx, desk_y + 0.12, desk_h + 0.14), mat_dark_aluminum)
        make_cylinder(f"SpeakerKevlarWoofer_{s}", 0.048, 0.01, (sx, desk_y + 0.038, desk_h + 0.11), mat_gold_accent, rot=(math.radians(90), 0, 0))

    # User PC Case (Cleanly imported from pc.blend)
    pc_parts = append_objects("pc_case/pc.blend", [])
    pc_root = bpy.data.objects.new("UserPCCase_Root", None)
    pc_root.location = (desk_x + desk_w/2 - 0.22, desk_y + 0.02, desk_h + 0.02)
    bpy.context.collection.objects.link(pc_root)
    
    if pc_parts:
        for p in list(pc_parts):
            if p.name.startswith("Plane") and (not hasattr(p.data, 'materials') or len(p.data.materials) == 0):
                bpy.data.objects.remove(p, do_unlink=True)
            elif p.type == 'LIGHT':
                bpy.data.objects.remove(p, do_unlink=True)
            else:
                p.parent = pc_root
                p.scale = (p.scale.x * 0.11, p.scale.y * 0.11, p.scale.z * 0.11)
                p.location = (p.location.x * 0.11, p.location.y * 0.11, p.location.z * 0.11)

    # 8. User Gaming Chair (All components parented, grounded at Z=0, realistic 1.25m height)
    chair_names = ['Plane', 'Plane.005', 'Cylinder', 'Cube', 'Cube.001', 'Plane.002', 'Plane.004']
    imported_chair = append_objects("gaming chair.blend", chair_names)
    
    chair_root = bpy.data.objects.new("Gaming_Chair_Interactive", None)
    chair_root.location = (desk_x, desk_y - 0.68, 0.0)
    bpy.context.collection.objects.link(chair_root)
    
    if imported_chair:
        chair_scale = 0.3262
        for obj in imported_chair:
            obj.parent = chair_root
            obj.location = (
                (obj.location.x + 0.12) * chair_scale,
                (obj.location.y + 4.5) * chair_scale,
                (obj.location.z - 0.13) * chair_scale
            )
            obj.scale = (obj.scale.x * chair_scale, obj.scale.y * chair_scale, obj.scale.z * chair_scale)

    # Chair Animation (Smooth Swivel and subtle roll over 120 frames)
    scene.frame_start = 1
    scene.frame_end = 120
    
    scene.frame_set(1)
    chair_root.location = (desk_x, desk_y - 0.68, 0.0)
    chair_root.rotation_euler = (0, 0, math.radians(15.0))
    chair_root.keyframe_insert(data_path="location", index=-1)
    chair_root.keyframe_insert(data_path="rotation_euler", index=-1)

    scene.frame_set(45)
    chair_root.location = (desk_x - 0.05, desk_y - 0.72, 0.0)
    chair_root.rotation_euler = (0, 0, math.radians(-12.0))
    chair_root.keyframe_insert(data_path="location", index=-1)
    chair_root.keyframe_insert(data_path="rotation_euler", index=-1)

    scene.frame_set(85)
    chair_root.location = (desk_x + 0.04, desk_y - 0.70, 0.0)
    chair_root.rotation_euler = (0, 0, math.radians(22.0))
    chair_root.keyframe_insert(data_path="location", index=-1)
    chair_root.keyframe_insert(data_path="rotation_euler", index=-1)

    scene.frame_set(120)
    chair_root.location = (desk_x, desk_y - 0.68, 0.0)
    chair_root.rotation_euler = (0, 0, math.radians(15.0))
    chair_root.keyframe_insert(data_path="location", index=-1)
    chair_root.keyframe_insert(data_path="rotation_euler", index=-1)
    
    scene.frame_set(25)

    # 9. Natural Sunlight with Soft Angle (No harsh slat shadow stripes!)
    sun = bpy.data.lights.new(name="GoldenSun", type='SUN')
    sun.energy = 2.0
    sun.color = (1.0, 0.95, 0.88)
    sun.angle = math.radians(24.0)
    sun_obj = bpy.data.objects.new(name="GoldenSun", object_data=sun)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.location = (-12.0, -8.0, 14.0)
    sun_obj.rotation_euler = (math.radians(38), math.radians(-25), math.radians(55))

    fill = bpy.data.lights.new(name="InteriorFillArea", type='AREA')
    fill.energy = 16.0
    fill.size = 4.2
    fill.color = (0.96, 0.97, 1.0)
    fill_obj = bpy.data.objects.new(name="InteriorFillArea", object_data=fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (floor_cx, floor_cy, room_h - 0.1)

    # 10. Hero 4K Architectural Camera (Wide 15.5mm lens framing garden, court, desk & bed)
    cam_data = bpy.data.cameras.new(name="Hero4KCamera")
    cam_data.lens = 15.5
    cam_obj = bpy.data.objects.new(name="Hero4KCamera", object_data=cam_data)
    bpy.context.collection.objects.link(cam_obj)
    
    cam_obj.location = (0.50, -2.85, 1.55)
    target = mathutils.Vector((-0.65, 0.9, 0.85))
    direction = target - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    bpy.context.scene.camera = cam_obj

    print("Master 4K Architectural Scene V8 built flawlessly!")

build_master_scene()
