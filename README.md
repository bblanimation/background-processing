# 'Background Processing':

Run blender processes in the background with separate instances of Blender.

[Demo of the Background Processor on YouTube](https://youtu.be/8iIMP1SrHIE)

# Instructions for Use:

* First, copy the `JobManager.py` file from the `background_processing/classes/` directory to your addon module
* Write your own background processing scripts
    * Background processing scripts will be executed from within a separate Blender instance
        * This allows for Blender-only module imports such as bpy and bmesh
        * This also allows for access to the source file's blend data (if no existing blend data must be accessed, consider setting `use_blend_file` to False in `JobManager.add_job` API call for efficiency)
    * Background processing scripts should include a `data_blocks` variable
        * `data_blocks` variable should be set to list of Blend data blocks
        * The background processor will automatically copy these data blocks to the active instance of Blender upon job completion
        * these data blocks can then be accessed with the `JobManager.get_retrieved_data_blocks` API call upon job completion.
            * Example use: `JobManager.get_retrieved_data_blocks(job).objects`
            * NOTE:
                ``` Python
                dir(JobManager.get_retrieved_data_blocks(job)) = [
                    'actions',
                    'armatures',
                    'brushes',
                    'cache_files',
                    'cameras',
                    'curves',
                    'fonts',
                    'grease_pencil',
                    'groups',
                    'images',
                    'ipos',
                    'lamps',
                    'lattices',
                    'linestyles',
                    'masks',
                    'materials',
                    'meshes',
                    'metaballs',
                    'movieclips',
                    'node_groups',
                    'objects',
                    'paint_curves',
                    'palettes',
                    'particles',
                    'scenes',
                    'sounds',
                    'speakers',
                    'texts',
                    'textures',
                    'worlds']
                ```
    * Background processing scripts should include a `python_data` variable
        * `python_data` variable should be set to dictionary containing any necessary data to retrieve
        * these data blocks can then be accessed with the `JobManager.get_retrieved_python_data` API call upon job completion.
* Send scripts to the JobManager for execution
    * Jobs can be added from within a separate operator/code block using the following code:
        ``` Python
        from .JobManager import *  # relative JobManager import path (current path assumes script is in same root folder as 'JobManager.py')
        job = "/tmp/test_script.py"  # REPLACE with path to your background processing script
        JobManager = JobManager.get_instance()
        JobManager.add_job(job)
        ```
    * You'll find the entire background processing API in the Job Manager class (`classes/JobManager.py`)
    * See `classes/AddJob.py` for an example use of the JobManager class API in a custom operator
