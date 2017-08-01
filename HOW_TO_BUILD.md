HCC on Windows
======================
- Clone `hcc-windows`
`git clone --recursive -b windows https://github.com/vsytch/hcc.git`
- Change branches of submodules
`git submodule update --remote`
- Copy the `clang` and `lld` folders to the `compiler/tools` folder
- Open the x64 Native Tools Command Promt for VS2015 (installed with Visual Studio 2015)
- Create a `build` folder in the `hcc` folder
- Fromt the `build` folder run the CMake command to generate the Visual Studio project for LLVM+Clang
`cmake -DLLVM_TARGETS_TO_BUILD="X86;AMDGPU" -G "Visual Studio 14 Win64" ../compiler`
- In the `build` folder, open `LLVM.sln`
- Change the build type from `Debug` to `Release` in the Visual Studio toolbar
- In the `Solution Explorer`, build the `ALL_BUILD` solution
- In the `lib` folder, compile `inject_kernel.cpp` using the following command - `cl inject_kernel.cpp /EHsc`
- Copy `inject_kernel.exe` to the `Release/bin` folder
- Copy the Python scripts to the `Release/bin` folder
- Add the `hcc/build/Release/bin` folder to your path
- In the `hcc/rocdl` folder run `build_rocdl.py` from the command line
- Copy the contents of the `hcc/rocdl/build/lib` folder to `hcc/release/lib/rocld/lib`
- To build a debug version of saxpy run, use the following command - `hcc_build debug saxpy.cpp`