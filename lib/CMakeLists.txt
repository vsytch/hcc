
option(HCC_RUNTIME_DEBUG "Enable debug build for HCC Runtime" OFF)

if (HCC_RUNTIME_DEBUG)
  add_compile_options(-g -O0)
endif (HCC_RUNTIME_DEBUG)

include_directories(${CMAKE_CURRENT_BINARY_DIR})

set( LIB_INSTALL_DIR ${CMAKE_INSTALL_LIBDIR} )
set( INCLUDE_INSTALL_DIR ${CMAKE_INSTALL_INCLUDEDIR} )
set( CONFIG_PACKAGE_INSTALL_DIR ${LIB_INSTALL_DIR}/cmake/hcc )

####################
# C++AMP runtime (mcwamp)
####################
add_mcwamp_library(mcwamp mcwamp.cpp)

####################
# C++AMP tools
####################
install(PROGRAMS ${PROJECT_BINARY_DIR}/compiler/bin/clamp-device.py
    ${PROJECT_BINARY_DIR}/compiler/bin/clamp-embed.py
    ${PROJECT_BINARY_DIR}/compiler/bin/clamp-assemble.py
    ${PROJECT_BINARY_DIR}/compiler/bin/clamp-link.py
    ${PROJECT_BINARY_DIR}/compiler/bin/hc-kernel-assemble.py
    ${PROJECT_BINARY_DIR}/compiler/bin/hc-host-assemble.py
    DESTINATION bin)

####################
# install targets
####################
install(TARGETS mcwamp
    EXPORT hcc-targets
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    )