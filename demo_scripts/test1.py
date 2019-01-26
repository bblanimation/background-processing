#** DO NOT DELETE THIS LINE OR EDIT THE LINES ABOVE **#

### DO NOT EDIT THESE LINES ###

import bpy
import os
if bpy.data.filepath == "":
    for obj in bpy.data.objects:
        obj.name = "background_removed"
    for mesh in bpy.data.meshes:
        mesh.name = "background_removed"
data_blocks = []
objDirectory = "%(sourceBlendFile)s/Object/" % locals()
meshDirectory = "%(sourceBlendFile)s/Mesh/" % locals()
def appendFrom(directory, filename):
    filepath = directory + filename
    bpy.ops.wm.append(
        filepath=filepath,
        filename=filename,
        directory=directory)

### WRITE YOUR PYTHON CODE HERE ###

import bmesh
import time

appendFrom(objDirectory, objName)
obj = bpy.data.objects.get(objName)
rMod = obj.modifiers.new(obj.name + '_remesh', 'REMESH')
m = obj.to_mesh(bpy.context.scene, True, 'PREVIEW')
m.name = objName + "_remesh"
time.sleep(4)

### SET 'data_blocks' EQUAL TO LIST OF OBJECT DATA TO BE SEND BACK TO THE BLENDER HOST ###

data_blocks = [m]

### DO NOT EDIT BEYOND THIS LINE ###

assert None not in data_blocks  # ensures that all data from data_blocks exists
if os.path.exists(storagePath):
    os.remove(storagePath)
bpy.data.libraries.write(storagePath, set(data_blocks), fake_user=True)
