# Copyright 2021 range3 (https://github.com/range3/)
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class SyscallIntercept(CMakePackage):
    """The system call intercepting library
    """

    homepage = "https://github.com/pmem/syscall_intercept"
    # url      = ""
    git      = "https://github.com/pmem/syscall_intercept.git"

    version('master',     branch='master')
    version('Sep-2-2020', commit='f7cebb7b7e7512a19b78a31ce236ad6ca22636dd')

    depends_on('cmake@3:')
    depends_on('capstone')

    patch('syscall_intercept.patch', when='@Sep-2-2020')

    def cmake_args(self):
        spec = self.spec

        args = [
            self.define('BUILD_TESTS', self.run_tests),
            self.define('BUILD_EXAMPLES', self.run_tests)
        ]

        return args
