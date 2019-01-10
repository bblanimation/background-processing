# 'Background Processing':

Run blender processes in the background with separate instances of Blender.

# Instructions for Use:

* First, add the 'background_processing' code to your addon module and register the classes as necessary
* Before any jobs can be processed in the background, the user must execute the 'scene.job_manager' operator manually.
    * Paste the following code in the 'draw' method of your Panel class to include a button within your addon's UI:
        self.layout.operator("scene.job_manager")
* Write your own background processing scripts using the template in the 'demo_scripts' folder of this addon
    * Background processing scripts will be executed from within a separate Blender instance, allowing for module imports such as bpy and bmesh.
* Add scripts to the JobManager class to be executed
    * Background processing scripts (jobs) can be added from within a separate operator/code block using the following code:
        from .background_processing.classes.JobManager import *  # relative JobManager import path (current path assumes script is in enclosing folder of 'background_processing')
        job = "/tmp/test_script.py"  # path to your background processing script
        JobManager = SCENE_OT_job_manager.get_instance()
        JobManager.add_job(job)
    * You'll find the entire background processing API in the Job Manager class ('classes/JobManager.py')
    * See 'classes/AddJob.py' for an example use of the JobManager class API in a separate operator
