storagePath = ''  # DO NOT DELETE THIS LINE
sourceBlendFile = ''  # DO NOT DELETE THIS LINE

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

# Pull objects and meshes from source file like this:
# appendFrom(objDirectory, "Cube")
# appendFrom(meshDirectory, "Cube")

obj = bpy.data.meshes.new("square_mesh_demo", m)
bm = bmesh.new()
v1 = bm.verts.new(( 2,  2, 0))
v2 = bm.verts.new((-2,  2, 0))
v3 = bm.verts.new((-2, -2, 0))
v4 = bm.verts.new(( 2, -2, 0))
f1 = bm.faces.new((v1, v2, v3, v4))
bm.to_mesh(m)

### SET 'data_blocks' EQUAL TO LIST OF OBJECT DATA TO BE SEND BACK TO THE BLENDER HOST ###

data_blocks = [m]

### DO NOT EDIT BEYOND THIS LINE ###

bpy.data.libraries.write(storagePath, set(data_blocks), fake_user=True)
