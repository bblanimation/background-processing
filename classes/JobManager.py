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
import sys

# Blender imports
import bpy
from bpy.types import Operator
from bpy.props import *

def splitpath(path):
    folders = []
    while 1:
        path, folder = os.path.split(path)
        if folder != "":
            folders.append(folder)
        else:
            if path != "": folders.append(path)
            break
    return folders[::-1]


class SCENE_OT_job_manager():
    """ Manages and distributes jobs for all available workers """

    ################################################
    # initialization method

    def __init__(self):
        scn = bpy.context.scene
        # initialize vars
        self.path = os.path.join(*["/", "tmp", "background_processing"][0 if sys.platform in ("linux", "linux2", "darwin") else 1:])
        self.jobs = list()
        self.passed_data = dict()
        self.uses_blend_file = dict()
        self.job_processes = dict()
        self.job_statuses = dict()
        self.stop_now = False
        self.blendfile_paths = dict()
        # create '/tmp/background_processing/' path if necessary
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    ###################################################
    # class variables

    instance = dict()
    timeout = 0  # amount of time to wait before killing the process (0 for infinite)
    max_workers = 5  # maximum number of blender instances to run at once
    max_attempts = 1  # maximum number of times the background processor will attempt to run a job if error occurs

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
        fullPath = str(splitpath(os.path.join(self.path, dataBlendFileName)))
        sourceBlendFile = str(splitpath(bpy.data.filepath))
        # add storage path and additional passed data to lines in job file in READ mode
        src=open(job,"r")
        oline=src.readlines()
        while not oline[0].startswith("#**"):
            oline.pop(0)
        oline.insert(0, "storagePath = os.path.join(*%(fullPath)s)  # DO NOT DELETE THIS LINE\n" % locals())
        oline.insert(0, "sourceBlendFile = os.path.join(*%(sourceBlendFile)s)  # DO NOT DELETE THIS LINE\n" % locals())
        oline.insert(0, "import os\n")
        for key in self.passed_data[job]:
            value = self.passed_data[job][key]
            value_str = str(value) if type(value) != str else "'%(value)s'" % locals()
            oline.insert(0, "%(key)s = %(value_str)s  # DO NOT DELETE THIS LINE\n" % locals())
        src.close()
        # write text to job file in WRITE mode
        src=open(job,"w")
        src.writelines(oline)
        src.close()

    def start_job(self, job:str, debug_level:int=0):
        # send job string to background blender instance with subprocess
        attempts = 1 if job not in self.job_statuses.keys() else (self.job_statuses[job]["attempts"] + 1)
        binary_path = bpy.app.binary_path
        blendfile_path = self.blendfile_paths[job].replace(" ", "\\ ") if self.uses_blend_file[job] else ""
        bash_safe_job = job.replace(" ", "\\ ")
        # TODO: Choose a better exit code than 155
        thread_func = "%(binary_path)s %(blendfile_path)s -b --python-exit-code 155 -P %(bash_safe_job)s" % locals()
        if debug_level == 0:
            self.job_processes[job] = subprocess.Popen(thread_func, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        elif debug_level == 1:
            self.job_processes[job] = subprocess.Popen(thread_func, stdout=subprocess.PIPE, shell=True)
        elif debug_level == 2:
            self.job_processes[job] = subprocess.Popen(thread_func, stderr=subprocess.PIPE, shell=True)
        else:
            self.job_processes[job] = subprocess.Popen(thread_func, shell=True)
        self.job_statuses[job] = {"returncode":None, "stdout":None, "stderr":None, "start_time":time.time(), "attempts":attempts}
        print("JOB STARTED:  ", self.get_job_name(job))

    def add_job(self, job:str, passed_data:dict={}, use_blend_file:bool=False, overwrite_blend:bool=True):
        if bpy.path.basename(bpy.data.filepath) == "":
            raise RuntimeError("'bpy.data.filepath' is empty, please save the Blender file")
        self.blendfile_paths[job] = os.path.join(self.path, bpy.path.basename(bpy.data.filepath))
        # cleanup the job if it already exists
        if job in self.jobs:
            self.cleanup_job(job)
        # add job to the queue
        self.jobs.append(job)
        self.passed_data[job] = passed_data
        # save the active blend file to be used in Blender instance
        if use_blend_file and (not os.path.exists(self.blendfile_paths[job]) or overwrite_blend):
            bpy.ops.wm.save_as_mainfile(filepath=self.blendfile_paths[job], copy=True)
        self.uses_blend_file[job] = use_blend_file
        return True

    def process_jobs(self):
        for job in self.jobs:
            if self.jobs_complete():
                break
            self.process_job(job)

    def process_job(self, job:str, debug_level:int=0):
        # check if job has been started
        if not self.job_started(job) or (self.job_statuses[job]["returncode"] not in (None, 0) and self.job_statuses[job]["attempts"] < self.max_attempts):
            # start job if background worker available
            if len(self.job_processes) < self.max_workers:
                self.setup_job(job)
                self.start_job(job, debug_level=debug_level)
            return
        job_status = self.job_statuses[job]
        # check if job already processed
        if job_status["returncode"] is not None:
            return
        # check if job has exceeded the time limit
        elif self.timeout > 0 and time.time() - job_status["start_time"] > self.timeout:
            self.kill_job(job)
        job_process = self.job_processes[job]
        job_process.poll()
        # check if job process still running
        if job_process.returncode is None:
            return
        else:
            self.job_processes.pop(job)
            # record status of completed job process
            job_status["returncode"] = job_process.returncode
            stdout_lines = tuple() if job_process.stdout is None else job_process.stdout.readlines()
            stderr_lines = tuple() if job_process.stderr is None else job_process.stderr.readlines()
            job_status["stdout"] = [line.decode("ASCII")[:-1] for line in stdout_lines]
            job_status["stderr"] = [line.decode("ASCII")[:-1] for line in stderr_lines]
            print("JOB CANCELLED:" if job_process.returncode != 0 else "JOB ENDED:    ", self.get_job_name(job), " (returncode:" + str(job_process.returncode) + ")")
            # if job was successful, retrieve any saved blend data
            if job_process.returncode == 0:
                self.retrieve_data(job)

    def retrieve_data(self, job:str):
        # retrieve blend data stored to temp directory
        dataBlendFileName = self.get_job_name(job) + "_data.blend"
        fullBlendPath = os.path.join(self.path, dataBlendFileName)
        with bpy.data.libraries.load(fullBlendPath) as (data_from, data_to):
            for attr in dir(data_to):
                setattr(data_to, attr, getattr(data_from, attr))

    @staticmethod
    def get_job_name(job:str):
        return os.path.splitext(os.path.basename(job))[0]

    def get_job_status(self, job:str):
        return self.job_statuses[job]

    def job_started(self, job:str):
        return job in self.job_statuses.keys()

    def job_complete(self, job:str):
        return job in self.job_statuses and self.job_statuses[job]["returncode"] == 0

    def job_dropped(self, job:str):
        return job in self.job_statuses and self.job_statuses[job]["attempts"] == self.max_attempts and self.job_statuses[job]["returncode"] not in (None, 0)

    def job_timed_out(self, job:str):
        return job in self.job_statuses and self.job_statuses[job]["attempts"] == self.max_attempts and self.job_statuses[job]["returncode"] == -9

    def jobs_complete(self):
        for job in self.jobs:
            if not self.job_complete(job):
                return False
        return True

    def kill_job(self, job:str):
        self.job_processes[job].kill()

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
