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
import os
import subprocess
import time
import json
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

def makeBashSafe(string):
    # protects against file names that would cause problems with bash calls
    if string.startswith(".") or string.startswith("-"):
        string = "_" + string[1:]
    # replaces problematic characters in shell with underscore '_'
    chars = "!#$&'()*,;<=>?[]^`{|}~: "
    for char in chars:
        string = string.replace(char, "\\" + char)
    return string

linesToAddAtBeginning = [
    "import bpy\n",
    "import json\n",
    # "if bpy.data.filepath == '':\n",
    # "    for obj in bpy.data.objects:\n",
    # "        obj.name = 'background_removed'\n",
    # "    for mesh in bpy.data.meshes:\n",
    # "        mesh.name = 'background_removed'\n",
    "data_blocks = list()\n",
    "python_data = list()\n",
    "def appendFrom(typ, filename):\n",
    "    directory = os.path.join(sourceBlendFile, typ)\n",
    "    filepath = os.path.join(directory, filename)\n",
    "    bpy.ops.wm.append(\n",
    "        filepath=filepath,\n",
    "        filename=filename,\n",
    "        directory=directory)\n",
    "### DO NOT EDIT ABOVE THESE LINES\n\n\n",
]
linesToAddAtEnd = [
    "\n\n### DO NOT EDIT BELOW THESE LINES\n",
    "assert None not in data_blocks  # ensures that all data from data_blocks exists\n",
    # write Blender data blocks to library in temp location 'storagePath'
    "if os.path.exists(storagePath):\n",
    "    os.remove(storagePath)\n",
    "bpy.data.libraries.write(storagePath, set(data_blocks), fake_user=True)\n",
    # write python data to library in temp location 'storagePath'
    "data_file = open(storagePath.replace('.blend', '.py'), 'w')\n",
    "print(json.dumps(python_data), file=data_file)\n",
]

def getElapsedTime(startTime, endTime, precision:int=2):
    """From seconds to Days;Hours:Minutes;Seconds"""
    value = endTime-startTime

    valueD = (((value/365)/24)/60)
    Days = int(valueD)

    valueH = (valueD-Days)*365
    Hours = int(valueH)

    valueM = (valueH - Hours)*24
    Minutes = int(valueM)

    valueS = (valueM - Minutes)*60
    Seconds = round(valueS, precision)

    outputString = str(Days) + ";" + str(Hours) + ":" + str(Minutes) + ";" + str(Seconds)
    return outputString


def addLines(script, fullPath, sourceBlendFile, passed_data):
    src=open(script,"r")
    oline=src.readlines()
    for line in linesToAddAtBeginning[::-1]:
        oline.insert(0, line)
    oline.insert(0, "storagePath = os.path.join(*%(fullPath)s)\n" % locals())
    oline.insert(0, "sourceBlendFile = os.path.join(*%(sourceBlendFile)s)\n" % locals())
    oline.insert(0, "import os\n" % locals())
    for key in passed_data:
        value = passed_data[key]
        value_str = str(value) if type(value) != str else "'%(value)s'" % locals()
        oline.insert(0, "%(key)s = %(value_str)s\n" % locals())
    for line in linesToAddAtEnd:
        oline.append(line)
    src.close()
    return oline


class JobManager():
    """ Manages and distributes jobs for all available workers """

    ################################################
    # initialization method

    def __init__(self):
        scn = bpy.context.scene
        # initialize vars
        self.temp_path = os.path.abspath(os.path.join(*[os.path.abspath(os.sep), "tmp", "background_processing"]))
        self.jobs = list()
        self.passed_data = dict()
        self.uses_blend_file = dict()
        self.job_processes = dict()
        self.job_statuses = dict()
        self.job_paths = dict()
        self.retrieved_data = dict()
        self.stop_now = False
        self.blendfile_paths = dict()
        # create '/tmp/background_processing/' path if necessary
        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)

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
        if index not in JobManager.instance:
            JobManager.instance[index] = JobManager()
        return JobManager.instance[index]

    def add_job(self, job:str, script:str, passed_data:dict={}, use_blend_file:bool=True, overwrite_blend:bool=True):
        # ensure blender file is saved
        if bpy.path.basename(bpy.data.filepath) == "":
            raise RuntimeError("'bpy.data.filepath' is empty, please save the Blender file")
        # cleanup the job if it already exists
        if job in self.jobs:
            self.cleanup_job(job)
        # add job to the queue
        self.jobs.append(job)
        self.job_paths[job] = self.get_job_path(script, hash=job)
        self.blendfile_paths[job] = os.path.abspath(os.path.join(self.temp_path, bpy.path.basename(bpy.data.filepath)))
        self.passed_data[job] = passed_data
        self.uses_blend_file[job] = use_blend_file
        # save the active blend file to be used in Blender instance
        if use_blend_file and (not os.path.exists(self.blendfile_paths[job]) or overwrite_blend):
            bpy.ops.wm.save_as_mainfile(filepath=self.blendfile_paths[job], compress=False, copy=True)
        # insert final blend file name to top of files
        fullPath = str(splitpath(os.path.join(self.temp_path, "%(job)s_data.blend" % locals())))
        sourceBlendFile = str(splitpath(bpy.data.filepath))
        # add storage path and additional passed data to lines in job file in READ mode
        lines = addLines(script, fullPath, sourceBlendFile, self.passed_data[job])
        # write text to job file in WRITE mode
        src=open(self.job_paths[job],"w")
        src.writelines(lines)
        src.close()
        return True

    def start_job(self, job:str, debug_level:int=0):
        # send job string to background blender instance with subprocess
        attempts = 1 if job not in self.job_statuses.keys() else (self.job_statuses[job]["attempts"] + 1)
        binary_path = makeBashSafe(bpy.app.binary_path)
        blendfile_path = makeBashSafe(self.blendfile_paths[job]) if self.uses_blend_file[job] else ""
        temp_job_path = makeBashSafe(self.job_paths[job])
        # TODO: Choose a better exit code than 155
        thread_func = "%(binary_path)s %(blendfile_path)s -b --python-exit-code 155 -P %(temp_job_path)s" % locals()
        self.job_processes[job] = subprocess.Popen(thread_func, stdout=subprocess.PIPE if debug_level < 2 else None, stderr=subprocess.PIPE if debug_level in (0, 2) else None, shell=True)
        self.job_statuses[job] = {"returncode":None, "stdout":None, "stderr":None, "start_time":time.time(), "end_time":None, "attempts":attempts}
        self.retrieved_data[job] = {"retrieved_data_blocks":None, "retrieved_python_data":None}
        print("JOB STARTED:  ", job)

    def process_job(self, job:str, debug_level:int=0):
        # check if job has been started
        if not self.job_started(job) or (self.job_statuses[job]["returncode"] not in (None, 0) and self.job_statuses[job]["attempts"] < self.max_attempts):
            # start job if background worker available
            if len(self.job_processes) < self.max_workers:
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
            job_status["end_time"] = time.time()
            job_status["returncode"] = job_process.returncode
            stdout_lines = tuple() if job_process.stdout is None else job_process.stdout.readlines()
            stderr_lines = tuple() if job_process.stderr is None else job_process.stderr.readlines()
            job_status["stdout"] = [line.decode("ASCII")[:-1] for line in stdout_lines]
            job_status["stderr"] = [line.decode("ASCII")[:-1] for line in stderr_lines]
            print("JOB CANCELLED:" if job_process.returncode != 0 else "JOB ENDED:    ", job, " (returncode:" + str(job_process.returncode) + ")" if job_process.returncode != 0 else "(time elapsed:" + getElapsedTime(job_status["start_time"], job_status["end_time"]) + ")")
            # if job was successful, retrieve any saved blend data
            if job_process.returncode == 0:
                self.retrieve_data(job)

    def process_jobs(self):
        for job in self.jobs:
            if self.jobs_complete():
                break
            self.process_job(job)

    def retrieve_data(self, job:str):
        # retrieve python data stored to temp directory
        dataFilePath = os.path.join(self.temp_path, "%(job)s_data.py" % locals())
        dumpedDict = open(dataFilePath, "r").readline()
        self.retrieved_data[job]["retrieved_python_data"] = json.loads(dumpedDict) if dumpedDict != "" else {}
        # retrieve blend data stored to temp directory
        fullBlendPath = os.path.join(self.temp_path, "%(job)s_data.blend" % locals())
        with bpy.data.libraries.load(fullBlendPath) as (data_from, data_to):
            for attr in dir(data_to):
                setattr(data_to, attr, getattr(data_from, attr))
        self.retrieved_data[job]["retrieved_data_blocks"] = data_to

    def get_job_path(self, script:str, hash:str):
        job_name = os.path.basename(script)
        name, ext = os.path.splitext(job_name)
        new_job_name = "{name}_{hash}{ext}".format(name=name, hash=hash, ext=ext)
        return os.path.join(self.temp_path, new_job_name)

    def get_job_names(self):
        return self.jobs

    def get_job_status(self, job:str):
        return self.job_statuses[job]

    def get_retrieved_python_data(self, job:str):
        return self.retrieved_data[job]["retrieved_python_data"]

    def get_retrieved_data_blocks(self, job:str):
        return self.retrieved_data[job]["retrieved_data_blocks"]

    def get_issue_string(self, job:str):
        if not self.job_dropped(job): return ""
        if self.job_timed_out(job):
            errormsg = "\nJob '%(job)s' timed out\n\n" % locals()
        else:
            errormsg = "\n------ ISSUE WITH BACKGROUND PROCESSOR ------\n\n"
            stderr = self.get_job_status(job)["stderr"]
            stdout = self.get_job_status(job)["stdout"]
            errormsg += "[stderr]\n" if len(stderr) > 0 else "[stdout]\n"
            for line in stderr if len(stderr) > 0 else stdout:
                if line.startswith("\r"):
                    errormsg = errormsg[:last_msg_len]
                last_msg_len = len(errormsg)
                errormsg += line + "\n"
            errormsg += "\n---------------------------------------------\n"
        return errormsg

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
        for job in self.jobs.copy():
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
        if job in self.retrieved_data:
            del self.retrieved_data[job]

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
