# Nadra Implementation Plan

Forward-only: this file describes work that remains. Available behavior and durable results belong
in [current-state documentation](current.md). Product behavior and evaluation belong in the
[specification](../design/spec.md).

Every task serves a capability from the
[capability registry](../design/spec.md#capability-registry). Capability groups follow registry
order in both lanes. Take the first required task in the earliest group that has one.

Task fields, statuses, ordering, and the capability-gap lifecycle are defined in the
[planning workflow](../guides/planning-workflow.md). Run `make plan-status` to view lane counts and
the next eligible work.

Work that belongs to the downstream corpus consumer rather than to this repository is held
separately in the [loc-lm-bench handoff plan](plan-loc-lm-bench.md). Nothing there is scheduled
here.

## Agent Implementation Tasks

### Acquisition ontology -- `acquisition-ontology`

#### ontology-objects-and-links

Consumers have no shared model to interface with, so each would need a bespoke export and every
change to one consumer would become a change to this repository.

- Serves: `acquisition-ontology` -- [Acquisition ontology](../design/spec.md#acquisition-ontology)
- Agent status: CLEAR
- Dependencies: none.
- User-visible outcome: A consumer reads a defined object model of the acquisition domain instead of
  this repository's storage layout.
- Scope boundary: In scope are the eight object types, their typed schemas, the defined links
  between them, and alignment to the published provenance vocabulary. Out of scope are actions,
  projections, persistence, and any object describing content rather than acquisition.
- Data and artifact paths: `src/nadra/ontology/objects.py` and `src/nadra/ontology/links.py`;
  fixtures under `tests/fixtures/ontology/`.
- Execution path: typed schemas expressing each object type and each link, with the provenance
  vocabulary class recorded per object type so the mapping is data rather than commentary.
- Acceptance gates: Every fixture object validates against its schema and every fixture link
  resolves to a defined relation. An object carrying an undefined link fails validation rather than
  being accepted and ignored.
- Documentation target: [Current implementation](current.md#areas), under a new ontology area page.

#### ontology-actions

Nothing stops a caller writing an object directly, so the security partition and the append-only
rule are conventions that no check can enforce.

- Serves: `acquisition-ontology` -- [Acquisition ontology](../design/spec.md#acquisition-ontology)
- Agent status: CLEAR
- Dependencies: `ontology-objects-and-links`.
- User-visible outcome: State changes only through declared actions, so an agent or a library cannot
  reach around the model to write an object it should not.
- Scope boundary: In scope are the action declarations, their typed parameters, submission criteria
  evaluated against object state, the edits each may make, and the single component permitted to
  execute each. Out of scope is the isolation mechanism itself, which the reader task owns.
- Data and artifact paths: `src/nadra/ontology/actions.py`; action fixtures under
  `tests/fixtures/ontology/`.
- Execution path: one declaration per action with parameters, criteria, edits, and executor, and a
  write path reachable only through them.
- Acceptance gates: A direct object write fails. An action whose submission criteria do not hold
  refuses rather than proceeding. No single executor is permitted both an action that reaches the
  network and an action that parses untrusted content.
- Documentation target: [Current implementation](current.md#areas), under a new ontology area page.

#### provenance-vocabulary-export (optional)

The model is readable only by code in this repository, which limits interoperability to consumers
someone has written an adapter for.

- Serves: `acquisition-ontology` -- [Acquisition ontology](../design/spec.md#acquisition-ontology)
- Agent status: CLEAR
- Dependencies: `ontology-actions`.
- User-visible outcome: A tool outside this stack reads the acquisition record without an adapter,
  because the model serializes to a published vocabulary.
- Scope boundary: In scope is serialization to the published provenance vocabulary and reading it
  back. Out of scope is a query engine, a triplestore, and reasoning over the serialized form.
- Data and artifact paths: `src/nadra/ontology/prov.py`; round-trip fixtures under
  `tests/fixtures/ontology/`.
- Execution path: map each object type to its provenance class and each link to its property, then
  round-trip a fixture graph.
- Acceptance gates: A fixture graph serializes and reads back with every object and every link
  intact. A link with no published equivalent is recorded as a local extension rather than dropped
  silently.
- Documentation target: [Current implementation](current.md#areas), under a new ontology area page.

### Evidence acquisition -- `evidence-acquisition`

#### acquisition-stack-bakeoff

An operator cannot yet say which capture and extraction components survive contact with the source
shapes this plane must handle, so every later choice would rest on reputation rather than
measurement.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: RUN NEEDED
- Research: yes
- Dependencies: `ontology-objects-and-links`.
- User-visible outcome: A recorded comparison naming the capture and extraction components the plane
  will use, with the measurement behind each choice.
- Scope boundary: In scope is capture fidelity and extraction quality across three source shapes: a
  JavaScript-rendered news page, a court-register document, and a static feed. Out of scope is
  crawling at volume, scheduling, storage layout, and any model work.
- Data and artifact paths: `$DATA_DIR/bakeoff/<run-id>/` holds captures, extracted text, and the
  comparison record.
- Execution path: `warcio` and Browsertrix Crawler on the capture side; Apache Tika, Docling, and
  trafilatura on the extraction side; a comparison entry point under `src/nadra/acquire/`.
- Acceptance gates: Every candidate runs against all three source shapes and the record states
  capture fidelity and extraction quality per shape. A negative result naming a shape that no
  candidate handles is a valid outcome and closes the task.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### capture-store

An operator has no way to fetch a source such that the fetch itself is evidence, so a claim made
from a page today cannot be defended once that page changes.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: CLEAR
- Dependencies: `ontology-actions`, `acquisition-stack-bakeoff`.
- User-visible outcome: A fetch produces a capture carrying target URI, capture time, and payload
  digest, and an index makes the store searchable without opening every record.
- Scope boundary: In scope is the egress component, credential handling, the capture store, its
  index, and the capture action. Out of scope is parsing or interpreting captured bytes, which
  belongs to the reader, and any scheduling of repeat captures.
- Data and artifact paths: `$DATA_DIR/captures/<acquisition-run-id>/` holds capture files and the
  index. Credentials resolve from the environment and never appear in artifacts or logs.
- Execution path: `src/nadra/acquire/egress.py` writing through `warcio`, invoking Browsertrix
  Crawler for sources the bakeoff marks as requiring a browser, executing only the capture action.
- Acceptance gates: A capture of a fixture source carries target URI, capture time, and payload
  digest, and appears as an object linked to its run. The capture action refuses a source with no
  current determination permitting retention. An error path forced by an unreachable host emits no
  credential material into stdout, stderr, or artifacts.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### isolated-reader

Untrusted document text would be read by a component that also holds credentials, which is the
condition that makes hidden instructions inside an acquired document dangerous rather than merely
present.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: CLEAR
- Dependencies: `capture-store`.
- User-visible outcome: The component that parses acquired text cannot reach the network, so a
  hidden instruction inside a document has nothing to exfiltrate to and no credential to use.
- Scope boundary: In scope is the reader process, its isolation mechanism, and the derive and revise
  actions producing documents from captures. Out of scope is the sandbox primitive for third-party
  collectors, which is a separate decision, and any guardrail library.
- Data and artifact paths: reads `$DATA_DIR/captures/<acquisition-run-id>/`, writes
  `$DATA_DIR/documents/<acquisition-run-id>/`. The reader receives no credential environment.
- Execution path: `src/nadra/acquire/reader.py` running under the isolation mechanism selected here,
  as a separate process from the egress component, executing only reader-side actions.
- Acceptance gates: A test asserting the reader can open a socket fails when isolation is active and
  passes when it is disabled, so the property is proven rather than asserted. Re-deriving one capture
  yields byte-identical text and the same document identity. A changed upstream produces a revision
  link and leaves the previous document untouched.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### corpus-projection

Nothing renders objects into the shape the downstream corpus consumer reads, so the acquired
material cannot reach it.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: CLEAR
- Dependencies: `isolated-reader`.
- User-visible outcome: An acquisition run produces a corpus the downstream consumer ingests with no
  hand-editing, without that consumer learning anything about how acquisition works.
- Scope boundary: In scope is one projection from objects to the corpus directory and per-document
  metadata that consumer reads. Out of scope is chunking, which the consumer owns, and any change to
  an object or action to suit that consumer.
- Data and artifact paths: `$DATA_DIR/projections/corpus/<acquisition-run-id>/`. The contract is
  stated in [the loc-lm-bench handoff plan](plan-loc-lm-bench.md).
- Execution path: `src/nadra/project/corpus.py`, executing the projection action, verified against a
  local checkout of the consumer.
- Acceptance gates: The consumer's corpus ingest reports every document ok with no hand-editing. The
  projection refuses any document whose determination forbids that distribution class. Producing it
  required no change to an object, a link, or an action.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### second-projection

Decoupling is currently a claim. One projection proves nothing, because a model shaped around a
single consumer is indistinguishable from that consumer's schema under a different name.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: CLEAR
- Dependencies: `corpus-projection`.
- User-visible outcome: A second consumer is served from the same objects, so adding consumers is
  adding projections rather than reworking the model.
- Scope boundary: In scope is a records-with-spans projection for analysis consumers and the check
  that adding it changed no object, link, or action. Out of scope is any analysis over the records,
  and the monitoring and content projections, which follow the same pattern later.
- Data and artifact paths: `$DATA_DIR/projections/records/<acquisition-run-id>/`.
- Execution path: `src/nadra/project/records.py`, rendered from the same objects the corpus
  projection reads.
- Acceptance gates: Both projections render from one acquisition run. A check comparing the object,
  link, and action definitions before and after this task reports no change. A change to either
  proves the model was shaped around one consumer and fails the task.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### provenance-round-trip

A claim resting on an acquired document cannot be re-defended later, because nothing resolves a
document back to the capture that produced it without going to the network.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: CLEAR
- Dependencies: `corpus-projection`.
- User-visible outcome: Any document resolves offline to the capture behind it, so a months-old claim
  can be checked against what the source actually said at capture time.
- Scope boundary: In scope is offline resolution from document to capture along the derivation link,
  and replay of that capture. Out of scope is comparing a capture against the live page, which is a
  freshness question rather than a provenance one.
- Data and artifact paths: resolves across `$DATA_DIR/documents/` and `$DATA_DIR/captures/`, with the
  sampling record under `$DATA_DIR/provenance/<acquisition-run-id>/`.
- Execution path: `src/nadra/acquire/trace.py` executing the resolve action, with `pywb` for replay,
  exercised with networking disabled.
- Acceptance gates: Ten documents sampled at random each resolve to their capture with no network
  access. Pass is ten of ten; any lower count fails the task rather than being averaged.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### injection-canary-test

The partition between reader and egress is an architectural claim, and an architectural claim that no
test can fail is indistinguishable from a comment.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: CLEAR
- Dependencies: `provenance-round-trip`.
- User-visible outcome: An instruction hidden in an acquired document is shown, by a failing test
  when the property breaks, to reach no component that holds credentials.
- Scope boundary: In scope is a canary fixture, its path through capture and derivation, and the
  assertion that it reaches no credential-holding component. Out of scope is detecting or classifying
  injection attempts, which is a guardrail question deferred until this structural defence exists.
- Data and artifact paths: canary fixture under `tests/fixtures/acquire/`, run records under
  `$DATA_DIR/canary/<run-id>/`.
- Execution path: `tests/acquire/test_injection_canary.py` exercising the egress and reader processes
  together.
- Acceptance gates: The canary appears in document text and in no egress-side log, request, or
  artifact. Removing the isolation makes the test fail, so the test is shown to have teeth.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### roundtrip-fixture

The projection contract between this repository and the downstream consumer is unwritten in
executable form, so it can drift on either side without anything noticing.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: CLEAR
- Dependencies: `corpus-projection`.
- User-visible outcome: A change on either side of the projection contract fails a check rather than
  surfacing later as a corpus the consumer silently mangles.
- Scope boundary: In scope is a small committed projection output and the check that ingests it. Out
  of scope is the consumer-side half of the check, tracked in
  [the loc-lm-bench handoff plan](plan-loc-lm-bench.md).
- Data and artifact paths: fixture under `tests/fixtures/corpus-roundtrip/`, roughly twenty
  documents, small enough to commit.
- Execution path: `tests/project/test_corpus_contract.py`, skipped with a stated reason when no
  consumer checkout is present so the gate stays green on a bare clone.
- Acceptance gates: The fixture ingests with every document ok. A deliberate change to a projected
  field name fails the check.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

## Human-Assisted Tasks

### Evidence acquisition -- `evidence-acquisition`

#### source-determinations

No source in the initial set has a recorded judgement of whether its terms permit retention and local
processing, so any capture taken now carries an unknown obligation and the capture action has nothing
to check against.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: HUMAN-GATED
- Dependencies: `ontology-objects-and-links`.
- User-visible outcome: Every source in the initial set carries a recorded judgement of what may be
  retained, processed, and redistributed, so acquisition can refuse material it must not keep.
- Scope boundary: In scope is one determination per source, with the date it was made and the terms
  it rests on. Out of scope is per-document judgement, and any legal opinion beyond what an operator
  can responsibly record.
- Data and artifact paths: the source register beside the source configuration in this repository.
- Execution path: read each source's published terms, record a determination through the action
  reserved for a human agent, and mark sources whose terms are unclear as not acquirable.
- Acceptance gates: Every source in the initial set has a determination with a date and a cited term.
  A source with no determination cannot be captured, enforced by the capture action rather than by
  convention.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### court-register-access-decision

Access to the court register can be taken directly from open data or through a commercial
intermediary, and the choice changes cost, licence position, and integration effort, but it has not
been made.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: HUMAN-GATED
- Dependencies: `source-determinations`.
- User-visible outcome: A recorded decision on how the court register is reached, with the licence
  position it implies and the cost it commits to.
- Scope boundary: In scope is the access route and its terms. Out of scope is any capability that
  joins register records across sources, which needs its own review before it is specified because
  anonymised records can still re-identify through linkage.
- Data and artifact paths: recorded as the determination for that source in the source register.
- Execution path: compare the direct open-data route against the commercial route on licence terms,
  coverage, latency after anonymisation, and cost, then record the choice.
- Acceptance gates: The decision names the route, the terms it rests on, and the cost committed. A
  determination that neither route is currently acceptable is a valid outcome and blocks register
  acquisition rather than downgrading it.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.

#### ukrainian-web-backend (optional)

Source discovery beyond the named set needs a search backend that indexes Ukrainian-language web, and
none is configured, so the plane can only reach sources somebody has already named.

- Serves: `evidence-acquisition` -- [Evidence acquisition](../design/spec.md#evidence-acquisition)
- Agent status: BLOCKED BY HUMAN
- Dependencies: none.
- User-visible outcome: An operator can discover Ukrainian-language sources the named set does not
  cover, rather than only acquiring from a hand-written list.
- Scope boundary: In scope is account creation, credential issue, and configuration. Out of scope is
  discovery logic, and the named-source acquisition path, which does not depend on this task.
- Data and artifact paths: the credential resolves from the environment or a secret manager and is
  never written into the repository or into artifacts.
- Execution path: create the account, issue a scoped key, and configure it for the egress component
  only.
- Acceptance gates: A discovery query returns Ukrainian-language results, and the credential is
  absent from the repository, from logs, and from any artifact under `$DATA_DIR`.
- Documentation target: [Current implementation](current.md#areas), under a new acquisition area
  page.
