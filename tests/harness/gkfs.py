################################################################################
#  Copyright 2018-2020, Barcelona Supercomputing Center (BSC), Spain           #
#  Copyright 2015-2020, Johannes Gutenberg Universitaet Mainz, Germany         #
#                                                                              #
#  This software was partially supported by the                                #
#  EC H2020 funded project NEXTGenIO (Project ID: 671951, www.nextgenio.eu).   #
#                                                                              #
#  This software was partially supported by the                                #
#  ADA-FS project under the SPPEXA project funded by the DFG.                  #
#                                                                              #
#  SPDX-License-Identifier: MIT                                                #
################################################################################

import os, sh, sys, re, pytest, signal
import random, socket, netifaces
from pathlib import Path
from itertools import islice
from harness.logger import logger
from harness.io import IOParser
from harness.cmd import CommandParser

### some definitions required to interface with the client/daemon
gkfs_daemon_cmd = 'gkfs_daemon'
gkfs_client_cmd = 'gkfs.io'
gkfs_client_lib_file = 'libgkfs_intercept.so'
gkfs_hosts_file = 'gkfs_hosts.txt'
gkfs_daemon_log_file = 'gkfs_daemon.log'
gkfs_daemon_log_level = '100'
gkfs_client_log_file = 'gkfs_client.log'
gkfs_client_log_level = 'all'
gkfs_daemon_active_log_pattern = r'Startup successful. Daemon is ready.'

def get_ip_addr(iface):
    return netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']

def get_ephemeral_host():
    """
    Returns a random IP in the 127.0.0.0/24. This decreases the likelihood of
    races for ports by 255^3.
    """

    res = '127.{}.{}.{}'.format(random.randrange(1, 255),
                                random.randrange(1, 255),
                                random.randrange(2, 255),)

    return res

def get_ephemeral_port(port=0, host=None):
    """
    Get an ephemeral socket at random from the kernel.

    Parameters
    ----------
    port: `str`
        If specified, use this port as a base and the next free port after that
        base will be returned.

    host: `str`
        If specified, use this host. Otherwise it will use a temporary IP in
        the 127.0.0.0/24 range

    Returns
    -------
    Available port to use
    """

    if host is None:
        host = get_ephemeral_host()

    # Dynamic port-range:
    # * cat /proc/sys/net/ipv4/ip_local_port_range
    # 32768   61000
    if port == 0:
        port = random.randrange(1024, 32768)

    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            port = s.getsockname()[1]
            s.close()
            return port
        except socket.error:
            port = random.randrange(1024, 32768)

def get_ephemeral_address(iface):
    """
    Get an ephemeral network address (IPv4:port) from an interface
    and a random port.

    Parameters
    ----------
    iface: `str`
        The interface that will be used to find out the IPv4 address
        for the ephemeral address.

    Returns
    -------
    A network address formed by iface's IPv4 address and an available
    randomly selected port.
    """

    return f"{iface}:{get_ephemeral_port(host=get_ip_addr(iface))}"

class Daemon:
    def __init__(self, interface, workspace):

        self._address = get_ephemeral_address(interface)
        self._workspace = workspace

        self._cmd = sh.Command(gkfs_daemon_cmd, self._workspace.bindirs)
        self._env = os.environ.copy()

        libdirs = ':'.join(
                filter(None, [os.environ.get('LD_LIBRARY_PATH', '')] +
                             [str(p) for p in self._workspace.libdirs]))

        self._patched_env = {
            'LD_LIBRARY_PATH'      : libdirs,
            'GKFS_HOSTS_FILE'      : self.cwd / gkfs_hosts_file,
            'GKFS_DAEMON_LOG_PATH' : self.logdir / gkfs_daemon_log_file,
            'GKFS_LOG_LEVEL'       : gkfs_daemon_log_level,
        }
        self._env.update(self._patched_env)

    def run(self):

        args = [ '--mountdir', self.mountdir,
                 '--rootdir', self.rootdir,
                 '-l', self._address ]

        logger.debug(f"spawning daemon")
        logger.debug(f"cmdline: {self._cmd} " + " ".join(map(str, args)))
        logger.debug(f"env: {self._patched_env}")

        self._proc = self._cmd(
                args,
                _env=self._env,
#                _out=sys.stdout,
#                _err=sys.stderr,
                _bg=True,
            )

        logger.debug(f"daemon process spawned (PID={self._proc.pid})")

        # make sure daemon is ready to accept requests
        if not self.wait_until_active(self._proc.pid):
            raise RuntimeError("GKFS daemon doesn't seem to be active")

        return self

    def wait_until_active(self, pid, retries=500, max_lines=50):
        """
        Waits until a GKFS daemon is active or until a certain number of retries
        has been exhausted. Checks if the daemon is running by searching its
        log for a pre-defined readiness message.

        Parameters
        ----------
        pid: `int`
            The PID of the daemon process to wait for.

        retries: `int`
            The number of retries before giving up.

        max_lines: `int`
            The maximum number of log lines to check for a match.

        Returns
        -------
        True if the message is found, False if the log file doesn't exist
        or the message can't be found.
        """

        gkfs_daemon_active_log_pattern = r'Startup successful. Daemon is ready.'

        is_active = False

        # wait a bit for the daemon to initialize
        sh.sleep(0.1)

        r = 0
        while not is_active and r < retries:
            r += 1
            try:
                #logger.debug(f"checking log file")
                with open(self.logdir / gkfs_daemon_log_file) as log:
                    for line in islice(log, max_lines):
                        if re.search(gkfs_daemon_active_log_pattern, line) is not None:
                            return True
            except FileNotFoundError:
                # Log is missing, the daemon might have crashed...
                logger.debug(f"daemon log file missing, checking if daemon is alive")

                pid=self._proc.pid
                try:
                    sh.ps(['-h', '-p', pid])
                except Exception:
                    logger.error(f"daemon process {pid} is not running")
                    raise

                # ... or it might just be lazy. let's give it some more time
                sh.sleep(0.05)
                pass

        return False

    def shutdown(self):
        logger.debug(f"terminating daemon")

        try:
            self._proc.terminate()
            err = self._proc.wait()
        except sh.SignalException_SIGTERM:
            pass

    @property
    def cwd(self):
        return self._workspace.twd

    @property
    def rootdir(self):
        return self._workspace.rootdir

    @property
    def mountdir(self):
        return self._workspace.mountdir

    @property
    def logdir(self):
        return self._workspace.logdir

    @property
    def interface(self):
        return self._interface

class _proxy_exec():
    def __init__(self, client, name):
        self._client = client
        self._name = name

    def __call__(self, *args, **kwargs):
        return self._client.run(self._name, *args, **kwargs)

class Client:
    """
    A class to represent a GekkoFS client process with a patched LD_PRELOAD.
    This class allows tests to interact with the file system using I/O-related
    function calls, be them system calls (e.g. read()) or glibc I/O functions
    (e.g. opendir()).
    """
    def __init__(self, workspace):
        self._parser = IOParser()
        self._workspace = workspace
        self._cmd = sh.Command(gkfs_client_cmd, self._workspace.bindirs)
        self._env = os.environ.copy()

        libdirs = ':'.join(
                filter(None, [os.environ.get('LD_LIBRARY_PATH', '')] +
                             [str(p) for p in self._workspace.libdirs]))

        # ensure the client interception library is available:
        # to avoid running code with potentially installed libraries,
        # it must be found in one (and only one) of the workspace's bindirs
        preloads = []
        for d in self._workspace.bindirs:
            search_path = Path(d) / gkfs_client_lib_file
            if search_path.exists():
                preloads.append(search_path)

        if len(preloads) != 1:
            logger.error(f'Multiple client libraries found in the test\'s binary directories:')
            for p in preloads:
                logger.error(f'  {p}')
            logger.error(f'Make sure that only one copy of the client library is available.')
            pytest.exit("Aborted due to initialization error")

        self._preload_library = preloads[0]

        self._patched_env = {
            'LD_LIBRARY_PATH'      : libdirs,
            'LD_PRELOAD'           : self._preload_library,
            'LIBGKFS_HOSTS_FILE'   : self.cwd / gkfs_hosts_file,
            'LIBGKFS_LOG'          : gkfs_client_log_level,
            'LIBGKFS_LOG_OUTPUT'   : self._workspace.logdir / gkfs_client_log_file
        }

        self._env.update(self._patched_env)

    @property
    def preload_library(self):
        """
        Return the preload library detected for this client
        """

        return self._preload_library

    def run(self, cmd, *args):
        logger.debug(f"running client")
        logger.debug(f"cmdline: {self._cmd} " + " ".join(map(str, list(args))))
        logger.debug(f"env: {self._patched_env}")

        out = self._cmd(
            [ cmd ] + list(args),
            _env = self._env,
    #        _out=sys.stdout,
    #        _err=sys.stderr,
            )

        logger.debug(f"command output: {out.stdout}")
        return self._parser.parse(cmd, out.stdout)

    def __getattr__(self, name):
        return _proxy_exec(self, name)

    @property
    def cwd(self):
        return self._workspace.twd

class ShellCommand:
    """
    A wrapper class for sh.RunningCommand that allows seamlessly using all
    its methods and properties plus extending it with additional methods
    for ease of use.
    """

    def __init__(self, cmd, proc):
        self._parser = CommandParser()
        self._cmd = cmd
        self._wrapped_proc = proc

    @property
    def parsed_stdout(self):
        return self._parser.parse(self._cmd, self._wrapped_proc.stdout.decode())

    @property
    def parsed_stderr(self):
        return self._parser.parse(self._cmd, self._wrapped_proc.stderr.decode())

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self._wrapped_proc, attr)

class ShellClient:
    """
    A class to represent a GekkoFS shell client process.
    This class allows tests to execute shell commands or scripts via bash -c
    on a GekkoFS instance.
    """

    def __init__(self, workspace):
        self._workspace = workspace
        self._cmd = sh.Command("bash")
        self._env = os.environ.copy()

        libdirs = ':'.join(
                filter(None, [os.environ.get('LD_LIBRARY_PATH', '')] +
                             [str(p) for p in self._workspace.libdirs]))

        # ensure the client interception library is available:
        # to avoid running code with potentially installed libraries,
        # it must be found in one (and only one) of the workspace's bindirs
        preloads = []
        for d in self._workspace.bindirs:
            search_path = Path(d) / gkfs_client_lib_file
            if search_path.exists():
                preloads.append(search_path)

        if len(preloads) != 1:
            logger.error(f'Multiple client libraries found in the test\'s binary directories:')
            for p in preloads:
                logger.error(f'  {p}')
            logger.error(f'Make sure that only one copy of the client library is available.')
            pytest.exit("Aborted due to initialization error")

        self._preload_library = preloads[0]

        self._patched_env = {
            'LD_LIBRARY_PATH'      : libdirs,
            'LD_PRELOAD'           : self._preload_library,
            'LIBGKFS_HOSTS_FILE'   : self.cwd / gkfs_hosts_file,
            'LIBGKFS_LOG'          : gkfs_client_log_level,
            'LIBGKFS_LOG_OUTPUT'   : self._workspace.logdir / gkfs_client_log_file
        }

        self._env.update(self._patched_env)

    @property
    def patched_environ(self):
        """
        Return the patched environment required to run a test as a string that
        can be prepended to a shell command.
        """

        return ' '.join(f'{k}="{v}"' for k,v in self._patched_env.items())

    def script(self, code, intercept_shell=True, timeout=None, timeout_signal=signal.SIGKILL):
        """
        Execute a shell script passed as an argument in bash.

        For instance, the following snippet:

            mountdir = pathlib.Path('/tmp')
            file01 = 'file01'

            ShellClient().script(
                f'''
                    expected_pathname={mountdir / file01}
                    if [[ -e ${{expected_pathname}} ]];
                    then
                        exit 0
                    fi
                    exit 1
                ''')

        transforms into:

            bash -c '
                expected_pathname=/tmp/file01
                if [[ -e ${expected_pathname} ]];
                then
                    exit 0
                fi
                exit 1
            '

        Note that since we are using Python's f-strings, for variable
        expansions to work correctly, they need to be defined with double
        braces, e.g.  ${{expected_pathname}}.

        Parameters
        ----------
        code: `str`
            The script code to be passed to 'bash -c'.

        intercept_shell: `bool`
            Controls whether the shell executing the script should be
            executed with LD_PRELOAD=libgkfs_intercept.so (default: True).

        timeout: `int`
            How much time, in seconds, we should give the process to complete.
            If the process does not finish within the timeout, it will be sent
            the signal defined by `timeout_signal`.

            Default value: None

        timeout_signal: `int`
            The signal to be sent to the process if `timeout` is not None.

            Default value: signal.SIGKILL

        Returns
        -------
        A sh.RunningCommand instance that allows interacting with
        the finished process.
        """

        logger.debug(f"running bash")
        logger.debug(f"cmd: bash -c '{code}'")
        logger.debug(f"timeout: {timeout} seconds")
        logger.debug(f"timeout_signal: {signal.Signals(timeout_signal).name}")

        if intercept_shell:
            logger.debug(f"env: {self._patched_env}")

        # 'sh' raises an exception if the return code is not zero;
        # since we'd rather check for return codes explictly, we
        # whitelist all exit codes from 1 to 255 as 'ok' using the
        # _ok_code argument
        return self._cmd('-c',
            code,
            _env = (self._env if intercept_shell else os.environ),
    #        _out=sys.stdout,
    #        _err=sys.stderr,
            _timeout=timeout,
            _timeout_signal=timeout_signal,
            _ok_code=list(range(0, 256))
            )

    def run(self, cmd, *args, timeout=None, timeout_signal=signal.SIGKILL):
        """
        Execute a shell command  with arguments.

        For example, the following snippet:

            mountdir = pathlib.Path('/tmp')
            file01 = 'file01'

            ShellClient().stat('--terse', mountdir / file01)

        transforms into:

            bash -c 'stat --terse /tmp/file01'

        Parameters:
        -----------
        cmd: `str`
            The command to execute.

        args: `list`
            The list of arguments for the command.

        timeout: `number`
            How much time, in seconds, we should give the process to complete.
            If the process does not finish within the timeout, it will be sent
            the signal defined by `timeout_signal`.

            Default value: None

        timeout_signal: `int`
            The signal to be sent to the process if `timeout` is not None.

            Default value: signal.SIGKILL

        Returns
        -------
        A ShellCommand instance that allows interacting with the finished
        process. Note that ShellCommand wraps sh.RunningCommand and adds s
        extra properties to it.
        """

        bash_c_args = f"{cmd} {' '.join(str(a) for a in args)}"
        logger.debug(f"running bash")
        logger.debug(f"cmd: bash -c '{bash_c_args}'")
        logger.debug(f"timeout: {timeout} seconds")
        logger.debug(f"timeout_signal: {signal.Signals(timeout_signal).name}")
        logger.debug(f"env: {self._patched_env}")

        # 'sh' raises an exception if the return code is not zero;
        # since we'd rather check for return codes explictly, we
        # whitelist all exit codes from 1 to 255 as 'ok' using the
        # _ok_code argument
        proc = self._cmd('-c',
            bash_c_args,
            _env = self._env,
    #        _out=sys.stdout,
    #        _err=sys.stderr,
            _timeout=timeout,
            _timeout_signal=timeout_signal,
            _ok_code=list(range(0, 256))
            )

        return ShellCommand(cmd, proc)

    def __getattr__(self, name):
        return _proxy_exec(self, name)

    @property
    def cwd(self):
        return self._workspace.twd
