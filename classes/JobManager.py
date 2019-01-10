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
import os
import subprocess
import time

# Blender imports
import bpy
from bpy.types import Operator
from bpy.props import *

# Addon imports
from ..functions import *

class SCENE_OT_job_manager(Operator):
    """ Manages and distributes jobs for all available workers """
    bl_idname = "scene.job_manager"
    bl_label = "Start the Job Manager"
    bl_description = "Manages and distributes jobs for all available workers"
    bl_options = {'REGISTER'}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        return not scn.backproc_job_manager_running

    def execute(self, context):
        if self.projectName == "":
            self.report({"WARNING"}, "Please save your Blender file before running a background process")
            return {"CANCELLED"}
        self.report({"INFO"}, "Running Job Manager")
        SCENE_OT_job_manager.instance = self
        # create timer for modal
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, context.window)
        wm.modal_handler_add(self)
        return{"RUNNING_MODAL"}

    def modal(self, context, event):
        if self.stop_now:
            return {"CANCELLED"}
        elif event.type == "ESC":
            self.kill_all()
            self.report({"INFO"}, "Background Process cancelled")
            return {"FINISHED"}
        elif event.type == "TIMER":
            self.process_jobs()
            self.update_exposed_values()
        return {"PASS_THROUGH"}

    def cancel(self, context):
        self.kill_all()

    ################################################
    # initialization method

    def __init__(self):
        scn = bpy.context.scene
        # initialize vars
        self.start_time = time.time()
        self.path = "/tmp/background_processing/"
        self.jobs = list()
        self.job_processes = dict()
        self.job_statuses = dict()
        self.stop_now = False
        self.sourceBlendFile = bpy.data.filepath
        self.projectName = bashSafeName(bpy.path.display_name_from_filepath(bpy.data.filepath))
        scn.backproc_job_manager_running = True
        # create temp background_processing path if necessary
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    ###################################################
    # class variables

    instance = None
    time_limit = FloatProperty(default=7)
    max_workers = IntProperty(default=2)
    max_attempts = IntProperty(default=2)

    #############################################
    # class methods

    @staticmethod
    def get_instance():
        if SCENE_OT_job_manager.instance is None:
            SCENE_OT_job_manager.instance = SCENE_OT_job_manager()
        return SCENE_OT_job_manager.instance

    def start_job(self, job):
        setup_job(job, self.path, self.sourceBlendFile)
        # send job string to background blender instance with subprocess
        attempts = 1 if job not in self.job_statuses.keys() else (self.job_statuses[job]["attempts"] + 1)
        # TODO: Choose a better exit code than 155
        thread_func = "/Applications/Blender/blender.app/Contents/MacOS/blender -b --python-exit-code 155 --factory-startup -P %(job)s" % locals()
        self.job_processes[job] = subprocess.Popen(thread_func, stdout=subprocess.PIPE, shell=True)  # stderr=subprocess.PIPE,
        self.job_statuses[job] = {"returncode":None, "lines":None, "start_time":time.time(), "attempts":attempts}
        print("JOB STARTED:  ", self.get_job_name(job))

    def add_job(self, job):
        if job in self.jobs:
            return False
        self.jobs.append(job)
        return True

    def process_jobs(self):
        try:
            for job in self.jobs:
                if self.jobs_complete() or self.stop_now:
                    break
                if not self.job_started(job) or (self.job_statuses[job]["returncode"] is not None and self.job_statuses[job]["returncode"] != 0 and self.job_statuses[job]["attempts"] < self.max_attempts):
                    if len(self.job_processes) < self.max_workers:
                        self.start_job(job)
                    continue
                job_status = self.job_statuses[job]
                if job_status["returncode"] is not None:
                    continue
                elif time.time() - job_status["start_time"] > self.time_limit:
                    self.kill_job(job)
                job_process = self.job_processes[job]
                job_process.poll()
                if job_process.returncode is None:
                    continue
                else:
                    self.job_processes.pop(job)
                    job_status["returncode"] = job_process.returncode
                    msgObject = job_process.stdout if job_process.returncode == 0 else job_process.stderr
                    lines = tuple() if msgObject is None else msgObject.readlines()
                    job_status["lines"] = [line.decode("ASCII") for line in lines]
                    print("JOB CANCELLED:" if job_process.returncode != 0 else "JOB ENDED:    ", self.get_job_name(job), " (returncode:" + str(job_process.returncode) + ")")
                    if job_process.returncode == 0:
                        self.retrieve_data(job)
        except (KeyboardInterrupt, SystemExit):
            self.kill_all()

    @staticmethod
    def get_job_name(job):
        return job.split("/")[-1].split(".")[0]

    def job_started(self, job):
        return job in self.job_statuses.keys()

    def job_complete(self, job):
        return job in self.job_statuses and self.job_statuses[job]["returncode"] == 0

    def job_dropped(self, job):
        return job in self.job_statuses and self.job_statuses[job]["attempts"] == self.max_attempts and self.job_statuses[job]["returncode"] is not None

    def jobs_complete(self):
        for job in self.jobs:
            if not self.job_complete(job):
                return False
        return True

    def kill_all(self):
        for job in self.job_processes.keys():
            self.kill_job(job)
        self.stop()
        self.reset_exposed_values()

    def kill_job(self, job):
        self.job_processes[job].kill()

    def stop(self):
        scn = bpy.context.scene
        self.stop_now = True
        scn.backproc_job_manager_running = False

    def retrieve_data(self, job):
        sourceBlendFileName = self.get_job_name(job) + ".blend"
        fullBlendPath = os.path.join(self.path, sourceBlendFileName)
        with bpy.data.libraries.load(fullBlendPath) as (data_from, data_to):
            for attr in dir(data_to):
                setattr(data_to, attr, getattr(data_from, attr))
        self.report({"INFO"}, "Background process '" + self.get_job_name(job) + "' completed... Data retrieved!")

    def reset_exposed_values(self):
        scn = bpy.context.scene
        scn.backproc_available_workers = self.max_workers
        scn.backproc_pending_jobs = 0
        scn.backproc_running_jobs = 0
        tag_redraw_areas("VIEW_3D")

    def update_exposed_values(self):
        scn = bpy.context.scene
        scn.backproc_available_workers = self.num_available_workers()
        scn.backproc_pending_jobs = self.num_pending_jobs()
        scn.backproc_running_jobs = self.num_running_jobs()
        scn.backproc_completed_jobs = self.num_completed_jobs()
        scn.backproc_dropped_jobs = self.num_dropped_jobs()
        tag_redraw_areas("VIEW_3D")

    def num_available_workers(self):
        return self.max_workers - len(self.job_processes)

    def num_pending_jobs(self):
        return len(self.jobs) - len(self.job_statuses)

    def num_running_jobs(self):
        return len(self.job_processes)

    def num_completed_jobs(self):
        return [self.job_complete(job) for job in self.jobs].count(True)

    def num_dropped_jobs(self):
        return [self.job_dropped(job) for job in self.jobs].count(True)

    ###################################################
