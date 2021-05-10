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

find_path(DATE_INCLUDE_DIR
    NAMES date/date.h
)

find_path(TZ_INCLUDE_DIR
    NAMES date/tz.h
)

find_library(TZ_LIBRARY
    NAMES tz
)
if(NOT Date_FOUND)
    find_library(TZ_LIBRARY
        NAMES date-tz
    )
endif()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args( Date 
    DEFAULT_MSG 
    DATE_INCLUDE_DIR
    TZ_INCLUDE_DIR
    TZ_LIBRARY
)

if(Date_FOUND)
    set(DATE_INCLUDE_DIRS ${DATE_INCLUDE_DIR})
    set(TZ_INCLUDE_DIRS ${TZ_INCLUDE_DIR})
    set(TZ_LIBRARIES ${TZ_LIBRARY})

    if(NOT TARGET Date::TZ)
        add_library(Date::TZ UNKNOWN IMPORTED)
        set_target_properties(Date::TZ PROPERTIES
            IMPORTED_LOCATION "${TZ_LIBRARY}"
            INTERFACE_COMPILE_DEFINITIONS "USE_OS_TZDB=1"
            INTERFACE_INCLUDE_DIRECTORIES "${TZ_INCLUDE_DIR}"
        )
    endif()
endif()

mark_as_advanced(
    DATE_INCLUDE_DIR
    TZ_INCLUDE_DIR
    TZ_LIBRARY
)
