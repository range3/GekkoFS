################################################################################
# Copyright 2018-2021, Barcelona Supercomputing Center (BSC), Spain            #
# Copyright 2015-2021, Johannes Gutenberg Universitaet Mainz, Germany          #
#                                                                              #
# This software was partially supported by the                                 #
# EC H2020 funded project NEXTGenIO (Project ID: 671951, www.nextgenio.eu).    #
#                                                                              #
# This software was partially supported by the                                 #
# ADA-FS project under the SPPEXA project funded by the DFG.                   #
#                                                                              #
# This file is part of GekkoFS.                                                #
#                                                                              #
# GekkoFS is free software: you can redistribute it and/or modify              #
# it under the terms of the GNU General Public License as published by         #
# the Free Software Foundation, either version 3 of the License, or            #
# (at your option) any later version.                                          #
#                                                                              #
# GekkoFS is distributed in the hope that it will be useful,                   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of               #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
# GNU General Public License for more details.                                 #
#                                                                              #
# You should have received a copy of the GNU General Public License            #
# along with GekkoFS.  If not, see <https://www.gnu.org/licenses/>.            #
#                                                                              #
# SPDX-License-Identifier: GPL-3.0-or-later                                    #
################################################################################

cmake_minimum_required(VERSION 3.6)

project(
    GekkoFS
    VERSION 0.8.0
)

enable_testing()

if (NOT CMAKE_COMPILER_IS_GNUCC)
    message(FATAL_ERROR "The choosen C compiler is not gcc and is not supported")
endif ()
if (NOT CMAKE_COMPILER_IS_GNUCXX)
    message(FATAL_ERROR "The choosen C++ compiler is not g++ and is not supported")
endif ()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release
        CACHE STRING "Choose the type of build: Debug Release Memcheck" FORCE)
ENDIF (NOT CMAKE_BUILD_TYPE)
message(STATUS "[gekkofs] Build type: ${CMAKE_BUILD_TYPE}")

# Compiler flags for various cmake build types
set(WARNINGS_FLAGS "-Wall -Wextra --pedantic -Wno-unused-parameter -Wno-missing-field-initializers")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -DNDEBUG -O3")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} ${WARNINGS_FLAGS} -g -O0 -DGKFS_DEBUG_BUILD -DHERMES_DEBUG_BUILD")
set(CMAKE_CXX_FLAGS_MEMCHECK "${WARNINGS_FLAGS} -g -O0 -fsanitize=address -fno-omit-frame-pointer")
set(CMAKE_CXX_FLAGS_MAINTAINER "${WARNINGS_FLAGS} -g -O0 -pg -no-pie")
set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -DNDEBUG -O3")
set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} ${WARNINGS_FLAGS} -g -O0 -DGKFS_DEBUG_BUILD")
set(CMAKE_C_FLAGS_MEMCHECK "${WARNINGS_FLAGS} -g -O0 -fsanitize=address -fno-omit-frame-pointer")
set(CMAKE_C_FLAGS_MAINTAINER "${WARNINGS_FLAGS} -g -O0 -pg -no-pie")
mark_as_advanced(CMAKE_CXX_FLAGS_MAINTAINER)

# Project version
set(GIT_VERSION_FOUND FALSE)
if (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/.git)
    find_package(Git)
    if (Git_FOUND)
        execute_process(COMMAND /bin/bash -c "${GIT_EXECUTABLE} describe --tags --match='v*.*.*' --long --dirty"
            WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
            RESULT_VARIABLE GIT_RET
            OUTPUT_VARIABLE GIT_VERSION
            ERROR_VARIABLE GIT_ERR
            OUTPUT_STRIP_TRAILING_WHITESPACE
            )
        if ("${GIT_RET}" STREQUAL "0")
            string(REGEX MATCH
                "^v([0-9]+)\.([0-9]+)\.([0-9]+)-([0-9]+)-(.*)$"
                DROP ${GIT_VERSION})
            set(PROJECT_VERSION_MAJOR ${CMAKE_MATCH_1})
            set(PROJECT_VERSION_MINOR ${CMAKE_MATCH_2})
            set(PROJECT_VERSION_PATCH ${CMAKE_MATCH_3})
            set(GKFS_COMMIT_GAP ${CMAKE_MATCH_4})
            set(GKFS_COMMIT_HASH ${CMAKE_MATCH_5})
            set(PROJECT_VERSION "${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}-snapshot+${GKFS_COMMIT_GAP}-${GKFS_COMMIT_HASH}")
            set(GIT_VERSION_FOUND TRUE)
        else ()
            message(WARNING "Failed to run `git describe`: [${GIT_RET}] '${GIT_ERR}'")
        endif ()
    endif ()
endif ()
message(STATUS "[gekkofs] Project version: ${PROJECT_VERSION}")
set(GKFS_VERSION_MAJOR ${PROJECT_VERSION_MAJOR})
set(GKFS_VERSION_MINOR ${PROJECT_VERSION_MINOR})
set(GKFS_VERSION_PATCH ${PROJECT_VERSION_PATCH})
set(GKFS_VERSION_STRING ${PROJECT_VERSION})
configure_file(include/version.hpp.in include/version.hpp)

set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/CMake" ${CMAKE_MODULE_PATH})


################################################################################
## Coverage generation support:
## ============================
## 
## The `gkfs-code-coverage' module enables the GKFS_ENABLE_CODE_COVERAGE option
## as well as the target_code_coverage() function.
################################################################################
include(gkfs-code-coverage)

set(CMAKE_EXPORT_COMPILE_COMMANDS 1)

# Rocksdb dependencies
find_package(LZ4 REQUIRED)
find_package(ZLIB REQUIRED)
find_package(BZip2 REQUIRED)
find_package(Snappy REQUIRED)
find_package(ZStd REQUIRED)
find_package(JeMalloc) # required if rocksdb has been build with jemalloc
find_package(RocksDB REQUIRED)
# margo dependencies
find_package(Mercury REQUIRED)
find_package(Abt REQUIRED)
find_package(Margo REQUIRED)
find_package(Syscall_intercept REQUIRED)

# boost dependencies
find_package(Boost 1.53 REQUIRED
    COMPONENTS
    program_options
    )

find_package(Threads REQUIRED)

find_package(Date REQUIRED)

option(CREATE_CHECK_PARENTS "Check parent directory existance before creating child node" ON)
message(STATUS "[gekkofs] Create checks parents: ${CREATE_CHECK_PARENTS}")

option(SYMLINK_SUPPORT "Compile with support for symlinks" ON)
if (SYMLINK_SUPPORT)
    add_definitions(-DHAS_SYMLINKS)
endif ()
message(STATUS "[gekkofs] Symlink support: ${SYMLINK_SUPPORT}")

set(MAX_INTERNAL_FDS 256 CACHE STRING "Number of file descriptors reserved for internal use")
add_definitions(-DMAX_INTERNAL_FDS=${MAX_INTERNAL_FDS})
message(STATUS "[gekkofs] File descriptors reserved for internal use: ${MAX_INTERNAL_FDS}")

execute_process(COMMAND getconf OPEN_MAX
    OUTPUT_VARIABLE GETCONF_MAX_FDS
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
if (NOT GETCONF_MAX_FDS)
    set(GETCONF_MAX_FDS=512)
endif ()
add_definitions(-DMAX_OPEN_FDS=${GETCONF_MAX_FDS})

option(ENABLE_CLIENT_LOG "Enable logging messages" ON)
if (ENABLE_CLIENT_LOG)
    add_definitions(-DGKFS_ENABLE_LOGGING)
endif ()
message(STATUS "[gekkofs] Client logging output: ${ENABLE_CLIENT_LOG}")

option(GKFS_ENABLE_FORWARDING "Enable forwarding mode" OFF)
option(GKFS_ENABLE_AGIOS "Enable AGIOS scheduling library" OFF)
if (GKFS_ENABLE_AGIOS)
    find_package(AGIOS REQUIRED)
endif ()


set(CLIENT_LOG_MESSAGE_SIZE 1024 CACHE STRING "Maximum size of a log message in the client library")
add_definitions(-DLIBGKFS_LOG_MESSAGE_SIZE=${CLIENT_LOG_MESSAGE_SIZE})
message(STATUS "[gekkofs] Maximum log message size in the client library: ${CLIENT_LOG_MESSAGE_SIZE}")
mark_as_advanced(CLIENT_LOG_MESSAGE_SIZE)

configure_file(include/global/cmake_configure.hpp.in include/global/cmake_configure.hpp)

# Imported target
add_library(RocksDB INTERFACE IMPORTED GLOBAL)
target_link_libraries(RocksDB
    INTERFACE
    ${ROCKSDB_LIBRARIES}
    # rocksdb libs
    ${Snappy_LIBRARIES}
    ${ZLIB_LIBRARIES}
    ${BZIP2_LIBRARIES}
    ${ZStd_LIBRARIES}
    ${LZ4_LIBRARIES}
    )

if (${JeMalloc_FOUND})
    target_link_libraries(RocksDB
        INTERFACE
        ${JEMALLOC_LIBRARIES}
        )
endif ()
# we cannot use target_include_directories with CMake < 3.11
set_target_properties(RocksDB
    PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES ${ROCKSDB_INCLUDE_DIRS}
    )

add_library(spdlog INTERFACE)
# we cannot use target_include_directories with CMake < 3.11
set_target_properties(spdlog
    PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${CMAKE_SOURCE_DIR}/external"
    )

add_subdirectory(external/fmt)
set_property(TARGET fmt PROPERTY POSITION_INDEPENDENT_CODE ON)

if (ENABLE_CLIENT_LOG)
    option(HERMES_LOGGING "" ON)
    option(HERMES_LOGGING_FMT_USE_BUNDLED "" OFF)
    option(HERMES_LOGGING_FMT_HEADER_ONLY "" OFF)
endif ()

option(HERMES_MARGO_COMPATIBLE_RPCS "" ON)
add_subdirectory(external/hermes)
target_compile_definitions(hermes INTERFACE)

set(INCLUDE_DIR "${CMAKE_SOURCE_DIR}/include")

# define include directories that are relevant for all targets
include_directories(
    ${INCLUDE_DIR}
    ${CMAKE_BINARY_DIR}/include
)

include(GNUInstallDirs)

# Global components
add_subdirectory(src/global)
# Daemon
add_subdirectory(src/daemon)
# Client library
add_subdirectory(src/client)

option(GKFS_BUILD_TESTS "Build GekkoFS self tests" OFF)

include(CMakeDependentOption)
cmake_dependent_option(GKFS_INSTALL_TESTS "Install GekkoFS self tests" OFF "GKFS_BUILD_TESTS" OFF)

if (GKFS_BUILD_TESTS)
    # check symbols exists doesn't work for statx. This is a workaround
    check_cxx_source_compiles("
        #include <fcntl.h>
        #include <sys/stat.h>

        int main() {
            struct statx buf;
            statx(AT_FDCWD, \"/foo\", AT_EMPTY_PATH, STATX_BASIC_STATS, &buf);
            return 0;
        }
        " GLIBC_HAS_STATX)
    # STATX_TYPE must be set for c++17 for statx() to be found for tests
    if (GLIBC_HAS_STATX)
        add_definitions(-DSTATX_TYPE=1)
    endif ()
    message(STATUS "[gekkofs] Preparing tests...")
    set(GKFS_TESTS_INTERFACE "lo" CACHE STRING "Network interface to use when running tests (default: lo)")
    message(STATUS "[gekkofs] Network interface for tests: ${GKFS_TESTS_INTERFACE}")

    message(STATUS "[gekkofs] Check for forwarding tests...")
    if (ENABLE_FORWARDING)
        set(GKFS_TESTS_FORWARDING "ON" CACHE STRING "Enable I/O forwarding tests (default: OFF)")
    else ()
        set(GKFS_TESTS_FORWARDING "OFF" CACHE STRING "Enable I/O forwarding tests (default: OFF)")
    endif ()
    message(STATUS "[gekkofs] Forwarding tests: ${GKFS_TESTS_FORWARDING}")

    add_subdirectory(tests)
    add_subdirectory(examples/gfind)
else()
    unset(GKFS_TESTS_INTERFACE CACHE)
endif()

# test
add_subdirectory(test)
