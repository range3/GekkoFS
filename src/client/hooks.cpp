/*
  Copyright 2018-2019, Barcelona Supercomputing Center (BSC), Spain
  Copyright 2015-2019, Johannes Gutenberg Universitaet Mainz, Germany

  This software was partially supported by the
  EC H2020 funded project NEXTGenIO (Project ID: 671951, www.nextgenio.eu).

  This software was partially supported by the
  ADA-FS project under the SPPEXA project funded by the DFG.

  SPDX-License-Identifier: MIT
*/

#include "client/hooks.hpp"
#include "client/preload.hpp"
#include "client/adafs_functions.hpp"
#include "client/resolve.hpp"
#include "client/open_dir.hpp"
#include "global/path_util.hpp"

#include <libsyscall_intercept_hook_point.h>
#include <sys/stat.h>
#include <fcntl.h>


static inline int with_errno(int ret) {
    return (ret < 0)? -errno : ret;
}


int hook_openat(int dirfd, const char *cpath, int flags, mode_t mode) {

    CTX->log()->trace("{}() called with fd: {}, path: {}, flags: {}, mode: {}",
                       __func__, dirfd, cpath, flags, mode);

    std::string resolved;
    auto rstatus = CTX->relativize_fd_path(dirfd, cpath, resolved);
    switch(rstatus) {
        case RelativizeStatus::fd_unknown:
            return syscall_no_intercept(SYS_openat, dirfd, cpath, flags, mode);

        case RelativizeStatus::external:
            return syscall_no_intercept(SYS_openat, dirfd, resolved.c_str(), flags, mode);

        case RelativizeStatus::fd_not_a_dir:
            return -ENOTDIR;

        case RelativizeStatus::internal:
            return with_errno(adafs_open(resolved, mode, flags));

        default:
            CTX->log()->error("{}() relativize status unknown: {}", __func__);
            return -EINVAL;
    }
}

int hook_close(int fd) {
    CTX->log()->trace("{}() called with fd {}", __func__, fd);
    if(CTX->file_map()->exist(fd)) {
        // No call to the daemon is required
        CTX->file_map()->remove(fd);
        return 0;
    }
    return syscall_no_intercept(SYS_close, fd);
}

int hook_stat(const char* path, struct stat* buf) {
    CTX->log()->trace("{}() called with path '{}'", __func__, path);
    std::string rel_path;
    if (CTX->relativize_path(path, rel_path, false)) {
            return with_errno(adafs_stat(rel_path, buf));
    }
    return syscall_no_intercept(SYS_stat, rel_path.c_str(), buf);
}

int hook_lstat(const char* path, struct stat* buf) {
    CTX->log()->trace("{}() called with path '{}'", __func__, path);
    std::string rel_path;
    if (CTX->relativize_path(path, rel_path)) {
        return with_errno(adafs_stat(rel_path, buf));
    }
    return syscall_no_intercept(SYS_lstat, rel_path.c_str(), buf);
}

int hook_fstat(unsigned int fd, struct stat* buf) {
    CTX->log()->trace("{}() called with fd '{}'", __func__, fd);
    if (CTX->file_map()->exist(fd)) {
        auto path = CTX->file_map()->get(fd)->path();
        return with_errno(adafs_stat(path, buf));
    }
    return syscall_no_intercept(SYS_fstat, fd, buf);
}

int hook_read(int fd, void* buf, size_t count) {
    CTX->log()->trace("{}() called with fd {}, count {}", __func__, fd, count);
    if (CTX->file_map()->exist(fd)) {
        auto ret = adafs_read(fd, buf, count);
        if(ret < 0) {
            return -errno;
        }
        return ret;
    }
    return syscall_no_intercept(SYS_read, fd, buf, count);
}

int hook_write(int fd, void* buf, size_t count) {
    CTX->log()->trace("{}() called with fd {}, count {}", __func__, fd, count);
    if (CTX->file_map()->exist(fd)) {
        auto ret = adafs_write(fd, buf, count);
        if(ret < 0) {
            return -errno;
        }
        return ret;
    }
    return syscall_no_intercept(SYS_write, fd, buf, count);
}

int hook_unlinkat(int dirfd, const char * cpath, int flags) {
    CTX->log()->trace("{}() called with path '{}' dirfd {}, flags {}",
                      __func__, cpath, dirfd, flags);

    if ((flags & ~AT_REMOVEDIR) != 0) {
        CTX->log()->error("{}() Flags unknown: {}", __func__, flags);
        return -EINVAL;
    }

    std::string resolved;
    auto rstatus = CTX->relativize_fd_path(dirfd, cpath, resolved, false);
    switch(rstatus) {
        case RelativizeStatus::fd_unknown:
            return syscall_no_intercept(SYS_unlinkat, dirfd, cpath, flags);

        case RelativizeStatus::external:
            return syscall_no_intercept(SYS_unlinkat, dirfd, resolved.c_str(), flags);

        case RelativizeStatus::fd_not_a_dir:
            return -ENOTDIR;

        case RelativizeStatus::internal:
            if(flags & AT_REMOVEDIR) {
                return with_errno(adafs_rmdir(resolved));
            } else {
                return with_errno(adafs_rm_node(resolved));
            }

        default:
            CTX->log()->error("{}() relativize status unknown: {}", __func__);
            return -EINVAL;
    }
}

int hook_access(const char* path, int mask) {
    CTX->log()->trace("{}() called path '{}', mask {}", __func__, path, mask);
    std::string rel_path;
    if (CTX->relativize_path(path, rel_path)) {
        auto ret = adafs_access(rel_path, mask);
        if(ret < 0) {
            return -errno;
        }
        return ret;
    }
    return syscall_no_intercept(SYS_access, rel_path.c_str(), mask);
}

int hook_lseek(unsigned int fd, off_t offset, unsigned int whence) {
    CTX->log()->trace("{}() called with fd {}, offset {}, whence {}", __func__, fd, offset, whence);
    if (CTX->file_map()->exist(fd)) {
        auto off_ret = adafs_lseek(fd, static_cast<off64_t>(offset), whence);
        if (off_ret > std::numeric_limits<off_t>::max()) {
            return -EOVERFLOW;
        } else if(off_ret < 0) {
            return -errno;
        }
        CTX->log()->trace("{}() returning {}", __func__, off_ret);
        return off_ret;
    }
   return syscall_no_intercept(SYS_lseek, fd, offset, whence);
}

int hook_dup(unsigned int fd) {
    CTX->log()->trace("{}() called with oldfd {}", __func__, fd);
    if (CTX->file_map()->exist(fd)) {
        return with_errno(adafs_dup(fd));
    }
    return syscall_no_intercept(SYS_dup, fd);
}

int hook_dup2(unsigned int oldfd, unsigned int newfd) {
    CTX->log()->trace("{}() called with fd {} newfd {}", __func__, oldfd, newfd);
    if (CTX->file_map()->exist(oldfd)) {
        return with_errno(adafs_dup2(oldfd, newfd));
    }
    return syscall_no_intercept(SYS_dup2, oldfd, newfd);
}

int hook_dup3(unsigned int oldfd, unsigned int newfd, int flags) {
    if (CTX->file_map()->exist(oldfd)) {
        // TODO implement O_CLOEXEC flag first which is used with fcntl(2)
        // It is in glibc since kernel 2.9. So maybe not that important :)
        CTX->log()->warn("{}() Not supported", __func__);
        return -ENOTSUP;
    }
    return syscall_no_intercept(SYS_dup3, oldfd, newfd, flags);
}

int hook_getdents(unsigned int fd, struct linux_dirent *dirp, unsigned int count) {
    CTX->log()->trace("{}() called with fd {}, count {}", __func__, fd, count);
    if (CTX->file_map()->exist(fd)) {
        return with_errno(getdents(fd, dirp, count));
    }
    return syscall_no_intercept(SYS_getdents, fd, dirp, count);
}

int hook_mkdirat(int dirfd, const char * cpath, mode_t mode) {
    CTX->log()->trace("{}() called with fd: {}, path: {}, mode: {}",
                      __func__, dirfd, cpath, mode);

    std::string resolved;
    auto rstatus = CTX->relativize_fd_path(dirfd, cpath, resolved);
    switch(rstatus) {
        case RelativizeStatus::external:
            return syscall_no_intercept(SYS_mkdirat, dirfd, resolved.c_str(), mode);

        case RelativizeStatus::fd_unknown:
            return syscall_no_intercept(SYS_mkdirat, dirfd, cpath, mode);

        case RelativizeStatus::fd_not_a_dir:
            return -ENOTDIR;

        case RelativizeStatus::internal:
            return with_errno(adafs_mk_node(resolved, mode | S_IFDIR));

        default:
            CTX->log()->error("{}() relativize status unknown: {}", __func__);
            return -EINVAL;
    }
}
