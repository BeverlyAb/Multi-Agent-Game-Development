# Finding Severity & Numbering

The severity classification used by reviews and the plan -> review ->
response workflow. Assign every finding a level and a number.

## Severity levels

| Level  | Meaning          | Example                                        | Blocks completion? |
| ------ | ---------------- | ---------------------------------------------- | -----------------: |
| **P0** | Critical         | Credential exposure, destructive data loss     |                Yes |
| **P1** | Serious          | Security/correctness bug, requirement violation |                Yes |
| **P2** | Moderate         | Maintainability, incomplete edge case, weaker design |         Usually no |
| **P3** | Improvement      | Naming, cleanup, minor simplification          |                 No |

- **P0 / P1** findings block completion: the change is not done until
  they are resolved.
- **P2** findings block completion only if the reviewer marks them as
  must-fix; treat them as "fix unless you have a reason not to."
- **P3** findings never block completion; address at your discretion.

## Finding numbers

Each finding gets a unique id composed of its severity and a zero-padded
sequence number within that severity, starting at 001:

```
P1-001
│   │
│   └── Finding number
│
└────── Severity
```

Examples: `P0-001`, `P1-003`, `P2-007`, `P3-012`.

## Usage

- The reviewer records each finding with its id in
  `docs/agent-reviews/review-<name>.md`.
- The implementation agent refers back by id in
  `docs/agent-responses/response-<name>.md` ("P1-001 — fixed in ...",
  "P2-004 — won't fix, reason ...").
- Only the reviewer assigns severity and numbers; the implementation
  agent does not renumber findings.
