
import sys
import os
import fnmatch
import argparse

import prj.util.MiscUtil as MiscUtil
import prj.util.PlatformUtil as PlatformUtil

from prj.config.YamlConfigLoader import loadYamlFilesThatExist
from prj.config.Config import Config
from prj.util.VarManager import VarManager
from prj.util.ZipHelper import ZipHelper
from prj.log.Logger import Logger
from prj.util.SystemHelper import SystemHelper
from prj.log.LogStreamFile import LogStreamFile
from prj.log.LogStreamConsole import LogStreamConsole
from prj.util.ProcessRunner import ProcessRunner
from prj.util.JunctionHelper import JunctionHelper
from prj.main.VisualStudioSolutionGenerator import VisualStudioSolutionGenerator
from prj.main.VisualStudioHelper import VisualStudioHelper
from prj.main.ProjectSchemaLoader import ProjectSchemaLoader
from prj.util.ScriptRunner import ScriptRunner
from prj.util.CommonSettings import CommonSettings
from prj.reg.UnityPackageExtractor import UnityPackageExtractor
from prj.reg.UnityPackageAnalyzer import UnityPackageAnalyzer

from prj.util.CommonSettings import ConfigFileName
from prj.reg.ReleaseRegistryManager import ReleaseRegistryManager

from prj.main.PrjRunner import PrjRunner

from prj.util.Assert import *

from prj.util.PlatformUtil import Platforms
from prj.main.PackageManager import PackageManager

import prj.ioc.Container as Container
from prj.ioc.Inject import Inject

from prj.util.UnityHelper import UnityHelper

def addArguments(parser):
    parser.add_argument('-cfg', '--configPath', metavar='CONFIG_PATH', type=str, help="TBD")

    parser.add_argument('-sp', '--suppressPrompts', action='store_true', help='If unset, confirmation prompts will be displayed for important operations.')

    parser.add_argument('-p', '--project', metavar='PROJECT_NAME', type=str, help="The project to apply changes to.")
    parser.add_argument('-pl', '--platform', type=str, default='win', choices=['win', 'webp', 'webgl', 'and', 'osx', 'ios', 'lin'], help='The platform to use.  If unspecified, windows is assumed.')

    parser.add_argument('-ul', '--updateLinks', action='store_true', help='Updates directory links for the given project using package manager')

    parser.add_argument('-lpr', '--listProjects', action='store_true', help='Display the list of all projects that are in the UnityProjects directory')
    parser.add_argument('-lpa', '--listPackages', action='store_true', help='')

    parser.add_argument('-lr', '--listReleases', action='store_true', help='')

    parser.add_argument('-uus', '--updateUnitySolution', action='store_true', help='Equivalent to executing the menu option "Assets/Sync MonoDevelop Project" in unity')
    parser.add_argument('-ucs', '--updateCustomSolution', action='store_true', help='Updates the custom solution for the given project with the files found in the Assets/ folder.  It will also take settings from the generated unity solution such as defines, and references.')

    parser.add_argument('-v', '--verbose', action='store_true', help='Output debug-level logging')
    parser.add_argument('-vv', '--veryVerbose', action='store_true', help='If set, detailed logging will be output to stdout rather than file')

    parser.add_argument('-b', '--buildCustomSolution', action='store_true', help='Build the generated custom solution for the given project')
    parser.add_argument('-d', '--openDocumentation', action='store_true', help='Opens the documentation page in a web browser')

    parser.add_argument('-clp', '--clearProjectGeneratedFiles', action='store_true', help='Remove the generated files for the given project')
    parser.add_argument('-cla', '--clearAllProjectGeneratedFiles', action='store_true', help='Remove all the generated files for all projects')

    parser.add_argument('-dal', '--deleteAllLinks', action='store_true', help='Delete all directory links for all projects')
    parser.add_argument('-dpr', '--deleteProject', metavar='PROJECT_NAME', type=str, help="")
    parser.add_argument('-dpa', '--deletePackage', metavar='PACKAGE_NAME', type=str, help="")

    parser.add_argument('-ula', '--updateLinksAllProjects', action='store_true', help='Updates the directory links for all projects')

    parser.add_argument('-bf', '--buildFull', action='store_true', help='Perform a full build of the given project')

    parser.add_argument('-ou', '--openUnity', action='store_true', help='Open unity for the given project')
    parser.add_argument('-ocs', '--openCustomSolution', action='store_true', help='Open the solution for the given project/platform')

    parser.add_argument('-cco', '--createConfig', action='store_true', help='')
    parser.add_argument('-cpr', '--createProject', metavar='NEW_PROJECT_NAME', type=str, help="")
    parser.add_argument('-cpa', '--createPackage', metavar='NEW_PACKAGE_NAME', type=str, help="")

    parser.add_argument('-epy', '--editProjectYaml', action='store_true', help='')

    parser.add_argument('-ins', '--installRelease', type=str, nargs=2, metavar=('RELEASE_NAME', 'RELEASE_VERSION'), help="")

def getProjenyDir():
    # This works for both exe builds (Bin/Prj/Data/Prj.exe) and running from source (Source/prj/main/Prj.py) by coincidence
    return os.path.join(MiscUtil.getExecDirectory(), '../../..')

def getExtraUserConfigPaths():
    return [os.path.join(os.path.expanduser('~'), ConfigFileName)]

def installBindings(mainConfigPath):

    projenyDir = getProjenyDir()
    projenyConfigPath = os.path.join(projenyDir, ConfigFileName)

    # Put the standard config first so it can be over-ridden by user settings
    configPaths = [projenyConfigPath]

    if mainConfigPath:
        configPaths += [mainConfigPath]

    configPaths += getExtraUserConfigPaths()

    Container.bind('Config').toSingle(Config, loadYamlFilesThatExist(*configPaths))

    initialVars = { 'ProjenyDir': projenyDir, }

    if mainConfigPath:
        initialVars['ConfigDir'] = os.path.dirname(mainConfigPath)

    if not MiscUtil.isRunningAsExe():
        initialVars['PythonPluginDir'] = getPluginDirPath()

    Container.bind('VarManager').toSingle(VarManager, initialVars)
    Container.bind('SystemHelper').toSingle(SystemHelper)
    Container.bind('Logger').toSingle(Logger)
    Container.bind('UnityHelper').toSingle(UnityHelper)
    Container.bind('ScriptRunner').toSingle(ScriptRunner)
    Container.bind('PackageManager').toSingle(PackageManager)
    Container.bind('ProcessRunner').toSingle(ProcessRunner)
    Container.bind('JunctionHelper').toSingle(JunctionHelper)
    Container.bind('VisualStudioSolutionGenerator').toSingle(VisualStudioSolutionGenerator)
    Container.bind('VisualStudioHelper').toSingle(VisualStudioHelper)
    Container.bind('ProjectSchemaLoader').toSingle(ProjectSchemaLoader)
    Container.bind('CommonSettings').toSingle(CommonSettings)
    Container.bind('UnityPackageExtractor').toSingle(UnityPackageExtractor)
    Container.bind('ZipHelper').toSingle(ZipHelper)
    Container.bind('UnityPackageAnalyzer').toSingle(UnityPackageAnalyzer)

    Container.bind('ReleaseRegistryManager').toSingle(ReleaseRegistryManager)

def processArgs(args):
    if args.buildFull:
        args.updateLinks = True
        args.updateUnitySolution = True
        args.updateCustomSolution = True
        args.buildCustomSolution = True

def findFilesByPattern(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

def getPluginDirPath():
    return os.path.join(MiscUtil.getExecDirectory(), '../../plugins')

def installPlugins():

    if MiscUtil.isRunningAsExe():
        # Must be running from source for plugins
        return

    import importlib

    pluginDir = getPluginDirPath()

    for filePath in findFilesByPattern(pluginDir, '*.py'):
        basePath = filePath[len(pluginDir) + 1:]
        basePath = os.path.splitext(basePath)[0]
        basePath = basePath.replace('\\', '.')
        importlib.import_module('plugins.' + basePath)

def tryGetMainConfigPath(args):
    if args.configPath:
        assertThat(os.path.isfile(args.configPath), "Could not find config file at '{0}'", args.configPath)
        return args.configPath

    configPathGuess = os.path.join(os.getcwd(), ConfigFileName)

    if os.path.isfile(configPathGuess):
        return configPathGuess

    return None

def main():
    # Here we split out some functionality into various methods
    # so that other python code can make use of them
    # if they want to extend projeny
    parser = argparse.ArgumentParser(description='Unity Package Manager')
    addArguments(parser)

    argv = sys.argv[1:]

    # If it's 2 then it only has the -cfg param
    if len(argv) == 0:
        parser.print_help()
        sys.exit(2)

    args = parser.parse_args(sys.argv[1:])

    processArgs(args)

    Container.bind('LogStream').toSingle(LogStreamFile)
    Container.bind('LogStream').toSingle(LogStreamConsole, args.verbose, args.veryVerbose)

    installBindings(tryGetMainConfigPath(args))
    installPlugins()

    PrjRunner().run(args)

if __name__ == '__main__':

    if (sys.version_info < (3, 0)):
        print('Wrong version of python!  Install python 3 and try again')
        sys.exit(2)

    succeeded = True

    try:
        main()

    except KeyboardInterrupt as e:
        print('Operation aborted by user by hitting CTRL+C')
        succeeded = False

    except Exception as e:
        sys.stderr.write(str(e))

        if not MiscUtil.isRunningAsExe():
            sys.stderr.write('\n' + traceback.format_exc())

        succeeded = False

    if not succeeded:
        sys.exit(1)