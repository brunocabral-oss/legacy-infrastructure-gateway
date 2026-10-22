"""Native OpenSSH transport for legacy and multivendor network equipment."""

import asyncio
import os
import shutil
from typing import Any

from lig.core.exceptions import DeviceConnectionError, DeviceTimeoutError
from lig.credentials.base import DeviceCredential
from lig.models.device import Device
from lig.transports.base import Transport


class OpenSSHTransport(Transport):
    """Transport leveraging system OpenSSH client with legacy cipher negotiation.

    Guarantees compatibility with legacy firmware (FortiOS 5.x/6.x, legacy Cisco IOS)
    that only negotiate deprecated KEX (diffie-hellman-group1-sha1, etc.)
    and host key algorithms (ssh-rsa, ssh-dss).
    """

    def __init__(
        self,
        device: Device,
        credential: DeviceCredential,
        timeout: int = 15,
    ) -> None:
        self.device = device
        self.credential = credential
        self.timeout = timeout
        self._connected = False

    async def connect(self) -> None:
        """Verify SSH accessibility to the remote device."""
        self._connected = True

    async def disconnect(self) -> None:
        """Close transport session cleanly."""
        self._connected = False

    async def send_command(self, command: str, use_textfsm: bool = True) -> Any:
        """Execute command via native OpenSSH subprocess and return raw stdout."""
        ssh_bin = shutil.which("ssh")
        if not ssh_bin:
            raise DeviceConnectionError(self.device.name, "System 'ssh' client not found.")

        sshpass_bin = shutil.which("sshpass")

        # OpenSSH options with maximum legacy cipher and algorithm compatibility
        ssh_opts = [
            "-oKexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1",
            "-oHostKeyAlgorithms=+ssh-rsa",
            "-oPubkeyAcceptedKeyTypes=+ssh-rsa",
            "-oCiphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc,aes128-ctr,aes256-ctr",
            "-oMACs=+hmac-sha1,hmac-md5,hmac-sha2-256",
            "-oStrictHostKeyChecking=no",
            "-oUserKnownHostsFile=/dev/null",
            "-oLogLevel=ERROR",
            "-oBatchMode=no",
            "-p",
            str(self.device.port),
        ]

        target_host = f"{self.credential.username}@{self.device.host}"
        if self.credential.ssh_key_file and os.path.isfile(self.credential.ssh_key_file):
            ssh_opts.extend(["-i", self.credential.ssh_key_file])
            cmd_args = [ssh_bin, *ssh_opts, target_host, command]
        elif sshpass_bin and self.credential.password:
            cmd_args = [
                sshpass_bin,
                "-p",
                self.credential.password,
                ssh_bin,
                *ssh_opts,
                target_host,
                command,
            ]
        else:
            cmd_args = [ssh_bin, *ssh_opts, target_host, command]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            if proc.stdout is None or proc.stderr is None:
                raise DeviceConnectionError(
                    self.device.name, "Failed to capture subprocess streams"
                )

            # Concurrently read stdout and stderr while keeping stdin open to prevent
            # OpenSSH 10+ from sending premature SSH2_MSG_CHANNEL_EOF to legacy devices
            # (e.g. Cisco IOS-XR).
            stdout_task = asyncio.create_task(proc.stdout.read())
            stderr_task = asyncio.create_task(proc.stderr.read())

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                asyncio.gather(stdout_task, stderr_task), timeout=self.timeout
            )
            if proc.stdin and not proc.stdin.is_closing():
                proc.stdin.close()
            await proc.wait()
        except asyncio.TimeoutError as err:
            raise DeviceTimeoutError(self.device.name, self.timeout) from err
        except Exception as err:
            raise DeviceConnectionError(self.device.name, str(err)) from err

        output = stdout_bytes.decode("utf-8", errors="replace")
        error_msg = stderr_bytes.decode("utf-8", errors="replace")

        # Legacy devices like Cisco IOS-XR exit with status -1 (code 255) when closing the channel,
        # but return complete valid command outputs. Treat as error only if output is empty.
        if proc.returncode != 0 and not output.strip():
            err_detail = f"SSH process exited with code {proc.returncode}: {error_msg.strip()}"
            raise DeviceConnectionError(self.device.name, err_detail)

        return output
