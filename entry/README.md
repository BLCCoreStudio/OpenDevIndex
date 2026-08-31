# Model Context Protocol (MCP)

Model Context Protocol (MCP) is an open protocol for connecting AI applications with external tools, data sources, and contextual capabilities through standardized client/server interactions.

## Why it matters

Without a common protocol, every AI application and external service needs custom integration glue. MCP defines shared message formats and capability models so an AI host can connect to compatible servers using a consistent interface rather than a unique API adapter for every tool.

## Core model

MCP distinguishes between hosts, clients, and servers. A host is the AI application. Clients manage connections from that host, while servers expose capabilities. The protocol uses JSON-RPC messages and defines interoperable features around tools, resources, prompts, authorization, and other capabilities depending on the negotiated protocol version.

The protocol evolves through dated specification revisions, so implementers must pay attention to version negotiation instead of assuming every MCP implementation supports the same feature set.

## Good fit

- AI assistants that need controlled access to external tools
- IDE and coding-agent integrations
- Connecting LLM applications to local or remote data
- Reusable integrations that should work across multiple AI hosts
- Building composable agent/tool ecosystems

## Trade-offs

MCP standardizes the interface but does not automatically make a tool safe. Hosts and servers still need strong authorization, input validation, least-privilege design, and careful handling of untrusted tool output. Protocol revisions and varying SDK support can also create compatibility gaps.

## Alternatives and related approaches

Direct REST/GraphQL APIs, custom function-calling adapters, plugin systems, and vendor-specific tool protocols can solve similar integration problems. MCP's advantage is interoperability across independently developed hosts and servers when both sides implement compatible revisions.

## Verification

Reviewed against the official MCP specification, repository, and July 2026 specification update on 2026-08-31.
