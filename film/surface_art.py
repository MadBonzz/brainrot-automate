"""Tileable architectural finishes for Workbench. Use object material slots on instanced geometry."""

import math
import bpy
import numpy as np


def texture(name, rgba):
    key = "Surface " + name + " " + "".join(f"{round(c * 255):02x}" for c in rgba[:3])
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    mat = bpy.data.materials.new(key)
    mat.diffuse_color = rgba
    if name == "paint":
        return mat
    n = 128
    y, x = np.mgrid[0:n, 0:n] / n
    rng = np.random.default_rng(774)
    grit = rng.normal(0, 0.035, x.shape)
    broad = np.sin(2 * math.pi * (3 * x + 2 * y)) * 0.042 + np.cos(2 * math.pi * (x - 4 * y)) * 0.047
    value = 1 + broad + grit
    if name in ("stone", "brick"):
        row = np.floor(y * 4)
        u = (x * (3 if name == "stone" else 2) + (row % 2) * 0.5 + 0.008 * np.sin(y * math.tau * 7)) % 1
        v = (y * 4 + 0.012 * np.cos(x * math.tau * 4)) % 1
        rim = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v))
        value += (
            np.sin((np.floor(x * (3 if name == "stone" else 2) + (row % 2) * 0.5) + row * 9) * 2.3) * 0.10
        )
        value *= np.where(rim < 0.018, 0.41, np.where(rim < 0.047, 0.68, np.where(rim < 0.074, 1.10, 1.0)))
    elif name == "wood":
        grain = 2 * math.pi * (15 * y + 0.38 * np.sin(x * math.tau) + 0.32 * np.sin((x + y) * math.tau * 2))
        value += 0.07 * np.sin(grain) + 0.06 * np.cos(grain * 3)
        value *= np.where((y * 4) % 1 < 0.027, 0.48, 1.0)
    elif name == "metal":
        value += 0.06 * np.sin(y * math.tau * 8)
        ring = ((x - 0.09) ** 2 + (y - 0.09) ** 2) ** 0.5
        value *= np.where(ring < 0.026, 0.50, np.where(ring < 0.034, 1.32, 1.0))
    elif name == "scales":
        row = np.floor(y * 7)
        u = (x * 6 + (row % 2) * 0.5) % 1 - 0.5
        v = (y * 7) % 1
        arc = np.sqrt(u * u + (v * 0.72) ** 2)
        value *= np.where(abs(arc - 0.54) < 0.040, 0.49, np.where(abs(arc - 0.49) < 0.044, 1.31, 1.0))
    elif name == "sky":
        value = 0.78 + 0.36 * (1 - y)
    im = bpy.data.images.new(key, width=n, height=n)
    # Generated pixel values are sRGB texels sampled by Workbench, whereas object colors are linear.
    rgb = np.array(rgba[:3])
    rgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(rgb, 1 / 2.4) - 0.055)
    pixels = np.empty((n, n, 4), dtype=np.float32)
    pixels[:, :, :3] = np.clip(rgb[None, None, :] * value[:, :, None], 0, 1)
    pixels[:, :, 3] = 1
    im.pixels.foreach_set(pixels.ravel())
    im.update()
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = im
    mat.node_tree.nodes.active = node
    mat.node_tree.links.new(
        node.outputs["Color"], mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"]
    )
    return mat


def finish(scene):
    meshes = {}
    for obj in scene.objects:
        if obj.type not in ("MESH", "FONT"):
            continue
        name = obj.get("surface_finish", "paint")
        if name != "paint" and obj.type == "MESH":
            mesh = obj.data
            size = tuple(round(abs(a), 3) for a in obj.scale)
            key = (mesh.as_pointer(), size, name)
            if key not in meshes:
                copy = mesh.copy()
                uv = copy.uv_layers.new(name="Story UV")
                period = {"brick": 2.10, "stone": 2.9, "wood": 1.65, "metal": 1.34, "scales": 0.71}.get(
                    name, 1
                )
                for poly in copy.polygons:
                    normal = poly.normal
                    axis = max(range(3), key=lambda i: abs(normal[i]))
                    u, v = ((1, 2), (0, 2), (0, 1))[axis]
                    for k in poly.loop_indices:
                        co = copy.vertices[copy.loops[k].vertex_index].co
                        uv.data[k].uv = (
                            (co[u] + 0.5, co[v] + 0.5)
                            if name == "sky"
                            else (co[u] * size[u] / period, co[v] * size[v] / period)
                        )
                copy.uv_layers.active = uv
                uv.active_render = True
                meshes[key] = copy
            obj.data = meshes[key]
        mat = texture(name, tuple(obj.color))
        if not obj.data.materials:
            obj.data.materials.append(mat)
        obj.material_slots[0].link = "OBJECT"
        obj.material_slots[0].material = mat
    scene.display.shading.color_type = "TEXTURE"
