#!/usr/bin/python

import os
from sys import argv, exit
from tempfile import mkdtemp
from shutil import rmtree, copyfile
from subprocess import Popen, check_call, check_output, PIPE, call

if __name__ == "__main__":
    debug = False
    bindir = os.path.dirname(argv[0])
    libpath = bindir + "/../lib"
    link = bindir + "/llvm-link"
    opt = bindir + "/opt"
    clang_offload_bundler = bindir + "/clang-offload-bundler"
    if os.name == "nt":
        clamp_device = bindir + "/clamp-device.py"
        clamp_embed = bindir + "/clamp-embed.py"
        obj_ext = ".obj"
        sl_ext = ".lib"
        libpath_flag = "-libpath:"
    else:
        clamp_device = bindir + "/clamp-device"
        clamp_embed = bindir + "/clamp-embed"
        obj_ext = ".o"
        sl_ext = ".a"
        libpath_flag = "-L"

    verbose = 0
    link_host_args = []
    link_other_args = []

    args = argv[1:]

    if not os.path.isfile(libpath + "/mcwamp.rar"):
        print("Can't find mcwamp.rar")
        exit(1)

    check_call(["unrar",
                "e",
                "-inul",
                libpath + "/mcwamp.rar"])

    link_host_args.append("mcwamp.host.obj")

    if "--verbose" in args:
        verbose = 2
        args.remove("--verbose")

    if "-debug" in args:
        debug = True
    
    for arg in args:
        if arg.endswith(obj_ext):
            if os.path.isfile(arg):
                link_host_args.append(arg)
        else:
            link_other_args.append(arg)

    if verbose != 0:
        print("new host args: ", link_host_args)
        print("new other args: ", link_other_args)
        
    command = ["link",
        "-force:multiple",
        "-ignore:4006",
        "-ignore:4078",
        "-ignore:4088",
        "-subsystem:console",
        "-nodefaultlib:libcmt",
        "-stack:1000000000",
        "kernel32.lib",
        "user32.lib",
        "gdi32.lib",
        "winspool.lib",
        "comdlg32.lib",
        "advapi32.lib",
        "shell32.lib",
        "ole32.lib",
        "oleaut32.lib",
        "uuid.lib",
        "odbc32.lib",
        "odbccp32.lib",
        "kernel_bundle_data.obj"]
    
    if debug:
        command += ["ucrtd.lib",
            "vcruntimed.lib",
            "msvcrtd.lib",
            "msvcprtd.lib"]
    else:
        command += ["ucrt.lib",
            "vcruntime.lib",
            "msvcrt.lib",
            "msvcprt.lib"]

    command += link_other_args
    command += link_host_args
    print(command)
    check_call(command)

    os.remove("kernel_bundle_data.obj")
    os.remove("mcwamp.host.obj")
    os.remove("mcwamp.kernel.bc")

    exit(0)



