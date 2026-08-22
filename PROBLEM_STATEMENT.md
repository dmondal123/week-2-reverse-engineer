Repositories: LlamaIndex and Haystack
Level: Intermediate
Course alignment: ingestion; retrieval; reranking; context assembly; citations; index release

Build equivalent retrieval pipelines over a small versioned corpus. Expose parsing, chunking, embedding, retrieval, reranking, context packing, generation, and citation as separately observable stages.

Questions to answer

What is the real entry point for an answer, and which abstractions obscure the implementation path?
Which configuration and global/default state affect retrieval without appearing in the top-level pipeline?
How are source identity, chunk identity, score, order, and citation provenance preserved or lost?
What must be versioned together for a reproducible RAG release?
How would a delete, schema change, or embedding-model change propagate safely without mixed index state?
Controlled experiment: swap only the retriever or reranker while holding corpus, parser, generator, and evaluation cases fixed.

Failure injection: index only half a new corpus version, then query. Design a release mechanism that prevents mixed-version answers.

Submission emphasis: a full trace and release manifest for a production RAG pipeline.

Common execution brief
Use an AI harness to reverse engineer the assigned repository or comparison set. The harness accelerates navigation, hypothesis generation, test construction, and evidence organization; it does not replace source reading or execution evidence.

For every repository:

Record repository URL, exact commit SHA, access date, license file, runtime/language versions, and relevant configuration.
Start from one observable capability, not from the folder tree.
Write at least three competing hypotheses before following the implementation.
Trace the capability through entry point, interfaces, configuration, dependencies, state, runtime boundary, tests, and telemetry.
Run one controlled experiment and one failure-injection experiment. Change one material variable at a time.
Maintain the supplied evidence ledger. Label facts, interpretations, hypotheses, counterevidence, and unknowns.
Produce a decision-ready insight: what design should a production team adopt, avoid, or investigate next, and under what constraints?
Do not use production accounts, real personal/customer data, live credentials, unauthorized targets, or destructive security tests. Red-team work must use a local or explicitly authorized target.

Insights paper and grading rubric
Length and audience
Write 3,000–4,500 words, excluding appendices, for a CTO/FDE review panel. The paper must be understandable without reading the repository README and precise enough for an engineer to reproduce the investigation.

Required structure
Executive claim (150–250 words). State the most important finding, decision, and confidence. Do not begin with project history.
Decision context and scope. Define the production decision, stakeholders, constraints, non-goals, and why the selected capability matters.
Competing hypotheses. Present at least three plausible explanations written before the trace/experiment and identify discriminating evidence.
Architecture reconstruction. Show the request/event path and ownership of context, data, state, model, tools, policy, execution, telemetry, and recovery.
Experiment design. Document pinned versions, environment, variables, controls, cases, success measures, limitations, and failure-injection point.
Results and evidence. Present observations with exact source/runtime references. Include at least one result that contradicted or weakened an initial hypothesis.
Production analysis. Evaluate quality, latency, cost, safety, privacy, scale, failure recovery, operability, portability, and release implications relevant to the assignment.
Decision and ADR. Recommend adopt, adapt, combine, avoid, or investigate. State alternatives, consequences, reversibility, and the next evidence worth buying.
Limitations and unknowns. Explain what was not executed, evidence conflicts, external/runtime ownership, and claims that remain hypotheses.
AI-use disclosure. State how AI assisted, material prompts/instructions, tools and models if known, suggestions accepted/rejected, verification methods, and residual uncertainty.
Minimum evidence standard
12 or more commit-bound source references across implementation, tests, and configuration.
2 or more pieces of runtime evidence from the controlled experiment.
1 failure-injection result.
2 or more history/issue/ADR references when inferring design drivers.
1 counterexample or counterevidence item.
1 explicit rejected explanation or failed hypothesis.
Reproduction commands and sanitized raw artifacts in an appendix or linked bundle.
No architectural claim based only on a README, marketing page, AI answer, or repository popularity.
Required diagrams/tables
One architecture or sequence diagram showing real execution ownership.
One hypothesis/evidence table.
One experiment results table.
One risk/control or failure/recovery table.
Grading rubric — 100 points
Criterion	Points	Excellent	Adequate	Weak
Decision framing and competing hypotheses	10	Decision, constraints, non-goals, and 3+ genuinely competing falsifiable hypotheses are crisp.	Scope and hypotheses exist but are broad or weakly discriminating.	Product summary or one favored explanation presented as fact.
Architecture reconstruction	20	Traces real entry point through context, state, model, tools, policy, data, runtime, telemetry, and recovery with exact evidence.	Main path is correct but one or more boundaries are assumed or omitted.	README-level component list; runtime ownership is unclear.
Experimental rigor	20	Reproducible controlled and failure experiments, one-variable changes, predictions, raw evidence, and counterevidence.	Experiments ran but controls, predictions, or artifacts are incomplete.	Demo only, unverifiable claims, or no executed/source-level test.
Production-systems reasoning	15	Connects findings to relevant SLOs, safety, privacy, cost, scale, release, idempotency, backpressure, and recovery without checklist padding.	Discusses several relevant concerns but causality/trade-offs are shallow.	Generic production advice disconnected from evidence.
Evidence quality and provenance	15	Commit-bound source/test/config citations, runtime artifacts, fact/interpretation separation, contradiction handling, and confidence.	Sources are mostly credible but links are unpinned or provenance labels inconsistent.	AI/README claims laundered as facts; missing ledger.
Synthesis and decision quality	10	Produces a non-obvious insight, weighs alternatives, states consequences/reversibility, and names the next useful evidence.	Reasonable recommendation with limited alternative analysis.	Preference or feature comparison without a defensible decision.
AI-use transparency and verification	5	Material AI contributions, prompts/instructions, accepted/rejected suggestions, and verification status are auditable.	AI use disclosed generally but material influence is hard to reconstruct.	AI use hidden or AI-generated evidence presented as execution.
Communication and reproducibility	5	Executive-first, precise visuals, glossary where needed, exact commands, sanitized artifacts, and clear limitations.	Understandable but uneven, or reproduction needs interpretation.	Difficult to follow or cannot be reproduced.
Total	100			
Performance bands
90–100 — Distinction: defensible architecture model, rigorous evidence, meaningful contradiction, and decision-ready synthesis.
80–89 — Strong pass: technically sound and reproducible, with minor gaps in evidence breadth or production analysis.
70–79 — Pass: core trace and experiment are credible, but insight, controls, or boundary analysis is underdeveloped.
60–69 — Revision required: substantial work exists, but central claims are not sufficiently proven or reproducible.
Below 60 — Insufficient: descriptive summary, unsafe/unverifiable work, missing experiment, or evidence provenance failure.
Grade caps and integrity rules
No exact commit SHA or version manifest: maximum 85.
No controlled experiment or equivalent source-level executable test: maximum 70.
No failure injection: maximum 80.
No evidence ledger or material claims without provenance: maximum 70.
No AI-use disclosure: maximum 75.
Fabricated execution, citations, results, or concealed AI-generated evidence: maximum 50 and integrity review.
Unsafe, unauthorized, or production-impacting security/destructive testing: not gradable until reviewed, regardless of technical quality.
Assignment-specific use of the synthesis criterion
Score the rubric’s 10-point “Synthesis and decision quality” criterion against the assignment’s “submission emphasis”:

9–10: directly answers the distinctive design decision with comparative or counterfactual evidence.
6–8: answers it credibly but with limited depth or one unsupported link.
3–5: mentions the distinctive concern but mostly submits a generic repository review.
0–2: does not address the assignment-specific decision.
The total remains 100 points; no scaling or extra-credit arithmetic is required.

Upload one ZIP containing the complete investigation bundle.

Include the README, pinned versions and commit SHAs, source and scripts, tests, evidence ledger, sanitized runtime artifacts, required diagrams/tables, the 3,000–4,500 word insights paper, and the AI-use disclosure/evidence log.

Exclude secrets, credentials, .env files, dependency caches, virtual environments, node_modules, and generated build folders. Verify that the ZIP opens before uploading.