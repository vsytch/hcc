import os
from sys import exit, argv
from shutil import rmtree, copyfile
from subprocess import check_call 

bin_dir = ""
src_file = ""
debug = False
clang = "clang++"
hcc = "hcc" 

args = ["-DWIN32=1",
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
        "-momit-leaf-frame-pointer",
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
        "-v"]

def compile_mcwamp():
    command = [clang]
    command += ["-I" + bin_dir + "/../../../include"]
    command += args

    if debug:
        command += ["-D_DEBUG=1",
                    "-gcodeview"]
    else:
        command += ["-DNDEBUG=1"]

    command += ["-c",
                "-o",
                bin_dir + "/../lib/mcwamp.obj",
                bin_dir + "/../../../lib/mcwamp.cpp"]

    check_call(command)

def compile_source():
    command = [hcc]
    command += ["-I" + bin_dir + "/../../../include"]
    command += args

    if debug:
        command += ["-D_DEBUG=1",
                    "-gcodeview"]
    else:
        command += ["-DNDEBUG=1"]

    command += ["-hc",
                "-o",
                src_file[:-4] + ".exe",
                src_file]

    check_call(command)

if __name__ == "__main__":
    bin_dir = os.path.dirname(argv[0])

    for arg in argv:
        if arg.endswith(".cpp"):
            src_file = arg
    if not src_file:
        print("No source file provided")
        exit(0)
    
    if "debug" in argv:
        debug = True
    elif "release" in argv:
        debug = False

    compile_mcwamp()
    compile_source()