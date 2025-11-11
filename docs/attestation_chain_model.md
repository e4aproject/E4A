# The E4A Attestation Chain of Trust
This chain describes the lineage from developer intent to a verifiable artifact.
\`\`\`mermaid
flowchart LR
    A["Developer Commit"] --> B["CI Pre-Flight: Validate"];
    B --> C["CI Release: Sign Attestation"];
    C --> D["Anchor Hash (URA)"];
    D --> E["Publish Artifacts"];
\`\`\`
This ensures every release is backed by a cryptographically verifiable history of its validity.
