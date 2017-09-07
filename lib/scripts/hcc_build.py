import os
from sys import exit, argv
from shutil import rmtree, copyfile
from subprocess import Popen, check_output

bin_dir = ""
src_file = ""
debug = False
link = True
verbose = False
clang = "clang++"
hcc = "hcc"

args = [#"-lmcwamp",
        "-DWIN32=1",
        "-D_WIN32=1",
        "-D_WIN64=1",
        "-D_M_X64=100",
        "-D_M_AMD64=100",
        "-D_MT=1",
        "-D_DLL=1",
        "-D_CONSOLE=1",
        "-D_WCHAR_T_DEFINED=1",
        "-D_NATIVE_WCHAR_T_DEFINED=1",
        "-D_CPPUNWIND=1",
        "-D_USE_MATH_DEFINES=1",
        "-D_CRT_SECURE_NO_WARNINGS=1",
        "-D_SCL_SECURE_NO_WARNINGS=1",
        "-IC:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/include",
        "-IC:/Program Files (x86)/Windows Kits/10/include/10.0.10240.0/ucrt",
        "-IC:/Program Files (x86)/Windows Kits/NETFXSDK/4.6.1/include/um",
        "-IC:/Program Files (x86)/Windows Kits/8.1/Include/um",
        "-IC:/Program Files (x86)/Windows Kits/8.1/Include/shared",
        "-fms-compatibility-version=19.0.24215",
        "-fms-compatibility",
        "-fms-extensions",
        "-fdelayed-template-parsing",
        "-fdeclspec",
        "-Xclang",
        "-flto-visibility-public-std",
        "-Xclang",
        "-fms-volatile",
        "-Xclang",
        "-fdiagnostics-format",
        "-Xclang",
        "msvc",
        "-Xclang",
        "-fexternc-nounwind",
        "-Xclang",
        "-relaxed-aliasing",
        "-Xclang",
        "-mrelocation-model",
        "-Xclang",
        "pic",
        "-Xclang",
        "-pic-level",
        "-Xclang",
        "2",
        "-Xclang",
        "-munwind-tables",
        "-Xclang",
        #"-momit-leaf-frame-pointer",
        "-mincremental-linker-compatible",
        "-std=c++amp",
        "-Wno-ignored-attributes",
        "-Wno-microsoft-template",
        "-Wno-duplicate-decl-specifier",
        "-Wno-logical-op-parentheses",
        "-Wno-dangling-else",
        "-Wno-nonportable-include-path",
        "-Wno-ignored-pragma-intrinsic",
        "-Wno-expansion-to-defined",
        "-Wno-int-to-void-pointer-cast",
        "-Wno-invalid-command-line-argument"]

def compile_mcwamp():
    command = [clang]
    command += ["-I" + bin_dir + "/../../../include"]
    command += args

    if debug:
        command += ["-D_DEBUG=1",
                    "-gcodeview"]
    else:
        command += ["-DNDEBUG=1"]
    
    if verbose:
        command += ["-v"]

    command += ["-c",
                "-hc",
                "-o",
                bin_dir + "/../lib/mcwamp.obj",
                bin_dir + "/../../../lib/mcwamp.cpp"]

    p = Popen(command)
    p.wait()

    if p.returncode != 0:
        exit(1)

    p = Popen(["lib",
                "/nologo",
                bin_dir + "/../lib/mcwamp.obj",
                "/out:" + bin_dir + "/../lib/mcwamp.lib"])
    p.wait()

    if p.returncode != 0:
        exit(1)

    os.remove(bin_dir + "/../lib/mcwamp.obj")

def compile_source(extra_args):
    command = [hcc]
    command += ["-I" + bin_dir + "/../../../include"]
    command += args
    command += extra_args

    if debug:
        command += ["-D_DEBUG=1",
                    "-gcodeview"]
    else:
        command += ["-DNDEBUG=1"]
    
    if verbose:
        command += ["-v"]
    
    if link:
        command += ["-lmcwamp",
                    "-z",
                    "-libpath:C:/hcc/build/Release/bin/../lib",
                    "-o",
                    src_file[:-4] + ".exe"]
    else:
        command += ["-c",
                    "-o",
                    src_file[:-4] + ".obj"]

    command += ["-hc",
                src_file]

    p = Popen(command)
    p.wait()

    if p.returncode != 0:
        exit(1)

if __name__ == "__main__":
    bin_dir = os.path.dirname(argv[0])
    extra_args = []

    for arg in argv[1:]:
        if arg == "-g":
            debug = True
        elif arg == "-c":
            link = False
        elif arg == "-v":
            verbose = True
        elif arg.endswith(".cpp"):
            src_file = arg
        else:
            extra_args.append(arg)

    if (src_file == "") and ("mcwamp" in argv[1:]): 
        compile_mcwamp()
    else:
        compile_source(extra_args)