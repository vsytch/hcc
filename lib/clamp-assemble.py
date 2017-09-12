#!/usr/bin/python
#clamp-assemble kernel-bitcode kernel-object

from sys import argv, exit
import os
from shutil import copyfile
from subprocess import check_call

if __name__ == "__main__":

    bindir = os.path.dirname(argv[0])
    embed = bindir + "/clamp-embed.py"
    kd = bindir + "/kd.py"
    obj_ext = ".obj"

    if len(argv) != 3:
        print("Usage: %s kernel-bitcode object" % argv[0])
        exit(1)

    if not os.path.isfile(argv[1]):
        print("kernel-bitcode %s is not valid" % argv[1])
        exit(1)

    if os.path.isfile(argv[2]):
        check_call(["editbin",
                    "/section:.pdata=.junk",
                    "/nologo",
                    argv[2]])

        with open(argv[2], "ab") as obj:
            check_call(["python",
                        kd,
                        "-i",
                        argv[1]],
                        stdout = obj)
        
        os.remove(argv[1])

    else:
        check_call(["python",
            embed,
            argv[1],
            argv[2]])

    exit(0)
