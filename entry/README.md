# JSON

> A lightweight, text-based, language-independent data interchange format standardized by IETF RFC 8259 and ECMA-404 for portable structured data exchange.

## What it is

JSON, short for JavaScript Object Notation, is a text syntax for representing structured data. Although its notation was derived from JavaScript, the format is language-independent and is implemented across most modern programming ecosystems.

A JSON value can be an object, array, number, string, Boolean, or `null`. Objects contain name/value members and arrays contain ordered values. The standards define the syntax and interoperability rules; programming languages decide how parsed JSON values map into their own runtime types.

## Why it exists

JSON provides a compact, human-readable interchange format that is simple enough to generate, parse, inspect, transmit, and store. Its small data model makes it useful as a common boundary between software written in different languages and running on different platforms.

## How it works

A producer serializes data into Unicode text that follows the JSON grammar. A consumer parses that text, validates the syntax, and maps JSON values into suitable application data structures. RFC 8259 specifies JSON as an Internet Standard and includes interoperability guidance. ECMA-404 specifies the JSON syntax independently of application semantics.

JSON does not itself define schemas, application meaning, network transport, authentication, compression, or database behavior. Those concerns are layered around the format.

## Important concepts

- **Objects** — unordered collections of name/value members at the data-model level.
- **Arrays** — ordered sequences of JSON values.
- **Strings** — Unicode text represented using JSON string escaping rules.
- **Numbers** — numeric syntax whose exact runtime representation depends on the implementation.
- **Interoperability** — producers and consumers should avoid assumptions that exceed what the standards reliably guarantee.
- **Serialization versus semantics** — valid JSON syntax does not by itself define what fields mean.

## Typical use cases

- HTTP and web API request or response bodies.
- Configuration and metadata files.
- Event and message payloads.
- Data exchange between services written in different languages.
- Structured logs and lightweight persistence where a text format is appropriate.

## Alternatives and trade-offs

Alternatives include XML, YAML, CBOR, Protocol Buffers, MessagePack, Avro, and other text or binary formats. JSON is widely supported and easy to inspect, but it lacks a built-in schema system, comments in the standard syntax, native binary values, and strong type information. Large numeric values and duplicate object member names can also create interoperability problems when implementations make different choices.

## Security and reliability considerations

Applications should treat JSON input as untrusted data. Parsers and consumers need limits for document size, nesting depth, string length, and resource use. Applications should validate expected structure and types after parsing rather than treating syntactic validity as semantic validity. Numeric precision, Unicode handling, duplicate names, and unsafe interpretation of user-controlled fields can become security or correctness issues at system boundaries.

## Learning path

Start with text encoding and basic data structures, then learn JSON values and grammar, serialization/parsing, API payload design, schema validation, interoperability constraints, streaming considerations, and security limits for untrusted input.

## Verification

This module was reviewed on **2026-08-31** against IETF RFC 8259 and ECMA-404. RFC 8259 is the Internet Standard for the JSON data interchange format, while ECMA-404 defines the JSON data interchange syntax. citeturn851022search4turn851022search3
