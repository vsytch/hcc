import os
import argparse
import sys
import subprocess
import binascii

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fname")
    group = parser.add_mutually_exclusive_group(required = True)
    group.add_argument("-i", action = "store_true")
    group.add_argument("-e", action = "store_true")
    args = vars(parser.parse_args(sys.argv[1:]))
    
    if not os.path.isfile(args["fname"]):
        print("Couldn't find " + args["fname"], file = sys.stderr)
        sys.exit(1)

    if args["e"]:
        with open("dump.txt", "w") as dump:
            p1 = subprocess.Popen(["dumpbin",
                                    "/section:.kernel",
                                    args["fname"]],
                                    stdout = subprocess.PIPE)
            p2 = subprocess.Popen(["findstr",
                                    "/c:file pointer to raw data"],
                                    stdin = p1.stdout,
                                    stdout = dump)
            p1.wait()
            p2.wait()

        beg = 0
        with open("dump.txt", "r") as dump:
            line = dump.readline()
            pos = line.find("(")
            beg = int(line[(pos + 1):(pos + 9)], 16)

        with open(args["fname"], "rb") as kbin:
            kbin.seek(beg)
            size = int.from_bytes(kbin.read(4), byteorder = "little", signed = False)
            sys.stdout.buffer.write(kbin.read(size))

        os.remove("dump.txt")

    elif args["i"]:
        with open(args["fname"], "rb") as kbin:
            fname = os.path.splitext(os.path.basename(args["fname"]))[0]
            data = kbin.read()
            sys.stdout.write("\n#pragma section(\".kernel\")\n")
            sys.stdout.write("__declspec(allocate(\".kernel\"), selectany)\n")
            if args["fname"].endswith(".bundle"):
                sys.stdout.write("unsigned char " + "kernel_binary_data[] = {")
            else:
                sys.stdout.write("unsigned char " + "temp_kernel_binary_data[] = {")
            size = (os.path.getsize(args["fname"])).to_bytes(4, byteorder = "little", signed = False)
            sys.stdout.write("0x{:02x}".format(size[0]) + ",")
            sys.stdout.write("0x{:02x}".format(size[1]) + ",")
            sys.stdout.write("0x{:02x}".format(size[2]) + ",")
            sys.stdout.write("0x{:02x}".format(size[3]))
            for c in data:
                sys.stdout.write(" ,0x{:02x}".format(c))
            sys.stdout.write("};")

            
    sys.exit(0)
