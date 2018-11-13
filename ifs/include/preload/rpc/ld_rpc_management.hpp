
#ifndef IFS_MARGO_IPC_HPP
#define IFS_MARGO_IPC_HPP

#include <preload/preload.hpp>
#include <global/rpc/rpc_types.hpp>


void send_minimal_ipc(const hg_id_t minimal_id);

bool ipc_send_get_fs_config();

#endif //IFS_MARGO_IPC_HPP
