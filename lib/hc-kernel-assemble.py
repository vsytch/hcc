#!/usr/bin/python

#hc-kernel-assemble kernel-bitcode

import os
from sys import argv, exit
from tempfile import mkdtemp
from subprocess import Popen, call, PIPE, check_call
from shutil import rmtree, copyfile

if __name__ == "__main__":
    bindir = os.path.dirname(argv[0])
    clamp_device = bindir + "/clamp-device.py"
    clang_offload_bundler = bindir + "/clang-offload-bundler"
    clang = bindir + "/clang"
    llvm_link = bindir + "/llvm-link"
    llvm_dis = bindir + "/llvm-dis"
    opt = bindir + "/opt"
    kd = bindir + "/kd.py"
    libpath = bindir + "/../lib"
    dumpdir = os.getenv("HCC_DUMPDIR")
    dump = os.getenv("HCC_DUMP")

    if not dumpdir:
        dumpdir = "."
    dumpdir += "/dump"

    if dump:
        if not os.path.isdir(dumpdir):
            os.mkdir(dumpdir)

    if len(argv) != 3:
        print("Usage: %s kernel-bitcode" % argv[0])
        exit(1)

    if not os.path.isfile(argv[1]):
        print("kernel-bitcode %s is not valid" % argv[1])
        exit(1)
    
    if dump:
        check_call([llvm_dis,
                    "-o",
                    dumpdir + "/dump.kernel_input.ll",
                    argv[1]])

    if "Temp" not in argv[2]: #fix recgonizing -c
        out = os.path.dirname(argv[1]) + "/" + os.path.splitext(os.path.basename(argv[2]))[0]

        with open(out + ".cpp", "ab") as obj:
            check_call(["python",
                        kd,
                        "-i",
                        argv[1]],
                        stdout = obj)
        
        check_call([clang,
                    "-c",
                    "-emit-llvm",
                    "-o",
                    out + ".bc",
                    out + ".cpp"])

        copyfile(out + ".bc", argv[2])
        os.remove(out + ".bc")
        os.remove(out + ".cpp")

    else:
        with open("temp_kernel.cpp", "ab") as obj:
            check_call(["python",
                        kd,
                        "-i",
                        argv[1]],
                        stdout = obj)
        
        check_call([clang,
                    "-c",
                    "-o",
                    argv[2],
                    "temp_kernel.cpp"])
        
        os.remove("temp_kernel.cpp")
    
    exit(0)

