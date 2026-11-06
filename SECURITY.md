# Security and public-data policy

Only code and explicitly fictional fixtures belong in this public repository. Do not add client workbooks, exports, screenshots, business totals, names, credentials or machine-specific paths. Ignoring a file does not remove an already tracked copy.

Legacy workbook documentation, copied test identifiers and the bundled PDF have been removed or replaced with fictional examples. Repository history was rewritten to remove the previous documentation and test-fixture paths; current replacements contain synthetic data only. Existing clones must be replaced or carefully reconciled without merging the old history back. History rewriting cannot retract downloaded copies, forks or cached content; those require separate cleanup.

The application is single-operator. A random server-configured bearer token gates all routes except health. The browser stores it only in memory. All holders share the same access; it is not a substitute for individual accounts or tenant isolation. Uploads and external AI processing require separate explicit opt-ins. Local ports bind to loopback. Authenticated responses use no-store. Global per-process request limits bound read/write/auth attempts; production deployments need additional edge controls.

Workbook validation caps expanded size (100 MiB), sheets (20), rows (100,000), cells (2,000,000), columns (256), and request body time/size before parsing. These bounds reduce resource abuse; they do not provide full process isolation. Exports store untrusted strings as text, never formulas.

Gemini keys use the documented x-goog-api-key header, not query parameters: https://ai.google.dev/api . Provider failures return generic errors without request URLs or response bodies. External AI remains off by default; only synthetic or approved minimized issue text may be sent. No automatic anonymizer can safely remove all confidential meaning from arbitrary free text.
