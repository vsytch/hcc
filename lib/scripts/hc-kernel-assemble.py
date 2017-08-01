#!/usr/bin/python

#hc-kernel-assemble kernel-bitcode

import os
from sys import argv, exit
from tempfile import mkdtemp
from subprocess import Popen, check_call, PIPE
from shutil import rmtree, copyfile

if __name__ == "__main__":
    bindir = os.path.dirname(argv[0])
    clamp_device = bindir + "/clamp-device.py"
    clang_offload_bundler = bindir + "/clang-offload-bundler"
    clang = bindir + "/clang"
    llvm_link = bindir + "/llvm-link"
    opt = bindir + "/opt"
    libpath = bindir + "/../lib"
    amdgpu_target = "gfx803"

    if len(argv) != 3:
        print("Usage: %s kernel-bitcode" % argv[0])
        exit(1)

    if not os.path.isfile(argv[1]):
        print("kernel-bitcode %s is not valid" % argv[1])
        exit(1)

    if not os.path.isfile(libpath + "/mcwamp.rar"):
        print("Can't find mcwamp.rar")
        exit(1)

    if (os.path.isfile("mcwamp.host.obj")):
        os.remove("mcwamp.host.obj")
    if (os.path.isfile("mcwamp.kernel.bc")):
        os.remove("mcwamp.kernel.bc")
    check_call(["unrar",
                "e",
                "-inul",
                libpath + "/mcwamp.rar"])

    p1 = Popen([llvm_link,
        "mcwamp.kernel.bc",
        argv[1]],
        stdout = PIPE)
    p2 = Popen([opt,
        "-always-inline",
        "-",
        "-o",
        "kernel.bc"],
        stdin = p1.stdout)
    p2.wait()

    open("empty.obj", "w").close()
    clang_offload_bundler_input_args = "-inputs=empty.obj"
    clang_offload_bundler_targets_args = "-targets=host-x86_64-pc-windows-msvc"

    check_call(["python",
        clamp_device,
        "kernel.bc",
        "kernel-" + amdgpu_target + ".hsaco",
        "--amdgpu-target=" + amdgpu_target])
    clang_offload_bundler_input_args += ",kernel-" + amdgpu_target + ".hsaco"
    clang_offload_bundler_targets_args += ",hcc-amdgcn--amdhsa-" + amdgpu_target

    check_call([clang_offload_bundler,
            "-type=o",
            clang_offload_bundler_input_args,
            clang_offload_bundler_targets_args,
            "-outputs=kernel.bundle"])
    source_code = os.path.basename(argv[1][:argv[1].rfind("-")]) + ".cpp"
    check_call(["inject_kernel",
        "kernel.bundle",
        "kernel_bundle_data.cpp"])
    check_call(["cl.exe",
        "kernel_bundle_data.cpp",
        "/nologo",
        "/c",
        "/EHsc"])

    os.remove("kernel_bundle_data.cpp")
    os.remove("mcwamp.host.obj")
    os.remove("mcwamp.kernel.bc")
    os.remove("kernel.bc")
    os.remove("empty.obj")
    os.remove("kernel-" + amdgpu_target + ".hsaco")
    os.remove("kernel.bundle")
    exit(0)

