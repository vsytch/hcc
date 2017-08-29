#!/usr/bin/python
# Compiles an LLVM bitcode file to GCN ISA, and store as HSACO
# $1 = input ll name
# $2 = HSACO code object file name
# $3 = (optional) --amdgpu-target=(GPU family name)
#                          selects AMDGPU target

import os
from sys import argv, exit
from tempfile import mkdtemp
from shutil import rmtree, copyfile
from subprocess import Popen, check_call, check_output, PIPE, call

if __name__ == "__main__":

    if len(argv) < 2:
        print("Usage: %s input_LLVM output_hsaco_kernel (--amdgpu-target=(GPU family name)" % argv[0])
        print("  --amdgpu-target=(GPU family name)")
        print("           selects AMDGPU target")
        exit(1)

    if not os.path.isfile(argv[1]):
        print("input LLVM IR %s is not valid" % argv[1])
        exit(1)

    bindir = os.path.dirname(argv[0])
    _as = bindir + "/llvm-as"
    opt = bindir + "/opt"
    llc = bindir + "/llc"
    link = bindir + "/llvm-link"
    lib = bindir + "/../lib"
    lld = bindir + "/ld.lld"
    llvm_dis = bindir + "/llvm-dis"
    llvm_objdump = bindir + "/llvm-objdump"
    dumpdir = os.getenv("HCC_DUMPDIR")
    dump = os.getenv("HCC_DUMP")

    if not dumpdir:
        dumpdir = "."
    dumpdir += "/dump"

    if dump:
        if os.path.isdir(dumpdir):
            rmtree(dumpdir)
        os.mkdir(dumpdir)

    if os.name == "nt":
        sl_ext = ".dll"
    else:
        sl_ext = ".so"

    ################
    # Determine the ROCm device libs path
    ################
    rocm_device_libs_search_paths = ["/home/vsytchenko/build/rocdl/lib",
        "/opt/rocm/hcc-1.0/rocdl/lib",
        bindir + "/../lib/rocdl/lib"]
    rocm_lib = ""
    for search_path in rocm_device_libs_search_paths:
        if os.path.isfile(search_path + "/ocml.amdgcn.bc"):
            rocm_lib = search_path
            break
    if not os.path.isfile(rocm_lib + "/ocml.amdgcn.bc"):
        print("ROCm Device Libs is missing")
        exit(1)

    ################
    # AMDGPU target
    ################
    args = argv[1:]
    amdgpu_target = ""

    for arg in args:
        ######################
        # Parse AMDGPU target
        ######################
        if arg.startswith("--amdgpu-target="):
            amdgpu_target = arg[16:]

    
    if dump:
        copyfile(argv[1], dumpdir + "/dump.input.bc")
        check_call([llvm_dis,
            dumpdir + "/dump.input.bc",
            "-o",
            dumpdir + "/dump.input.ll"])

    # Invoke HCC-specific opt passes
    f = open(argv[1], "rb")
    if os.name == "nt":
        p = Popen([opt,
            "-erase-nonkernels",
            "-dce",
            "-globaldce",
            "-o",
            argv[2] + ".promote.bc"],
            stdin = f)
    else:
        p = Popen([opt,
            "-load",
            lib + "/LLVMEraseNonkernel" + sl_ext,
            "-erase-nonkernels",
            "-dce",
            "-globaldce",
            "-o",
            argv[2] + ".promote.bc"],
            stdin = f)
    p.wait()
    f.close()
    retval = p.returncode
    if retval != 0:
        print("Generating AMD GCN kernel failed in HCC-specific opt passes for target: %s" % amdgpu_target)
        exit(retval)

    if dump:
        copyfile(argv[2] + ".promote.bc", dumpdir + "/dump.promote.bc")
        check_call([llvm_dis,
            dumpdir + "/dump.promote.bc",
            "-o",
            dumpdir + "/dump.promote.ll"])
    
    hcc_extra_arch_file = ""

    if amdgpu_target == "gfx700":
        oclc_isa_version_lib = rocm_lib + "/oclc_isa_version_700.amdgcn.bc"
    if amdgpu_target == "gfx701":
        oclc_isa_version_lib = rocm_lib + "/oclc_isa_version_701.amdgcn.bc"
    if amdgpu_target == "gfx801":
        oclc_isa_version_lib = rocm_lib + "/oclc_isa_version_801.amdgcn.bc"
    if amdgpu_target == "gfx802":
        oclc_isa_version_lib = rocm_lib + "/oclc_isa_version_802.amdgcn.bc"
    if amdgpu_target == "gfx803":
        oclc_isa_version_lib = rocm_lib + "/oclc_isa_version_803.amdgcn.bc"
    if amdgpu_target == "gfx900":
        oclc_isa_version_lib = rocm_lib + "/oclc_isa_version_900.amdgcn.bc"
    if amdgpu_target == "gfx901":
        oclc_isa_version_lib = rocm_lib + "/oclc_isa_version_901.amdgcn.bc"

    hcc_bc_libs = [(rocm_lib + '/' + lib_name + ".amdgcn.bc") for lib_name in [
        "hc",
        "opencl",
        "ocml",
        "ockl",
        "irif",
        "oclc_finite_only_off",
        "oclc_daz_opt_off",
        "oclc_correctly_rounded_sqrt_on",
        "oclc_unsafe_math_off"]]
    hcc_bc_libs.append(oclc_isa_version_lib)
    
    p = Popen([link,
        "-suppress-warnings",
        "-o",
        argv[2] + ".linked.bc",
        argv[2] + ".promote.bc"] +
        hcc_bc_libs)
    p.wait()
    retval = p.returncode
    if retval != 0:
       print("Generating AMD GCN kernel failed in llvm-link with ROCm-Device-Libs for target: %s" % amdgpu_target)
       exit(retval)

    if dump:
        copyfile(argv[2] + ".linked.bc", dumpdir + "/dump.linked.bc")
        check_call([llvm_dis,
            dumpdir + "/dump.linked.bc",
            "-o",
            dumpdir + "/dump.linked.ll"])

    p = Popen([opt,
        "-inline",
        "-inline-threshold=1048576",
        "-mtriple",
        "amdgcn--amdhsa-amdgiz",
        "-mcpu=" + amdgpu_target,
        "-infer-address-spaces",
        "-amdgpu-internalize-symbols",
        "-disable-simplify-libcalls",
        "-O3",
        "-verify",
        argv[2] + ".linked.bc",
        "-o",
        argv[2] + ".opt.bc"])
    p.wait()
    retval = p.returncode
    if retval != 0:
        print("Generating AMD GCN kernel failed in opt for target: %s" % amdgpu_target)
        exit(retval)

    if dump:
        copyfile(argv[2] + ".opt.bc", dumpdir + "/dump.opt.bc")
        check_call([llvm_dis,
            dumpdir + "/dump.opt.bc",
            "-o",
            dumpdir + "/dump.opt.ll"])

    p = Popen([llc,
        "-O2",
        "-mtriple",
        "amdgcn--amdhsa-amdgiz",
        "-mcpu=" + amdgpu_target,
        "-filetype=obj",
        "-o",
        argv[2] + ".isabin",
        argv[2] + ".opt.bc"])
    p.wait()
    retval = p.returncode
    if retval != 0:
        print("Generating AMD GCN kernel failed in llc for target: %s" % amdgpu_target)
        exit(retval)

    if dump:
        copyfile(argv[1], dumpdir + "/dump-" + amdgpu_target + ".isabin")
            
    p = Popen([lld,
        "-shared",
        argv[2] + ".isabin",
        "-o",
        argv[2]])
    p.wait()
    retval = p.returncode
    if retval != 0:
        print("Generating AMD GCN kernel failed in ld.lld for target: %s" % amdgpu_target)
        exit(retval)
    
    if dump:
        copyfile(argv[2], dumpdir + "/dump.hsaco")
        f = open(dumpdir + "/dump-" + amdgpu_target + ".isa", "w")
        check_call([llvm_objdump,
            "-disassemble",
            "-mcpu=gfx803",
            dumpdir + "/dump.hsaco"],
            stdout = f)
        f.close()

    for ext in [".promote.bc", ".linked.bc", ".opt.bc", ".isabin"]:
        os.remove(argv[2] + ext)

    exit(0)
