# 'Background Processing':

Run blender processes in the background with separate instances of Blender.

# Instructions for Use:

* First, add the 'background_processing' code to your addon module and register the classes as necessary
* Write your own background processing scripts using the template in the 'demo_scripts' folder of this addon
    * Background processing scripts will be executed from within a separate Blender instance
        * This allows for Blender-only module imports such as bpy and bmesh
        * This also allows for access to the source file's blend data (if no existing blend data must be accessed, consider setting 'use_blend_file' to False in 'add_job' call for efficiency)
* Send scripts to the JobManager for execution
    * Jobs can be added from within a separate operator/code block using the following code:
        from .background_processing.classes.JobManager import *  # relative JobManager import path (current path assumes script is in same root folder as 'background_processing')
        job = "/tmp/test_script.py"  # REPLACE with path to your background processing script
        JobManager = JobManager.get_instance()
        JobManager.add_job(job)
    * You'll find the entire background processing API in the Job Manager class ('classes/JobManager.py')
    * See 'classes/AddJob.py' for an example use of the JobManager class API in a custom operator
