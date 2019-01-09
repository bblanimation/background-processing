storagePath = '/tmp/background_processing/test3.blend'  # DO NOT DELETE THIS LINE
sourceBlendFile = '/Users/cgear13/Desktop/deleteme.blend'  # DO NOT DELETE THIS LINE

### DO NOT EDIT THESE LINES ###

import bpy
for obj in bpy.data.objects:
    obj.name = "background_removed"
for mesh in bpy.data.meshes:
    mesh.name = "background_removed"
objDirectory = "%(sourceBlendFile)s/Object/" % locals()
meshDirectory = "%(sourceBlendFile)s/Mesh/" % locals()
data_blocks = []
def appendFrom(directory, filename):
    filepath = directory + filename
    bpy.ops.wm.append(
        filepath=filepath,
        filename=filename,
        directory=directory)

### WRITE YOUR PYTHON CODE HERE ###

import bmesh
import time

# Pull objects and meshes from source file like this:
# appendFrom(objDirectory, "Cube")
# appendFrom(meshDirectory, "Cube")

appendFrom(meshDirectory, "Cube")
m = bpy.data.meshes.get("Cube")
bm = bmesh.new()
bm.from_mesh(m)
v1 = bm.verts.new(( 2,  2, 0))
v2 = bm.verts.new((-2,  2, 0))
v3 = bm.verts.new((-2, -2, 0))
v4 = bm.verts.new(( 2, -2, 0))
f1 = bm.faces.new((v1, v2, v3, v4))
bm.to_mesh(m)
obj = bpy.data.objects.new("test_object", m)
time.sleep(6)

### SET 'data_blocks' EQUAL TO LIST OF OBJECT DATA YOU WISH TO STORE ###

data_blocks = [m]

### DO NOT EDIT BEYOND THIS LINE ###

bpy.data.libraries.write(storagePath, set(data_blocks), fake_user=True)
