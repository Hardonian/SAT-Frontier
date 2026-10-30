"""Industry network topology importers for SAT-Frontier Enterprise.

Supports zero-dependency parsing and conversion for:
1. GraphML (.graphml, .xml): XML-based standard used by Gephi, yEd, NetworkX, and Internet Topology Zoo.
2. GML (.gml): Graph Modelling Language widely used in network topology databases.
3. NetworkX / Cytoscape JSON (.json): Standard node-link and graph exchange formats.
4. Delimited CSV / TSV (.csv, .tsv): Tabular link inventories with MTBF, MTTR, FIT, or availability columns.
"""
from __future__ import annotations

import csv
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import xml.etree.ElementTree as ET

from .topology import EnterpriseTopology, LinkAttributes, availability_from_fit, availability_from_mtbf


def parse_availability_value(val: Any, default: Fraction = Fraction(99, 100)) -> Fraction:
    """Parse availability from float, string fraction ('99/100'), decimal string ('0.99'), or percentage."""
    if val is None:
        return default
    if isinstance(val, Fraction):
        return val
    if isinstance(val, (int, float)):
        # Handle percentage (e.g. 99.9 -> 0.999)
        f_val = float(val)
        if f_val > 1.0:
            f_val /= 100.0
        return Fraction(str(round(f_val, 8))).limit_denominator(10**10)
    val_str = str(val).strip()
    if not val_str:
        return default
    if val_str.endswith("%"):
        f_val = float(val_str[:-1].strip()) / 100.0
        return Fraction(str(round(f_val, 8))).limit_denominator(10**10)
    if "/" in val_str:
        parts = val_str.split("/")
        return Fraction(int(parts[0].strip()), int(parts[1].strip()))
    f_val = float(val_str)
    if f_val > 1.0:
        f_val /= 100.0
    return Fraction(str(round(f_val, 8))).limit_denominator(10**10)


def import_graphml(
    file_path: Union[str, Path],
    default_availability: Union[float, Fraction] = Fraction(99, 100),
    name: Optional[str] = None,
) -> EnterpriseTopology:
    """Parse a GraphML (.graphml, .xml) file into an EnterpriseTopology.
    
    Extracts node IDs and labels, edge sources and targets, and custom data keys
    such as availability, capacity, latency, and MTBF.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"GraphML file not found: {path}")

    tree = ET.parse(path)
    root = tree.getroot()

    # GraphML XML namespace handling
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # Parse key mappings
    key_attrs: Dict[str, Tuple[str, str]] = {}  # id -> (name, target_type)
    for key_elem in root.findall(f"{ns}key"):
        k_id = key_elem.get("id")
        k_name = key_elem.get("attr.name", key_elem.get("id"))
        k_for = key_elem.get("for", "all")
        if k_id and k_name:
            key_attrs[k_id] = (k_name.lower(), k_for)

    # Locate graph element
    graph_elem = root.find(f"{ns}graph")
    if graph_elem is None:
        raise ValueError(f"Malformed GraphML: no <graph> tag found in {path}")

    topo_name = name or graph_elem.get("id", path.stem)
    topo = EnterpriseTopology(name=topo_name)

    # Map node XML id -> human label
    node_labels: Dict[str, str] = {}
    for node_elem in graph_elem.findall(f"{ns}node"):
        n_id = node_elem.get("id", "")
        n_label = n_id
        for data_elem in node_elem.findall(f"{ns}data"):
            k_id = data_elem.get("key", "")
            attr_name, _ = key_attrs.get(k_id, (k_id.lower(), "node"))
            if attr_name in ("label", "name", "nodename"):
                text = (data_elem.text or "").strip()
                if text:
                    n_label = text
                    break
        node_labels[n_id] = n_label

    def_p = parse_availability_value(default_availability)

    for edge_elem in graph_elem.findall(f"{ns}edge"):
        src = edge_elem.get("source", "")
        tgt = edge_elem.get("target", "")
        if not src or not tgt:
            continue

        u = node_labels.get(src, src)
        v = node_labels.get(tgt, tgt)

        p_val = def_p
        mtbf_h: Optional[float] = None
        mttr_h: Optional[float] = None
        fit_r: Optional[float] = None
        bw: float = 10.0
        lat: float = 0.0
        metadata: Dict[str, Any] = {}

        for data_elem in edge_elem.findall(f"{ns}data"):
            k_id = data_elem.get("key", "")
            attr_name, _ = key_attrs.get(k_id, (k_id.lower(), "edge"))
            val_text = (data_elem.text or "").strip()
            if not val_text:
                continue

            metadata[attr_name] = val_text
            if attr_name in ("availability", "avail", "reliability", "prob", "p"):
                p_val = parse_availability_value(val_text, def_p)
            elif attr_name == "mtbf":
                try:
                    mtbf_h = float(val_text)
                except ValueError:
                    pass
            elif attr_name == "mttr":
                try:
                    mttr_h = float(val_text)
                except ValueError:
                    pass
            elif attr_name == "fit":
                try:
                    fit_r = float(val_text)
                except ValueError:
                    pass
            elif attr_name in ("bandwidth", "bandwidth_gbps", "capacity", "cap"):
                try:
                    bw = float(val_text)
                except ValueError:
                    pass
            elif attr_name in ("latency", "latency_ms", "delay"):
                try:
                    lat = float(val_text)
                except ValueError:
                    pass

        if mtbf_h is not None and mttr_h is not None:
            p_val = availability_from_mtbf(mtbf_h, mttr_h)
        elif fit_r is not None:
            p_val = availability_from_fit(fit_r)

        topo.add_link(
            u=u,
            v=v,
            availability=p_val,
            mtbf_hours=mtbf_h,
            mttr_hours=mttr_h,
            fit_rate=fit_r,
            bandwidth_gbps=bw,
            latency_ms=lat,
            metadata=metadata,
        )

    return topo


def import_gml(
    file_path: Union[str, Path],
    default_availability: Union[float, Fraction] = Fraction(99, 100),
    name: Optional[str] = None,
) -> EnterpriseTopology:
    """Parse a Graph Modelling Language (.gml) file into an EnterpriseTopology.
    
    Robust lexical parser handling nested blocks, string keys, and numeric IDs.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"GML file not found: {path}")

    content = path.read_text(encoding="utf-8", errors="replace")

    # Simple tokenizer for GML
    # Tokens: '[' , ']' , strings "...", integers/floats, keys/identifiers
    token_pattern = re.compile(r'\[|\]|"(?:\\.|[^"\\])*"|[^\s\[\]"]+')
    tokens = token_pattern.findall(content)

    def parse_dict(idx: int) -> Tuple[Dict[str, Any], int]:
        d: Dict[str, Any] = {}
        while idx < len(tokens):
            tok = tokens[idx]
            if tok == "]":
                return d, idx + 1
            idx += 1
            key = tok
            if idx >= len(tokens):
                break
            val_tok = tokens[idx]
            if val_tok == "[":
                sub_dict, idx = parse_dict(idx + 1)
                # If key already in dict, convert to list (e.g. multiple 'node' or 'edge')
                if key in d:
                    if not isinstance(d[key], list):
                        d[key] = [d[key]]
                    d[key].append(sub_dict)
                else:
                    d[key] = sub_dict
            else:
                # Literal value (int, float, string)
                if val_tok.startswith('"') and val_tok.endswith('"'):
                    val: Any = val_tok[1:-1].replace('\\"', '"')
                else:
                    try:
                        val = int(val_tok)
                    except ValueError:
                        try:
                            val = float(val_tok)
                        except ValueError:
                            val = val_tok
                idx += 1
                if key in d:
                    if not isinstance(d[key], list):
                        d[key] = [d[key]]
                    d[key].append(val)
                else:
                    d[key] = val
        return d, idx

    parsed_root, _ = parse_dict(0)
    graph_data = parsed_root.get("graph", parsed_root)
    topo_name = name or str(graph_data.get("label", graph_data.get("id", path.stem)))
    topo = EnterpriseTopology(name=topo_name)

    # Extract nodes
    raw_nodes = graph_data.get("node", [])
    if isinstance(raw_nodes, dict):
        raw_nodes = [raw_nodes]

    node_map: Dict[Union[int, str], str] = {}
    for n in raw_nodes:
        n_id = n.get("id")
        n_label = n.get("label", n.get("name", str(n_id)))
        if n_id is not None:
            node_map[n_id] = str(n_label)
            node_map[str(n_id)] = str(n_label)

    # Extract edges
    raw_edges = graph_data.get("edge", [])
    if isinstance(raw_edges, dict):
        raw_edges = [raw_edges]

    def_p = parse_availability_value(default_availability)

    for e in raw_edges:
        src = e.get("source")
        tgt = e.get("target")
        if src is None or tgt is None:
            continue

        u = node_map.get(src, str(src))
        v = node_map.get(tgt, str(tgt))

        p_val = def_p
        if "availability" in e:
            p_val = parse_availability_value(e["availability"], def_p)
        elif "reliability" in e:
            p_val = parse_availability_value(e["reliability"], def_p)
        elif "p" in e:
            p_val = parse_availability_value(e["p"], def_p)

        mtbf_h = float(e["mtbf"]) if "mtbf" in e else None
        mttr_h = float(e["mttr"]) if "mttr" in e else None
        fit_r = float(e["fit"]) if "fit" in e else None
        bw = float(e.get("bandwidth", e.get("capacity", 10.0)))
        lat = float(e.get("latency", 0.0))

        if mtbf_h is not None and mttr_h is not None:
            p_val = availability_from_mtbf(mtbf_h, mttr_h)
        elif fit_r is not None:
            p_val = availability_from_fit(fit_r)

        topo.add_link(
            u=u,
            v=v,
            availability=p_val,
            mtbf_hours=mtbf_h,
            mttr_hours=mttr_h,
            fit_rate=fit_r,
            bandwidth_gbps=bw,
            latency_ms=lat,
            metadata=e,
        )

    return topo


def import_csv(
    file_path: Union[str, Path],
    default_availability: Union[float, Fraction] = Fraction(99, 100),
    name: Optional[str] = None,
    delimiter: Optional[str] = None,
) -> EnterpriseTopology:
    """Parse a CSV or TSV link table into an EnterpriseTopology.
    
    Header columns can include:
    source, target, availability (or p / reliability), mtbf, mttr, fit, bandwidth, latency.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    content = path.read_text(encoding="utf-8", errors="replace")
    if delimiter is None:
        delimiter = "\t" if path.suffix.lower() == ".tsv" or "\t" in content.splitlines()[0] else ","

    reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
    topo = EnterpriseTopology(name=name or path.stem)
    def_p = parse_availability_value(default_availability)

    for row in reader:
        # Standardize keys to lowercase stripped
        r = {k.strip().lower(): v.strip() for k, v in row.items() if k is not None}
        src = r.get("source", r.get("src", r.get("u", r.get("node1", r.get("from")))))
        tgt = r.get("target", r.get("dst", r.get("v", r.get("node2", r.get("to")))))
        if not src or not tgt:
            continue

        p_str = r.get("availability", r.get("avail", r.get("reliability", r.get("p", r.get("prob")))))
        p_val = parse_availability_value(p_str, def_p)

        mtbf_h = float(r["mtbf"]) if "mtbf" in r and r["mtbf"] else None
        mttr_h = float(r["mttr"]) if "mttr" in r and r["mttr"] else None
        fit_r = float(r["fit"]) if "fit" in r and r["fit"] else None
        bw = float(r.get("bandwidth", r.get("bandwidth_gbps", r.get("capacity", 10.0)))) if "bandwidth" in r or "capacity" in r else 10.0
        lat = float(r.get("latency", r.get("latency_ms", 0.0))) if "latency" in r or "latency_ms" in r else 0.0

        if mtbf_h is not None and mttr_h is not None:
            p_val = availability_from_mtbf(mtbf_h, mttr_h)
        elif fit_r is not None:
            p_val = availability_from_fit(fit_r)

        topo.add_link(
            u=src,
            v=tgt,
            availability=p_val,
            mtbf_hours=mtbf_h,
            mttr_hours=mttr_h,
            fit_rate=fit_r,
            bandwidth_gbps=bw,
            latency_ms=lat,
            metadata=r,
        )

    return topo


def import_json(
    file_path: Union[str, Path],
    default_availability: Union[float, Fraction] = Fraction(99, 100),
    name: Optional[str] = None,
) -> EnterpriseTopology:
    """Parse a NetworkX, Cytoscape, or Enterprise JSON file into an EnterpriseTopology."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    def_p = parse_availability_value(default_availability)

    # 1. Native Enterprise Schema (has "links" with "source" and "target")
    if "links" in data and isinstance(data["links"], list):
        topo = EnterpriseTopology(name=name or data.get("name", path.stem))
        for link in data["links"]:
            u = link.get("source", link.get("u"))
            v = link.get("target", link.get("v"))
            if not u or not v:
                continue
            avail = link.get("availability", link.get("p", def_p))
            p_val = parse_availability_value(avail, def_p)
            topo.add_link(
                u=u,
                v=v,
                availability=p_val,
                mtbf_hours=link.get("mtbf_hours"),
                mttr_hours=link.get("mttr_hours"),
                fit_rate=link.get("fit_rate"),
                bandwidth_gbps=link.get("bandwidth_gbps", 10.0),
                latency_ms=link.get("latency_ms", 0.0),
                metadata=link.get("metadata", {}),
            )
        return topo

    # 2. Cytoscape Schema (has "elements" with "nodes" and "edges")
    if "elements" in data:
        elements = data["elements"]
        topo = EnterpriseTopology(name=name or path.stem)
        node_labels = {}
        for n in elements.get("nodes", []):
            n_data = n.get("data", {})
            n_id = str(n_data.get("id", ""))
            n_label = str(n_data.get("label", n_data.get("name", n_id)))
            if n_id:
                node_labels[n_id] = n_label

        for e in elements.get("edges", []):
            e_data = e.get("data", {})
            src = str(e_data.get("source", ""))
            tgt = str(e_data.get("target", ""))
            if not src or not tgt:
                continue
            u = node_labels.get(src, src)
            v = node_labels.get(tgt, tgt)
            p_val = parse_availability_value(e_data.get("availability", e_data.get("weight")), def_p)
            topo.add_link(u=u, v=v, availability=p_val, metadata=e_data)
        return topo

    # 3. NetworkX adjacency or edge list format
    if "edges" in data or "links" in data:
        edges = data.get("edges", data.get("links", []))
        topo = EnterpriseTopology(name=name or path.stem)
        for e in edges:
            if isinstance(e, (list, tuple)) and len(e) >= 2:
                u, v = e[0], e[1]
                topo.add_link(u=u, v=v, availability=def_p)
            elif isinstance(e, dict):
                u = e.get("source", e.get("u"))
                v = e.get("target", e.get("v"))
                if u and v:
                    p_val = parse_availability_value(e.get("availability", e.get("weight")), def_p)
                    topo.add_link(u=u, v=v, availability=p_val, metadata=e)
        return topo

    raise ValueError(f"Unrecognized JSON topology schema in: {path}")


def load_topology(
    file_path: Union[str, Path],
    default_availability: Union[float, Fraction] = Fraction(99, 100),
    name: Optional[str] = None,
) -> EnterpriseTopology:
    """Universal topology loader with auto-detection of format.
    
    Supports .graphml, .xml, .gml, .json, .csv, and .tsv.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in (".graphml", ".xml"):
        return import_graphml(path, default_availability=default_availability, name=name)
    elif suffix == ".gml":
        return import_gml(path, default_availability=default_availability, name=name)
    elif suffix in (".csv", ".tsv"):
        return import_csv(path, default_availability=default_availability, name=name)
    elif suffix == ".json":
        return import_json(path, default_availability=default_availability, name=name)
    else:
        # Inspect content
        first_chunk = path.read_text(encoding="utf-8", errors="replace")[:500].strip()
        if first_chunk.startswith("<?xml") or "<graphml" in first_chunk:
            return import_graphml(path, default_availability=default_availability, name=name)
        elif "graph" in first_chunk and "[" in first_chunk:
            return import_gml(path, default_availability=default_availability, name=name)
        elif first_chunk.startswith("{"):
            return import_json(path, default_availability=default_availability, name=name)
        else:
            return import_csv(path, default_availability=default_availability, name=name)

