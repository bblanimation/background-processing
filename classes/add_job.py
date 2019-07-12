# Copyright (C) 2019 Christopher Gearhart
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
from .job_manager import *

demo_scripts_path = join(dirname(dirname(abspath(__file__))), "demo_scripts")
scripts = [
    join(demo_scripts_path, "test1.py"),
    join(demo_scripts_path, "test2.py"),
    join(demo_scripts_path, "test3.py"),
    join(demo_scripts_path, "test4.py"),
    ]

class SCENE_OT_add_job(Operator):
    """ Adds a job """
    bl_idname = "backproc.add_job"
    bl_label = "Add Job"
    bl_description = "Adds a job"
    bl_options = {"REGISTER"}

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
        # NOTE: Job will run until it is finished or until it times out (specify timeout in seconds; 0 for infinite)
        job_added, msg = self.job_manager.add_job(self.job["name"], timeout=17.5, script=self.job["script"], use_blend_file=False, passed_data={"objName":self.obj.name, "mesh_name":self.obj.data.name})
        if not job_added:
            raise Exception(msg)
            return {"CANCELLED"}
        # create timer for modal
        wm = context.window_manager
        if self._timer is None:
            self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return{"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "TIMER":
            self.job_manager.process_job(self.job["name"], debug_level=3)
            if self.job_manager.job_complete(self.job["name"]):
                self.report({"INFO"}, "Background process '{job_name}' was finished".format(job_name=self.job["name"]))
                retrieved_data_blocks = self.job_manager.get_retrieved_data_blocks(self.job["name"])
                retrieved_python_data = self.job_manager.get_retrieved_python_data(self.job["name"])
                print(retrieved_data_blocks.objects)
                print(retrieved_python_data)
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                self._timer = None
                tag_redraw_areas()
                return {"FINISHED"}
            elif self.job_manager.job_dropped(self.job["name"]):
                if self.job_manager.job_timed_out(self.job["name"]):
                    self.report({"WARNING"}, "Background process '{job_name}' timed out".format(job_name=self.job["name"]))
                elif self.job_manager.job_killed(self.job["name"]):
                    self.report({"WARNING"}, "Background process '{job_name}' was killed".format(job_name=self.job["name"]))
                else:
                    self.report({"WARNING"}, "Background process '{job_name}' failed".format(job_name=self.job["name"]))
                    errormsg = self.job_manager.get_issue_string(self.job["name"])
                    print(errormsg)
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                self._timer = None
                tag_redraw_areas()
                return {"CANCELLED"}
            else:
                tag_redraw_areas()
        return {"PASS_THROUGH"}

    def cancel(self, context):
        self.job_manager.kill_job(self.job["name"])
        self.JobManager.kill_job(self.job["name"])
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self._timer = None

    ################################################
    # initialization method

    def __init__(self):
        self.obj = bpy.context.object
        script = scripts[self.job_index]
        self.job = {"name":os.path.basename(script) + "_" + self.obj.name, "script":script}
        self.job_manager = JobManager.get_instance(-1)
        self.JobManager.max_workers = bpy.context.scene.backproc_max_workers

    ###################################################
    # class variables

    job_index = IntProperty(default=0)
    _timer = None

    ################################################
