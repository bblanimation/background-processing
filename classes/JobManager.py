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

class SCENE_OT_job_manager():
    """ Manages and distributes jobs for all available workers """

    ################################################
    # initialization method

    def __init__(self):
        scn = bpy.context.scene
        # initialize vars
        self.path = "/tmp/background_processing/"
        self.jobs = list()
        self.passed_data = dict()
        self.uses_blend_file = dict()
        self.job_processes = dict()
        self.job_statuses = dict()
        self.stop_now = False
        self.sourceBlendFile = bpy.data.filepath
        self.blendfile_path = os.path.join(self.path, bpy.path.basename(bpy.data.filepath))
        # create '/tmp/background_processing/' path if necessary
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    ###################################################
    # class variables

    instance = dict()
    timeout = 0
    max_workers = 5
    max_attempts = 2

    #############################################
    # class methods

    @staticmethod
    def get_instance(index=0):
        if index not in SCENE_OT_job_manager.instance:
            SCENE_OT_job_manager.instance[index] = SCENE_OT_job_manager()
        return SCENE_OT_job_manager.instance[index]

    def setup_job(self, job:str):
        # insert final blend file name to top of files
        dataBlendFileName = self.get_job_name(job) + "_data.blend"
        fullPath = os.path.join(self.path, dataBlendFileName)
        sourceBlendFile = self.sourceBlendFile
        # add new storage path to lines in job file in READ mode
        src=open(job.replace("\\", ""),"r")
        oline=src.readlines()
        while not oline[0].startswith("#**"):
            oline.pop(0)
        oline.insert(0, "storagePath = '%(fullPath)s'  # DO NOT DELETE THIS LINE\n" % locals())
        oline.insert(0, "sourceBlendFile = '%(sourceBlendFile)s'  # DO NOT DELETE THIS LINE\n" % locals())
        for key in self.passed_data[job]:
            value = self.passed_data[job][key]
            value_str = str(value) if type(value) != str else "'%(value)s'" % locals()
            oline.insert(0, "%(key)s = %(value_str)s  # DO NOT DELETE THIS LINE\n" % locals())
        src.close()
        # write text to job file in WRITE mode
        src=open(job.replace("\\", ""),"w")
        src.writelines(oline)
        src.close()

    def start_job(self, job:str, debug:bool=False):
        # send job string to background blender instance with subprocess
        attempts = 1 if job not in self.job_statuses.keys() else (self.job_statuses[job]["attempts"] + 1)
        # TODO: Choose a better exit code than 155
        binary_path = bpy.app.binary_path
        blendfile_path = self.blendfile_path.replace(" ", "\\ ") if self.uses_blend_file[job] else ""
        bash_safe_job = job.replace(" ", "\\ ")
        thread_func = "%(binary_path)s %(blendfile_path)s -b --python-exit-code 155 -P %(bash_safe_job)s" % locals()
        if debug:
            self.job_processes[job] = subprocess.Popen(thread_func, shell=True)
        else:
            self.job_processes[job] = subprocess.Popen(thread_func, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        self.job_statuses[job] = {"returncode":None, "stdout":None, "stderr":None, "start_time":time.time(), "attempts":attempts}
        print("JOB STARTED:  ", self.get_job_name(job))

    def add_job(self, job:str, passed_data:dict={}, use_blend_file:bool=False, overwrite_blend:bool=True):
        if job in self.jobs:
            self.cleanup_job(job)
        self.jobs.append(job.replace("\\", ""))
        self.passed_data[job] = passed_data
        if use_blend_file and (not os.path.exists(self.blendfile_path) or overwrite_blend):
            bpy.ops.wm.save_as_mainfile(filepath=self.blendfile_path, copy=True)
        self.uses_blend_file[job] = use_blend_file
        return True

    def process_jobs(self):
        try:
            for job in self.jobs:
                if self.jobs_complete():
                    break
                self.process_job(job)
        except (KeyboardInterrupt, SystemExit):
            self.kill_all()

    def process_job(self, job:str, debug:bool=False):
        if not self.job_started(job) or (self.job_statuses[job]["returncode"] is not None and self.job_statuses[job]["returncode"] != 0 and self.job_statuses[job]["attempts"] < self.max_attempts):
            if len(self.job_processes) < self.max_workers:
                self.setup_job(job)
                self.start_job(job, debug=debug)
            return
        job_status = self.job_statuses[job]
        if job_status["returncode"] is not None:
            return
        elif self.timeout > 0 and time.time() - job_status["start_time"] > self.timeout:
            self.kill_job(job)
        job_process = self.job_processes[job]
        job_process.poll()
        if job_process.returncode is None:
            return
        else:
            self.job_processes.pop(job)
            job_status["returncode"] = job_process.returncode
            stdout_lines = tuple() if job_process.stdout is None else job_process.stdout.readlines()
            stderr_lines = tuple() if job_process.stderr is None else job_process.stderr.readlines()
            job_status["stdout"] = [line.decode("ASCII")[:-1] for line in stdout_lines]
            job_status["stderr"] = [line.decode("ASCII")[:-1] for line in stderr_lines]
            print("JOB CANCELLED:" if job_process.returncode != 0 else "JOB ENDED:    ", self.get_job_name(job), " (returncode:" + str(job_process.returncode) + ")")
            if job_process.returncode == 0:
                self.retrieve_data(job)

    def retrieve_data(self, job:str):
        dataBlendFileName = self.get_job_name(job) + "_data.blend"
        fullBlendPath = os.path.join(self.path, dataBlendFileName)
        with bpy.data.libraries.load(fullBlendPath) as (data_from, data_to):
            for attr in dir(data_to):
                setattr(data_to, attr, getattr(data_from, attr))

    @staticmethod
    def get_job_name(job:str):
        return job.split("/")[-1].split(".")[0]

    def get_job_status(self, job:str):
        return self.job_statuses[job]

    def job_started(self, job:str):
        return job in self.job_statuses.keys()

    def job_complete(self, job:str):
        return job in self.job_statuses and self.job_statuses[job]["returncode"] == 0

    def job_dropped(self, job:str):
        return job in self.job_statuses and self.job_statuses[job]["attempts"] == self.max_attempts and self.job_statuses[job]["returncode"] not in (None, 0)

    def jobs_complete(self):
        for job in self.jobs:
            if not self.job_complete(job):
                return False
        return True

    def kill_job(self, job:str):
        self.job_processes[job].kill()
        print("JOB KILLED:   ", self.get_job_name(job))

    def kill_all(self):
        for job in self.jobs:
            self.cleanup_job(job)

    def cleanup_job(self, job):
        assert job in self.jobs
        self.jobs.remove(job)
        del self.passed_data[job]
        if job in self.job_processes:
            self.kill_job(job)
            del self.job_processes[job]
        if job in self.job_statuses:
            del self.job_statuses[job]

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
