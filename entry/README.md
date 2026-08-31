# Apache Parquet

> An open, column-oriented data file format designed for efficient storage, compression, selective reads, and analytics across large structured datasets.

## What it is

Apache Parquet is a column-oriented file format for structured data. Instead of storing complete rows one after another, Parquet organizes values by columns inside row groups. This layout makes it possible for analytical workloads to read only the columns they need and gives compression and encoding algorithms long runs of similar values to work with.

Parquet is a format specification, not one particular database or query engine. Multiple libraries and systems implement readers and writers around the common file-format definition.

## Why it exists

Large analytical datasets are often queried by selecting a subset of columns across many rows. A row-oriented representation can force unnecessary I/O for fields that a query never uses. Parquet was designed to make column projection, compression, encoding, metadata-driven skipping, and interoperability practical across large data-processing ecosystems.

## How it works

A Parquet file is divided into row groups. Within each row group, data for each column is stored in a column chunk, which is further divided into pages. File metadata records schemas and locations needed by readers. The file format places metadata at the end of the file, allowing writers to stream data before finalizing metadata.

Readers typically inspect file metadata first, determine which column chunks or pages are relevant, and then read the required data. Optional statistics, indexes, encodings, compression, and other format features can reduce I/O or storage costs when supported by the chosen implementation.

## Important concepts

- **Row group** — a horizontal partition of rows that contains column chunks for the fields in that group.
- **Column chunk** — the data for one column within a row group.
- **Page** — a smaller encoded unit within a column chunk.
- **Physical and logical types** — the storage representation and higher-level interpretation of values.
- **Metadata** — schema, offsets, sizes, encodings, statistics, and other information used to navigate or interpret a file.
- **Projection** — reading only the columns required by a workload.

## Typical use cases

- Analytical data lakes and warehouses.
- Data exchange between query engines and processing frameworks.
- Long-term storage of tabular datasets where selective reads matter.
- Batch analytics, feature pipelines, and machine-learning data preparation.
- Interoperable datasets consumed by several languages or engines.

## Alternatives and trade-offs

Alternatives include ORC, Avro, Arrow IPC, CSV, JSON, database-native storage formats, and specialized binary encodings. Parquet is especially strong for analytical scans and column projection, but it is not inherently optimized for frequent in-place row updates or tiny transactional writes. File size, row-group sizing, sort order, compression, statistics, and implementation support can strongly affect performance.

## Compatibility and versioning

The Parquet ecosystem contains multiple independent implementations, and feature support can differ between them. Newer format features may have different forward-compatibility properties. Systems that exchange Parquet files should test the exact combinations of features, readers, and writers they depend on rather than assuming every implementation supports every optional feature.

## Security and reliability considerations

Parquet readers process complex binary metadata, encodings, compression streams, nested structures, and potentially very large files. Untrusted files should be handled with maintained libraries and resource limits. Applications should validate schemas and logical types, avoid trusting metadata as application authorization or business validation, and account for decompression or allocation costs when processing attacker-controlled input.

## Learning path

Start with row-oriented versus column-oriented storage, then learn projection and compression, row groups, column chunks, pages, schemas and types, encodings, file metadata, statistics and indexes, implementation compatibility, and query-engine behavior.

## Verification

This module was reviewed on **2026-08-31** against the Apache Parquet project documentation and the canonical `apache/parquet-format` specification repository.
