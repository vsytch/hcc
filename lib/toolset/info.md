Installing the HCC toolset
==============================
- Under `C:\Program Files (x86)\MSBuild\Microsoft.Cpp\v4.0\V140\Platforms\x64\PlatformToolsets` create a folder `HCC`
- Copy `toolset.targets`, `toolset.props` and `ClangTasks.dll` to `C:\Program Files (x86)\MSBuild\Microsoft.Cpp\v4.0\V140\Platforms\x64\PlatformToolsets\HCC`

Using the HCC toolset
=====================
- From your build directory run `cmake -G "Visual Studio 14 Win64" -T HCC /path/to/CMakeLists.txt`
- To create a build (defaults to debug) run `msbuild ALL_BUILD.vcxproj`
- For a release build add `/p:Configuration=Release` to the command.
- For verbose output add `/p:Verbose=1` to the command.
