"""World-space atmosphere and exposure cues on the ensemble shot clock."""

from math import cos, sin, pi
import bpy
from animate import part


def stage(scene, effect, frames, fps, clock):
    kind = effect["kind"]
    start = 1 + round(effect["start"] * (frames - 1))
    end = max(start + 1, 1 + round(effect["end"] * (frames - 1)))
    if kind == "fog":
        for i in range(25):
            x = (i % 9 - 4) * 1.7
            y = 2.85 + (i // 9) * 1.60
            cloud = part(
                (x, y, 0.35 + (i * 7 % 6) * 0.18),
                (2.53, 1.17, 1.14 + (i % 3) * 0.27),
                ("ACB4BA", "C3CBCE", "A6B2BD")[i % 3],
                shape="sphere",
            )
            for f in (1, frames):
                cloud.delta_location.x = 0.33 * sin((clock + f / fps) * 0.50 + i)
                cloud.keyframe_insert(data_path="delta_location", index=0, frame=f)
    if kind in ("sunpatch", "eclipse"):
        # A real aperture in the shadow lets the existing floor remain visible in the light.
        verts = []
        faces = []
        n = 64
        for r in (25, 1):
            verts += [(r * cos(i * 2 * pi / n), r * sin(i * 2 * pi / n), 0.034) for i in range(n)]
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, n + j, n + i))
        mesh = bpy.data.meshes.new("Canyon penumbra")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        shadow = part((0, 0, 0), (1, 1, 1), "59566A", shape=mesh)
        shadow.shape_key_add(name="Shadow edge")
        aperture = shadow.shape_key_add(name="Last sunlight")
        begin, finish = (3.4, 1.25) if kind == "sunpatch" else (1.25, 0.02)
        for i in range(n, 2 * n):
            v = mesh.vertices[i].co.copy()
            mesh.shape_keys.key_blocks[0].data[i].co = (v.x * begin, v.y * begin, v.z)
            aperture.data[i].co = (v.x * finish, v.y * finish, v.z)
        aperture.value = 0
        aperture.keyframe_insert(data_path="value", frame=start)
        aperture.value = 1
        aperture.keyframe_insert(data_path="value", frame=end)
    if kind in ("flicker", "eclipse", "blackout", "dawn"):
        base = scene.view_settings.exposure
        levels = {
            "flicker": [
                (0, 0),
                (0.09, -2.45),
                (0.22, -2.45),
                (0.24, 0),
                (0.60, 0),
                (0.63, -2.45),
                (0.80, -2.45),
                (0.82, 0),
                (1, 0),
            ],
            "eclipse": [(0, 0), (0.64, -0.22), (1, -2.2)],
            "blackout": [(0, 0), (0.46, 0), (0.50, -3.4), (1, -3.4)],
            "dawn": [(0, -1.72), (0.72, 0.16), (1, 0.16)],
        }[kind]
        for t, value in levels:
            scene.view_settings.exposure = base + value
            scene.keyframe_insert(
                data_path="view_settings.exposure", frame=start + round(t * (end - start))
            )
