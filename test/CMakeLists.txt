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
project(GekkoFS_test LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS 1)


set(SOURCE_FILES main.cpp)
add_executable(gkfs_test ${SOURCE_FILES})

set(SOURCE_FILES_IO main_IO_testing.cpp)
add_executable(gkfs_test_IO ${SOURCE_FILES_IO})
add_executable(gkfs_test_IO_min IO_test.cpp)

set(SOURCE_FILES_TEMP main_temp.cpp)
add_executable(gkfs_test_temp ${SOURCE_FILES_TEMP})


add_executable(gkfs_test_wr wr_test.cpp)

add_executable(gkfs_test_dir dir_test.cpp)

add_executable(gkfs_test_truncate truncate.cpp)

add_executable(gkfs_test_lseek lseek.cpp)
add_executable(gkfs_test_symlink symlink_test.cpp)

find_package(MPI)
if(${MPI_FOUND})
    set(SOURCE_FILES_MPI main_MPI.cpp)
    add_executable(gkfs_test_MPI ${SOURCE_FILES_MPI})
    if(TARGET MPI::MPI_CXX)
        # should be defined for CMAKE > 3.9
        target_link_libraries(gkfs_test_MPI MPI::MPI_CXX ${MPI_LIBRARIES})
    else()
        target_link_libraries(gkfs_test_MPI ${MPI_CXX_LIBRARIES})
        target_include_directories(gkfs_test_MPI PUBLIC ${MPI_CXX_INCLUDE_PATH})
    endif()
endif()
