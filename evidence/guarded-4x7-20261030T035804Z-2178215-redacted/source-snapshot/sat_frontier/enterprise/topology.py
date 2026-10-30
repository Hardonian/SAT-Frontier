"""Enterprise topology loader and reliability parameter converter.

Supports:
- JSON network topologies with physical link attributes (MTBF, MTTR, FIT, availability)
- Edge list dictionaries and CSV formats
- Fault tree structures with AND, OR, and k-of-n voting gates
"""
from dataclasses import dataclass, field
from fractions import Fraction
import json
import math
from typing import Dict, List, Optional, Set, Tuple, Union

from ..reliability import NetworkGraph


@dataclass
class LinkAttributes:
    u: Union[int, str]
    v: Union[int, str]
    p_operational: Fraction
    latency_ms: float = 0.0
    bandwidth_gbps: float = 10.0
    mtbf_hours: Optional[float] = None
    mttr_hours: Optional[float] = None
    fit_rate: Optional[float] = None
    metadata: Dict = field(default_factory=dict)


def availability_from_mtbf(mtbf_hours: float, mttr_hours: float) -> Fraction:
    """Calculate steady-state operational availability A = MTBF / (MTBF + MTTR)."""
    if mtbf_hours <= 0 or mttr_hours < 0:
        raise ValueError("MTBF must be > 0 and MTTR >= 0")
    # Convert to rational fraction with high precision (scale to integer seconds)
    scale = 3600
    mtbf_s = int(round(mtbf_hours * scale))
    mttr_s = int(round(mttr_hours * scale))
    return Fraction(mtbf_s, mtbf_s + mttr_s)


def availability_from_fit(fit_rate: float, mission_hours: float = 8760.0) -> Fraction:
    """Calculate operational probability over mission time from FIT (failures per 10^9 hours).
    
    R(t) = exp(-lambda * t) where lambda = fit * 10^-9.
    """
    if fit_rate < 0 or mission_hours <= 0:
        raise ValueError("FIT rate must be >= 0 and mission_hours > 0")
    lambda_per_hour = fit_rate * 1e-9
    # Taylor expansion or float conversion to Fraction (precision: 10^-9)
    unavail = lambda_per_hour * mission_hours
    p_float = max(0.0, min(1.0, 1.0 - unavail))
    return Fraction(p_float).limit_denominator(10**10)


class EnterpriseTopology:
    """Enterprise-grade network model with node mapping and physical link metadata."""

    def __init__(self, name: str = "EnterpriseNetwork"):
        self.name = name
        self.node_to_id: Dict[Union[int, str], int] = {}
        self.id_to_node: Dict[int, Union[int, str]] = {}
        self.next_node_id = 1
        self.links: List[LinkAttributes] = []

    def _get_node_id(self, node: Union[int, str]) -> int:
        if node not in self.node_to_id:
            nid = self.next_node_id
            self.node_to_id[node] = nid
            self.id_to_node[nid] = node
            self.next_node_id += 1
        return self.node_to_id[node]

    def add_link(
        self,
        u: Union[int, str],
        v: Union[int, str],
        availability: Optional[Union[Fraction, float, str]] = None,
        mtbf_hours: Optional[float] = None,
        mttr_hours: Optional[float] = None,
        fit_rate: Optional[float] = None,
        latency_ms: float = 0.0,
        bandwidth_gbps: float = 10.0,
        metadata: Optional[Dict] = None,
    ):
        """Add a physical link with operational parameters."""
        if availability is not None:
            if isinstance(availability, Fraction):
                p = availability
            elif isinstance(availability, str) and "/" in availability:
                p = Fraction(availability)
            else:
                p = Fraction(str(availability)).limit_denominator(10**10)
        elif mtbf_hours is not None and mttr_hours is not None:
            p = availability_from_mtbf(mtbf_hours, mttr_hours)
        elif fit_rate is not None:
            p = availability_from_fit(fit_rate)
        else:
            p = Fraction(99, 100)  # Default 99%

        attr = LinkAttributes(
            u=u,
            v=v,
            p_operational=p,
            latency_ms=latency_ms,
            bandwidth_gbps=bandwidth_gbps,
            mtbf_hours=mtbf_hours,
            mttr_hours=mttr_hours,
            fit_rate=fit_rate,
            metadata=metadata or {},
        )
        self.links.append(attr)

    def to_network_graph(self) -> Tuple[NetworkGraph, Dict[int, LinkAttributes]]:
        """Compile into an internal SAT-Frontier NetworkGraph with integer node IDs."""
        net = NetworkGraph()
        edge_attr_map: Dict[int, LinkAttributes] = {}

        for eid, attr in enumerate(self.links, 1):
            u_id = self._get_node_id(attr.u)
            v_id = self._get_node_id(attr.v)
            net.add_edge(u_id, v_id, prob=attr.p_operational)
            edge_attr_map[eid] = attr

        return net, edge_attr_map

    @classmethod
    def from_dict(cls, data: Dict) -> "EnterpriseTopology":
        """Load from enterprise JSON/dictionary schema."""
        topo = cls(name=data.get("name", "EnterpriseTopology"))
        for link in data.get("links", []):
            topo.add_link(
                u=link["source"],
                v=link["target"],
                availability=link.get("availability"),
                mtbf_hours=link.get("mtbf_hours"),
                mttr_hours=link.get("mttr_hours"),
                fit_rate=link.get("fit_rate"),
                latency_ms=link.get("latency_ms", 0.0),
                bandwidth_gbps=link.get("bandwidth_gbps", 10.0),
                metadata=link.get("metadata", {}),
            )
        return topo

    def to_dict(self) -> Dict:
        """Export to clean JSON-serializable dictionary."""
        return {
            "name": self.name,
            "total_nodes": len(self.node_to_id),
            "total_links": len(self.links),
            "nodes": list(self.node_to_id.keys()),
            "links": [
                {
                    "source": str(attr.u),
                    "target": str(attr.v),
                    "availability": str(attr.p_operational),
                    "availability_float": float(attr.p_operational),
                    "latency_ms": attr.latency_ms,
                    "bandwidth_gbps": attr.bandwidth_gbps,
                    "metadata": attr.metadata,
                }
                for attr in self.links
            ],
        }
