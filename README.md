# Sac-read: Qurʾānic Readings Network

This repository contains a computational representation of the seven canonical Qurʾānic readings (*al-qirāʾāt al-sabʿ*) and their transmitters, structured as a network for analysis and visualization in [Gephi](<https://gephi.org/>) The resulted graph can be accessed directly through this link:
[gehi lite visualization of qiraat7](https://lite.gephi.org/v1.1.1/?file=https://raw.githubusercontent.com/hamazimi/sac_read/refs/heads/main/qiraat7.gexf)

The project converts word-level variant readings into a graph connecting canonical reciters and their transmitters to the textual variants attributed to them. It also incorporates the Cairo 1924 edition of the Qurʾān, representing the reading of Ḥafṣ ʿan ʿĀṣim, as an explicit reference layer.

The broader objective is to facilitate the computational study of relationships among Qurʾānic readings, their transmission, and their textual points of divergence.

## Repository Contents

| File | Description |
| --- | --- |
| `Qiraat combiner & converter.py` | Python script for combining the Taisīr variant dataset with the Cairo 1924 reference text and generating Gephi-compatible network files. |
| `qiraat7.gexf` | Updated network incorporating the Cairo 1924 reference reading of Ḥafṣ ʿan ʿĀṣim. |
| `taisir_variants_network.gexf` | Earlier version of the network, generated from the Taisīr readings without the additional Cairo reference-reading layer. |

The two GEXF files represent successive stages of the same network-building process. The updated `qiraat7.gexf` should be used when the Cairo reference reading is required.

## Data Sources and Acknowledgements

### Corpus Coranicum

[Corpus Coranicum](<https://corpuscoranicum.de/>) is the principal scholarly digital resource underlying this project.

Its databases document early Qurʾānic manuscripts, variant readings preserved in Islamic scholarly literature, and the Cairo 1924 printed edition. Its *Variae Lectiones Coranicae* database provides the textual and scholarly context for the study of Qurʾānic variant readings.

The present project draws on this work in two ways:

- The readings attributed to the seven canonical reciters and their transmitters are based on the tradition documented in Corpus Coranicum, particularly its presentation of ad-Dānī's *at-Taysīr fī al-qirāʾāt al-sabʿ*.
- The Cairo 1924 edition and its word-level transliteration provide the reference reading used in the updated network.

This project is independent and is not affiliated with or endorsed by Corpus Coranicum.

### Abdul Rahim Nizamani's Corpus Coranicum Dataset

The structured Taisīr data used in this project builds on the work of Abdul Rahim Nizamani:

[Corpus Coranicum Quranic Variants Dataset](<https://github.com/arnizamani/corpus_coranicum_variants_dataset>)

This project provides machine-readable Qurʾānic variant readings for the seven canonical reciters, including their transmitters, in CSV and JSON formats.

Its `taisir_variants.csv` dataset is the input for the network-construction script. The dataset's organization of reciter-level and transmitter-level readings makes it possible to represent the relationships between readers and individual textual variants.

The present repository builds on that dataset by transforming the tabular representation into a graph structure and integrating the Cairo 1924 reference reading.

### ad-Dānī's *at-Taysīr*

The principal textual tradition represented in the network is the seven-reading system as presented by Abū ʿAmr al-Dānī (d. 444/1053) in:

*al-Taysīr fī al-qirāʾāt al-sabʿ.*

The network distinguishes the seven canonical reciters (*qurrāʾ*) and their two transmitters (*ruwāt*):

1. Nāfiʿ — Qālūn and Warš
2. Ibn Kaṯīr — al-Bazzī and Qunbul
3. Abū ʿAmr — ad-Dūrī and as-Sūsī
4. Ibn ʿĀmir — Hišām and Ibn Ḏakwān
5. ʿĀṣim — Šuʿba and Ḥafṣ
6. Ḥamza — Ḫallād and Ḫalaf
7. al-Kisāʾī — ad-Dūrī and al-Laiṯ

## Network Structure

The graph contains three principal types of nodes:

- **Reciters (`reciter`)**: the seven canonical readers.
- **Transmitters (`transmitter`)**: the two transmitters associated with each reciter.
- **Variants (`variant`)**: word-level readings at specific Qurʾānic locations.

Two principal types of edges represent the relationships:

- **`transmits_for`**: connects a transmitter to the reciter with whom the transmitter is associated.
- **`reads_variant`**: connects a reciter or transmitter to the reading attributed to them at a particular textual location.

Each variant is associated with its surah, verse, and word position. Its transliteration and, where applicable, Arabic text are retained as node attributes.

### Reading Assignment and Reference Logic

The conversion script applies the following rules:

1. At every location where the Taisīr dataset records at least one variant, the corresponding Cairo 1924 reference reading is represented as a variant node.
2. If a reciter has an explicit reading in the Taisīr dataset, that reading is assigned to the reciter. Otherwise, the Cairo reference reading is inherited.
3. If a transmitter has an explicit reading, it takes precedence over the reading assigned to its reciter. Otherwise, the transmitter inherits the resolved reading of its reciter.
4. Explicit transmitter readings are therefore preserved even when they differ from the reciter-level reading.
5. Explicit Ḥafṣ readings that differ from the Cairo reference are retained as distinct variants rather than being overwritten by the reference text.

Variant identifiers are generated from the combination of the Qurʾānic location and normalized transliteration. This allows the same reading at the same location to retain a consistent identifier across the datasets, while identical transliterations at different locations remain distinct nodes.

## Generating the Network

The converter is written in Python and uses the standard library.

### Required input files

The script expects two input files:

- `taisir_variants.csv` — the structured Taisīr variant dataset.
- `cairo_quran.txt` — the Cairo 1924 reference text in JSON format, including word-level transliteration and Arabic text.

Place both files in the same directory as the Python script, or provide their paths when prompted.

### Running the converter

``` bash
python "Qiraat combiner & converter.py"
```

The script will request the paths to the two input files. Press Enter if they are in the same directory as the script.

It generates:

``` text
qiraat_nodes.csv
qiraat_edges.csv
qiraat_graph.gexf
```

The GEXF export is optional. The CSV files can also be imported separately into Gephi.

### Importing into Gephi

1. Open Gephi and create a new project.
2. Import `qiraat_nodes.csv` as a node table.
3. Import `qiraat_edges.csv` as an edge table.
4. Alternatively, open the generated GEXF file directly.

The GEXF files included in this repository can be opened directly in Gephi.

## Research Scope and Limitations

This network represents the readings documented in the selected Taisīr dataset and should not be understood as an exhaustive representation of every historical Qurʾānic reading tradition.

In particular:

- The network reflects the scope and editorial decisions of its underlying dataset.
- Word-level transliteration does not necessarily represent every phonetic or recitational distinction.
- The Cairo 1924 edition functions as a reference reading, not as a claim that all other readings are historically derived from it.
- Graph edges encode documented reading assignments and transmission relationships; they do not, by themselves, establish historical genealogical relationships between textual variants.

The graph is intended as a research instrument for exploring the distribution and relationships of readings, rather than as a substitute for critical editions or primary sources.

## Citation and Further Reading

Please acknowledge the following resources when using this project:

- **Corpus Coranicum**: [https://corpuscoranicum.de/](<https://corpuscoranicum.de/>)
- **Nizamani, Abdul Rahim**: [Corpus Coranicum Quranic Variants Dataset](<https://github.com/arnizamani/corpus_coranicum_variants_dataset>)
- **al-Dānī**: *al-Taysīr fī al-qirāʾāt al-sabʿ*.

## License and Attribution

The network and conversion code are provided for research and educational use. Users should consult the licensing and attribution requirements of the original datasets before redistributing source data or derivative datasets.

This repository is an independent research project. It is not an official product of Corpus Coranicum or of Abdul Rahim Nizamani's dataset project.

## Project

Repository: https://github.com/hamazimi/sac\_read

Two points to settle before publishing:

* The README describes `taisir_variants.csv` and `cairo_quran.txt` as required inputs, but they are not among the three repository files you listed. If you intend to keep them outside the repository, the current wording is appropriate.

* I have deliberately described the graph as a network of reading assignments and transmission relationships, not as a proven historical genealogy. That distinction matters for the project's scholarly framing.

The roles of Corpus Coranicum and Nizamani's dataset are supported by their project documentation. Corpus Coranicum +2
