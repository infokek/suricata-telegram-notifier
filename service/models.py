from dataclasses import dataclass


@dataclass
class Alert:
    timestamp: str
    sid_and_rev: str
    message: str
    classification: str
    priority: int
    protocol: str
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    count: int

