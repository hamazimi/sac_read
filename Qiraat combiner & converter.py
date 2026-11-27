
#!/usr/bin/env python3
# Taisir variants CSV + Cairo 1924 Hafs JSON -> Gephi nodes and edges.
# Python standard library only; compatible with Pydroid 3.

import csv
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

METADATA_COLUMNS = {
    "surah", "verse", "word", "reference", "reference_cairo"
}


def clean_text(value):
    return " ".join(unicodedata.normalize("NFC", value or "").split())


def stable_id(prefix, value):
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def variant_id(surah, verse, word, transliteration):
    location = f"{surah}:{verse}:{word}"
    key = location + "|" + clean_text(transliteration)
    return stable_id("variant", key)


def read_taisir(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(8192)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)
        headers = reader.fieldnames or []
        rows = list(reader)

    if not headers:
        raise ValueError("The Taisir CSV has no header row.")

    required = {"surah", "verse", "word", "reference"}
    missing = required - set(headers)

    if missing:
        raise ValueError(
            "Missing required Taisir columns: "
            + ", ".join(sorted(missing))
        )

    return headers, rows


def read_cairo(path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    reading = clean_text(data.get("reading", ""))

    if "Ḥafṣ" not in reading and "Hafs" not in reading:
        print("WARNING: Cairo source metadata does not clearly identify Hafs:", reading)

    words = {}

    for verse_data in data.get("verses", []):
        surah = str(int(verse_data["surah"]))
        verse = str(int(verse_data["verse"]))

        for word_data in verse_data.get("words", []):
            word = str(int(word_data["position"]))

            words[(surah, verse, word)] = {
                "transliteration": clean_text(
                    word_data.get("transliteration", "")
                ),
                "arabic": clean_text(word_data.get("arabic", "")),
            }

    return words, reading

def write_gexf(nodes, edges, output_path):

    ns = "http://www.gexf.net/1.3"
    ET.register_namespace("", ns)

    def tag(name):
        return f"{{{ns}}}{name}"

    root = ET.Element(
        tag("gexf"),
        {"version": "1.3"}
    )

    meta = ET.SubElement(root, tag("meta"))
    ET.SubElement(meta, tag("creator")).text = "Taisir + Cairo Converter"
    ET.SubElement(meta, tag("description")).text = (
        "Qiraat graph generated from Taisir variants and Cairo 1924."
    )

    graph = ET.SubElement(
        root,
        tag("graph"),
        {
            "mode": "static",
            "defaultedgetype": "undirected"
        }
    )

    # Define node attributes.
    node_reserved = {"Id", "Label"}
    node_attrs = sorted({
        key
        for node in nodes.values()
        for key in node
        if key not in node_reserved and node[key] not in (None, "")
    })

    node_attr_ids = {}

    if node_attrs:
        attributes = ET.SubElement(
            graph, tag("attributes"),
            {"class": "node", "mode": "static"}
        )

        for i, name in enumerate(node_attrs):
            aid = str(i)
            node_attr_ids[name] = aid

            ET.SubElement(
                attributes, tag("attribute"),
                {
                    "id": aid,
                    "title": name,
                    "type": "string"
                }
            )

    # Define edge attributes.
    edge_reserved = {"Source", "Target", "Type", "Label"}
    edge_attrs = sorted({
        key
        for edge in edges.values()
        for key in edge
        if key not in edge_reserved and edge[key] not in (None, "")
    })

    edge_attr_ids = {}

    if edge_attrs:
        attributes = ET.SubElement(
            graph, tag("attributes"),
            {"class": "edge", "mode": "static"}
        )

        for i, name in enumerate(edge_attrs):
            aid = str(i)
            edge_attr_ids[name] = aid

            ET.SubElement(
                attributes, tag("attribute"),
                {
                    "id": aid,
                    "title": name,
                    "type": "string"
                }
            )

    # Write nodes.
    graph_nodes = ET.SubElement(graph, tag("nodes"))

    for node in nodes.values():
        element = ET.SubElement(
            graph_nodes,
            tag("node"),
            {
                "id": str(node["Id"]),
                "label": str(node["Label"])
            }
        )

        values = ET.SubElement(element, tag("attvalues"))

        for name, aid in node_attr_ids.items():
            value = node.get(name)

            if value not in (None, ""):
                ET.SubElement(
                    values, tag("attvalue"),
                    {
                        "for": aid,
                        "value": str(value)
                    }
                )

    # Write edges.
    graph_edges = ET.SubElement(graph, tag("edges"))

    for i, edge in enumerate(edges.values()):
        element = ET.SubElement(
            graph_edges,
            tag("edge"),
            {
                "id": str(i),
                "source": str(edge["Source"]),
                "target": str(edge["Target"]),
                "label": str(edge.get("Label", ""))
            }
        )

        values = ET.SubElement(element, tag("attvalues"))

        for name, aid in edge_attr_ids.items():
            value = edge.get(name)

            if value not in (None, ""):
                ET.SubElement(
                    values, tag("attvalue"),
                    {
                        "for": aid,
                        "value": str(value)
                    }
                )

    tree = ET.ElementTree(root)

    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass

    tree.write(
        str(output_path),
        encoding="utf-8",
        xml_declaration=True
    )

    print("GEXF graph created:", output_path)

def main():
    here = Path(__file__).resolve().parent

    print("Taisir + Cairo 1924 -> unified Gephi graph")

    taisir_input = input(
        "Path to taisir_variants.csv [Enter = same folder as this script]: "
    ).strip().strip('"').strip("'")

    cairo_input = input(
        "Path to cairo_quran.txt [Enter = same folder as this script]: "
    ).strip().strip('"').strip("'")

    taisir_path = (
        Path(taisir_input)
        if taisir_input
        else here / "taisir_variants.csv"
    )

    cairo_path = (
        Path(cairo_input)
        if cairo_input
        else here / "cairo_quran.txt"
    )

    if not taisir_path.is_file():
        raise FileNotFoundError("Taisir CSV not found: " + str(taisir_path))

    if not cairo_path.is_file():
        raise FileNotFoundError("Cairo Quran JSON not found: " + str(cairo_path))

    headers, rows = read_taisir(taisir_path)
    cairo_words, cairo_reading = read_cairo(cairo_path)

    person_cols = [
        h for h in headers
        if h
        and h.strip().lower() not in METADATA_COLUMNS
        and re.match(r"^\s*\d+\s+.+", h)
    ]

    reciter_cols = [
        h for h in person_cols
        if not re.match(r"^\s*\d+\s+.+\s*\(.+\)\s*$", h)
    ]

    transmitter_cols = [
        h for h in person_cols
        if re.match(r"^\s*\d+\s+.+\s*\(.+\)\s*$", h)
    ]

    if not reciter_cols or not transmitter_cols:
        raise ValueError(
            "Could not identify reciter and transmitter columns."
        )

    reciter_by_number = {}
    transmitter_by_col = {}

    nodes = {}
    edges = {}

    def add_node(node_id, label, node_type, **attrs):
        if node_id not in nodes:
            item = {
                "Id": node_id,
                "Label": label,
                "type": node_type
            }
            item.update(attrs)
            nodes[node_id] = item
        else:
            for key, value in attrs.items():
                if value not in (None, "") and nodes[node_id].get(key) in (None, ""):
                    nodes[node_id][key] = value

    def add_edge(source, target, relation, **attrs):
        key = (source, target, relation)

        if key not in edges:
            item = {
                "Source": source,
                "Target": target,
                "Type": "Undirected",
                "Label": relation,
                "relation": relation,
            }
            item.update(attrs)
            edges[key] = item

    # Create reciter nodes.
    for col in reciter_cols:
        match = re.match(r"^\s*(\d+)\s+(.+?)\s*$", col)

        if not match:
            continue

        number, name = match.groups()
        rid = f"reciter_{number}"

        reciter_by_number[number] = rid

        add_node(
            rid,
            clean_text(name),
            "reciter",
            reader_number=number,
            source_column=col
        )

    # Create transmitter nodes and parent relationships.
    for col in transmitter_cols:
        match = re.match(
            r"^\s*(\d+)\s+(.+?)\s*\((.+?)\)\s*$",
            col
        )

        if not match:
            continue

        number, parent_name, transmitter_name = match.groups()

        tid = stable_id("transmitter", clean_text(col))
        transmitter_by_col[col] = tid

        add_node(
            tid,
            clean_text(transmitter_name),
            "transmitter",
            parent_reciter=clean_text(parent_name),
            reader_number=number,
            source_column=col
        )

        parent_id = reciter_by_number.get(number)

        if parent_id:
            add_edge(
                tid,
                parent_id,
                "transmits_for",
                source_column=col
            )
        else:
            print(
                "WARNING: no parent reciter node for transmitter:",
                col
            )

    # Retain only locations where Taisir records at least one variant.
    variant_rows = []

    for row in rows:
        if not any(clean_text(row.get(col, "")) for col in person_cols):
            continue

        try:
            loc = tuple(
                str(int(row[k]))
                for k in ("surah", "verse", "word")
            )
        except (TypeError, ValueError):
            print("WARNING: skipping invalid location:", row)
            continue

        cairo = cairo_words.get(loc)

        if cairo is None:
            raise ValueError(
                "Cairo source has no word at Taisir variant location "
                + ":".join(loc)
            )

        variant_rows.append((row, loc, cairo))

    def connect(
        person_id,
        text,
        loc,
        cairo,
        person_type,
        source_col,
        assignment_source
    ):
        text = clean_text(text)

        if not text:
            raise ValueError(
                "Attempted to connect an empty reading at "
                + ":".join(loc)
            )

        surah, verse, word = loc
        location = ":".join(loc)

        vid = variant_id(surah, verse, word, text)
        is_reference = text == cairo["transliteration"]

        add_node(
            vid,
            text,
            "variant",
            surah=surah,
            verse=verse,
            word=word,
            location=location,
            reference=cairo["transliteration"],
            reference_cairo=cairo["arabic"],
            transliteration=text,
            arabic=cairo["arabic"] if is_reference else "",
            is_reference="true" if is_reference else "false",
            source="Cairo 1924 / Taisir",
        )

        add_edge(
            person_id,
            vid,
            "reads_variant",
            person_type=person_type,
            source_column=source_col,
            location=location,
            assignment_source=assignment_source,
        )

    reference_mismatches = []
    explicit_hafs = []

    for row, loc, cairo in variant_rows:
        surah, verse, word = loc
        location = ":".join(loc)

        taisir_reference = clean_text(row.get("reference", ""))
        cairo_reference = cairo["transliteration"]

        if taisir_reference and taisir_reference != cairo_reference:
            reference_mismatches.append(
                (location, taisir_reference, cairo_reference)
            )

        # Always create the Cairo reference node at this location.
        ref_id = variant_id(
            surah, verse, word, cairo_reference
        )

        add_node(
            ref_id,
            cairo_reference,
            "variant",
            surah=surah,
            verse=verse,
            word=word,
            location=location,
            reference=cairo_reference,
            reference_cairo=cairo["arabic"],
            transliteration=cairo_reference,
            arabic=cairo["arabic"],
            is_reference="true",
            source="Cairo 1924 / Taisir reference",
        )

        # Resolve reciter readings.
        resolved_reciter = {}

        for col in reciter_cols:
            match = re.match(r"^\s*(\d+)\s+.+$", col)

            if not match:
                continue

            number = match.group(1)
            rid = reciter_by_number.get(number)

            if not rid:
                continue

            explicit = clean_text(row.get(col, ""))

            if explicit:
                reading = explicit
                origin = "explicit_reciter"
            else:
                reading = cairo_reference
                origin = "inherited_reference"

            resolved_reciter[number] = reading

            connect(
                rid,
                reading,
                loc,
                cairo,
                "reciter",
                col,
                origin
            )

        # Resolve transmitter readings.
        # An explicit transmitter reading always overrides inheritance.
        for col in transmitter_cols:
            match = re.match(
                r"^\s*(\d+)\s+.+?\s*\((.+?)\)\s*$",
                col
            )

            if not match:
                continue

            number = match.group(1)
            tid = transmitter_by_col.get(col)

            if not tid:
                continue

            explicit = clean_text(row.get(col, ""))

            if explicit:
                reading = explicit
                origin = "explicit_transmitter"
            else:
                reading = resolved_reciter.get(
                    number,
                    cairo_reference
                )
                origin = "inherited_reciter"

            connect(
                tid,
                reading,
                loc,
                cairo,
                "transmitter",
                col,
                origin
            )

            # Track explicit Hafs forms differing from Cairo.
            if col == "5 ʿĀṣim (Ḥafṣ)" and explicit:
                if explicit != cairo_reference:
                    explicit_hafs.append(
                        (location, explicit, cairo_reference)
                    )

    # Write the unified datasets.
    out_dir = taisir_path.parent

    nodes_path = out_dir / "qiraat_nodes.csv"
    edges_path = out_dir / "qiraat_edges.csv"

    node_fields = [
        "Id", "Label", "type", "reader_number",
        "parent_reciter", "surah", "verse", "word",
        "location", "reference", "reference_cairo",
        "transliteration", "arabic", "is_reference",
        "source_column", "source",
    ]

    edge_fields = [
        "Source", "Target", "Type", "Label", "relation",
        "person_type", "source_column", "location",
        "assignment_source",
    ]

    with nodes_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=node_fields,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(nodes.values())

    with edges_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=edge_fields,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(edges.values())
	
	    choice = input(
        "\nAlso create a GEXF graph file? [Y/n]: "
    ).strip().lower()

    if choice in ("", "y", "yes"):
        gexf_path = out_dir / "qiraat_graph.gexf"
        write_gexf(nodes, edges, gexf_path)
	
    # Report results.
    node_counts = {}
    edge_counts = {}

    for item in nodes.values():
        node_counts[item["type"]] = (
            node_counts.get(item["type"], 0) + 1
        )

    for item in edges.values():
        edge_counts[item["relation"]] = (
            edge_counts.get(item["relation"], 0) + 1
        )

    print("\nConversion complete.")
    print("Taisir input rows:", f"{len(rows):,}")
    print("Taisir variant locations:", f"{len(variant_rows):,}")
    print("Cairo reading:", cairo_reading)

    print("Reciter nodes:", f"{node_counts.get('reciter', 0):,}")
    print("Transmitter nodes:", f"{node_counts.get('transmitter', 0):,}")
    print("Variant nodes:", f"{node_counts.get('variant', 0):,}")

    print(
        "Transmits-for edges:",
        f"{edge_counts.get('transmits_for', 0):,}"
    )
    print(
        "Reads-variant edges:",
        f"{edge_counts.get('reads_variant', 0):,}"
    )

    print(
        "Taisir/Cairo reference mismatches:",
        len(reference_mismatches)
    )

    print(
        "Explicit Hafs entries differing from Cairo reference:",
        len(explicit_hafs)
    )

    for location, hafs_form, cairo_form in explicit_hafs:
        print(
            f"  {location}: Taisir Hafs={hafs_form!r} "
            f"| Cairo={cairo_form!r}"
        )

    if reference_mismatches:
        print("First reference mismatches:")

        for location, taisir_form, cairo_form in reference_mismatches[:10]:
            print(
                f"  {location}: {taisir_form!r} "
                f"| Cairo={cairo_form!r}"
            )

    print("\nCreated:")
    print(nodes_path)
    print(edges_path)

    print(
        "\nImport qiraat_nodes.csv first, "
        "then qiraat_edges.csv in Gephi."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", exc)
        raise
