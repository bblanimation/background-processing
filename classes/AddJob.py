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

# System imports
from os.path import join, dirname, abspath

# Blender imports
import bpy
from bpy.types import Operator

# Addon imports
from .JobManager import *

demo_scripts_path = join(dirname(dirname(abspath(__file__))), "demo_scripts")
jobs = [
    join(demo_scripts_path, "test1.py"),
    join(demo_scripts_path, "test2.py"),
    join(demo_scripts_path, "test3.py"),
    join(demo_scripts_path, "test4.py"),
    ]

class SCENE_OT_add_job(Operator):
    """ Adds a job """
    bl_idname = "scene.add_job"
    bl_label = "Add Job"
    bl_description = "Adds a job"
    bl_options = {'REGISTER'}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        return bpy.context.object is not None

    def execute(self, context):
        if bpy.data.filepath == "":
            self.report({"WARNING"}, "Please save the file first")
            return {"CANCELLED"}
        # NOTE: Set 'use_blend_file' to True to access data from the current blend file in script (False to execute script from default startup)
        jobAdded = self.JobManager.add_job(jobs[self.job_index], use_blend_file=True, passed_data={"objName":self.targetObjName})
        if not jobAdded:
            self.report({"WARNING"}, "Job already added")
            return {"CANCELLED"}
        # create timer for modal
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, context.window)
        wm.modal_handler_add(self)
        return{"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "TIMER":
            self.JobManager.process_job(self.job, debug_level=4)
            job_name = self.JobManager.get_job_name(self.job)
            if self.JobManager.job_complete(self.job):
                self.report({"INFO"}, "Background process '%(job_name)s' was finished" % locals())
                return {"FINISHED"}
            if self.JobManager.job_dropped(self.job):
                if self.JobManager.job_timed_out(self.job):
                    self.report({"WARNING"}, "Background process '%(job_name)s' timed out" % locals())
                else:
                    self.report({"WARNING"}, "Background process '%(job_name)s' was dropped" % locals())
                return {"CANCELLED"}
        return {"PASS_THROUGH"}

    def cancel(self, context):
        self.JobManager.kill_job(self.job)

    ################################################
    # initialization method

    def __init__(self):
        self.job = jobs[self.job_index]
        self.JobManager = SCENE_OT_job_manager.get_instance(-1)
        self.JobManager.max_workers = 5
        self.JobManager.timeout = 7
        self.targetObjName = bpy.context.object.name

    ###################################################
    # class variables

    job_index = IntProperty(default=0)

    ################################################
