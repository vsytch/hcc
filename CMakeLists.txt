cmake_minimum_required( VERSION 3.0 )
project (HCC)

SET(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/scripts/cmake")
MESSAGE("Module path: ${CMAKE_MODULE_PATH}")

# set as release build by default
IF (NOT CMAKE_BUILD_TYPE)
  SET(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build, options are: Release Debug" FORCE)
ENDIF(NOT CMAKE_BUILD_TYPE)

include (MCWAMP)

# Regression test
set(LLVM_SRC "${PROJECT_SOURCE_DIR}/compiler")
set(LLVM_ROOT "${PROJECT_BINARY_DIR}/compiler")

# obtain specific information about llvm setup
SET(LOCAL_LLVM_INCLUDE compiler/include)

# setup compilation environment
set(EXECUTABLE_OUTPUT_PATH "${CMAKE_BINARY_DIR}/bin" )
set(LIBRARY_OUTPUT_PATH "${CMAKE_BINARY_DIR}/lib" )

SET(PROJ_SEARCH_PATH "${PROJECT_BINARY_DIR}/include" "${PROJECT_SOURCE_DIR}/include" "${PROJECT_SOURCE_DIR}/${LOCAL_LLVM_INCLUDE}")
include_directories( ${PROJ_SEARCH_PATH} )

LINK_DIRECTORIES( ${LLVM_LIB_DIR} )

################
# Detect ROCm Device Libs
################

option(HCC_INTEGRATE_ROCDL "Build and use the ROCm Device Library integrated into HCC (Recommended)" ON)

if (NOT HCC_INTEGRATE_ROCDL)

  # If not using the integrated ROCm Device Library,
  # then the one installed on the system
  # or provided by a user
  find_path(ROCM_DEVICE_LIB ocml.amdgcn.bc
    PATH_SUFFIXES
      lib
    HINTS
      ${ROCM_DEVICE_LIB_DIR}
    PATHS
      ${ROCM_ROOT}/lib
  )

  if (NOT ROCM_DEVICE_LIB)
    MESSAGE(FATAL_ERROR "ROCm Device Libs not found. Use -DROCM_DEVICE_LIB=<path_to_ocml.amdgcn.bc>.")
  endif (NOT ROCM_DEVICE_LIB)

  set(ROCM_DEVICE_LIB_PATHS ${ROCM_DEVICE_LIB})
  list(APPEND ROCM_DEVICE_LIB_PATHS ${ROCM_DEVICE_LIB_DIR} ${ROCM_ROOT}/lib)
endif(NOT HCC_INTEGRATE_ROCDL)

#################
# Set up version information
#################

# define HCC version information
SET(KALMAR_VERSION_MAJOR "1")
SET(KALMAR_VERSION_MINOR "0")

include(GenerateVersionFromGit)

if (NOT KALMAR_VERSION_STRING)
  set(KALMAR_VERSION_STRING
    "${KALMAR_VERSION_MAJOR}.${KALMAR_VERSION_MINOR}")
endif()

# Set HCC version string. The rule for version string is:
# KALMAR_VERSION_MAJOR . KALMAR_VERSION_MINOR . KALMAR_VERSION_PATCH-KALMAR_SDK_COMIT-KALMAR_FRONTEND_COMMIT-KALMAR_BACKEND_COMMIT
add_version_info_from_git(KALMAR_VERSION_STRING
  KALMAR_VERSION_PATCH KALMAR_SDK_COMMIT KALMAR_FRONTEND_COMMIT KALMAR_BACKEND_COMMIT)

# set default installation path
set(INSTALL_DIR_NAME "hcc-${KALMAR_VERSION_MAJOR}.${KALMAR_VERSION_MINOR}")

# show HCC version string
MESSAGE("=============================================")
MESSAGE("HCC version: ${KALMAR_VERSION_STRING}")
MESSAGE("=============================================")

#################
# Detect AMDGPU backend for native codegen
#################

set(HSA_AMDGPU_GPU_TARGET "auto" CACHE STRING "Target AMDGPU ISA version")

# Tokenize HSA_AMDGPU_GPU_TARGET

# Temporary workaround for use of old long-form GFX_ip names, to be removed once
# we fully deprecate them.
string(REGEX MATCHALL "AMD:AMDGPU:(7:0:0|7:0:1|8:0:1|8:0:2|8:0:3|9:0:0|9:0:1)"
                      tmp
                      ${HSA_AMDGPU_GPU_TARGET})
foreach(long_form IN LISTS tmp)
  string(REPLACE "AMD:AMDGPU:" "gfx" short_form ${long_form})
  string(REPLACE ":" "" short_form ${short_form})
  message(DEPRECATION "Be advised that use of long-form GFX_ip names, such as \
                       ${long_form}, is deprecated. Please use the short-form: \
                       ${short_form}.")
  list(REMOVE_ITEM HSA_AMDGPU_GPU_TARGET ${long_form})
  list(APPEND HSA_AMDGPU_GPU_TARGET ${short_form})
endforeach()

# join list
string(REPLACE ";" " " AMDGPU_TARGET "${HSA_AMDGPU_GPU_TARGET}")
MESSAGE(STATUS "HCC configured with AMDGPU targets: ${AMDGPU_TARGET}")

#################
# Setup HCC backend macro string
# Possible values:
# - AMDGPU : for HSA systems configured with Lightning backend
#################

set(KALMAR_BACKEND "HCC_BACKEND_AMDGPU")

#########################
# build target: world
#########################

# build Clang frontend + AMDGPU backend
set(CLANG_SRC_DIR "${PROJECT_SOURCE_DIR}/compiler")
set(CLANG_BIN_DIR "${PROJECT_BINARY_DIR}/compiler")

if ("${CMAKE_BUILD_TYPE}" STREQUAL "Debug")
  set(LLVM_ENABLE_ASSERTIONS "On" CACHE BOOL "Compile with assertion checks enabled")
else ("${CMAKE_BUILD_TYPE}" STREQUAL "Debug")
  set(LLVM_ENABLE_ASSERTIONS "Off" CACHE BOOL "Compile with assertion checks enabled")
endif ("${CMAKE_BUILD_TYPE}" STREQUAL "Debug")

set(LLVM_EXTERNAL_CLANG_SOURCE_DIR "${PROJECT_SOURCE_DIR}/clang")
set(LLVM_EXTERNAL_LLD_SOURCE_DIR "${PROJECT_SOURCE_DIR}/lld")
set(LLVM_TARGETS_TO_BUILD "AMDGPU" "X86" CACHE STRING "" FORCE)
set(LLVM_INSTALL_TOOLCHAIN_ONLY ON CACHE BOOL "" FORCE)

add_subdirectory(${CLANG_SRC_DIR})

install(PROGRAMS $<TARGET_FILE:llvm-as>
                 $<TARGET_FILE:llvm-dis>
                 $<TARGET_FILE:llvm-link>
                 $<TARGET_FILE:llvm-objdump>
                 $<TARGET_FILE:llvm-mc>
                 $<TARGET_FILE:opt>
                 $<TARGET_FILE:llc>
        DESTINATION bin
        COMPONENT compiler)

# install certain LLVM libraries needed by HIP
install(PROGRAMS $<TARGET_FILE:LLVMAMDGPUDesc>
                 $<TARGET_FILE:LLVMAMDGPUUtils>
                 $<TARGET_FILE:LLVMMC>
                 $<TARGET_FILE:LLVMCore>
                 $<TARGET_FILE:LLVMSupport>
        DESTINATION lib
        COMPONENT compiler
)

add_custom_target(world DEPENDS clang)

# move headers to build dir before building rocdl and hcc lib
add_subdirectory(include)

if (HCC_INTEGRATE_ROCDL)

  set(ROCDL_SRC_DIR "${PROJECT_SOURCE_DIR}/rocdl")
  set(ROCDL_BUILD_DIR "${PROJECT_BINARY_DIR}/rocdl")
  file(MAKE_DIRECTORY ${ROCDL_BUILD_DIR})

  set(LLVM_DIR ${CLANG_BIN_DIR})
  set(AMDHSACOD ${AMDHSACOD})
  # override default option value in ROCDL
  set(GENERIC_IS_ZERO ON CACHE BOOL ON FORCE)
  set(BUILD_HC_LIB ON)
  set(AMDGCN_TARGETS_LIB_LIST "AMDGCN_LIB_TARGETS")
  find_package(LLVM REQUIRED CONFIG PATHS ${CMAKE_BINARY_DIR}/compiler NO_DEFAULT_PATH)

  list(APPEND CMAKE_MODULE_PATH "${LLVM_CMAKE_DIR}")
  include(AddLLVM)

  add_definitions(${LLVM_DEFINITIONS})

  # build rocdl
  add_subdirectory(${ROCDL_SRC_DIR})

  file(MAKE_DIRECTORY ${ROCDL_BUILD_DIR}/lib)
  add_custom_target(rocdl_links DEPENDS ${AMDGCN_LIB_TARGETS})
  add_custom_command(TARGET rocdl_links POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../irif/irif.amdgcn.bc                              irif.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../opencl/opencl.amdgcn.bc                          opencl.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../ockl/ockl.amdgcn.bc                              ockl.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../hc/hc.amdgcn.bc                                  hc.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_701.amdgcn.bc              oclc_isa_version_701.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_802.amdgcn.bc              oclc_isa_version_802.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_810.amdgcn.bc              oclc_isa_version_810.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_finite_only_on.amdgcn.bc               oclc_finite_only_on.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_900.amdgcn.bc              oclc_isa_version_900.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_finite_only_off.amdgcn.bc              oclc_finite_only_off.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_801.amdgcn.bc              oclc_isa_version_801.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_700.amdgcn.bc              oclc_isa_version_700.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_daz_opt_on.amdgcn.bc                   oclc_daz_opt_on.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_unsafe_math_off.amdgcn.bc              oclc_unsafe_math_off.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_800.amdgcn.bc              oclc_isa_version_800.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_daz_opt_off.amdgcn.bc                  oclc_daz_opt_off.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_unsafe_math_on.amdgcn.bc               oclc_unsafe_math_on.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_correctly_rounded_sqrt_off.amdgcn.bc   oclc_correctly_rounded_sqrt_off.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_803.amdgcn.bc              oclc_isa_version_803.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_correctly_rounded_sqrt_on.amdgcn.bc    oclc_correctly_rounded_sqrt_on.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_901.amdgcn.bc              oclc_isa_version_901.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../oclc/oclc_isa_version_804.amdgcn.bc              oclc_isa_version_804.amdgcn.bc
    COMMAND ${CMAKE_COMMAND} -E create_symlink ../ocml/ocml.amdgcn.bc                              ocml.amdgcn.bc
    WORKING_DIRECTORY ${ROCDL_BUILD_DIR}/lib
  )
  # install ROCm Device Library in hcc
  install(DIRECTORY ${ROCDL_BUILD_DIR}/hc
                    ${ROCDL_BUILD_DIR}/irif
                    ${ROCDL_BUILD_DIR}/lib
                    ${ROCDL_BUILD_DIR}/ockl
                    ${ROCDL_BUILD_DIR}/oclc
                    ${ROCDL_BUILD_DIR}/ocml
                    ${ROCDL_BUILD_DIR}/opencl
          DESTINATION rocdl
          PATTERN CMake* EXCLUDE
          PATTERN CPack* EXCLUDE
          PATTERN *.cmake EXCLUDE
          PATTERN Makefile EXCLUDE
          PATTERN test EXCLUDE
          PATTERN cuda2gcn EXCLUDE
          PATTERN *.lib.bc EXCLUDE
          PATTERN *.optout.bc EXCLUDE
          PATTERN src EXCLUDE
          PATTERN CMakeFiles EXCLUDE
          PATTERN transformed_src EXCLUDE
          PATTERN utils EXCLUDE
  )

  # create search paths for ROCDL
  list(APPEND ROCM_DEVICE_LIB_PATHS ${ROCDL_BUILD_DIR}/lib)
  if (NOT CPACK_SET_DESTDIR)
    list(APPEND ROCM_DEVICE_LIB_PATHS ${CPACK_PACKAGING_INSTALL_PREFIX}/rocdl/lib)
  endif(NOT CPACK_SET_DESTDIR)
  list(APPEND ROCM_DEVICE_LIB_PATHS ${CMAKE_INSTALL_PREFIX}/rocdl/lib)

endif(HCC_INTEGRATE_ROCDL)

#add_subdirectory(hcc_config)
add_subdirectory(lib)
#add_subdirectory(utils)
#add_subdirectory(tests)
#add_subdirectory(amp-conformance)

# control the list of package dependency depending on whether this is an official release build.
# for non-official release build, we want to relax the dependency on rocr runtime
if (OFFICIAL_RELEASE_BUILD)
  if (HCC_INTEGRATE_ROCDL)
    set(HCC_ROCR_DEP ", hsa-rocr-dev, hsa-ext-rocr-dev, rocm-utils")
  else (HCC_INTEGRATE_ROCDL)
    set(HCC_ROCR_DEP ", hsa-rocr-dev, hsa-ext-rocr-dev, rocm-device-libs, rocm-utils")
  endif(HCC_INTEGRATE_ROCDL)
else (OFFICIAL_RELEASE_BUILD)
  set(HCC_ROCR_DEP "")
endif (OFFICIAL_RELEASE_BUILD)

set(CPACK_COMPONENTS_ALL compiler)

include (CPack)
MESSAGE("")
MESSAGE("** For the first time:")
MESSAGE("   'make' to build all")
MESSAGE("   'make docs' to build the HTML API reference")
MESSAGE("")
