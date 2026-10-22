"""Netmiko-based SSH transport with non-blocking async execution."""

import asyncio
from typing import Any

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoBaseException,
    NetmikoTimeoutException,
)

from lig.core.exceptions import (
    AuthenticationError,
    DeviceConnectionError,
    DeviceTimeoutError,
)
from lig.credentials.base import DeviceCredential
from lig.models.device import Device
from lig.transports.base import Transport


class NetmikoTransport(Transport):
    """Transport implementation wrapping Netmiko in asynchronous worker threads."""

    def __init__(
        self,
        device: Device,
        credential: DeviceCredential,
        device_type: str = "cisco_ios",
        timeout: int = 15,
    ) -> None:
        self.device = device
        self.credential = credential
        self.device_type = device_type
        self.timeout = timeout
        self._connection: Any = None

    def _sync_connect(self) -> Any:
        connection_params: dict[str, Any] = {
            "device_type": self.device_type,
            "host": self.device.host,
            "port": self.device.port,
            "username": self.credential.username,
            "password": self.credential.password,
            "timeout": self.timeout,
            "conn_timeout": self.timeout,
            "session_log": None,  # Security: Never log raw sessions to files
        }
        if self.credential.secret:
            connection_params["secret"] = self.credential.secret
        if self.credential.ssh_key_file:
            connection_params["use_keys"] = True
            connection_params["key_file"] = self.credential.ssh_key_file

        return ConnectHandler(**connection_params)

    async def connect(self) -> None:
        """Establish Netmiko connection asynchronously."""
        try:
            self._connection = await asyncio.to_thread(self._sync_connect)
        except NetmikoAuthenticationException as err:
            raise AuthenticationError(self.device.name, str(err)) from err
        except NetmikoTimeoutException as err:
            raise DeviceTimeoutError(self.device.name, self.timeout) from err
        except (NetmikoBaseException, OSError, ConnectionError) as err:
            raise DeviceConnectionError(self.device.name, str(err)) from err

    def _sync_disconnect(self) -> None:
        if self._connection is not None:
            try:
                self._connection.disconnect()
            except Exception:
                pass
            finally:
                self._connection = None

    async def disconnect(self) -> None:
        """Disconnect Netmiko connection asynchronously."""
        if self._connection is not None:
            await asyncio.to_thread(self._sync_disconnect)

    def _sync_send_command(self, command: str, use_textfsm: bool) -> Any:
        if self._connection is None:
            raise DeviceConnectionError(self.device.name, "Transport not connected")
        return self._connection.send_command(command, use_textfsm=use_textfsm)

    async def send_command(self, command: str, use_textfsm: bool = True) -> Any:
        """Send command to device and return structured (or text) response."""
        if self._connection is None:
            await self.connect()

        try:
            return await asyncio.to_thread(self._sync_send_command, command, use_textfsm)
        except NetmikoTimeoutException as err:
            raise DeviceTimeoutError(self.device.name, self.timeout) from err
        except Exception as err:
            raise DeviceConnectionError(self.device.name, str(err)) from err
