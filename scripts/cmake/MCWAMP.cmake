if(POLICY CMP0046)
  cmake_policy(PUSH)
  cmake_policy(SET CMP0046 OLD)
endif()

# MCWAMP
set(MCWAMP_INC_DIR "${PROJECT_SOURCE_DIR}/include")

# Additional compile-time options for HCC runtime could be set via:
# - HCC_RUNTIME_CFLAGS
#
# For example: cmake -DHCC_RUNTIME_CFLAGS=-g would configure HCC runtime be built
# with debug information while other parts are not.

macro(amp_target name )
  set(CMAKE_CXX_COMPILER "${PROJECT_BINARY_DIR}/compiler/bin/hcc")
  add_compile_options(-std=c++11)
  target_compile_definitions(${name} PRIVATE "GTEST_HAS_TR1_TUPLE=0")
  target_include_directories(${name} SYSTEM PRIVATE ${GTEST_INC_DIR})
  target_include_directories(${name} PRIVATE ${MCWAMP_INC_DIR})
  target_include_directories(${name} SYSTEM INTERFACE $<INSTALL_INTERFACE:$<INSTALL_PREFIX>/include>)
  target_compile_options(${name} PUBLIC -std=c++amp -fPIC)

  # Enable debug line info only if it's a release build and HCC_RUNTIME_DEBUG is OFF
  # Otherwise, -gline-tables-only would override other existing debug flags
  if ((NOT HCC_RUNTIME_DEBUG) AND ("${CMAKE_BUILD_TYPE}" STREQUAL "Release"))
	  target_compile_options(${name} PUBLIC -gline-tables-only)
  endif ((NOT HCC_RUNTIME_DEBUG) AND ("${CMAKE_BUILD_TYPE}" STREQUAL "Release"))
endmacro(amp_target name )

####################
# C++AMP runtime interface (mcwamp) 
####################
macro(add_mcwamp_library name )
  add_library( ${name} ${ARGN} )
  amp_target(${name})
  target_link_libraries(${name} PRIVATE unwind)
  # LLVM and Clang shall be compiled beforehand
  add_dependencies(${name} llvm-link opt clang rocdl)
endmacro(add_mcwamp_library name )

if(POLICY CMP0046)
  cmake_policy(POP)
endif()
