"""Diagnostic models (Ping and Traceroute)."""

from pydantic import BaseModel, Field


class PingRequest(BaseModel):
    """Parameters for executing a remote ping diagnostic."""

    destination: str = Field(description="Target destination IP or hostname")
    source: str | None = Field(default=None, description="Source IP address or interface")
    vrf: str | None = Field(default=None, description="VRF routing table context")
    count: int = Field(default=5, ge=1, le=50, description="Number of packets to send")
    timeout_seconds: int = Field(
        default=2, ge=1, le=10, description="Timeout per packet in seconds"
    )


class PingResult(BaseModel):
    """Normalized ping execution result."""

    destination: str
    packets_transmitted: int
    packets_received: int
    packet_loss_percentage: float
    rtt_min_ms: float | None = None
    rtt_avg_ms: float | None = None
    rtt_max_ms: float | None = None


class TracerouteRequest(BaseModel):
    """Parameters for executing a traceroute diagnostic."""

    destination: str = Field(description="Target destination IP or hostname")
    source: str | None = Field(default=None, description="Source IP address or interface")
    vrf: str | None = Field(default=None, description="VRF routing table context")
    max_hops: int = Field(default=30, ge=1, le=64)
    timeout_seconds: int = Field(default=3, ge=1, le=10)


class TracerouteHop(BaseModel):
    """Single hop entry in a traceroute result."""

    hop_number: int
    ip_address: str | None = None
    hostname: str | None = None
    rtt_ms: float | None = None


class TracerouteResult(BaseModel):
    """Normalized traceroute execution result."""

    destination: str
    hops: list[TracerouteHop] = Field(default_factory=list)
