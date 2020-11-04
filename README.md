# Introduction
Mysubmodules contains functions to load submodules in my projects. I decided not to use the submodules features built into git repositories after finding them difficult to use.

I provide a script that can be used to download and set up the submodules listed in .mysubmodules in a git repository.

I also provide the functions I use on my own systems to manage repositories (these are primarily link-based since I can avoid making multiple copies of directories to save space) and external files (in particular data).

# Possible Functions
In each project, I give a .mysubmodules file which I can use to specify which submodules to call. Another option is mysubmodules_func.py:getsubmodules which parses the documents in a project to work out which submodules to call.

mysubmodules_func.py:dosubmodules is the function I use to generally get the submoduels for a folder. I also include a number of specific functions for specific tasks.

# .mysubmodules
Specify global options by placing GLOBALOPTIONS: in first line and then giving CSV without any spaces. To give a .mysubmodules file but still parse for other submodules, specify the global option 'parseforsubmodules'.

Specify submodules to download by giving each submodules on a new line (following any global options). If want to give options, following the submodule with a comma and then give a CSV of options. To not yield an error if a submodules is not found, use option no_error_not_found.

