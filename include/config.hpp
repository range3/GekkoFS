/*
  Copyright 2018-2021, Barcelona Supercomputing Center (BSC), Spain
  Copyright 2015-2021, Johannes Gutenberg Universitaet Mainz, Germany

  This software was partially supported by the
  EC H2020 funded project NEXTGenIO (Project ID: 671951, www.nextgenio.eu).

  This software was partially supported by the
  ADA-FS project under the SPPEXA project funded by the DFG.

  This file is part of GekkoFS.

  GekkoFS is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  GekkoFS is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with GekkoFS.  If not, see <https://www.gnu.org/licenses/>.

  SPDX-License-Identifier: GPL-3.0-or-later
*/

#ifndef GEKKOFS_CONFIG_HPP
#define GEKKOFS_CONFIG_HPP

#include <global/cmake_configure.hpp>

// environment prefixes (are concatenated in env module at compile time)
#define CLIENT_ENV_PREFIX "LIBGKFS_"
#define DAEMON_ENV_PREFIX "GKFS_"

namespace gkfs::config {

constexpr auto hostfile_path = "./gkfs_hosts.txt";
constexpr auto forwarding_file_path = "./gkfs_forwarding.map";

namespace io {
/*
 * Zero buffer before read. This is relevant if sparse files are used.
 * If buffer is not zeroed, sparse regions contain invalid data.
 */
constexpr auto zero_buffer_before_read = false;
} // namespace io

namespace log {
constexpr auto client_log_path = "/tmp/gkfs_client.log";
constexpr auto daemon_log_path = "/tmp/gkfs_daemon.log";

constexpr auto client_log_level = "info,errors,critical,hermes";
constexpr auto daemon_log_level = 4; // info
} // namespace log

namespace metadata {
// which metadata should be considered apart from size and mode
constexpr auto use_atime = false;
constexpr auto use_ctime = true;
constexpr auto use_mtime = true;
constexpr auto use_link_cnt = false;
constexpr auto use_blocks = false;
/*
 * If true, all chunks on the same host are removed during a metadata remove
 * rpc. This is a technical optimization that reduces the number of RPCs for
 * remove operations. This setting could be useful for future asynchronous
 * remove implementations where the data should not be removed immediately.
 */
constexpr auto implicit_data_removal = true;

// metadata logic
// Check for existence of file metadata before create. This done on RocksDB
// level
constexpr auto create_exist_check = true;
} // namespace metadata

namespace rpc {
constexpr auto chunksize = 524288; // in bytes (e.g., 524288 == 512KB)
// size of preallocated buffer to hold directory entries in rpc call
constexpr auto dirents_buff_size = (8 * 1024 * 1024); // 8 mega
/*
 * Indicates the number of concurrent progress to drive I/O operations of chunk
 * files to and from local file systems The value is directly mapped to created
 * Argobots xstreams, controlled in a single pool with ABT_snoozer scheduler
 */
constexpr auto daemon_io_xstreams = 8;
// Number of threads used for RPC handlers at the daemon
constexpr auto daemon_handler_xstreams = 8;
} // namespace rpc

namespace rocksdb {
// Write-ahead logging of rocksdb
constexpr auto use_write_ahead_log = false;
} // namespace rocksdb

} // namespace gkfs::config

#endif // GEKKOFS_CONFIG_HPP
