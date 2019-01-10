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
    "blender"     : (2, 79, 0),
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
    bpy.utils.register_module(__name__)
    def updateMaxWorkers(self, context):
        if context.scene.backproc_job_manager_running:
            JobManager = SCENE_OT_job_manager.get_instance()
            JobManager.max_workers = context.scene.backproc_max_workers
    Scene.backproc_max_workers = IntProperty(
        name="Maximum Workers",
        description="Maximum number of Blender instances to run in the background",
        min=0, max=100,
        update=updateMaxWorkers,
        default=2)
    Scene.backproc_available_workers = IntProperty(default=0)
    Scene.backproc_pending_jobs = IntProperty(default=0)
    Scene.backproc_running_jobs = IntProperty(default=0)
    Scene.backproc_completed_jobs = IntProperty(default=0)
    Scene.backproc_dropped_jobs = IntProperty(default=0)
    Scene.backproc_job_manager_running = BoolProperty(default=False)

def unregister():
    del Scene.backproc_job_manager_running
    del Scene.backproc_dropped_jobs
    del Scene.backproc_completed_jobs
    del Scene.backproc_running_jobs
    del Scene.backproc_pending_jobs
    del Scene.backproc_available_workers
    del Scene.backproc_max_workers
    bpy.utils.unregister_module(__name__)
