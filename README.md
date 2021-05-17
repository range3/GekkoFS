# GekkoFS
forked from
- https://github.com/NGIOproject/GekkoFS
- https://storage.bsc.es/gitlab/hpc/gekkofs


# build with spack

## pre-requirements
```bash
# .bash_profile
source scl_source enable devtoolset-9
```

```bash
$ uname -a
Linux chris80 3.10.0-1160.21.1.el7.x86_64 #1 SMP Tue Mar 16 18:28:22 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux
$ cat /etc/redhat-release
CentOS Linux release 7.9.2009 (Core)
$  gcc -v
Using built-in specs.
COLLECT_GCC=gcc
COLLECT_LTO_WRAPPER=/opt/rh/devtoolset-9/root/usr/libexec/gcc/x86_64-redhat-linux/9/lto-wrapper
Target: x86_64-redhat-linux
Configured with: ../configure --enable-bootstrap --enable-languages=c,c++,fortran,lto --prefix=/opt/rh/devtoolset-9/root/usr --mandir=/opt/rh/devtoolset-9/root/usr/share/man --infodir=/opt/rh/devtoolset-9/root/usr/share/info --with-bugurl=http://bugzilla.redhat.com/bugzilla --enable-shared --enable-threads=posix --enable-checking=release --enable-multilib --with-system-zlib --enable-__cxa_atexit --disable-libunwind-exceptions --enable-gnu-unique-object --enable-linker-build-id --with-gcc-major-version-only --with-linker-hash-style=gnu --with-default-libstdcxx-abi=gcc4-compatible --enable-plugin --enable-initfini-array --with-isl=/builddir/build/BUILD/gcc-9.3.1-20200408/obj-x86_64-redhat-linux/isl-install --disable-libmpx --enable-gnu-indirect-function --with-tune=generic --with-arch_32=x86-64 --build=x86_64-redhat-linux
Thread model: posix
gcc version 9.3.1 20200408 (Red Hat 9.3.1-2) (GCC)

$ cmake --version
cmake3 version 3.17.5
```

## build with spack
```bash
$ git clone git@github.com:range3/GekkoFS.git
$ cd GekkoFS
$ git co -b gitlab/master-eval origin/gitlab/master-eval
$ git submodule update --init --recursive
# install deps using spack
$ spack env activate -d envs/chris80
$ spack install
# install a dep that spack doesn't hava a package for.
$ ./scripts/dl_dep.sh -d syscall_intercept $HOME/.local/src
$ ./scripts/compile_dep.sh -d syscall_intercept $HOME/.local/src $HOME/.local
# build GekkoFS
$ mkdir build
$ cd build
$ cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH=$HOME/.local \
  -DCMAKE_INSTALL_PREFIX=$HOME/.local \
  # optional: for convenience
  -DCMAKE_BUILD_WITH_INSTALL_RPATH=1 \
  -DCMAKE_INSTALL_RPATH=/path/to/gekkofs/envs/chris80/.spack-env/view/lib:/path/to/gekkofs/envs/chris80/.spack-env/view/lib64 \
  -DCMAKE_RUNTIME_OUTPUT_DIRECTORY=$(pwd)/bin \
  -DCMAKE_LIBRARY_OUTPUT_DIRECTORY=$(pwd)/lib \
  -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY=$(pwd)/lib 
$ cmake --build . -j
$ cmake --build . --target install
```
