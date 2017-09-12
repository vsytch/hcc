#!/usr/bin/python

#hc-host-assemble host-bitcode host-object (options)

from sys import argv, exit
import os
from subprocess import Popen, check_call
from tempfile import mkdtemp
from shutil import rmtree, copyfile

if __name__ == "__main__":

    bindir = os.path.dirname(argv[0])
    clang = bindir + "/clang"
    opt = bindir + "/opt"
    llvm_as = bindir + "/llvm-as"
    llvm_dis = bindir + "/llvm-dis"
    llvm_link = bindir + "/llvm-link"
    libpath = bindir + "/../lib"
    dumpdir = os.getenv("HCC_DUMPDIR")
    dump = os.getenv("HCC_DUMP")

    if not dumpdir:
        dumpdir = "."
    dumpdir += "/dump"

    if dump:
        if not os.path.isdir(dumpdir):
            os.mkdir(dumpdir)

    if len(argv) < 3:
        print("Usage: %s host-bitcode host-object (options)" % argv[0])
        exit(1)

    if not os.path.isfile(argv[1]):
        print("host-bitcode %s is not valid" % argv[1])
        exit(1)

    if dump:
        check_call([llvm_dis,
                    "-o",
                    dumpdir + "/dump.host_input.ll",
                    argv[1]])

    command = [clang]

    if len(argv) >= 3:
        command += argv[3:]

    if os.path.isfile(argv[2]): # -c
        copyfile(argv[2], argv[2] + ".bc")
        check_call([llvm_link,
                    argv[1],
                    argv[2] + ".bc",
                    "-o",
                    argv[1] + ".bc"])
        os.remove(argv[2])
        os.remove(argv[2] + ".bc")
    else:
        copyfile(argv[1], argv[1] + ".bc")

    os.remove(argv[1])
    command.append(argv[1] + ".bc")

    command += [
        "-c",
        "-o",
        argv[2]]

    check_call(command)
    # check_call(["editbin",
    #             "/nologo",
    #             "/section:.pdata=.junk",
    #             argv[2]])

    if os.path.isfile(argv[1] + ".bc"):
        os.remove(argv[1] + ".bc")

    exit(0)
