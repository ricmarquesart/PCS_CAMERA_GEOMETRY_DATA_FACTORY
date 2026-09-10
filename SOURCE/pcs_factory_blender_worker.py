from __future__ import annotations

# This script is executed by Blender's bundled Python with --factory-startup.
import argparse
import hashlib
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

from pcs_factory_blender_protocol import (COMPLETION_SCHEMA, file_record, validate_request, resolve_render_layer_socket_name,
    ndc_to_pcs_pixel, initial_blender_camera_from_K, pixel_in_physical_raster)
from pcs_factory_camera import project_world, vanishing_point, horizon_from_plane_normal, world_to_cv
from pcs_factory_coordinates import B_FROM_C, C_FROM_B, mat_mul, mat_vec
from pcs_factory_paths import write_json_atomic
from pcs_factory_scene_recipe import validate_scene
from pcs_factory_qualification import is_factory_qualification_split
from pcs_factory_appearance import validate_profile
from pcs_factory_micro100_gt import validate_aux_gt
from pcs_factory_rgb8 import apply_fixed_rgb8_contrast_png, apply_fixed_rgb8_gain_png
from pcs_factory_rgb_rescue_r23 import r23_systemic_rgb_policy
from pcs_factory_blueprint_r33 import r33_blueprint_vertical_dominant_policy
from pcs_factory_blueprint_r36 import r36_blueprint_extreme_vertical_policy
from pcs_factory_blueprint_g101_r2 import g101_r2_blueprint_foreground_vertical_policy
from pcs_factory_reprojection_r14 import camera_graphics_probe_specs, reprojection_acceptance
from pcs_factory_visibility_r15 import r15_camera_inside_fill_policy
from pcs_factory_visibility_r17 import r17_camera_inside_contrast_policy


def _sha_color(text: str):
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # bounded mid-value color to avoid accidental black/white collapse
    return tuple(0.18 + (h[i] / 255.0) * 0.62 for i in range(3)) + (1.0,)


def _mat3_mul(A, B):
    return [[sum(float(A[i][k]) * float(B[k][j]) for k in range(3)) for j in range(3)] for i in range(3)]


def _diag3(v):
    return [[float(v[0]), 0.0, 0.0], [0.0, float(v[1]), 0.0], [0.0, 0.0, float(v[2])]]


def _canonical_point_to_blender(p):
    return Vector(mat_vec(B_FROM_C, p))


def _object_matrix_blender(obj):
    # q_b -> q_c via C_FROM_B, then dimensions in canonical local axes,
    # then canonical object rotation, then world basis canonical->Blender.
    Rc = obj["R_local_to_world"]
    D = _diag3(obj["dimensions_m"])
    A = _mat3_mul(B_FROM_C, _mat3_mul(Rc, _mat3_mul(D, C_FROM_B)))
    tb = mat_vec(B_FROM_C, obj["center_world"])
    return Matrix((
        (A[0][0], A[0][1], A[0][2], tb[0]),
        (A[1][0], A[1][1], A[1][2], tb[1]),
        (A[2][0], A[2][1], A[2][2], tb[2]),
        (0.0, 0.0, 0.0, 1.0),
    ))


def _camera_matrix_blender(pose):
    Rc2w = pose["R_camera_to_world_graphics"]
    Rb = _mat3_mul(B_FROM_C, Rc2w)
    Cb = mat_vec(B_FROM_C, pose["camera_center_world"])
    return Matrix((
        (Rb[0][0], Rb[0][1], Rb[0][2], Cb[0]),
        (Rb[1][0], Rb[1][1], Rb[1][2], Cb[1]),
        (Rb[2][0], Rb[2][1], Rb[2][2], Cb[2]),
        (0.0, 0.0, 0.0, 1.0),
    ))


def _world_from_camera_graphics(pose, p_cam):
    q = mat_vec(pose["R_camera_to_world_graphics"], p_cam)
    C = pose["camera_center_world"]
    return tuple(C[i] + q[i] for i in range(3))


def _blender_pixel(scene, cam_obj, p_world_canonical, width, height):
    pb = _canonical_point_to_blender(p_world_canonical)
    ndc = world_to_camera_view(scene, cam_obj, pb)
    u, v = ndc_to_pcs_pixel(float(ndc.x), float(ndc.y), width, height)
    return (u, v, float(ndc.z))


def _configure_camera_from_K(scene, pose, K, width, height):
    cam_data = bpy.data.cameras.new("PCS_CAMERA")
    cam_obj = bpy.data.objects.new("PCS_CAMERA", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    cam_obj.matrix_world = _camera_matrix_blender(pose)
    cam_data.type = "PERSP"
    # Camera projection in Blender depends on render resolution/aspect, so freeze
    # target raster dimensions before any world_to_camera_view calibration.
    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = 36.0
    cam_data.clip_start = 0.01
    cam_data.clip_end = 10000.0

    fx, fy, cx, cy = float(K[0][0]), float(K[1][1]), float(K[0][2]), float(K[1][2])
    initial = initial_blender_camera_from_K(K, width, height, cam_data.sensor_width)
    scene.render.pixel_aspect_x = initial["pixel_aspect_x"]
    scene.render.pixel_aspect_y = initial["pixel_aspect_y"]
    cam_data.lens = initial["lens_mm"]
    cam_data.shift_x = initial["shift_x"]
    cam_data.shift_y = initial["shift_y"]
    bpy.context.view_layer.update()

    # Version-robust numeric calibration against Blender's own projection.
    # It is not a learned correction; it solves Blender lens/shift parameters so the
    # frozen canonical K remains the authority under the pixel-center convention.
    def measure_center_and_focal():
        z = 5.0
        a = 0.3
        c = _world_from_camera_graphics(pose, (0.0, 0.0, -z))
        xp = _world_from_camera_graphics(pose, (a, 0.0, -z))
        xm = _world_from_camera_graphics(pose, (-a, 0.0, -z))
        yp = _world_from_camera_graphics(pose, (0.0, a, -z))
        ym = _world_from_camera_graphics(pose, (0.0, -a, -z))
        pc = _blender_pixel(scene, cam_obj, c, width, height)
        pxp = _blender_pixel(scene, cam_obj, xp, width, height)
        pxm = _blender_pixel(scene, cam_obj, xm, width, height)
        pyp = _blender_pixel(scene, cam_obj, yp, width, height)
        pym = _blender_pixel(scene, cam_obj, ym, width, height)
        fx_obs = abs(pxp[0] - pxm[0]) / (2.0 * a / z)
        fy_obs = abs(pyp[1] - pym[1]) / (2.0 * a / z)
        return pc[0], pc[1], fx_obs, fy_obs

    initial_measured = measure_center_and_focal()
    iterations = 0
    for _ in range(8):
        iterations += 1
        uc, vc, fxo, fyo = measure_center_and_focal()
        if fxo <= 1e-9 or fyo <= 1e-9:
            raise RuntimeError("BLENDER_CAMERA_CALIBRATION_DEGENERATE")
        scale = math.sqrt((fx / fxo) * (fy / fyo))
        cam_data.lens *= scale
        bpy.context.view_layer.update()
        uc, vc, _, _ = measure_center_and_focal()

        # Numeric shift sensitivities avoid depending on undocumented sign/fit details.
        sx0 = cam_data.shift_x
        cam_data.shift_x = sx0 + 0.01
        bpy.context.view_layer.update()
        u2, _, _, _ = measure_center_and_focal()
        sensx = (u2 - uc) / 0.01
        cam_data.shift_x = sx0
        if abs(sensx) > 1e-8:
            cam_data.shift_x = sx0 + (cx - uc) / sensx
        bpy.context.view_layer.update()

        sy0 = cam_data.shift_y
        _, vc, _, _ = measure_center_and_focal()
        cam_data.shift_y = sy0 + 0.01
        bpy.context.view_layer.update()
        _, v2, _, _ = measure_center_and_focal()
        sensy = (v2 - vc) / 0.01
        cam_data.shift_y = sy0
        if abs(sensy) > 1e-8:
            cam_data.shift_y = sy0 + (cy - vc) / sensy
        bpy.context.view_layer.update()

        uc2, vc2, fxo2, fyo2 = measure_center_and_focal()
        if max(abs(uc2-cx), abs(vc2-cy), abs(fxo2-fx), abs(fyo2-fy)) <= 1e-7:
            break

    final_measured = measure_center_and_focal()
    calibration = {
        "schema": "DF-G51-BLENDER-CAMERA-CALIBRATION-R8",
        "raster_mapping": "PIXEL_CENTER_U_EQ_NDCX_TIMES_W_MINUS_HALF",
        "width": int(width), "height": int(height),
        "canonical": {"fx": fx, "fy": fy, "cx": cx, "cy": cy},
        "initial_blender_parameters": initial,
        "initial_measured": {"cx": initial_measured[0], "cy": initial_measured[1], "fx": initial_measured[2], "fy": initial_measured[3]},
        "final_measured": {"cx": final_measured[0], "cy": final_measured[1], "fx": final_measured[2], "fy": final_measured[3]},
        "final_abs_error": {"cx": abs(final_measured[0]-cx), "cy": abs(final_measured[1]-cy), "fx": abs(final_measured[2]-fx), "fy": abs(final_measured[3]-fy)},
        "iterations": iterations,
    }
    return cam_obj, calibration


def _clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        # cameras/lights created after clear; only remove truly orphaned data
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def _make_material(name: str, profile_id: str, category: str, object_id: str):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    color = _sha_color(object_id)
    if profile_id == "CLAY":
        color = (0.55, 0.46, 0.38, 1.0)
    elif profile_id in {"LINE_ART", "TECH_SKETCH"}:
        color = (0.06, 0.06, 0.06, 1.0)
    elif profile_id == "BLUEPRINT":
        color = (0.92, 0.97, 1.0, 1.0)
    elif profile_id == "TOON":
        color = tuple(round(c * 3.0) / 3.0 for c in color[:3]) + (1.0,)
    elif profile_id == "PAINTERLY_CONCEPT":
        # R10 explicit DCC implementation. Value grouping is deterministic and
        # appearance-only; no UV/vertex/camera/object coordinate is changed.
        grouped = []
        for c in color[:3]:
            q = round(float(c) * 4.0) / 4.0
            grouped.append(min(0.88, max(0.16, q)))
        color = tuple(grouped) + (1.0,)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        if profile_id == "PAINTERLY_CONCEPT":
            bsdf.inputs["Roughness"].default_value = 0.82
            bsdf.inputs["Metallic"].default_value = 0.0
            # Explicit material-space brush/value overlay. Generated coordinates
            # alter only shading values; mesh/camera/raster coordinates are untouched.
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            tex = nodes.new("ShaderNodeTexCoord")
            noise = nodes.new("ShaderNodeTexNoise")
            ramp = nodes.new("ShaderNodeValToRGB")
            noise.inputs["Scale"].default_value = 5.0
            noise.inputs["Detail"].default_value = 2.0
            noise.inputs["Roughness"].default_value = 0.58
            base = tuple(float(c) for c in color[:3])
            def shade(mult):
                return tuple(min(1.0, max(0.0, c * mult)) for c in base) + (1.0,)
            cr = ramp.color_ramp
            cr.elements[0].position = 0.28
            cr.elements[0].color = shade(0.62)
            cr.elements[1].position = 0.72
            cr.elements[1].color = shade(1.24)
            mid1 = cr.elements.new(0.44); mid1.color = shade(0.84)
            mid2 = cr.elements.new(0.58); mid2.color = shade(1.04)
            links.new(tex.outputs["Generated"], noise.inputs["Vector"])
            links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
            links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        elif profile_id == "BLUEPRINT":
            # DF-G100 addendum: shader-only blueprint wireframe. The prior mesh
            # WIREFRAME modifier is forbidden because G100 carries exact Depth,
            # Normal and Object Index against the frozen OBB/cuboid geometry.
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            wire = nodes.new("ShaderNodeWireframe")
            wire.use_pixel_size = False
            wire.inputs["Size"].default_value = 0.018
            mix = nodes.new("ShaderNodeMixRGB")
            mix.blend_type = "MIX"
            mix.inputs[1].default_value = (0.018, 0.055, 0.16, 1.0)
            mix.inputs[2].default_value = (0.78, 0.96, 1.0, 1.0)
            links.new(wire.outputs["Fac"], mix.inputs[0])
            links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Roughness"].default_value = 0.88
            bsdf.inputs["Metallic"].default_value = 0.0
        else:
            bsdf.inputs["Roughness"].default_value = 0.72 if category in {"NPR", "EDGE_DISPLAY"} else 0.42
            bsdf.inputs["Metallic"].default_value = 0.0 if category in {"NPR", "EDGE_DISPLAY"} else 0.08
    return mat


def _build_scene_objects(scene_recipe, appearance):
    profile_id = appearance.get("profile_id", "PBR_REALISTIC_INTENT")
    category = appearance.get("category", "PBR")
    made = []
    for idx, obj in enumerate(scene_recipe.get("objects", []), 1):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
        ob = bpy.context.object
        ob.name = str(obj["object_id"])
        ob.matrix_world = _object_matrix_blender(obj)
        ob.pass_index = idx
        mat = _make_material(f"MAT_{idx:04d}", profile_id, category, str(obj["object_id"]))
        ob.data.materials.append(mat)
        if profile_id in {"LINE_ART", "TECH_SKETCH"}:
            wf = ob.modifiers.new(name="PCS_WIREFRAME_STYLE", type="WIREFRAME")
            wf.thickness = 0.012
            wf.use_even_offset = True
            wf.use_replace = True
        made.append(ob)
    return made


def _configure_world_lighting(scene, request, cam_obj):
    appearance = request.get("appearance") or {}
    scene_recipe = request.get("scene") or {}
    pid = appearance.get("profile_id", "PBR_REALISTIC_INTENT")
    category = appearance.get("category", "PBR")
    world = bpy.data.worlds.new("PCS_WORLD") if bpy.data.worlds.get("PCS_WORLD") is None else bpy.data.worlds["PCS_WORLD"]
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if pid == "BLUEPRINT":
        bg.inputs["Color"].default_value = (0.012, 0.035, 0.11, 1.0)
        bg.inputs["Strength"].default_value = 0.35
    elif pid in {"LINE_ART", "TECH_SKETCH"}:
        bg.inputs["Color"].default_value = (0.95, 0.95, 0.95, 1.0)
        bg.inputs["Strength"].default_value = 0.8
    elif pid == "DARK_LOW_CONTRAST":
        bg.inputs["Color"].default_value = (0.015, 0.02, 0.03, 1.0)
        bg.inputs["Strength"].default_value = 0.12
    else:
        bg.inputs["Color"].default_value = (0.12, 0.15, 0.20, 1.0)
        bg.inputs["Strength"].default_value = 0.45

    def add_sun(name, energy, rot):
        data = bpy.data.lights.new(name=name, type="SUN")
        data.energy = energy
        ob = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(ob)
        ob.rotation_euler = rot
        return ob

    def add_area(name, energy, loc, size):
        data = bpy.data.lights.new(name=name, type="AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        ob = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(ob)
        ob.location = loc
        return ob

    def add_point(name, energy, loc, radius):
        data = bpy.data.lights.new(name=name, type="POINT")
        data.energy = float(energy)
        data.shadow_soft_size = float(radius)
        ob = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(ob)
        ob.location = loc
        return ob

    if pid not in {"LINE_ART", "TECH_SKETCH", "BLUEPRINT"}:
        add_sun("PCS_SUN", 2.2 if pid == "DAY_HARD" else 1.3, (math.radians(28), math.radians(-18), math.radians(35)))
        add_area("PCS_FILL", 650.0, (0.0, -3.0, 8.0), 7.0)
        if pid == "PAINTERLY_CONCEPT":
            # Frozen R10 visibility recovery: camera-local fill for a camera
            # inside a closed room whose generic external rig is occluded.
            add_point("PCS_PAINTERLY_CAMERA_FILL", 800.0, cam_obj.location.copy(), 2.0)
    else:
        add_area("PCS_FLAT_LIGHT", 900.0, (0.0, -2.0, 8.0), 12.0)

    # DF-G100 frozen pilot visibility aid. This is shading-only and applies only
    # to closed-room families when Painterly's stronger R10 fill is not active.
    family = str((scene_recipe or {}).get("scene_family", ""))
    closed_room_fill_active = family in {"INTERIOR", "CORRIDOR", "CLUTTER", "HYBRID_CONCEPT"} and pid != "PAINTERLY_CONCEPT"
    if closed_room_fill_active:
        # R9: TOON + closed-room used the generic 350 W pilot fill and the
        # real sample001 fixture became high-luma/low-span. Preserve the same
        # camera-local point/radius but halve only this deterministic profile-
        # family interaction. All other non-Painterly closed-room profiles stay
        # exactly at the frozen 350 W pilot value.
        g100_fill_energy = 175.0 if pid == "TOON" else 350.0
        add_point("PCS_G100_INTERIOR_CAMERA_FILL", g100_fill_energy, cam_obj.location.copy(), 2.0)

    # R15: camera-inside-solid stress cases can have valid geometry/GT while an
    # exterior lighting rig produces unusable near-black RGB. The policy is
    # derived only from frozen canonical request geometry and never from image
    # statistics or acceptance thresholds. Existing Painterly/closed-room fills
    # are never doubled.
    r15_policy = r15_camera_inside_fill_policy(request)
    if r15_policy.get("applied"):
        add_point("PCS_G100_CAMERA_INSIDE_SOLID_FILL_R15", 350.0, cam_obj.location.copy(), 2.0)
    return r15_policy


def _configure_render(scene, request, out_dir: Path):
    renderer = request["renderer"]
    engine = renderer["engine"]
    scene.render.engine = engine
    w = int(request["camera"]["width"])
    h = int(request["camera"]["height"])
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.filepath = str(out_dir / "rgb.png")
    scene.render.film_transparent = False
    # R6 makes the inherited Blender/Cycles reconstruction filter explicit.
    # This is the same effective 1.5 px default used by prior accepted renders;
    # it is provenance, not a visual/render-setting change.
    scene.render.filter_size = 1.5
    scene.render.use_file_extension = True
    if engine == "BLENDER_EEVEE_NEXT":
        # API-safe Eevee settings kept intentionally minimal.
        pass
    elif engine == "CYCLES":
        scene.cycles.samples = int(renderer.get("samples", 8))
        scene.cycles.use_denoising = bool(renderer.get("denoise", True))
        device = str(renderer.get("device", "AUTO")).upper()
        if device in {"CUDA", "AUTO"}:
            try:
                prefs = bpy.context.preferences.addons["cycles"].preferences
                prefs.compute_device_type = "CUDA"
                prefs.get_devices()
                cuda_devices = [d for d in prefs.devices if d.type == "CUDA"]
                if cuda_devices:
                    for d in prefs.devices:
                        d.use = d in cuda_devices
                    scene.cycles.device = "GPU"
                elif device == "CUDA":
                    raise RuntimeError("CYCLES_CUDA_REQUIRED_BUT_UNAVAILABLE")
                else:
                    scene.cycles.device = "CPU"
            except Exception:
                if device == "CUDA":
                    raise
                scene.cycles.device = "CPU"
        else:
            scene.cycles.device = "CPU"

    requested = set(request.get("passes", []))
    aux_requested = bool(requested.intersection({"DEPTH", "NORMAL", "OBJECT_INDEX"}))
    if aux_requested:
        layer = scene.view_layers[0]
        layer.use_pass_z = "DEPTH" in requested
        layer.use_pass_normal = "NORMAL" in requested
        layer.use_pass_object_index = "OBJECT_INDEX" in requested
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        rlayer = tree.nodes.new("CompositorNodeRLayers")
        comp = tree.nodes.new("CompositorNodeComposite")
        tree.links.new(rlayer.outputs["Image"], comp.inputs["Image"])

        available_socket_names = [str(sock.name) for sock in rlayer.outputs]

        def file_node(pass_name, prefix, color_mode):
            socket_name = resolve_render_layer_socket_name(engine, pass_name, available_socket_names)
            node = tree.nodes.new("CompositorNodeOutputFile")
            node.base_path = str(out_dir)
            node.format.file_format = "OPEN_EXR"
            node.format.color_depth = "32"
            node.format.color_mode = color_mode
            node.file_slots[0].path = prefix + "_"
            tree.links.new(rlayer.outputs[socket_name], node.inputs[0])

        if "DEPTH" in requested:
            file_node("DEPTH", "depth", "BW")
        if "NORMAL" in requested:
            file_node("NORMAL", "normal", "RGB")
        if "OBJECT_INDEX" in requested:
            file_node("OBJECT_INDEX", "object_index", "BW")


def _rename_aux_outputs(out_dir: Path, requested):
    mapping = {"DEPTH": ("depth_*.exr", "depth.exr"), "NORMAL": ("normal_*.exr", "normal.exr"), "OBJECT_INDEX": ("object_index_*.exr", "object_index.exr")}
    for key, (pattern, name) in mapping.items():
        if key not in requested:
            continue
        matches = sorted(out_dir.glob(pattern))
        if len(matches) != 1:
            raise RuntimeError(f"AUX_PASS_FILE_COUNT:{key}:{len(matches)}")
        os.replace(matches[0], out_dir / name)


def _scene_landmarks(scene_recipe, pose, K, limit=24):
    pts = []
    seen = set()
    for ob in scene_recipe.get("objects", []):
        for e in ob.get("edges", []):
            for p in (e.get("p0_world"), e.get("p1_world")):
                if p is None:
                    continue
                key = tuple(round(float(x), 9) for x in p)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    q = project_world(p, pose, K)
                except Exception:
                    continue
                pts.append((tuple(map(float, p)), (float(q[0]), float(q[1]))))
                if len(pts) >= limit:
                    return pts
    return pts


def _camera_reprojection(scene, cam_obj, scene_recipe, pose, K, width, height):
    # R13 preserves the exact scene-landmark sampling order, but only canonical
    # projections inside the physical raster carry acceptance authority. Extreme
    # off-raster / near-camera-plane projections remain diagnostics.
    scene_candidates = _scene_landmarks(scene_recipe, pose, K, limit=32)
    authoritative = []
    diagnostics = []
    for pw, expected in scene_candidates:
        (authoritative if pixel_in_physical_raster(expected, width, height) else diagnostics).append((pw, expected, "SCENE", None))

    synthetic_added = 0
    synthetic_probe_records = []
    if len(authoritative) < 8:
        # R14 fallback calibration evidence is intrinsics-adaptive.  Probe rays
        # are defined by deterministic interior raster targets, converted through
        # the active K to camera-local 3D, then reprojected through project_world.
        # They test Blender effective K/pose without claiming scene visibility.
        for probe in camera_graphics_probe_specs(K, width, height):
            pw = _world_from_camera_graphics(pose, tuple(probe["camera_graphics"]))
            q = project_world(pw, pose, K)
            expected = (float(q[0]), float(q[1]))
            src = "SYNTHETIC_INTRINSICS_ADAPTIVE_RASTER_R14"
            meta = {"fraction": list(probe["fraction"]), "target_pixel": list(probe["target_pixel"]), "depth_cv_m": float(probe["depth_cv_m"])}
            if pixel_in_physical_raster(expected, width, height):
                authoritative.append((pw, expected, src, meta))
                synthetic_probe_records.append({**meta, "canonical_pixel": [expected[0], expected[1]], "authority": True})
                synthetic_added += 1
            else:
                diagnostics.append((pw, expected, src, meta))
                synthetic_probe_records.append({**meta, "canonical_pixel": [expected[0], expected[1]], "authority": False})
            if len(authoritative) >= 8:
                break

    authoritative_records = []
    residuals = []
    for pw, expected, source, probe_meta in authoritative:
        got = _blender_pixel(scene, cam_obj, pw, width, height)
        r = math.hypot(got[0] - expected[0], got[1] - expected[1])
        residuals.append(r)
        rec={"world": list(pw), "canonical_pixel": list(expected), "blender_pixel": [got[0], got[1]], "residual_px": r, "source": source, "authority": True}
        if probe_meta is not None: rec["probe"] = probe_meta
        authoritative_records.append(rec)

    diagnostic_records = []
    diagnostic_residuals = []
    for pw, expected, source, probe_meta in diagnostics:
        got = _blender_pixel(scene, cam_obj, pw, width, height)
        r = math.hypot(got[0] - expected[0], got[1] - expected[1])
        diagnostic_residuals.append(r)
        rec={"world": list(pw), "canonical_pixel": list(expected), "blender_pixel": [got[0], got[1]], "residual_px": r, "source": source, "authority": False, "diagnostic_reason": "CANONICAL_PIXEL_OUTSIDE_PHYSICAL_RASTER"}
        if probe_meta is not None: rec["probe"] = probe_meta
        diagnostic_records.append(rec)

    acc = reprojection_acceptance(residuals, minimum_authoritative_landmarks=8, max_tolerance_px=0.50, median_tolerance_px=0.20)
    mx = float(acc["max_residual_px"]); med = float(acc["median_residual_px"])
    return {
        "schema": "DF-G100-CAMERA-REPROJECTION-R14-V1",
        "status": acc["status"],
        "authority_domain": "CANONICAL_PIXEL_CENTER_INSIDE_PHYSICAL_RASTER_R13",
        "synthetic_probe_semantics": "INTRINSICS_ADAPTIVE_INTERIOR_RASTER_PROBES_R14_V1",
        "physical_raster_bounds": {"u_min": -0.5, "u_max": float(width) - 0.5, "v_min": -0.5, "v_max": float(height) - 0.5, "inclusive": True},
        "minimum_authoritative_landmarks": 8,
        "scene_candidate_landmark_count": len(scene_candidates),
        "landmark_count": len(authoritative_records),
        "authoritative_landmark_count": len(authoritative_records),
        "synthetic_authoritative_landmarks_added": synthetic_added,
        "synthetic_probe_records": synthetic_probe_records,
        "off_raster_diagnostic_count": len(diagnostic_records),
        "off_raster_diagnostic_max_residual_px": max(diagnostic_residuals, default=0.0),
        "max_residual_px": mx,
        "median_residual_px": med,
        "tolerance_max_px": 0.50,
        "tolerance_median_px": 0.20,
        "landmarks": authoritative_records,
        "diagnostic_landmarks": diagnostic_records,
    }


def _truth_overlay(scene_recipe, pose, K, width, height, repro):
    vps = {}
    for name, d in [("X", (1,0,0)), ("Y", (0,1,0)), ("Z", (0,0,1))]:
        vp = vanishing_point(d, pose, K, width, height)
        vps[name] = {"finite": vp["finite"], "pixel": list(vp["pixel"]) if vp.get("pixel") is not None else None, "location_class": vp.get("location_class")}
    horizon = horizon_from_plane_normal((0,1,0), pose, K)["line_normalized"]
    return {
        "vps": vps,
        "horizon_line_abc": list(horizon),
        "landmarks": [{"pixel": r["canonical_pixel"]} for r in repro.get("landmarks", [])[:16]],
    }


def _render(request, runtime_lock, run_root):
    validate_request(request)
    out_dir = Path(run_root) / Path(request["output_rel"])
    out_dir.mkdir(parents=True, exist_ok=True)
    _clear_scene()
    scene = bpy.context.scene
    scene.render.engine = request["renderer"]["engine"]
    scene.frame_set(1)

    scene_recipe = request["scene"]
    appearance = request["appearance"]
    sv = validate_scene(scene_recipe)
    av = validate_profile(appearance)
    if sv["status"] != "PASS":
        raise RuntimeError("SCENE_RECIPE_VALIDATION_FAIL:" + ",".join(sv["findings"]))
    if av["status"] != "PASS":
        raise RuntimeError("APPEARANCE_VALIDATION_FAIL:" + ",".join(av["errors"]))

    camrec = request["camera"]
    pose = camrec["pose"]
    K = camrec["K"]
    width, height = int(camrec["width"]), int(camrec["height"])
    cam_obj, camera_calibration = _configure_camera_from_K(scene, pose, K, width, height)
    write_json_atomic(out_dir / "camera_calibration.json", camera_calibration)
    _build_scene_objects(scene_recipe, appearance)
    r15_visibility_policy = _configure_world_lighting(scene, request, cam_obj)
    _configure_render(scene, request, out_dir)
    bpy.context.view_layer.update()

    repro_before = _camera_reprojection(scene, cam_obj, scene_recipe, pose, K, width, height)
    write_json_atomic(out_dir / "pre_render_reprojection.json", repro_before)
    if repro_before["status"] != "PASS":
        raise RuntimeError(f"CAMERA_REPROJECTION_FAIL_PRE_RENDER:max={repro_before['max_residual_px']}:median={repro_before['median_residual_px']}")

    t0 = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    elapsed = time.perf_counter() - t0
    _rename_aux_outputs(out_dir, set(request.get("passes", [])))

    # R10 frozen RGB appearance correction. The raw Blender RGB is preserved
    # byte-exact before a fixed, non-adaptive per-channel RGB8 contrast transform.
    # This is deliberately appearance-only: no spatial operation and no GT/pass
    # mutation. Constants are frozen by the R10 Drive addendum.
    r10_rgb_contrast = None
    r10_closed_room = str(scene_recipe.get("scene_family", "")) in {"INTERIOR", "CORRIDOR", "CLUTTER", "HYBRID_CONCEPT"}
    r10_toon = str(appearance.get("profile_id", "")) == "TOON"
    if is_factory_qualification_split(request.get("split")) and r10_closed_room and r10_toon:
        rgb_path = out_dir / "rgb.png"
        if not rgb_path.is_file():
            raise RuntimeError("R10_RGB_RENDER_OUTPUT_MISSING")
        raw_path = out_dir / "rgb_renderer_raw.png"
        raw_path.write_bytes(rgb_path.read_bytes())
        r10_rgb_contrast = apply_fixed_rgb8_contrast_png(
            raw_path, rgb_path, pivot=128, numerator=5, denominator=4
        )
        r10_rgb_contrast.update({
            "implementation_id": "DF_G100_TOON_CLOSED_ROOM_RGB_CONTRAST_V1_R10",
            "raw_rgb_rel": "rgb_renderer_raw.png",
            "final_rgb_rel": "rgb.png",
            "geometry_preserving": True,
            "threshold_adaptive": False,
            "sample_statistics_used": False,
        })

    # R17 fixed camera-inside RGB contrast. Eligibility is categorical from the
    # frozen R15 visibility policy and never depends on image statistics or
    # acceptance thresholds. The post-R15 renderer RGB is preserved byte-exact.
    r17_rgb_contrast = None
    r17_policy = r17_camera_inside_contrast_policy(request)
    if r17_policy.get("applied"):
        if r10_rgb_contrast is not None:
            raise RuntimeError("R17_UNEXPECTED_R10_DOUBLE_CONTRAST_ELIGIBILITY")
        rgb_path = out_dir / "rgb.png"
        if not rgb_path.is_file():
            raise RuntimeError("R17_RGB_RENDER_OUTPUT_MISSING")
        raw_path = out_dir / "rgb_renderer_raw.png"
        raw_path.write_bytes(rgb_path.read_bytes())
        r17_rgb_contrast = apply_fixed_rgb8_contrast_png(
            raw_path, rgb_path, pivot=128, numerator=17, denominator=16
        )
        r17_rgb_contrast.update({
            "implementation_id": "DF_G100_CAMERA_INSIDE_FIXED_RGB_CONTRAST_V1_R17",
            "raw_rgb_rel": "rgb_renderer_raw.png",
            "final_rgb_rel": "rgb.png",
            "geometry_preserving": True,
            "threshold_adaptive": False,
            "sample_statistics_used": False,
            "eligibility_semantics": "R15_CAMERA_INSIDE_VISIBILITY_AID_CATEGORY_R17",
        })

    # R23/R24 production fixed RGB rescue for analytically low-diversity camera views.
    # Eligibility is geometry/camera-only and never reads RGB statistics. The
    # inherited final RGB is preserved byte-exact before the fixed transform.
    r23_rgb_policy = r23_systemic_rgb_policy(request)
    r23_rgb_contrast = None
    if r23_rgb_policy.get("applied"):
        rgb_path = out_dir / "rgb.png"
        if not rgb_path.is_file():
            raise RuntimeError("R21_RGB_RENDER_OUTPUT_MISSING")
        pre_path = out_dir / "rgb_pre_r23.png"
        pre_path.write_bytes(rgb_path.read_bytes())
        r23_rgb_contrast = apply_fixed_rgb8_contrast_png(
            pre_path, rgb_path,
            pivot=int(r23_rgb_policy["pivot_u8"]),
            numerator=int(r23_rgb_policy["factor_numerator"]),
            denominator=int(r23_rgb_policy["factor_denominator"]),
        )
        r23_rgb_contrast.update({
            "implementation_id": r23_rgb_policy["implementation_id"],
            "source_rgb_rel": "rgb_pre_r23.png",
            "final_rgb_rel": "rgb.png",
            "geometry_preserving": True,
            "threshold_adaptive": False,
            "sample_statistics_used": False,
            "eligibility": r23_rgb_policy,
            "lab_only": False,
            "production_authorized": True,
        })

    # R33 BLUEPRINT vertical-dominant visibility normalization. Eligibility is
    # derived exclusively from frozen geometry/camera plus inherited fill
    # categories. No rendered RGB statistic or acceptance threshold is read.
    r33_rgb_policy = r33_blueprint_vertical_dominant_policy(request)
    r33_rgb_gain = None
    if r33_rgb_policy.get("applied"):
        rgb_path = out_dir / "rgb.png"
        if not rgb_path.is_file():
            raise RuntimeError("R33_RGB_RENDER_OUTPUT_MISSING")
        pre_path = out_dir / "rgb_pre_r33.png"
        pre_path.write_bytes(rgb_path.read_bytes())
        r33_rgb_gain = apply_fixed_rgb8_gain_png(
            pre_path, rgb_path, numerator=2, denominator=1
        )
        r33_rgb_gain.update({
            "implementation_id": r33_rgb_policy["implementation_id"],
            "source_rgb_rel": "rgb_pre_r33.png",
            "final_rgb_rel": "rgb.png",
            "geometry_preserving": True,
            "eligibility": r33_rgb_policy,
            "r33_spec_drive_id": r33_rgb_policy.get("r33_spec_drive_id"),
        })

    # R36 BLUEPRINT extreme distributed vertical-coverage normalization.
    # This is a second, fixed severity tier applied only when R33 does not
    # already apply and near-total visible raster coverage is vertical.
    r36_rgb_policy = r36_blueprint_extreme_vertical_policy(request)
    r36_rgb_gain = None
    if r36_rgb_policy.get("applied"):
        rgb_path = out_dir / "rgb.png"
        if not rgb_path.is_file():
            raise RuntimeError("R36_RGB_RENDER_OUTPUT_MISSING")
        pre_path = out_dir / "rgb_pre_r36.png"
        pre_path.write_bytes(rgb_path.read_bytes())
        r36_rgb_gain = apply_fixed_rgb8_gain_png(
            pre_path, rgb_path, numerator=3, denominator=1
        )
        r36_rgb_gain.update({
            "implementation_id": r36_rgb_policy["implementation_id"],
            "source_rgb_rel": "rgb_pre_r36.png",
            "final_rgb_rel": "rgb.png",
            "geometry_preserving": True,
            "eligibility": r36_rgb_policy,
            "r36_spec_drive_id": r36_rgb_policy.get("r36_spec_drive_id"),
        })

    # G101 R2 BLUEPRINT foreground-dominant near-total vertical visibility gain.
    # This terminal layer is geometry/light-only and composes after inherited R36.
    g101_r2_rgb_policy = g101_r2_blueprint_foreground_vertical_policy(request)
    g101_r2_rgb_gain = None
    if g101_r2_rgb_policy.get("applied"):
        rgb_path = out_dir / "rgb.png"
        if not rgb_path.is_file():
            raise RuntimeError("G101_R2_RGB_RENDER_OUTPUT_MISSING")
        pre_path = out_dir / "rgb_pre_g101_r2.png"
        pre_path.write_bytes(rgb_path.read_bytes())
        g101_r2_rgb_gain = apply_fixed_rgb8_gain_png(
            pre_path, rgb_path, numerator=2, denominator=1
        )
        g101_r2_rgb_gain.update({
            "implementation_id": g101_r2_rgb_policy["implementation_id"],
            "source_rgb_rel": "rgb_pre_g101_r2.png",
            "final_rgb_rel": "rgb.png",
            "geometry_preserving": True,
            "eligibility": g101_r2_rgb_policy,
            "g101_r2_spec_drive_id": g101_r2_rgb_policy.get("g101_r2_spec_drive_id"),
        })

    # G100 invokes exhaustive analytic auxiliary-GT validation before a completion
    # manifest is allowed to exist. Raw EXRs remain byte-immutable.
    micro100_gt = None
    if is_factory_qualification_split(request.get("split")):
        micro100_gt = validate_aux_gt(request, out_dir, renderer_filter_width_px=float(scene.render.filter_size))

    repro_after = _camera_reprojection(scene, cam_obj, scene_recipe, pose, K, width, height)
    if repro_after["status"] != "PASS":
        raise RuntimeError("CAMERA_REPROJECTION_FAIL_POST_RENDER")
    overlay = _truth_overlay(scene_recipe, pose, K, width, height, repro_after)

    files = []
    for name in ["rgb.png", "rgb_renderer_raw.png", "rgb_pre_r23.png", "rgb_pre_r33.png", "rgb_pre_r36.png", "rgb_pre_g101_r2.png", "depth.exr", "normal.exr", "object_index.exr", "normal_authority_mask.uint8.bin", "normal_filter_safe_interior_mask.uint8.bin", "depth_filter_safe_interior_mask.uint8.bin", "micro100_aux_gt_qa.json"]:
        p = out_dir / name
        if p.exists():
            files.append(file_record(p, out_dir))
    completion = {
        "schema": COMPLETION_SCHEMA,
        "status": "PASS_REAL_BLENDER_RENDERED",
        "sample_id": request["sample_id"],
        "input_digest_sha256": request["input_digest_sha256"],
        "runtime_archive_sha256": runtime_lock["archive_sha256"],
        "blender_version": bpy.app.version_string,
        "blender_build_hash": (bpy.app.build_hash.decode("ascii", "replace") if isinstance(bpy.app.build_hash, (bytes, bytearray)) else str(bpy.app.build_hash)),
        "renderer": request["renderer"],
        "renderer_filter_provenance": {"reconstruction_filter_width_px": float(scene.render.filter_size), "r6_explicit_inherited_default": True},
        "passes_requested": request["passes"],
        "render_elapsed_seconds": elapsed,
        "camera_reprojection": repro_after,
        "camera_calibration": camera_calibration,
        "raster_mapping": "PIXEL_CENTER_U_EQ_NDCX_TIMES_W_MINUS_HALF",
        "truth_overlay": overlay,
        "scene_validation": sv,
        "appearance_validation": av,
        "micro100_aux_gt": micro100_gt,
        "r10_rgb_contrast": r10_rgb_contrast,
        "r15_camera_inside_visibility_aid": r15_visibility_policy,
        "r17_camera_inside_rgb_contrast": r17_rgb_contrast,
        "r23_systemic_rgb_contrast": r23_rgb_contrast,
        "r23_systemic_rgb_policy": r23_rgb_policy,
        "r33_blueprint_vertical_dominant_policy": r33_rgb_policy,
        "r33_blueprint_fixed_rgb_gain": r33_rgb_gain,
        "r36_blueprint_extreme_vertical_policy": r36_rgb_policy,
        "r36_blueprint_fixed_rgb_gain": r36_rgb_gain,
        "g101_r2_blueprint_foreground_vertical_policy": g101_r2_rgb_policy,
        "g101_r2_blueprint_fixed_rgb_gain": g101_r2_rgb_gain,
        "micro100_visibility_aid": ({
            "implementation_id": ("DF_G100_CLOSED_ROOM_CAMERA_FILL_V2_R9_TOON_BALANCED"
                                  if appearance.get("profile_id") == "TOON"
                                  else "DF_G100_CLOSED_ROOM_CAMERA_FILL_V1"),
            "type":"POINT",
            "energy_w": (175.0 if appearance.get("profile_id") == "TOON" else 350.0),
            "soft_shadow_radius_m":2.0,
            "location":"BLENDER_CAMERA_LOCATION","geometry_preserving":True,"spatial_warp":False,
            "r9_toon_closed_room_balance": (appearance.get("profile_id") == "TOON")
        } if is_factory_qualification_split(request.get("split")) and scene_recipe.get("scene_family") in {"INTERIOR","CORRIDOR","CLUTTER","HYBRID_CONCEPT"} and appearance.get("profile_id") != "PAINTERLY_CONCEPT" else None),
        "appearance_dcc_implementation": ({
            "implementation_id": "PAINTERLY_CONCEPT_DCC_V2_R10",
            "profile_id": "PAINTERLY_CONCEPT",
            "geometry_preserving": True,
            "spatial_warp": False,
            "value_grouping": "4_LEVEL_DETERMINISTIC_SHA_COLOR_PLUS_4_STOP_PROCEDURAL_RAMP",
            "roughness": 0.82,
            "metallic": 0.0,
            "camera_local_fill": {"type": "POINT", "energy_w": 800.0, "soft_shadow_radius_m": 2.0, "location": "BLENDER_CAMERA_LOCATION"},
            "generic_world_sun_area_preserved": True,
            "brush_overlay": "MATERIAL_SPACE_GENERATED_COORD_NOISE_COLOR_RAMP_SHADING_ONLY"
        } if appearance.get("profile_id") == "PAINTERLY_CONCEPT" else ({
            "implementation_id": "BLUEPRINT_DCC_V2_G100_SHADER_WIREFRAME",
            "profile_id": "BLUEPRINT",
            "geometry_preserving": True,
            "spatial_warp": False,
            "geometry_modifier_used": False,
            "edge_mask": "SHADER_WIREFRAME_NODE"
        } if appearance.get("profile_id") == "BLUEPRINT" else {
            "implementation_id": "INHERITED_GENERIC_OR_PROFILE_SPECIFIC_V8R2",
            "profile_id": appearance.get("profile_id"),
            "geometry_preserving": True
        })),
        "files": files,
        "real_blender_rendered": True,
        "product_mutated": False,
        "maya_mutated": False,
        "training_started": False,
        "test77_accessed": False,
    }
    write_json_atomic(out_dir / "completion.json", completion)
    return completion


def _parse_args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--runtime-lock", required=True)
    ap.add_argument("--run-root", required=True)
    return ap.parse_args(argv)


def main():
    args = _parse_args(sys.argv)
    req = json.loads(Path(args.request).read_text(encoding="utf-8"))
    lock = json.loads(Path(args.runtime_lock).read_text(encoding="utf-8"))
    try:
        out = _render(req, lock, Path(args.run_root))
        print("PCS_BLENDER_COMPLETION=" + json.dumps({"status": out["status"], "sample_id": out["sample_id"]}, sort_keys=True))
        return 0
    except Exception as e:
        fail = {
            "schema": "DF-G51-BLENDER-WORKER-FAILURE-V1",
            "status": "FAIL_REAL_BLENDER_WORKER",
            "sample_id": req.get("sample_id"),
            "input_digest_sha256": req.get("input_digest_sha256"),
            "error_type": type(e).__name__,
            "error": str(e),
            "real_blender_rendered": False,
            "product_mutated": False,
            "maya_mutated": False,
            "training_started": False,
            "test77_accessed": False,
        }
        out_dir = Path(args.run_root) / Path(req.get("output_rel", "."))
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(out_dir / "failure.json", fail)
        print("PCS_BLENDER_FAILURE=" + json.dumps(fail, sort_keys=True), file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
