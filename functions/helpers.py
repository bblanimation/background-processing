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

# Blender imports
import bpy


def appendFrom(directory, filename):
    filepath = directory + filename
    bpy.ops.wm.append(
        filepath=filepath,
        filename=filename,
        directory=directory)


def bashSafeName(string):
    # protects against file names that would cause problems with bash calls
    if string.startswith(".") or string.startswith("-"):
        string = "_" + string[1:]
    # replaces problematic characters in shell with underscore '_'
    chars = "!#$&'()*,;<=>?[]^`{|}~: "
    for char in list(chars):
        string = string.replace(char, "_")
    return string

def setup_job(job, path, sourceBlendFile):
    # insert final blend file name to top of files
    sourceBlendFileName = job.split("/")[-1].split(".")[0] + ".blend"
    fullPath = os.path.join(path, sourceBlendFileName)
    # add new storage path to lines in job file in READ mode
    src=open(job,"r")
    oline=src.readlines()
    oline[0] = "storagePath = '%(fullPath)s'  # DO NOT DELETE THIS LINE\n" % locals()
    oline[1] = "sourceBlendFile = '%(sourceBlendFile)s'  # DO NOT DELETE THIS LINE\n" % locals()
    src.close()
    # write text to job file in WRITE mode
    src=open(job,"w")
    src.writelines(oline)
    src.close()
