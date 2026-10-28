import bpy
import bmesh
import math
import mathutils
import os
import random
import numpy as np

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
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)

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

def add_box_uvs(obj, projection='Z'):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv_layer = bm.loops.layers.uv.verify()
    
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    dx = max(max_x - min_x, 1e-5)
    dy = max(max_y - min_y, 1e-5)
    dz = max(max_z - min_z, 1e-5)
    
    for face in bm.faces:
        for loop in face.loops:
            v = loop.vert.co
            if projection == 'Z':
                u = (v.x - min_x) / dx
                w = (v.y - min_y) / dy
            elif projection == 'Y':
                u = (v.x - min_x) / dx
                w = (v.z - min_z) / dz
            elif projection == 'X':
                u = (v.y - min_y) / dy
                w = (v.z - min_z) / dz
            loop[uv_layer].uv = (u, w)
            
    bm.to_mesh(mesh)
    bm.free()

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
        bsdf.inputs['Transmission Weight'].default_value = 0.96
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
    mat.diffuse_color = (0.22, 0.12, 0.06, 1.0)
    
    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.28
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.55
    
    coord = nodes.new(type="ShaderNodeTexCoord")
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.inputs['Scale'].default_value[0] = 1.2
    mapping.inputs['Scale'].default_value[1] = 6.0
    
    wave = nodes.new(type="ShaderNodeTexWave")
    wave.inputs['Scale'].default_value = 0.8
    wave.inputs['Distortion'].default_value = 1.2
    
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[0].color = (0.14, 0.07, 0.035, 1.0) # Deep dark walnut
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (0.28, 0.15, 0.08, 1.0) # Rich warm cognac wood
    
    bump = nodes.new(type="ShaderNodeBump")
    bump.inputs['Strength'].default_value = 0.15
    
    links.new(coord.outputs['Object'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], wave.inputs['Vector'])
    links.new(wave.outputs['Color'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(wave.outputs['Color'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# ----------------- Screen Texture Generator -----------------
def generate_hd_screen_texture():
    W, H = 1920, 800
    arr = np.zeros((H, W, 4), dtype=np.float32)
    arr[:, :, 3] = 1.0
    
    # 1. Dark futuristic background with gradient
    y_coords, x_coords = np.ogrid[:H, :W]
    grad_bg = (x_coords / W) * 0.03 + (y_coords / H) * 0.02
    arr[:, :, 0] = 0.02 + grad_bg * 0.2
    arr[:, :, 1] = 0.03 + grad_bg * 0.5
    arr[:, :, 2] = 0.06 + grad_bg * 0.9
    
    # 2. Top Menu Bar (H - 35 to H)
    arr[H-35:H, :, 0] = 0.08
    arr[H-35:H, :, 1] = 0.09
    arr[H-35:H, :, 2] = 0.12
    arr[H-24:H-12, 20:32, :] = [0.9, 0.9, 0.95, 1.0]
    for mx in [50, 90, 130, 175, 220, 275]:
        arr[H-22:H-14, mx:mx+30, :] = [0.65, 0.70, 0.80, 1.0]
    arr[H-22:H-14, W-140:W-60, :] = [0.85, 0.90, 0.95, 1.0]
    arr[H-22:H-14, W-50:W-30, :] = [0.2, 0.85, 0.35, 1.0]
    
    # 3. Main Window: Modern VS Code IDE (left: 40 to 1280, bottom: 40 to H-45)
    win_l, win_r = 40, 1280
    win_b, win_t = 40, H - 45
    arr[win_b:win_t, win_l:win_r, 0] = 0.04
    arr[win_b:win_t, win_l:win_r, 1] = 0.05
    arr[win_b:win_t, win_l:win_r, 2] = 0.07
    
    arr[win_t-32:win_t, win_l:win_r, :] = [0.07, 0.08, 0.11, 1.0]
    arr[win_t-22:win_t-10, win_l+14:win_l+26, :] = [0.95, 0.30, 0.30, 1.0]
    arr[win_t-22:win_t-10, win_l+32:win_l+44, :] = [0.95, 0.75, 0.20, 1.0]
    arr[win_t-22:win_t-10, win_l+50:win_l+62, :] = [0.25, 0.85, 0.35, 1.0]
    
    arr[win_b:win_t-32, win_l:win_l+48, :] = [0.05, 0.06, 0.08, 1.0]
    for iy in range(5):
        arr[win_t-80-iy*45:win_t-60-iy*45, win_l+14:win_l+34, :] = [0.45, 0.55, 0.70, 1.0]
        
    arr[win_b:win_t-32, win_l+48:win_l+240, :] = [0.06, 0.07, 0.09, 1.0]
    for fy in range(12):
        y_pos = win_t - 70 - fy * 24
        if y_pos > win_b + 40:
            arr[y_pos:y_pos+10, win_l+65:win_l+75, :] = [0.2, 0.65, 0.9, 1.0]
            arr[y_pos:y_pos+8, win_l+82:win_l+160 + (fy*7)%50, :] = [0.65, 0.72, 0.82, 1.0]
            
    ed_l = win_l + 240
    arr[win_t-64:win_t-32, ed_l:win_r, :] = [0.055, 0.065, 0.085, 1.0]
    arr[win_t-64:win_t-32, ed_l:ed_l+180, :] = [0.08, 0.10, 0.14, 1.0]
    arr[win_t-34:win_t-32, ed_l:ed_l+180, :] = [0.0, 0.85, 1.0, 1.0]
    arr[win_t-52:win_t-44, ed_l+20:ed_l+130, :] = [0.9, 0.95, 1.0, 1.0]
    
    colors = [
        [0.85, 0.25, 0.45, 1.0],
        [0.20, 0.80, 0.95, 1.0],
        [0.95, 0.75, 0.30, 1.0],
        [0.40, 0.85, 0.40, 1.0],
        [0.60, 0.75, 0.95, 1.0],
        [0.90, 0.90, 0.95, 1.0]
    ]
    np.random.seed(101)
    for line in range(18):
        ly = win_t - 80 - line * 20
        if ly > win_b + 160:
            arr[ly:ly+10, ed_l+15:ed_l+30, :] = [0.35, 0.40, 0.48, 1.0]
            cur_x = ed_l + 45 + (line % 4) * 20
            num_tokens = np.random.randint(3, 7)
            for _ in range(num_tokens):
                t_len = np.random.randint(25, 85)
                c = colors[np.random.randint(0, len(colors))]
                if cur_x + t_len < win_r - 20:
                    arr[ly:ly+9, cur_x:cur_x+t_len, :] = c
                    cur_x += t_len + np.random.randint(8, 18)
                    
    term_h = 135
    arr[win_b:win_b+term_h, ed_l:win_r, :] = [0.03, 0.038, 0.05, 1.0]
    arr[win_b+term_h-2:win_b+term_h, ed_l:win_r, :] = [0.15, 0.18, 0.25, 1.0]
    arr[win_b+100:win_b+110, ed_l+20:ed_l+140, :] = [0.2, 0.88, 0.4, 1.0]
    arr[win_b+100:win_b+110, ed_l+150:ed_l+260, :] = [0.0, 0.85, 1.0, 1.0]
    arr[win_b+75:win_b+85, ed_l+20:ed_l+380, :] = [0.8, 0.85, 0.9, 1.0]
    arr[win_b+50:win_b+60, ed_l+20:ed_l+320, :] = [0.95, 0.85, 0.2, 1.0]
    arr[win_b+25:win_b+35, ed_l+20:ed_l+40, :] = [0.0, 0.85, 1.0, 1.0]
    
    # 4. Right Side Panel: Music Player & System Dashboard
    dash_l, dash_r = 1310, W - 40
    arr[H-360:H-50, dash_l:dash_r, 0] = 0.06
    arr[H-360:H-50, dash_l:dash_r, 1] = 0.07
    arr[H-360:H-50, dash_l:dash_r, 2] = 0.11
    arr[H-360:H-358, dash_l:dash_r, :] = [0.2, 0.3, 0.45, 0.8]
    arr[H-52:H-50, dash_l:dash_r, :] = [0.2, 0.3, 0.45, 0.8]
    arr[H-240:H-90, dash_l+25:dash_l+175, 0] = 0.85
    arr[H-240:H-90, dash_l+25:dash_l+175, 1] = 0.15
    arr[H-240:H-90, dash_l+25:dash_l+175, 2] = 0.55
    arr[H-130:H-118, dash_l+195:dash_r-30, :] = [0.95, 0.95, 1.0, 1.0]
    arr[H-160:H-150, dash_l+195:dash_r-80, :] = [0.55, 0.65, 0.80, 1.0]
    arr[H-280:H-272, dash_l+25:dash_r-25, :] = [0.15, 0.18, 0.25, 1.0]
    arr[H-280:H-272, dash_l+25:dash_l+280, :] = [0.0, 0.85, 1.0, 1.0]
    for bx in [dash_l+150, dash_l+200, dash_l+250]:
        arr[H-330:H-308, bx:bx+22, :] = [0.85, 0.90, 0.98, 1.0]
        
    arr[40:H-385, dash_l:dash_r, 0] = 0.05
    arr[40:H-385, dash_l:dash_r, 1] = 0.06
    arr[40:H-385, dash_l:dash_r, 2] = 0.09
    for gi, (gname, gfill, gcolor) in enumerate([
        ("FPS", 0.92, [0.2, 0.85, 0.35, 1.0]),
        ("GPU", 0.68, [0.0, 0.85, 1.0, 1.0]),
        ("VRAM", 0.54, [0.95, 0.75, 0.20, 1.0]),
        ("TEMP", 0.42, [0.95, 0.35, 0.35, 1.0])
    ]):
        by = H - 425 - gi * 60
        arr[by:by+12, dash_l+30:dash_l+110, :] = [0.65, 0.72, 0.82, 1.0]
        arr[by-25:by-15, dash_l+30:dash_r-30, :] = [0.12, 0.15, 0.20, 1.0]
        fill_w = int((dash_r - dash_l - 60) * gfill)
        arr[by-25:by-15, dash_l+30:dash_l+30+fill_w, :] = gcolor
        
    img = bpy.data.images.get("HD_ScreenDisplay_Pro")
    if not img:
        img = bpy.data.images.new("HD_ScreenDisplay_Pro", W, H)
    img.pixels.foreach_set(arr.flatten())
    img.update()
    
    mat = bpy.data.materials.new(name="PhotorealOLEDDisplay")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.05
    
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    if 'Emission Color' in bsdf.inputs:
        links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 2.4
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# ----------------- Basketball Court Texture Generator -----------------
def generate_hd_court_texture():
    W, H = 2048, 2048
    arr = np.zeros((H, W, 4), dtype=np.float32)
    arr[:, :, 3] = 1.0
    
    # Outer apron: Forest Athletic Green
    arr[:, :, 0] = 0.08
    arr[:, :, 1] = 0.25
    arr[:, :, 2] = 0.16
    
    # Inner court: Cobalt Blue
    border_px = 120
    arr[border_px:H-border_px, border_px:W-border_px, 0] = 0.06
    arr[border_px:H-border_px, border_px:W-border_px, 1] = 0.22
    arr[border_px:H-border_px, border_px:W-border_px, 2] = 0.58
    
    # Key lane: Emerald green
    key_l = int(W * 0.35)
    key_r = int(W * 0.65)
    key_b = int(H * 0.48)
    key_t = H - border_px
    arr[key_b:key_t, key_l:key_r, 0] = 0.08
    arr[key_b:key_t, key_l:key_r, 1] = 0.30
    arr[key_b:key_t, key_l:key_r, 2] = 0.18
    
    y_idx, x_idx = np.ogrid[:H, :W]
    line_color = np.array([0.96, 0.97, 0.98, 1.0], dtype=np.float32)
    line_thickness = 9
    
    mask_baseline = (y_idx >= (key_t - line_thickness)) & (y_idx <= key_t) & (x_idx >= border_px) & (x_idx <= W - border_px)
    mask_halfline = (y_idx >= border_px) & (y_idx <= (border_px + line_thickness)) & (x_idx >= border_px) & (x_idx <= W - border_px)
    mask_left_side = (x_idx >= border_px) & (x_idx <= (border_px + line_thickness)) & (y_idx >= border_px) & (y_idx <= H - border_px)
    mask_right_side = (x_idx >= (W - border_px - line_thickness)) & (x_idx <= (W - border_px)) & (y_idx >= border_px) & (y_idx <= H - border_px)
    arr[mask_baseline | mask_halfline | mask_left_side | mask_right_side] = line_color
    
    mask_key_left = (x_idx >= key_l) & (x_idx <= key_l + line_thickness) & (y_idx >= key_b) & (y_idx <= key_t)
    mask_key_right = (x_idx >= key_r - line_thickness) & (x_idx <= key_r) & (y_idx >= key_b) & (y_idx <= key_t)
    mask_ft_line = (y_idx >= key_b) & (y_idx <= key_b + line_thickness) & (x_idx >= key_l) & (x_idx <= key_r)
    arr[mask_key_left | mask_key_right | mask_ft_line] = line_color
    
    cx = W / 2.0
    cy_ft = key_b
    r_ft = (key_r - key_l) / 2.0
    dist_ft = np.sqrt((x_idx - cx)**2 + (y_idx - cy_ft)**2)
    mask_ft_circle = (np.abs(dist_ft - r_ft) <= line_thickness / 2.0) & (y_idx <= key_b + 20)
    angle_ft = np.arctan2(y_idx - cy_ft, x_idx - cx)
    dash_mask = (np.sin(angle_ft * 12) > 0)
    mask_ft_dashed = (np.abs(dist_ft - r_ft) <= line_thickness / 2.0) & (y_idx > key_b + 20) & dash_mask
    arr[mask_ft_circle | mask_ft_dashed] = line_color
    
    hoop_cy = H - border_px - int(H * 0.08)
    corner_offset_x = int(W * 0.13)
    c_left = border_px + corner_offset_x
    c_right = W - border_px - corner_offset_x
    r_3pt = cx - c_left
    
    dist_hoop = np.sqrt((x_idx - cx)**2 + (y_idx - hoop_cy)**2)
    mask_3pt_arc = (np.abs(dist_hoop - r_3pt) <= line_thickness / 2.0) & (y_idx <= hoop_cy) & (x_idx >= c_left) & (x_idx <= c_right)
    mask_3pt_str_l = (x_idx >= c_left) & (x_idx <= c_left + line_thickness) & (y_idx >= hoop_cy) & (y_idx <= key_t)
    mask_3pt_str_r = (x_idx >= c_right - line_thickness) & (x_idx <= c_right) & (y_idx >= hoop_cy) & (y_idx <= key_t)
    arr[mask_3pt_arc | mask_3pt_str_l | mask_3pt_str_r] = line_color
    
    r_ra = 120.0
    mask_ra = (np.abs(dist_hoop - r_ra) <= line_thickness / 2.0) & (y_idx <= hoop_cy)
    arr[mask_ra] = line_color
    
    r_center = 320.0
    dist_center = np.sqrt((x_idx - cx)**2 + (y_idx - border_px)**2)
    mask_center = (np.abs(dist_center - r_center) <= line_thickness / 2.0) & (y_idx >= border_px)
    arr[mask_center] = line_color
    
    np.random.seed(42)
    noise = (np.random.rand(H, W) - 0.5) * 0.035
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] + noise, 0.0, 1.0)
        
    img = bpy.data.images.get("HD_BasketballCourt_Pro")
    if not img:
        img = bpy.data.images.new("HD_BasketballCourt_Pro", W, H)
    img.pixels.foreach_set(arr.flatten())
    img.update()
    
    mat = bpy.data.materials.new(name="PhotorealBasketballCourtMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.55
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.35
        
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# ----------------- Drawing Board Artwork Texture Generator -----------------
def generate_hd_canvas_texture():
    W, H = 1024, 1024
    arr = np.zeros((H, W, 4), dtype=np.float32)
    arr[:, :, 3] = 1.0
    
    arr[:, :, 0] = 0.95
    arr[:, :, 1] = 0.93
    arr[:, :, 2] = 0.89
    
    np.random.seed(99)
    grain = (np.random.rand(H, W) - 0.5) * 0.03
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] + grain, 0.0, 1.0)
        
    grid_spacing = 40
    grid_color = np.array([0.78, 0.83, 0.90, 1.0], dtype=np.float32)
    for x in range(60, W - 60, grid_spacing):
        arr[60:H-60, x:x+1] = grid_color
    for y in range(60, H - 60, grid_spacing):
        arr[y:y+1, 60:W-60] = grid_color
        
    sketch_col = np.array([0.22, 0.24, 0.28, 1.0], dtype=np.float32)
    arr[60:64, 60:W-60] = sketch_col
    arr[H-64:H-60, 60:W-60] = sketch_col
    arr[60:H-60, 60:64] = sketch_col
    arr[60:H-60, W-64:W-60] = sketch_col
    
    for ox, oy, sz_x, sz_y in [
        (200, 320, 620, 480),
        (260, 360, 240, 180),
        (560, 360, 220, 280),
        (420, 640, 180, 120),
    ]:
        arr[oy:oy+sz_y:2, ox:ox+sz_x] = sketch_col
        arr[oy:oy+sz_y, ox:ox+3] = sketch_col
        arr[oy:oy+sz_y, ox+sz_x-3:ox+sz_x] = sketch_col
        arr[oy:oy+3, ox:ox+sz_x] = sketch_col
        arr[oy+sz_y-3:oy+sz_y, ox:ox+sz_x] = sketch_col
        
    swatches = [
        (80, 100, [0.15, 0.45, 0.85, 1.0]),
        (160, 100, [0.95, 0.35, 0.20, 1.0]),
        (240, 100, [0.20, 0.75, 0.45, 1.0]),
        (320, 100, [0.95, 0.80, 0.20, 1.0]),
        (400, 100, [0.75, 0.25, 0.70, 1.0]),
    ]
    for sx, sy, scol in swatches:
        arr[sy:sy+35, sx:sx+60] = np.array(scol, dtype=np.float32)
        
    arr[90:94, W-380:W-80] = sketch_col
    for tx in [W-360, W-300, W-240, W-180, W-120]:
        arr[105:115, tx:tx+45] = [0.35, 0.38, 0.42, 1.0]
        
    img = bpy.data.images.get("HD_DrawingBoard_Sketch")
    if not img:
        img = bpy.data.images.new("HD_DrawingBoard_Sketch", W, H)
    img.pixels.foreach_set(arr.flatten())
    img.update()
    
    mat = bpy.data.materials.new(name="PhotorealDrawingCanvasMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.85
    
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
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

# ----------------- User 3D Trees from trees_3d.zip -----------------
def import_and_setup_user_trees(tree_instances):
    obj_path = os.path.join(base_dir, "trees_3d/trees9.obj")
    if not os.path.exists(obj_path):
        print(f"User tree model not found: {obj_path}")
        return []
        
    bpy.ops.wm.obj_import(filepath=obj_path)
    imported = {o.name: o for o in bpy.context.selected_objects}
    
    templates = {}
    for name, obj in imported.items():
        verts = [v.co for v in obj.data.vertices]
        min_x = min(v.x for v in verts)
        max_x = max(v.x for v in verts)
        min_y = min(v.y for v in verts)
        max_y = max(v.y for v in verts)
        min_z = min(v.z for v in verts)
        max_z = max(v.z for v in verts)
        
        # In OBJ Y is height: transform so height -> Blender Z, base at Z=0
        for v in obj.data.vertices:
            ox, oy, oz = v.co.x, v.co.y, v.co.z
            v.co.x = ox - (min_x + max_x) / 2.0
            v.co.y = -(oz - (min_z + max_z) / 2.0)
            v.co.z = oy - min_y
            
        obj.data.update()
        templates[name] = obj
        bpy.context.collection.objects.unlink(obj)
        
    created_trees = []
    for idx, (tmpl_name, loc, scale, rot_z) in enumerate(tree_instances):
        if tmpl_name in templates:
            tmpl = templates[tmpl_name]
            tree_obj = bpy.data.objects.new(f"UserTree_{idx}_{tmpl_name}", tmpl.data)
            tree_obj.location = mathutils.Vector(loc)
            tree_obj.scale = (scale, scale, scale)
            tree_obj.rotation_euler = (0, 0, math.radians(rot_z))
            bpy.context.collection.objects.link(tree_obj)
            created_trees.append(tree_obj)
            
    for obj in templates.values():
        bpy.data.objects.remove(obj, do_unlink=True)
        
    print(f"Successfully placed {len(created_trees)} user 3D trees from trees_3d.zip!")
    return created_trees

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

# ----------------- Master 4K Scene Builder V9 -----------------
def build_master_scene():
    clean_entire_blend_file()
    scene = bpy.context.scene
    
    # 1. Physical Atmosphere & Color Grading
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = -0.15
    
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
    w_sky.sun_elevation = math.radians(32.0)
    w_sky.sun_rotation = math.radians(115.0)
    w_bg.inputs['Strength'].default_value = 0.95
    wlinks.new(w_sky.outputs['Color'], w_bg.inputs['Color'])
    wlinks.new(w_bg.outputs['Background'], w_out.inputs['Surface'])

    # 2. Materials
    mat_floor = create_luxury_walnut_floor()
    mat_wall_slat = create_pbr_mat("AcousticWoodSlat", (0.12, 0.07, 0.04, 1.0), roughness=0.35)
    mat_wall_plaster = create_pbr_mat("DesignerPlaster", (0.92, 0.92, 0.90, 1.0), roughness=0.85)
    mat_ceiling = create_pbr_mat("CeilingMat", (0.96, 0.96, 0.96, 1.0), roughness=0.8)
    mat_glass = create_pbr_mat("ArchitecturalGlass", (0.95, 0.98, 1.0, 0.1), roughness=0.01, is_glass=True)
    mat_dark_aluminum = create_pbr_mat("AnodizedBlackAluminum", (0.04, 0.04, 0.05, 1.0), roughness=0.25, metallic=0.92)
    mat_gold_accent = create_pbr_mat("BrushedChampagneGold", (0.92, 0.75, 0.35, 1.0), roughness=0.22, metallic=0.96)
    
    mat_warm_led = create_pbr_mat("WarmCoveLED", (1.0, 0.88, 0.72, 1.0), emission=(1.0, 0.88, 0.72, 1.0), emission_strength=4.5)
    mat_rgb_cyan = create_pbr_mat("RGBCyanGlow", (0.0, 0.9, 1.0, 1.0), emission=(0.0, 0.88, 1.0, 1.0), emission_strength=6.0)
    mat_rgb_magenta = create_pbr_mat("RGBMagentaGlow", (1.0, 0.05, 0.55, 1.0), emission=(1.0, 0.05, 0.55, 1.0), emission_strength=5.5)
    
    mat_lawn = create_pbr_mat("LushGardenLawn", (0.13, 0.36, 0.11, 1.0), roughness=0.88)
    mat_patio_stone = create_pbr_mat("TravertinePatio", (0.82, 0.79, 0.75, 1.0), roughness=0.45)
    mat_rim_orange = create_pbr_mat("RimOrangePro", (0.95, 0.28, 0.04, 1.0), roughness=0.3, metallic=0.2)
    mat_easel_wood = create_pbr_mat("BeechwoodStudioEasel", (0.58, 0.40, 0.24, 1.0), roughness=0.45)

    # Generated Photoreal Textures
    mat_screen_wallpaper = generate_hd_screen_texture()
    mat_court_surface = generate_hd_court_texture()
    mat_drawing_canvas = generate_hd_canvas_texture()

    # 3. Room Architecture (X from -2.6 to 3.2, Y from -2.4 to 2.4, height 3.2m)
    room_w, room_d, room_h = 5.8, 4.8, 3.2
    floor_cx = 0.3
    floor_cy = 0.0
    make_box("RoomFloor", (room_w, room_d, 0.1), (floor_cx, floor_cy, -0.05), mat_floor)
    
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

    # ----------------- 4. "Roshan" Name Board on Exterior Roof / Header -----------------
    # Illuminated architectural billboard plaque above open terrace header beam
    sign_rot_z = math.radians(-25.0) # Angled gracefully towards camera for maximum readability!
    sign_cx = left_threshold_x + 0.2
    sign_cy = -0.3
    sign_cz = room_h + 0.38
    
    # Backing Plaque with beveled styling
    make_box("RoshanSign_BackingPlaque", (2.4, 0.06, 0.65), (sign_cx, sign_cy, sign_cz), mat_dark_aluminum, rot=(0, 0, sign_rot_z))
    make_box("RoshanSign_GoldRim", (2.44, 0.05, 0.69), (sign_cx, sign_cy, sign_cz), mat_gold_accent, rot=(0, 0, sign_rot_z))
    make_box("RoshanSign_BacklightHalo", (2.2, 0.02, 0.50), (
        sign_cx - math.sin(sign_rot_z) * 0.04,
        sign_cy + math.cos(sign_rot_z) * 0.04,
        sign_cz
    ), mat_warm_led, rot=(0, 0, sign_rot_z))
    
    # 3D 4K Bold Mesh Letters "ROSHAN"
    curve_data = bpy.data.curves.new(name="RoshanFontCurve", type='FONT')
    curve_data.body = "ROSHAN"
    curve_data.extrude = 0.05
    curve_data.bevel_depth = 0.012
    curve_data.bevel_resolution = 3
    curve_data.size = 0.42
    
    temp_text_obj = bpy.data.objects.new("TempRoshanSign", curve_data)
    bpy.context.collection.objects.link(temp_text_obj)
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    text_mesh = bpy.data.meshes.new_from_object(temp_text_obj.evaluated_get(depsgraph))
    bpy.data.objects.remove(temp_text_obj, do_unlink=True)
    bpy.data.curves.remove(curve_data)
    
    roshan_mesh_obj = bpy.data.objects.new("Roshan_3D_Exterior_Sign", text_mesh)
    roshan_mesh_obj.data.materials.append(mat_gold_accent)
    bpy.context.collection.objects.link(roshan_mesh_obj)
    
    # Position text on the face of the backing plaque
    # Centering offset for "ROSHAN" (width ~1.75m)
    half_text_len = 0.90
    roshan_mesh_obj.rotation_euler = (math.radians(90), 0, sign_rot_z + math.radians(90))
    roshan_mesh_obj.location = (
        sign_cx - math.cos(sign_rot_z) * half_text_len - math.sin(sign_rot_z) * 0.04,
        sign_cy - math.sin(sign_rot_z) * half_text_len + math.cos(sign_rot_z) * 0.04,
        sign_cz - 0.20
    )

    # ----------------- 5. Surroundings & Mountains -----------------
    create_panoramic_landscape()
    make_box("LushGardenLawn", (13.0, 24.0, 0.1), (-11.7, 0.0, -0.06), mat_lawn)
    
    for i, py in enumerate([-1.8, -1.0, -0.2, 0.6, 1.4]):
        make_box(f"StepStone_{i}", (0.75, 0.5, 0.025), (left_threshold_x - terrace_w - 0.5 - (i%2)*0.15, py, 0.01), mat_patio_stone)

    # User 3D Trees from trees_3d.zip (Authentic textured 3D trees)
    tree_instances = [
        # (Template Name, (X, Y, Z), scale, rot_z)
        ("Oak_Leav", (-5.6, -2.8, 0.0), 1.25, 35),
        ("Oak_Leav", (-6.2, 3.8, 0.0), 1.30, 110),
        ("Sonnerat", (-11.2, -4.5, 0.0), 0.65, 45),
        ("Walnut_L", (-12.0, 5.2, 0.0), 0.60, 80),
        ("Bark___S", (-6.8, 6.8, 0.0), 0.65, 15),
        ("Bark___S", (-5.8, -6.5, 0.0), 0.60, 140),
        ("Mossy_Tr", (-15.5, 2.5, 0.0), 0.50, 60),
        ("Bark___0", (-14.8, -5.5, 0.0), 0.52, 210),
        ("Bark___1", (-21.0, 8.5, 0.8), 0.45, 95),
        ("Bottom_T", (-24.0, -1.0, 1.2), 0.40, 30),
        ("Bark___1", (-22.5, -8.5, 0.9), 0.45, 175)
    ]
    import_and_setup_user_trees(tree_instances)

    # ----------------- 6. Drawing Board / Studio Easel Setup -----------------
    # Positioned in garden/terrace transition area between court and room
    easel_x = -5.4
    easel_y = 1.1
    easel_z = 0.0
    easel_rot_z = math.radians(20.0) # Angled towards room and camera
    
    # Tripod Legs
    leg_len = 1.75
    leg_pitch = math.radians(12.0)
    leg_w = 0.045
    # Front Left Leg
    make_box("EaselLeg_FL", (leg_w, leg_w, leg_len), (
        easel_x - 0.28 * math.cos(easel_rot_z),
        easel_y - 0.28 * math.sin(easel_rot_z),
        leg_len/2 * math.cos(leg_pitch)
    ), mat_easel_wood, rot=(0, leg_pitch, easel_rot_z))
    # Front Right Leg
    make_box("EaselLeg_FR", (leg_w, leg_w, leg_len), (
        easel_x + 0.28 * math.cos(easel_rot_z),
        easel_y + 0.28 * math.sin(easel_rot_z),
        leg_len/2 * math.cos(leg_pitch)
    ), mat_easel_wood, rot=(0, -leg_pitch, easel_rot_z))
    # Back Strut Leg
    make_box("EaselLeg_Back", (leg_w, leg_w, leg_len * 0.95), (
        easel_x - 0.40 * math.sin(easel_rot_z),
        easel_y + 0.40 * math.cos(easel_rot_z),
        leg_len/2 * 0.9
    ), mat_easel_wood, rot=(-math.radians(22.0), 0, easel_rot_z))
    
    # Central Mast & Horizontal Tray
    make_box("EaselMast", (0.06, 0.05, 1.85), (easel_x, easel_y, 0.92), mat_easel_wood, rot=(0, 0, easel_rot_z))
    make_box("EaselShelfTray", (0.95, 0.14, 0.04), (
        easel_x + 0.03 * math.sin(easel_rot_z),
        easel_y - 0.03 * math.cos(easel_rot_z),
        0.82
    ), mat_easel_wood, rot=(0, 0, easel_rot_z))
    
    # Large Drawing Board & Canvas
    canvas_w, canvas_h = 0.92, 0.72
    canvas_pitch = math.radians(-10.0) # Leaned back naturally
    make_box("DrawingBoard_Backing", (canvas_w + 0.04, 0.025, canvas_h + 0.04), (
        easel_x + 0.02 * math.sin(easel_rot_z),
        easel_y - 0.02 * math.cos(easel_rot_z),
        0.84 + canvas_h/2
    ), mat_wall_slat, rot=(canvas_pitch, 0, easel_rot_z))
    
    # Canvas with Architectural Concept Sketch
    art_canvas = make_box("DrawingBoard_CanvasArt", (canvas_w, 0.015, canvas_h), (
        easel_x + 0.035 * math.sin(easel_rot_z),
        easel_y - 0.035 * math.cos(easel_rot_z),
        0.84 + canvas_h/2
    ), mat_drawing_canvas, rot=(canvas_pitch, 0, easel_rot_z))
    add_box_uvs(art_canvas, projection='Y')
    
    # Artist Wooden Palette & Brushes on Shelf
    make_cylinder("ArtistPalette", 0.16, 0.01, (easel_x + 0.32, easel_y - 0.08, 0.85), mat_easel_wood)
    for pi, pcol in enumerate([mat_rgb_cyan, mat_rgb_magenta, mat_gold_accent, mat_rim_orange]):
        ang = pi * 1.2
        make_cylinder(f"PaintBlob_{pi}", 0.018, 0.008, (easel_x + 0.32 + math.cos(ang)*0.09, easel_y - 0.08 + math.sin(ang)*0.09, 0.86), pcol)
    make_cylinder("BrushHolderCup", 0.035, 0.10, (easel_x - 0.32, easel_y - 0.06, 0.88), mat_dark_aluminum)
    for bi, (bang_x, bang_y) in enumerate([(0.1, 0.15), (-0.12, 0.08), (0.05, -0.15)]):
        make_cylinder(f"ArtistBrush_{bi}", 0.006, 0.22, (easel_x - 0.32 + bang_x*0.1, easel_y - 0.06 + bang_y*0.1, 0.96), mat_gold_accent, rot=(bang_x, bang_y, 0))

    # ----------------- 7. Basketball Court & Regulation Straight Hoop -----------------
    court_x = -7.8
    court_y = 0.4
    court_w, court_l = 4.8, 5.8
    
    # Photoreal Athletic Acrylic Half-Court Surface with complete lines
    court_obj = make_box("BasketballCourt_Surface", (court_w, court_l, 0.035), (court_x, court_y, -0.015), mat_court_surface)
    add_box_uvs(court_obj, projection='Z')
    make_box("BasketballCourt_BorderGravel", (court_w + 0.6, court_l + 0.6, 0.025), (court_x, court_y, -0.025), mat_patio_stone)

    # Regulation Hoop System: 100% SEEDHA / STRAIGHT (Angle = 0.0) facing South (-Y)
    hoop_rot = 0.0
    bb_x = court_x
    bb_y = court_y + court_l/2 - 0.35
    bb_z = 3.25
    
    pole_h = 3.8
    pole_x = bb_x
    pole_y = bb_y + 0.85 # directly behind backboard
    
    # Support Pole & Base
    make_box("HoopSupportPole", (0.18, 0.18, pole_h), (pole_x, pole_y, pole_h/2), mat_dark_aluminum)
    make_box("HoopBaseplate", (0.44, 0.44, 0.03), (pole_x, pole_y, 0.015), mat_dark_aluminum)
    make_box("HoopPolePad", (0.28, 0.28, 1.8), (pole_x, pole_y, 0.9), mat_dark_aluminum)
    make_box("HoopPadAccentTop", (0.285, 0.285, 0.05), (pole_x, pole_y, 1.7), mat_rim_orange)
    make_box("HoopPadAccentMid", (0.285, 0.285, 0.05), (pole_x, pole_y, 1.0), mat_rim_orange)
    
    # Overhang Arms connecting straight to backboard
    make_box("HoopOverhangArm", (0.14, 0.85, 0.06), (bb_x, (pole_y + bb_y)/2, 3.0), mat_dark_aluminum)
    make_box("HoopDiagonalStrut", (0.06, 0.70, 0.06), (bb_x, (pole_y + bb_y)/2 + 0.05, 3.4), mat_dark_aluminum, rot=(math.radians(28.0), 0, 0))

    # Regulation Glass Backboard facing straight South (-Y)
    make_box("BackboardGlass", (1.83, 0.03, 1.07), (bb_x, bb_y, bb_z), mat_glass)
    make_box("BackboardFrameOuter", (1.87, 0.05, 1.11), (bb_x, bb_y, bb_z), mat_dark_aluminum)
    make_box("BackboardCrashPadBottom", (1.87, 0.08, 0.08), (bb_x, bb_y, bb_z - 0.54), mat_dark_aluminum)

    # Inner Target Rectangle
    target_w, target_h = 0.61, 0.46
    target_z = 3.12
    make_box("TargetLineTop", (target_w, 0.02, 0.04), (bb_x, bb_y - 0.025, target_z + target_h/2), mat_rim_orange)
    make_box("TargetLineBottom", (target_w, 0.02, 0.04), (bb_x, bb_y - 0.025, target_z - target_h/2), mat_rim_orange)
    make_box("TargetLineLeft", (0.04, 0.02, target_h), (bb_x - target_w/2, bb_y - 0.025, target_z), mat_rim_orange)
    make_box("TargetLineRight", (0.04, 0.02, target_h), (bb_x + target_w/2, bb_y - 0.025, target_z), mat_rim_orange)

    # User Hoop & Net from Basketball Hoop.blend
    hoop_objs = append_objects("Basketball Hoop.blend", ["Hoop"])
    if hoop_objs:
        hoop = hoop_objs[0]
        hoop.name = "BasketballRimAndNet"
        hoop.scale = (0.28, 0.28, 0.28)
        hoop.location = (bb_x, bb_y - 0.42, 2.95)
        hoop.rotation_euler = (0, 0, 0)

    # User Basketball
    ball_objs = append_objects("low-poly basketball ball.blend", ["BasketBall_Low"])
    if ball_objs:
        ball = ball_objs[0]
        ball.name = "InteractiveBasketball"
        ball.location = (court_x + 0.3, court_y - 0.6, 0.13)
        ball.scale = (1.0, 1.0, 1.0)

    # ----------------- 8. Luxury Master Bed (Grounded & Pillows Facing Room) -----------------
    bed_objs = append_objects("bed.blend", ["Plane.001"])
    if bed_objs:
        bed = bed_objs[0]
        bed.name = "MasterBed"
        bed.scale = (0.92, 0.92, 0.92)
        bed.rotation_euler = (0.0, math.radians(-53.05), math.radians(-90.0))
        bpy.context.view_layer.update()
        
        verts_world = [bed.matrix_world @ v.co for v in bed.data.vertices]
        min_z = min(v.z for v in verts_world)
        bed.location = (1.80, 0.70, -min_z)

    # Nightstand & Designer Lamp
    make_box("Nightstand", (0.5, 0.5, 0.54), (2.80, 1.85, 0.27), mat_wall_slat)
    make_box("NightstandDrawer", (0.51, 0.46, 0.2), (2.80, 1.83, 0.35), mat_dark_aluminum)
    make_box("DrawerBrassPull", (0.02, 0.14, 0.02), (2.80, 1.59, 0.35), mat_gold_accent)
    make_cylinder("LampBase", 0.09, 0.02, (2.80, 1.85, 0.55), mat_gold_accent)
    make_cylinder("LampStem", 0.012, 0.32, (2.80, 1.85, 0.71), mat_gold_accent)
    make_cone("LampFabricShade", 0.16, 0.22, (2.80, 1.85, 0.92), mat_warm_led)
    
    bed_light = bpy.data.lights.new(name="BedsideWarmLight", type='POINT')
    bed_light.energy = 18.0
    bed_light.color = (1.0, 0.88, 0.68)
    bed_light_obj = bpy.data.objects.new(name="BedsideWarmLight", object_data=bed_light)
    bpy.context.collection.objects.link(bed_light_obj)
    bed_light_obj.location = (2.80, 1.85, 0.90)

    # ----------------- 9. Modern Battlestation Desk & Peripherals -----------------
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

    make_box("ProDeskMat", (0.92, 0.42, 0.005), (desk_x - 0.1, desk_y - 0.08, desk_h + 0.0215), mat_dark_aluminum)

    # 49" Curved OLED Ultrawide Monitor with HD Screen Display
    mon_w, mon_h = 1.15, 0.38
    mon_z = desk_h + 0.25
    make_box("MonArmBase", (0.16, 0.16, 0.02), (desk_x, desk_y + 0.30, desk_h + 0.025), mat_dark_aluminum)
    make_cylinder("MonArmPillar", 0.03, 0.38, (desk_x, desk_y + 0.30, desk_h + 0.20), mat_dark_aluminum)
    make_box("MonArmElbow", (0.08, 0.20, 0.05), (desk_x, desk_y + 0.22, mon_z), mat_dark_aluminum)
    make_box("MonChassis", (mon_w, 0.03, mon_h), (desk_x, desk_y + 0.12, mon_z), mat_dark_aluminum)
    mon_scr = make_box("MonScreenOLED", (mon_w - 0.02, 0.004, mon_h - 0.02), (desk_x, desk_y + 0.102, mon_z), mat_screen_wallpaper)
    add_box_uvs(mon_scr, projection='Y')
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

    # ----------------- 10. PC Case Straightened & Colors Perfected -----------------
    pc_parts = append_objects("pc_case/pc.blend", [])
    pc_root = bpy.data.objects.new("UserPCCase_Root", None)
    # Positioned neatly on the right side of desk, aligned along Y
    pc_root.location = (desk_x + desk_w/2 - 0.22, desk_y + 0.04, desk_h + 0.02)
    # Rotate 90 degrees so case length is along Y (front facing user, glass facing left)
    pc_root.rotation_euler = (0, 0, math.radians(90.0))
    bpy.context.collection.objects.link(pc_root)
    
    # Perfect PC Materials
    mat_pc_chassis = create_pbr_mat("PCChassisStealthBlack", (0.018, 0.018, 0.022, 1.0), roughness=0.28, metallic=0.92)
    mat_pc_glass = create_pbr_mat("PCTemperedGlassPanel", (0.1, 0.1, 0.12, 1.0), roughness=0.02, is_glass=True)
    mat_pc_rgb_fan = create_pbr_mat("PCRGBFanGlow", (0.0, 0.88, 1.0, 1.0), emission=(0.0, 0.88, 1.0, 1.0), emission_strength=7.5)
    
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
                
                # Assign professional materials
                if "Fan" in p.name or "Industrial" in p.name:
                    p.data.materials.clear()
                    p.data.materials.append(mat_pc_rgb_fan)
                    p.data.materials.append(mat_pc_chassis)
                elif "Cube.001" in p.name: # Tempered glass side panel
                    p.data.materials.clear()
                    p.data.materials.append(mat_pc_glass)
                else:
                    p.data.materials.clear()
                    p.data.materials.append(mat_pc_chassis)

    # ----------------- 11. User Gaming Chair (Keyframed Swivel Animation) -----------------
    chair_names = ['Plane', 'Plane.005', 'Cylinder', 'Cube', 'Cube.001', 'Plane.002', 'Plane.004']
    imported_chair = append_objects("gaming chair.blend", chair_names)
    
    chair_root = bpy.data.objects.new("Gaming_Chair_Interactive", None)
    chair_root.location = (desk_x, desk_y - 0.68, 0.0)
    bpy.context.collection.objects.link(chair_root)
    
    if imported_chair:
        # Decimate high-poly seat mesh if needed (reduces 1.66M verts to ~100k)
        for obj in imported_chair:
            if obj.data and hasattr(obj.data, 'vertices') and len(obj.data.vertices) > 500000:
                mod = obj.modifiers.new("DecimateChair", 'DECIMATE')
                mod.ratio = 0.06
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier="DecimateChair")
                
        chair_scale = 0.3262
        for obj in imported_chair:
            obj.parent = chair_root
            obj.location = (
                (obj.location.x + 0.12) * chair_scale,
                (obj.location.y + 4.5) * chair_scale,
                (obj.location.z - 0.13) * chair_scale
            )
            obj.scale = (obj.scale.x * chair_scale, obj.scale.y * chair_scale, obj.scale.z * chair_scale)

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

    # ----------------- 12. Balanced Architectural Lighting -----------------
    sun = bpy.data.lights.new(name="GoldenSun", type='SUN')
    sun.energy = 2.2
    sun.color = (1.0, 0.95, 0.88)
    sun.angle = math.radians(24.0)
    sun_obj = bpy.data.objects.new(name="GoldenSun", object_data=sun)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.location = (-12.0, -8.0, 14.0)
    sun_obj.rotation_euler = (math.radians(38), math.radians(-25), math.radians(55))

    # Balanced interior ambient fill (tuned down so floor doesn't wash out!)
    fill = bpy.data.lights.new(name="InteriorFillArea", type='AREA')
    fill.energy = 4.8
    fill.size = 3.6
    fill.color = (0.95, 0.96, 1.0)
    fill_obj = bpy.data.objects.new(name="InteriorFillArea", object_data=fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (floor_cx, floor_cy, room_h - 0.1)

    # ----------------- 13. Hero 4K Architectural Camera -----------------
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

    print("Master 4K Architectural Scene V9 successfully built!")

build_master_scene()
