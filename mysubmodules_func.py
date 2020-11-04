#!/usr/bin/env python3
# PYTHON_PREAMBLE_START_STANDARD:{{{

# Christopher David Cotton (c)
# http://www.cdcotton.com

# modules needed for preamble
import importlib
import os
from pathlib import Path
import sys

# Get full real filename
__fullrealfile__ = os.path.abspath(__file__)

# Function to get git directory containing this file
def getprojectdir(filename):
    curlevel = filename
    while curlevel is not '/':
        curlevel = os.path.dirname(curlevel)
        if os.path.exists(curlevel + '/.git/'):
            return(curlevel + '/')
    return(None)

# Directory of project
__projectdir__ = Path(getprojectdir(__fullrealfile__))

# Function to call functions from files by their absolute path.
# Imports modules if they've not already been imported
# First argument is filename, second is function name, third is dictionary containing loaded modules.
modulesdict = {}
def importattr(modulefilename, func, modulesdict = modulesdict):
    # get modulefilename as string to prevent problems in <= python3.5 with pathlib -> os
    modulefilename = str(modulefilename)
    # if function in this file
    if modulefilename == __fullrealfile__:
        return(eval(func))
    else:
        # add file to moduledict if not there already
        if modulefilename not in modulesdict:
            # check filename exists
            if not os.path.isfile(modulefilename):
                raise Exception('Module not exists: ' + modulefilename + '. Function: ' + func + '. Filename called from: ' + __fullrealfile__ + '.')
            # add directory to path
            sys.path.append(os.path.dirname(modulefilename))
            # actually add module to moduledict
            modulesdict[modulefilename] = importlib.import_module(''.join(os.path.basename(modulefilename).split('.')[: -1]))

        # get the actual function from the file and return it
        return(getattr(modulesdict[modulefilename], func))

# PYTHON_PREAMBLE_END:}}}

import copy
import datetime
import functools
import shutil
import subprocess

# Get Files:{{{1
# Basic Definitions:{{{1
submodulecharacters_default = 'a-z0-9_-'
parsefilestype = 'gitls'
filestoparse = None

# Add Chmod and Recursive so don't load modules:{{{1
def chmodrecursive(folder, mode):
    """
    Mode takes format 0o777

    Also used in mysubmodules project.
    """
    import os

    if not os.path.islink(folder):
        if os.path.isdir(folder):
            os.chmod(folder, mode)
            for root, dirs, files in os.walk(folder):
                for d in dirs :
                    if not os.path.islink(os.path.join(root, d)):
                        os.chmod(os.path.join(root, d), mode)
                for f in files :
                    if not os.path.islink(os.path.join(root, f)):
                        os.chmod(os.path.join(root, f), mode)
        else:
            os.chmod(folder, mode)




def rmrecursive(folder):
    if not os.path.islink(folder) and os.path.isdir(folder):
        chmodrecursive(folder, 0o755)

        # need to make folder containing thing to be deleted readable as well
        if folder.endswith('/') or folder.endswith('\\'):
            folder = folder[: -1]
        os.chmod(folder, 0o755)
        shutil.rmtree(folder)
    else:
        os.remove(folder)


# Getting Submodules Functions:{{{1
def getsubmodules(modulepath, submoduleid = 'submodules', submodulecharacters = submodulecharacters_default, filestoparse = None, submoduleslistcheck = None):
    """
    Parse the files in a module for terms satisfying something like 'submodules/SUBMODULENAME/'.
    Output a unique list of the SUBMODULENAME terms.

    If filestoparse is None, parse by gitls. If, instead, filestoparse is list of files then go through these.
    Or can give list of files to go through (better when making changes since otherwise have to do git add when introduce new files).

    submoduleslistcheck is a list of possible modules. If outside of this list then print a message and don't include the submodule.
    """
    import os
    import re
    import sys
    import subprocess

    if modulepath[-1] != '/':
        modulepath = modulepath + '/'

    resubmodule = re.compile('(?<![a-z0-9_-])' + re.escape(submoduleid + '/') + '([' + submodulecharacters + ']*?)' + re.escape('/'))

    if filestoparse is None:
        # do git ls
        files = subprocess.check_output(['git', 'ls-files'], cwd = modulepath).decode('latin-1').splitlines()
        files = [modulepath + f for f in files]
    else:
        files = filestoparse

    submodules = set()
    for filename in files:
        if not os.path.isfile(filename):
            continue
        with open(filename, encoding = 'latin-1') as f:
            text = f.read()

        matches = resubmodule.finditer(text)
        for match in matches:
            submodule = match.group(1)
            if submoduleslistcheck is None or submodule in submoduleslistcheck:
                submodules.add(submodule)
            else:
                print('WARNING: submodule is not in modulelistcheck so is ignored: Filename: ' + filename + '. Submodule: ' + submodule + '.')

    submodules = sorted(list(submodules))

    return(submodules)

    
def getsubmodulesall(modulepathstodolist, submodulepathdict, submodulename1 = 'submodules', submodulename2 = 'submodules2', submodulecharacters = submodulecharacters_default, filestoparsedict = None, submoduleslistcheck = None, modulescansearchlist = None):
    """
    Get the submodules for a list of modules and their submodules.

    By default, only consider modules in modulestodolist
    However, if I only want to consider a limited number of modules and then also do any modules that appear as submodules, I should specify the potential module list as modulescansearchlist
    """
    if submodulename1 is not None:
        submodules1dict = {}
    else:
        submodules1dict = None
    if submodulename2 is not None:
        submodules2dict = {}
    else:
        submodules2dict = None

    # codemodulepathdict[modulename] is the path to the folder for modulename where I look for whether there are references to a submodule in a given modulename
    # should be formed of submoduledict except for the modulepaths I'm doing where it is just the basename
    codemodulepathdict = copy.deepcopy(submodulepathdict)
    modulestodolist = []
    for modulepath in modulepathstodolist:
        if modulepath[-1] == '/':
            modulename = os.path.basename(modulepath[: -1])
        else:
            modulename = os.path.basename(modulepath)
        codemodulepathdict[modulename] = modulepath
        modulestodolist.append(modulename)

    completedmodules = set()
    while len(modulestodolist) > 0:
        modulename = modulestodolist.pop(0)
        if submodulename1 is not None:
            submodules1dict[modulename] = importattr(__projectdir__ / Path('mysubmodules_func.py'), 'getsubmodules')(codemodulepathdict[modulename], submoduleid = 'submodules', submodulecharacters = submodulecharacters, filestoparse = filestoparsedict[modulename], submoduleslistcheck = submoduleslistcheck)
        if submodulename2 is not None:
            submodules2dict[modulename] = importattr(__projectdir__ / Path('mysubmodules_func.py'), 'getsubmodules')(codemodulepathdict[modulename], submoduleid = 'submodules2', submodulecharacters = submodulecharacters, filestoparse = filestoparsedict[modulename], submoduleslistcheck = submoduleslistcheck)

        completedmodules.add(modulename)

        for submodulename in submodules1dict[modulename] + submodules2dict[modulename]:
            # if this is a module I may add and I wasn't already going through it, I add it to my modulestodolist
            if submodulename not in completedmodules and submodulename not in modulestodolist and submodulename != modulename:
                if modulescansearchlist is not None and submodulename in modulescansearchlist:
                    modulestodolist.append(submodulename)
                # shouldn't return error since here I'm only parsing modules
                # should have the option to not parse particular modules
                # else:
                #     print('Submodule not parsed from module since not included in modulescansearchlist. Submodule: ' + submodulesname + '. Module: ' + modulename + '.')

    return(submodules1dict, submodules2dict)


# Add Local Submodules:{{{1
def getsubmodulepathdicts(modulepathstodolist, submodulepathdict, submodules1dict, submodules2dict, submodulename1 = 'submodules', submodulename2 = 'submodules2', modulescansearchlist = None):
    """
    Get list of every saved location of modules which I need to adjust submodules for with the submodules I need.
    """
    # want to get two objects:
    # submodulepathsubmodulesdict - each place where I physically have a module/submodules and the submodules that it calls
    submodulepathsubmodulesdict = {}

    # add submodules2 for each moduletodo:
    for modulepathtodo in modulepathstodolist:
        submodulepathsubmodulesdict[os.path.join(modulepathtodo, submodulename2) + '/'] = set()

    # to do this go through list of modules and add to these submodulesfull dicts
    # elements of toparselist: path, submodulename2root
    toparselist = [[modulepathtodo, os.path.join(modulepathtodo, submodulename2) + '/'] for modulepathtodo in modulepathstodolist]
    while len(toparselist) > 0:
        thislist = toparselist.pop(0)
        modulepath = thislist[0]
        submodule2rootpath = thislist[1]

        modulename = modulepath.split('/')[-2]

        # add submodules1_adjusted elements
        submodules1_adjusted = copy.deepcopy(submodules1dict[modulename])
        # remove if circular
        for submodule1 in submodules1_adjusted:
            if submodulename1 + '/' + submodule1 + '/' in modulepath:
                print('Circular module path skipped: ' + modulepath + submodulename1 + '/' + submodule1 + '/' + '.')
                submodules1_adjusted.remove(submodule1)
        submodulepathsubmodulesdict[os.path.join(modulepath, submodulename1) + '/'] = submodules1_adjusted

        # add submodules2 elements to existing set
        submodulepathsubmodulesdict[submodule2rootpath].union(set(submodules2dict[modulename]))

        # add every submodule1 and submodule2 to parselist
        for submodule in submodules1_adjusted:
            if submodule in modulescansearchlist:
                toparselist.append([os.path.join(modulepath, submodulename1, submodule) + '/', submodule2rootpath])
        for submodule in submodules2dict[modulename]:
            if submodule in modulescansearchlist:
                toparselist.append([os.path.join(submodule2rootpath, submodule) + '/', submodule2rootpath])

    return(submodulepathsubmodulesdict)
        

def addlocalsubmodules(submodulepathsubmodulesdict, submodulepathdict, readonly = False, gitclonedict = None, submodulename1 = 'submodules', submodulename2 = 'submodules2', rsync_gitskip = True, gitclonelocal = False):
    """
    gitclonedict allows possibility of cloning from an external repository i.e. github
    gitclonedict[submodulename] should be the repository to be cloned from

    gitclonelocal means that I use git clone to copy over modeuls rather than rsync - slower but avoid copying git ignored files
    """
    if gitclonedict is None:
        gitclonedict = {}

    for thispath in submodulepathsubmodulesdict:
        submodules = submodulepathsubmodulesdict[thispath]

        if len(submodules) == 0:
            # delete if no submodules
            if os.path.lexists(thispath):
                rmrecursive(thispath)
        else:
            if os.path.isdir(thispath):
                # ensure can write in this folder - needed when have readonly = True
                os.chmod(thispath, 0o770)

                # delete any superfluous items in the submodules folder
                for folder in os.listdir(thispath):
                    if folder not in submodules:
                        rmrecursive(os.path.join(thispath, folder))
            else:
                # ensure that I can write the submodules/ folder - needed when have readonly = True
                os.chmod(os.path.dirname(thispath[: -1]), 0o770)
                # add if submodules folder does not exist
                os.mkdir(thispath)

        for submodule in submodules:
            submodulepath = os.path.join(thispath, submodule)

            if submodule in submodulepathdict:
                if gitclonelocal is True:
                    # delete everything
                    if os.path.lexists(submodulepath):
                        rmrecursive(submodulepath)

                    subprocess.call(['git', 'clone', submodulepathdict[submodule], submodulepath])
                else:
                    # rsync across
                    # add / to end of dest for rsync to sync folder to folder
                    rsynclist = ['rsync', '-a', '--delete', submodulepathdict[submodule], submodulepath]
                    if submodulename1 is not None:
                        rsynclist = rsynclist + ['--exclude', submodulename1]
                    if submodulename2 is not None:
                        rsynclist = rsynclist + ['--exclude', submodulename2]
                    # skip .git/ folder since if I already have my main local version of the git folder
                    if rsync_gitskip is True:
                        rsynclist = rsynclist + ['--exclude', '.git/*', '--delete-excluded']
                    subprocess.call(rsynclist)


                # make submodule read only so I don't rewrite it
                if readonly is True:
                    chmodrecursive(submodulepath, 0o555)

            elif submodule in gitclonedict:
                # use git clone to copy submodule

                # delete existing modules
                if os.path.lexists(submodulepath):
                    rmrecursive(submodulepath)
                # git clone
                subprocess.call(['git', 'clone', gitclonedict[submodule], submodulepath + '/'])
            
            else:
                print('Submodule path does not have a place to be copied/linked from: ' + submodulepath + '.')
                


def addlocalsubmodules_full(modulepathstodolist, submodulepathdict, submodulename1 = 'submodules', submodulename2 = 'submodules2', submodulescharacters = submodulecharacters_default, filestoparsedict = None, submoduleslistcheck = None, modulescansearchlist = None, symlinkdict = None, readonly = False, gitclonedict = None):
    """
    Implement submodules using local submodules folders.
    Works with/without symlinks.
    """
    # get all potential submodules
    # input copy of modulepathstodolist so don't adjust modulepathstodolist here
    submodules1dict, submodules2dict = importattr(__projectdir__ / Path('mysubmodules_func.py'), 'getsubmodulesall')(copy.deepcopy(modulepathstodolist), submodulepathdict, submodulename1 = submodulename1, submodulename2 = submodulename2, submodulecharacters = submodulecharacters_default, filestoparsedict = filestoparsedict, submoduleslistcheck = submoduleslistcheck, modulescansearchlist = modulescansearchlist)

    # get the submodule path dicts to run
    submodulepathsubmodulesdict = importattr(__projectdir__ / Path('mysubmodules_func.py'), 'getsubmodulepathdicts')(modulepathstodolist, submodulepathdict, submodules1dict, submodules2dict, submodulename1 = submodulename1, submodulename2 = submodulename2, modulescansearchlist = modulescansearchlist)

    # actually implement the submodules locally
    addlocalsubmodules(submodulepathsubmodulesdict, submodulepathdict, readonly = readonly, submodulename1 = submodulename1, submodulename2 = submodulename2, gitclonedict = gitclonedict)


# Overall Function:{{{1
def dosubmodules(modulepathstodolist, findsubmodulefunc, addsubmodulefunc, submodulename1 = 'submodules', submodulename2 = 'submodules2', modulescansearchlist = None, printdetails = False):
    """

    This is designed to be a relatively flexible function that does everything except determine which submodules need to be added and actually adding the submodules.

    modulepathstodolist should be a list of modules to implement submodules for
    """

    for modulepath in modulepathstodolist:
        if not os.path.isdir(modulepath):
            raise ValueError('Modulepath does not exist: ' + modulepath + '.')

    if printdetails is True:
        print(str(datetime.datetime.now()) + ': Basic setup.')
    # list is [modulepath, overallmodulepath] for each element to do
    todolist = [[modulepath, modulepath] for modulepath in modulepathstodolist]

    # define submodules2dictoverall for each modulepath
    # this allows me to keep track of which submodules2 appear overall in each project
    submodules2dictoverall = {}
    for modulepath in modulepathstodolist:
        submodules2dictoverall[modulepath] = set()
    
    # now go through every module, find relevant submodules, mkdir submodules and delete unnecessary things, add submodules
    while len(todolist) > 0:
        modulepath, overallmodulepath = todolist.pop(0)

        if modulepath[-1] == '/':
            modulename = os.path.basename(modulepath[: -1])
        else:
            modulename = os.path.basename(modulepath)

        if printdetails is True:
            print('\n' + str(datetime.datetime.now()))
            print('Modulepath: ' + modulepath + '.')
            print('Modulename: ' + modulename + '.')

        # find submodules to do:{{{
        # get the submodules to add to the dict
        # submodules1dict is differentiated by modulename since the modulename could come up in multiple places
        submodules1dict = {}
        submodules2dict = {}
        if modulename not in submodules1dict:
            submodules1dict[modulename], submodules2dict[modulename] = findsubmodulefunc(modulepath)

        # figure out which submodules2 are new
        submodules2donow = []
        for submodule2 in submodules2dict[modulename]:
            if submodule2 not in submodules2dictoverall[overallmodulepath]:
                submodulels2dictoverall[overallmodulepath].append(submodule2)
                submodules2donow.add(submodule2)

        if printdetails is True:
            if len(submodules1dict[modulename]) > 0:
                print('Submodules1: ' + ', '.join(submodules1dict[modulename]) + '.')
            else:
                print('No submodules1.')
            if len(submodules2dict[modulename]) > 0:
                print('Submodules2: ' + ', '.join(submodules2dict[modulename]) + '.')
            else:
                print('No submodules2.')
        # find submodules to do:}}}

        # mkdir submodules and remove unneeded submodules{{{
        # only do for submodules1 since might get submodules2 later
        thispath = os.path.join(modulepath, submodulename1)
        if len(submodules1dict[modulename]) == 0:
            if os.path.exists(thispath):
                rmrecursive(thispath)
        else:
            # mkdir submodules/ path for submodules1
            if not os.path.isdir(thispath):
                if os.path.exists(thispath):
                    rmrecursive(thispath)
                os.mkdir(thispath)

            # delete submodules/submodulename if shouldn't be there in submodules1
            # do submodules2 later since other code might want this submodule
            for folder in os.listdir(thispath):
                if folder not in submodules1dict[modulename]:
                    rmrecursive(os.path.join(thispath, folder))

        # now mkdir for submodules2 if necessary
        thispath = os.path.join(overallmodulepath, submodulename2)
        if len(submodules2donow) > 0 and not os.path.isdir(thispath):
            os.mkdir(thispath)
        # delete submodules folder if there are no submodules}}}

        # add submodules1:{{{
        # to verify that submodule1 is not a submodule of itself, need to get list of all folder names in modulepath including the modulepath project itself
        if overallmodulepath[-1] == '/':
            modulepathroot = os.path.dirname(overallmodulepath[: -1])
        else:
            modulepathroot = os.path.dirname(overallmodulepath)
        elementsinmodulepath = (modulepath[len(modulepathroot + '/'): ]).split('/')

        for submodule1 in submodules1dict[modulename]:

            if submodule1 in elementsinmodulepath:
                print('submodule cannot be a submodule of itself: Modulepath: ' + modulepath + '. Submodule: ' + submodule1 + '.')
                continue

            # add submodules
            try:
                addsubmodulefunc(modulepath, submodulename1, submodule1)
                addsubmodules = True
            except Exception:
                print('Adding module failed: Modulepath: ' + modulepath + '. Modulename: ' + submodule1 + '.')
                addsubmodules = False

            if addsubmodules is True and (modulescansearchlist is None or submodule1 in modulescansearchlist):
                # add to start of list to ensure I complete one module at a time
                todolist.insert(0, [os.path.join(modulepath, submodulename1, submodule1), overallmodulepath])
        # add submodules1:}}}

        # add submodules2:{{{
        for submodule2 in submodules2donow:
            # don't need to worry about submodule2 being a submodule of itself since this won't keep going recursively
            try:
                addsubmodulefunc(overallmodulepath, submodulename2, submodule2)
                # add to todolist
                addsubmodules = True
            except Exception:
                print('Adding module failed: Submodulepath: ' + overallmodulepath + '. Modulename: ' + modulename + '.')
                addsubmodules = False

            if addsubmodules is True and (modulescansearchlist is None or submodule2 in modulescansearchlist):
                todolist.insert(0, [os.path.join(overallmodulepath, submodulename2, submodule2), overallmodulepath])
        # add submodules2:}}}

    # after parsed all modules need to go through and delete remaining unneeded submodules2
    # delete submodules2:{{{
    # need to do afterwards because only get full list of submodules2 at end of parsing


    for modulepath in submodules2dictoverall:
        # delete overallmodulepath/submodules2 if empty
        thispath = os.path.join(modulepath, submodulename2)
        if len(submodules2dictoverall[modulepath]) == 0:
            if os.path.exists(thispath):
                rmrecursive(thispath)

        else:
                
            # delete overallmodulepath/submodules2/redundantsubmodule
            for folder in os.listdir(os.path.join(modulepath, submodulename2)):
                if folder not in submodules2dictoverall[modulepath]:
                    rmrecursive(os.path.join(modulepath, submodulename2, folder))

    # delete submodules2:}}}
    
def getsubmodules_local(modulepath, submodulename1 = 'submodules', submodulename2 = 'submodules2', submodulecharacters = submodulecharacters_default, filestoparsedict = None):

    if filestoparsedict is not None:
        if modulepath[-1] == '/':
            modulename = os.path.basename(modulepath[: -1])
        else:
            modulename = os.path.basename(modulepath)
        if modulename in filestoparsedict:
            filestoparse = filestoparsedict[modulename]
        else:
            print('Modulename not in filestoparsedict: Modulename: ' + modulename + '.')
            filestoparse = None

    submodules1 = getsubmodules(modulepath, submoduleid = submodulename1, submodulecharacters = submodulecharacters_default, filestoparse = filestoparse, submoduleslistcheck = None)
    submodules2 = getsubmodules(modulepath, submoduleid = submodulename2, submodulecharacters = submodulecharacters_default, filestoparse = filestoparse, submoduleslistcheck = None)

    return(submodules1, submodules2)


def addsubmodules_local(submodulepathdict, overallmodulepath, submodulename, submodule, submodulename1 = 'submodules', submodulename2 = 'submodules2', gitclonelocal = False, rsync_gitskip = True):

    submodulepath = os.path.join(overallmodulepath, submodulename, submodule)
    if gitclonelocal is True:
        # delete everything
        if os.path.exists(submodulepath):
            rmrecursive(submodulepath)

        subprocess.call(['git', 'clone', submodulepathdict[submodule], submodulepath])
    else:
        # rsync across
        # add / to end of dest for rsync to sync folder to folder
        rsynclist = ['rsync', '-a', '--delete', submodulepathdict[submodule], submodulepath]
        if submodulename1 is not None:
            rsynclist = rsynclist + ['--exclude', submodulename1]
        if submodulename2 is not None:
            rsynclist = rsynclist + ['--exclude', submodulename2]
        # skip stuff in .git/ folder since if I already have my main local version of the git folder
        # note that I include .git/ folder since that's needed for my code to identify project folders
        if rsync_gitskip is True:
            rsynclist = rsynclist + ['--exclude', '.git/*']
        subprocess.call(rsynclist)



def dosubmodules_local(modulepathstodolist, submodulepathdict, filestoparsedict = None, gitclonelocal = False, rsync_gitskip = True, submodulename1 = 'submodules', submodulename2 = 'submodules2', modulescansearchlist = None, printdetails = False):
    findsubmodulefunc = functools.partial(getsubmodules_local, filestoparsedict = filestoparsedict, submodulename1 = submodulename1, submodulename2 = submodulename2)

    addsubmodulefunc = functools.partial(addsubmodules_local, submodulepathdict, submodulename1 = submodulename1, submodulename2 = submodulename2, gitclonelocal = gitclonelocal, rsync_gitskip = rsync_gitskip)

    dosubmodules(modulepathstodolist, findsubmodulefunc, addsubmodulefunc, submodulename1 = submodulename1, submodulename2 = submodulename2, modulescansearchlist = modulescansearchlist, printdetails = printdetails)

