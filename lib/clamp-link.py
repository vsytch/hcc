#!/usr/bin/python

import os
from sys import argv, exit
from tempfile import mkdtemp
from shutil import rmtree, copyfile
from subprocess import Popen, check_call, check_output, PIPE, call

verbose = False

def detect_kernel(obj):
    if verbose:
            print("Looking for kernel in: " + obj)

    p1 = Popen(["dumpbin",
                    obj],
                    stdout = PIPE)
    p2 = Popen(["findstr",
                ".kernel"],
                stdin = p1.stdout,
                stdout = open("nul", "ab"))
    p1.wait()
    p2.wait()
    
    if p2.returncode == 0:
        if verbose:
            print("HCC kernel detected in " + obj)
        with open(os.path.splitext(obj)[0] + ".bc", "wb") as obj_kernel:
                p = Popen(["python",
                            kd,
                            "-e",
                            obj],
                            stdout = obj_kernel)
                p.wait()

if __name__ == "__main__":
    debug = False
    bindir = os.path.dirname(argv[0])
    libpath = bindir + "/../lib"
    link = bindir + "/llvm-link"
    opt = bindir + "/opt"
    clang = bindir + "/clang"
    clang_offload_bundler = bindir + "/clang-offload-bundler"
    clamp_device = bindir + "/clamp-device.py"
    clamp_embed = bindir + "/clamp-embed.py"
    kd = bindir + "/kd.py"
    obj_ext = ".obj"
    sl_ext = ".lib"
    libpath_flag = "-libpath:"
    amdgpu_target = "gfx803"

    objs_to_process = []
    lib_search_paths = []
    link_host_args = []
    link_kernel_args = []
    link_other_args = []

    cur_dir = os.getcwd()
    temp_dir = mkdtemp()

    args = argv[1:]
    out_name = ""

    if "--verbose" in args:
        verbose = True
        args.remove("--verbose")
    if "-debug" in args:
        debug = True

    for arg in args:
        if arg.startswith("-out:"):
            out_name = arg[5:]

    for arg in args:
        if arg.startswith("--amdgpu-target="):
            amdgpu_target = arg[16:]
            args.remove(arg)
            break

    for arg in args:
        if arg.endswith(obj_ext):
            if verbose:
                print("Detected object file to process further: " + arg)
            objs_to_process.append(arg)
        elif arg.startswith(libpath_flag):
            if verbose:
                print("Add library path: " + arg[len(libpath_flag):])
            lib_search_paths.append(arg[len(libpath_flag):])
            link_other_args.append(arg)
        elif not arg.endswith(sl_ext):
            if verbose:
                print("Passing down linker args: " + arg)
            link_other_args.append(arg)
  
    for arg in args:
        if arg.endswith(sl_ext):
            detected_static_library = ""
            if verbose:
                print("Looking for static library: " + arg)
            for lib_path in lib_search_paths:
                if verbose:
                    print("Trying to detect: " + lib_path + "/" + arg)
                if os.path.isfile(lib_path + "/" + arg):
                    detected_static_library = lib_path + "/" + arg
                    break
            if detected_static_library != "":
                if verbose:
                    print("Detected: " + detected_static_library)
                with open(temp_dir + "/lib_objs.txt", "w") as lib_objs:
                        check_call(["lib",
                                    "/nologo",
                                    "/list",
                                    detected_static_library],
                                    stdout = lib_objs)
                with open(temp_dir + "/lib_objs.txt", "r") as lib_objs:
                    for lib_obj in lib_objs.readlines():
                        lib_obj = lib_obj.strip()
                        check_call(["lib",
                                    "/nologo",
                                    "/extract:" + lib_obj,
                                    "/out:" + temp_dir + "/" + os.path.basename(lib_obj),
                                    detected_static_library])
                        detect_kernel(temp_dir + "/" + os.path.basename(lib_obj))
                        if os.path.isfile(temp_dir + "/" + os.path.basename(os.path.splitext(lib_obj)[0]) + ".bc"):
                            link_kernel_args.append(temp_dir + "/" + os.path.basename(os.path.splitext(lib_obj)[0]) + ".bc")
                            link_host_args.append(temp_dir + "/" + os.path.basename(lib_obj))

                os.remove(temp_dir + "/lib_objs.txt")

    for obj in objs_to_process:
        detect_kernel(obj)
        if os.path.isfile(os.path.splitext(obj)[0] + ".bc"):
            link_kernel_args.append(os.path.splitext(obj)[0] + ".bc")
            link_host_args.append(obj)
        else:
            link_other_args.append(obj)
                
    if verbose:
        print("new host args: ", link_host_args)
        print("new kernel args: ", link_kernel_args)
        print("new other args: ", link_other_args)

    if link_kernel_args:
        p1 = Popen([link]
                    + link_kernel_args,
                    stdout = PIPE)
        p2 = Popen([opt,
            "-always-inline",
            "-",
            "-o",
            temp_dir + "/kernel.bc"],
            stdin = p1.stdout)
        p1.wait()
        p2.wait()

        open(temp_dir + "/empty.obj", "w").close()
        clang_offload_bundler_input_args = "-inputs=" + temp_dir + "/empty.obj"
        clang_offload_bundler_targets_args = "-targets=host-x86_64-pc-windows-msvc"

        call(["python",
            clamp_device,
            temp_dir + "/kernel.bc",
            temp_dir + "/kernel-" + amdgpu_target + ".hsaco",
            "--amdgpu-target=" + amdgpu_target])
        clang_offload_bundler_input_args += "," + temp_dir + "/kernel-" + amdgpu_target + ".hsaco"
        clang_offload_bundler_targets_args += ",hcc-amdgcn--amdhsa-" + amdgpu_target

        call([clang_offload_bundler,
            "-type=o",
            clang_offload_bundler_input_args,
            clang_offload_bundler_targets_args,
            "-outputs=" + temp_dir + "/kernel.bundle"])

        with open(temp_dir + "/kernel_bundle_data.cpp", "wb") as kb_obj:
            p = Popen(["python",
                        kd,
                        "-i",
                        temp_dir + "/kernel.bundle"],
                        stdout = kb_obj)
            p.wait()
        check_call([clang,
                    "-c",
                    "-o",
                    temp_dir + "/kernel_bundle_data.obj",
                    temp_dir + "/kernel_bundle_data.cpp"])
        
        link_other_args.append(temp_dir + "/kernel_bundle_data.obj")
    
    command = ["link",
        "-force:multiple",
        "-ignore:4006",
        "-ignore:4078",
        "-ignore:4088",
        "-subsystem:console",
        "-nodefaultlib:libcmt",
        "-nodefaultlib:msvcrt",
        "-stack:100000000"]
    
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

    command += link_host_args
    command += link_other_args



    print(command)
    p = Popen(command)#, stdout = open("nul", "ab"))
    p.wait()

    rmtree(temp_dir)
    for f in link_kernel_args:
        if os.path.isfile(f):
            os.remove(f)

    exit(0)



