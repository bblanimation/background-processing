# Copyright (C) 2018 Christopher Gearhart
# chris@bblanimation.com
# http://bblanimation.com/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name"        : "Background Processing",
    "author"      : "Christopher Gearhart <chris@bblanimation.com>",
    "version"     : (1, 0, 0),
    "blender"     : (2, 80, 0),
    "description" : "Process in the background with a separate instance of Blender",
    "location"    : "View3D > Tools > Bricker",
    "warning"     : "",  # used for warning icon and text in addons panel
    "wiki_url"    : "",
    "tracker_url" : "",
    "category"    : "Object"}

import bpy
from bpy.types import Scene

from .classes import *
from .ui import *

def register():
    bpy.utils.register_class(SCENE_OT_add_job)
    bpy.utils.register_class(BACKGROUND_PT_interface)
    def updateMaxWorkers(self, context):
        JobManager = JobManager.get_instance()
        JobManager.max_workers = context.scene.backproc_max_workers
    Scene.backproc_max_workers = IntProperty(
        name="Maximum Workers",
        description="Maximum number of Blender instances to run in the background",
        min=0, max=100,
        update=updateMaxWorkers,
        default=5)

def unregister():
    del Scene.backproc_max_workers
    bpy.utils.unregister_class(BACKGROUND_PT_interface)
    bpy.utils.unregister_class(SCENE_OT_add_job)
