#!/usr/bin/env python

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

jobs = [
    '/Users/cgear13/scripts/patrick_moore/background_processing/test_scripts/test1.py',
    # '/Users/cgear13/scripts/patrick_moore/background_processing/test_scripts/test2.py',
    # '/Users/cgear13/scripts/patrick_moore/background_processing/test_scripts/test3.py',
    # '/Users/cgear13/scripts/patrick_moore/background_processing/test_scripts/test4.py',
    ]

class SCENE_OT_job_manager(Operator):
    """ Manages and distributes jobs for all available hosts """
    bl_idname = "scene.job_manager"
    bl_label = "Background Processor"
    bl_description = "Popup menu to check and display current updates available"
    bl_options = {'REGISTER'}

    ################################################
    # Blender Operator methods

    def execute(self, context):
        if self.projectName == "":
            self.report({"WARNING"}, "Please save your Blender file before running a background process")
            return {"CANCELLED"}
        self.process_jobs()
        # create timer for modal
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, context.window)
        wm.modal_handler_add(self)
        return{"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "ESC":
            self.kill_all()
            self.report({"INFO"}, "Background Process cancelled")
            return {"FINISHED"}
        elif self.jobs_complete() or self.stop_now:
            self.retrieve_data()
            return {"FINISHED"}
        elif time.time() - self.start_time > self.time_limit:
            self.kill_all()
            self.report({"INFO"}, "Background Process timed out")
            return {"FINISHED"}
        elif event.type == "TIMER":
            self.process_jobs()
        return {"PASS_THROUGH"}

    def cancel(self, context):
        self.kill_all()

    ################################################
    # initialization method

    def __init__(self):
        # initialize vars
        self.start_time = time.time()
        self.path = "/tmp/background_processing/"
        self.jobs = jobs
        self.job_processes = dict()
        self.stop_now = False
        self.blendfile = bpy.data.filepath
        self.projectName = bashSafeName(bpy.path.display_name_from_filepath(bpy.data.filepath))
        # create temp background_processing path if necessary
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    ###################################################
    # class variables

    time_limit = FloatProperty(default=10)

    #############################################
    # class methods

    def start_job(self, job):
        setup_job(job, self.blendfile)
        # send job string to background blender instance with subprocess
        thread_func = "/Applications/Blender/blender.app/Contents/MacOS/blender -b -P %(job)s" % locals()
        self.job_processes[job] = subprocess.Popen(thread_func, shell=True)#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("JOB STARTED:", job.split("/")[-1].split(".")[0])

    def add_job(self, job):
        self.jobs.append(job)

    def process_jobs(self):
        try:
            for job in self.jobs:
                if self.jobs_complete() or self.stop_now:
                    break
                if not job_started(job):
                    self.start_job(self, job)
                    continue
                job_process = self.job_processes[job]
                if type(job_process) == dict:
                    continue
                job_process.poll()
                if job_process.returncode == None:
                    continue
                elif job_process.returncode != 0:
                    print("JOB CANCELLED: ", job.split("/")[-1].split(".")[0], " (returncode:" + str(job_process.returncode) + ")")
                    # for rl in job_process.stderr.readlines():
                    #     print(rl.decode("ASCII"), end="")
                    self.job_processes[job] = dict()
                else:
                    print("JOB ENDED:  ", job.split("/")[-1].split(".")[0], " (returncode:" + str(job_process.returncode) + ")")
                    # for rl in job_process.stdout.readlines():
                    #     print(rl.decode("ASCII"), end="")
                    self.job_processes[job] = dict()
        except (KeyboardInterrupt, SystemExit):
            self.kill_all()

    def job_started(self, job):
        return job in self.job_processes.keys()

    def job_complete(self, job):
        return job in self.job_processes and type(self.job_processes[job]) == dict

    def jobs_complete(self):
        for job in self.jobs:
            if not self.job_complete(job):
                return False
        return True

    def kill_all(self):
        self.stop_now = True
        for job_key in self.job_processes.keys():
            job_process = self.job_processes[job_key]
            if type(job_process) != dict:
                job_process.kill()

    def stop(self):
        self.stop_now = True

    def retrieve_data(self):
        for job in self.jobs:
            blendFileName = job.split("/")[-1].split(".")[0] + ".blend"
            fullBlendPath = os.path.join(self.path, blendFileName)
            with bpy.data.libraries.load(fullBlendPath) as (data_from, data_to):
                for attr in dir(data_to):
                    setattr(data_to, attr, getattr(data_from, attr))
        self.report({"INFO"}, "Background process completed... Data retrieved!")

    ###################################################

# def register():
#     bpy.utils.register_module(__name__)
#
# def unregister():
#     bpy.utils.unregister_module(__name__)
