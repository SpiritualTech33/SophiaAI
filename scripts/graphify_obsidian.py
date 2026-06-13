#!/usr/bin/env python3
"""Generate an Obsidian vault from a graphify graph.json output."""

import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

def slugify(text: str) -> str:
    """Create an Obsidian-safe filename from a node label."""
    # Remove or replace characters that are problematic in filenames
    slug = re.sub(r'[<>:"/\\|?*]', '', text)
    slug = re.sub(r'\s+', ' ', slug).strip()
    # Truncate very long names
    if len(slug) > 120:
        slug = slug[:120]
    return slug

def main():
    graph_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("graphify-out/graph.json")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("graphify-out/obsidian")

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    links = data.get("links", [])
    hyperedges = data.get("hyperedges", [])

    print(f"Loaded {len(nodes)} nodes, {len(links)} edges, {len(hyperedges)} hyperedges")

    # Build lookup: id -> node
    node_map = {}
    for n in nodes:
        nid = n.get("id", "")
        if nid:
            node_map[nid] = n

    # Build adjacency: source -> [(target, edge_data)]
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for link in links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        if src in node_map and tgt in node_map:
            outgoing[src].append((tgt, link))
            incoming[tgt].append((src, link))

    # Build hyperedge memberships: node_id -> [hyperedge_labels]
    node_hyperedges = defaultdict(list)
    for he in hyperedges:
        members = he.get("nodes", [])
        label = he.get("label", "Hyperedge")
        for m in members:
            if m in node_map:
                node_hyperedges[m].append(label)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track filenames to avoid collisions
    used_names = {}
    filenames = {}  # node_id -> filename

    for n in nodes:
        nid = n.get("id", "")
        label = n.get("label", nid)
        base_name = slugify(label)

        if not base_name:
            base_name = nid

        # Handle collisions
        if base_name in used_names:
            used_names[base_name] += 1
            filename = f"{base_name}_{used_names[base_name]}"
        else:
            used_names[base_name] = 0
            filename = base_name

        filenames[nid] = filename

    # Generate one .md file per node
    files_created = 0
    for n in nodes:
        nid = n.get("id", "")
        label = n.get("label", nid)
        filename = filenames.get(nid, nid)
        filepath = output_dir / f"{filename}.md"

        # Build content
        lines = []

        # Frontmatter
        fm = {
            "label": label,
            "id": nid,
            "file_type": n.get("file_type", ""),
            "source_file": n.get("source_file", ""),
            "source_location": n.get("source_location", ""),
            "community": n.get("community", -1),
            "origin": n.get("_origin", ""),
        }
        # Remove empty values
        fm = {k: v for k, v in fm.items() if v != "" and v is not None}

        lines.append("---")
        for k, v in fm.items():
            if isinstance(v, str):
                lines.append(f'{k}: "{v}"')
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# {label}")
        lines.append("")

        # Source info
        src_file = n.get("source_file", "")
        src_loc = n.get("source_location", "")
        if src_file:
            lines.append(f"**Source:** `{src_file}` {src_loc}")
            lines.append("")

        # Community
        comm = n.get("community", -1)
        if comm >= 0:
            lines.append(f"**Community:** {comm}")
            lines.append("")

        # Outgoing links (this node -> others)
        if nid in outgoing:
            lines.append("## Outgoing Links")
            lines.append("")
            for tgt_id, edge in sorted(outgoing[nid], key=lambda x: x[1].get("relation", "")):
                tgt_label = node_map[tgt_id].get("label", tgt_id)
                rel = edge.get("relation", "related")
                conf = edge.get("confidence_score", "")
                origin = edge.get("_origin", edge.get("confidence", ""))
                conf_str = f" (conf: {conf})" if conf else ""
                origin_str = f" [{origin}]" if origin else ""
                tgt_filename = filenames.get(tgt_id, tgt_id)
                lines.append(f"- [[{tgt_filename}|{tgt_label}]] -- `{rel}`{conf_str}{origin_str}")
            lines.append("")

        # Incoming links (others -> this node)
        if nid in incoming:
            lines.append("## Incoming Links")
            lines.append("")
            for src_id, edge in sorted(incoming[nid], key=lambda x: x[1].get("relation", "")):
                src_label = node_map[src_id].get("label", src_id)
                rel = edge.get("relation", "related")
                conf = edge.get("confidence_score", "")
                origin = edge.get("_origin", edge.get("confidence", ""))
                conf_str = f" (conf: {conf})" if conf else ""
                origin_str = f" [{origin}]" if origin else ""
                src_filename = filenames.get(src_id, src_id)
                lines.append(f"- [[{src_filename}|{src_label}]] — `{rel}`{conf_str}{origin_str}")
            lines.append("")

        # Hyperedges
        if nid in node_hyperedges:
            lines.append("## Hyperedges")
            lines.append("")
            for he_label in node_hyperedges[nid]:
                lines.append(f"- {he_label}")
            lines.append("")

        # Write file
        filepath.write_text("\n".join(lines), encoding="utf-8")
        files_created += 1

    # Generate index file
    index_path = output_dir / "_INDEX.md"
    index_lines = [
        "# SophiaAI Knowledge Graph — Index",
        "",
        f"**Nodes:** {len(nodes)}",
        f"**Edges:** {len(links)}",
        f"**Hyperedges:** {len(hyperedges)}",
        "",
        "## All Nodes by Community",
        "",
    ]

    # Group by community
    communities = defaultdict(list)
    for n in nodes:
        comm = n.get("community", -1)
        communities[comm].append(n)

    for comm in sorted(communities.keys()):
        comm_nodes = communities[comm]
        index_lines.append(f"### Community {comm} ({len(comm_nodes)} nodes)")
        index_lines.append("")
        for n in sorted(comm_nodes, key=lambda x: x.get("label", "")):
            nid = n.get("id", "")
            label = n.get("label", nid)
            filename = filenames.get(nid, nid)
            index_lines.append(f"- [[{filename}|{label}]]")
        index_lines.append("")

    index_path.write_text("\n".join(index_lines), encoding="utf-8")
    files_created += 1

    # Generate graph.canvas for Obsidian (structured layout by community)
    canvas = {
        "nodes": [],
        "edges": []
    }

    # Position communities in a grid
    comm_list = sorted(communities.keys())
    grid_cols = max(1, int(len(comm_list) ** 0.5))
    for i, comm in enumerate(comm_list):
        col = i % grid_cols
        row = i // grid_cols
        x_base = col * 800
        y_base = row * 600

        comm_nodes = communities[comm]
        for j, n in enumerate(comm_nodes[:30]):  # Cap 30 per community for canvas readability
            nid = n.get("id", "")
            label = n.get("label", nid)
            filename = filenames.get(nid, nid)
            angle = (j / max(1, len(comm_nodes))) * 2 * 3.14159
            radius = 150
            nx = x_base + int(radius * __import__('math').cos(angle))
            ny = y_base + int(radius * __import__('math').sin(angle))
            canvas["nodes"].append({
                "id": nid,
                "x": nx,
                "y": ny,
                "width": 200,
                "height": 60,
                "text": label[:40],
                "file": f"{filename}.md"
            })

    canvas_path = output_dir / "graph.canvas"
    canvas_path.write_text(json.dumps(canvas, indent=2), encoding="utf-8")
    files_created += 1

    print(f"Created {files_created} files in {output_dir}")
    print(f"  {len(nodes)} node notes")
    print(f"  1 index (_INDEX.md)")
    print(f"  1 canvas (graph.canvas)")
    print(f"\nOpen {output_dir} as an Obsidian vault to explore.")

if __name__ == "__main__":
    main()
