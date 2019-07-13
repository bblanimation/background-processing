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

# Addon imports
from .common import *


lines_to_add_at_beginning = [
    # python imports
    "import bpy\n",
    "import marshal\n",
    "import os\n",
    # remove default objects & meshes
    "if bpy.data.filepath == '':\n",
    "    bpy.ops.wm.read_homefile(use_empty=True)\n",
    # initialize variables
    "data_blocks = list()\n",
    "python_data = list()\n",
    # functions to be used in background_processing scripts
    # "def append_from(typ, filename):\n",
    # "    directory = os.path.join(source_blend_file, typ)\n",
    # "    filepath = os.path.join(directory, filename)\n",
    # "    bpy.ops.wm.append(\n",
    # "        filepath=filepath,\n",
    # "        filename=filename,\n",
    # "        directory=directory)\n",
    "def update_job_progress(percent_complete):\n",
    "    assert type(percent_complete) in (int, float)\n"
    "    progress_file = open(target_path_base + '_progress.py', 'w')\n",
    "    print(percent_complete, file=progress_file, end='')\n",
    "    progress_file.close()\n",
    # retrieve passed data blocks
    "passed_data_block_infos = []\n",
    "passed_data_blocks = []\n",
    "if os.path.exists(sent_data_blocks_path):\n",
    "    with bpy.data.libraries.load(sent_data_blocks_path) as (data_from, data_to):\n",
    "        for attr in dir(data_to):\n",
    "            setattr(data_to, attr, getattr(data_from, attr))\n",
    "            for item in getattr(data_from, attr):\n",
    "                passed_data_block_infos.append({'attr':attr, 'item':item})\n",
    "    for d in passed_data_block_infos:\n",
    "        passed_data_blocks.append(getattr(bpy.data, d['attr'])[d['item']])\n",
    "### DO NOT EDIT ABOVE THESE LINES\n\n\n",
]
lines_to_add_at_end = [
    "\n\n### DO NOT EDIT BELOW THESE LINES\n",
    "assert None not in data_blocks  # ensures that all data from data_blocks exists\n",
    # write Blender data blocks to library in temp location
    "bpy.data.libraries.write(target_path_base + '_retrieved_data.blend', set(data_blocks), fake_user=True)\n",
    # write python data to library in temp location
    "data_file = open(target_path_base + '_retrieved_data.py', 'w')\n",
    "print(marshal.dumps(python_data).hex(), file=data_file, end='')\n",
    "data_file.close()\n"
]


def add_lines(script, target_path_base, passed_data, sent_data_blocks_path):
    # get paths
    source_blend_file = str(splitpath(bpy.data.filepath))
    target_path_base_split = str(splitpath(target_path_base))
    sent_data_blocks_path_split = str(splitpath(sent_data_blocks_path))
    # write lines to script file
    src = open(script,"r")
    oline = src.readlines()
    for line in lines_to_add_at_beginning[::-1]:
        oline.insert(0, line)
    oline.insert(0, "target_path_base = os.path.join(*%(target_path_base_split)s)\n" % locals())
    oline.insert(0, "source_blend_file = os.path.join(*%(source_blend_file)s)\n" % locals())
    oline.insert(0, "sent_data_blocks_path = os.path.join(*%(sent_data_blocks_path_split)s)\n" % locals())
    oline.insert(0, "import os\n" % locals())
    for key in passed_data:
        value = passed_data[key]
        value_str = str(value) if type(value) != str else "'%(value)s'" % locals()
        oline.insert(0, "%(key)s = %(value_str)s\n" % locals())
    for line in lines_to_add_at_end:
        oline.append(line)
    src.close()
    return oline


def get_elapsed_time(start_time, end_time, precision:int=2):
    """ from seconds to Days;Hours:Minutes;Seconds """
    value = end_time - start_time

    d_value = (((value / 365) / 24) / 60)
    days = int(d_value)

    h_value = (d_value - days) * 365
    hours = int(h_value)

    m_value = (h_value - hours) * 24
    minutes = int(m_value)

    s_value = (m_value - minutes) * 60
    seconds = round(s_value, precision)

    output_string = str(days) + ";" + str(hours) + ":" + str(minutes) + ";" + str(seconds)
    return output_string
