# Pre-trace hypotheses

Recorded: 2026-08-22T10:50:42Z

Scope: these are predictions before framework-source tracing or runtime experiments.

## H1 LlamaIndex hidden convenience state

**Timestamp:** 2026-08-22T10:50:42Z

**Prediction:** LlamaIndex convenience APIs and global `Settings` can conceal material retrieval behavior, including model, chunking, callback, or storage choices, unless each resolved value is captured.

**Supporting/discriminating evidence:** Source tracing should show whether index and query paths read `Settings` or apply defaults not present in the explicit experiment configuration. A run with identical explicit configuration but changed global settings would discriminate this hypothesis if it changes trace events or retrieved output.

**Rejection condition:** The traced, configured index and query paths have no material global/default reads, or every such read is overridden and emitted in normalized trace evidence.

**Status:** OPEN

**Confidence before trace:** medium

## H2 Haystack graph visibility versus transformation risk

**Timestamp:** 2026-08-22T10:50:42Z

**Prediction:** Haystack's explicit component graph improves observability, while converters and splitters can still invisibly transform document identity or metadata.

**Supporting/discriminating evidence:** Source tracing should expose graph component inputs and outputs, then compare source ID, content hash, and metadata before and after conversion/splitting. A preservation result across every transition would weaken the transformation-risk portion.

**Rejection condition:** The traced graph does not improve stage observability relative to the alternative, or every relevant converter/splitter demonstrably preserves identity and metadata without an unrecorded transformation.

**Status:** OPEN

**Confidence before trace:** medium

## H3 Frameworks do not provide atomic reproducible releases alone

**Timestamp:** 2026-08-22T10:50:42Z

**Prediction:** Neither framework alone supplies atomic, reproducible release promotion that validates immutable corpus/configuration identity and prevents mixed-version answers.

**Supporting/discriminating evidence:** Source and runtime evidence should show whether either framework validates a complete versioned manifest and atomically switches a query-visible release pointer. A documented and exercised native mechanism satisfying both would reject this hypothesis.

**Rejection condition:** Either framework independently validates all versioned artifacts and atomically promotes one immutable, query-isolated release without external release logic.

**Status:** OPEN

**Confidence before trace:** high
