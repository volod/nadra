# Design: Nadra Acquisition and Provenance Plane

Branch: nd-01-design
Repo: volod/nadra
Status: DRAFT

## Purpose

Nadra acquires evidence from external sources, preserves it with provenance strong enough
to re-defend a claim months later, and publishes it as a shared semantic model that any
consumer can read without knowing how acquisition works.

It is the common substrate under a set of automation tasks that otherwise each grow their
own collector and their own private data shape. Every one of those tasks reads text an
attacker may control, so the acquisition boundary is also the security boundary, and the
plane owns both.

## Scope: the tasks this plane serves

| Area | What the plane supplies | What lives elsewhere |
| --- | --- | --- |
| Big-data analytics, OSINT, document processing: court decisions, risk in draft laws, tax datasets and fictitious-company detection, connections between defendants | Registry and document acquisition, anonymisation-aware handling, immutable captures, provenance, licence facts | Analysis, entity resolution, model selection and scoring |
| Real-time monitoring, parsing, transcription: official activity, court hearings and meetings, streaming news | Stream and feed acquisition, scheduling, capture of transient sources before they change, transcription intake | Alerting policy, summarisation, downstream judgement |
| Content creation and audience work: video comment analysis, editorial correction, audio digests | Acquisition of comments, media and source material with provenance | Generation, synthesis, publishing, and every credential those need |
| Internal tooling built with coding agents | Nothing. This is a development practice | Lock files, sandboxes, dependency and review policy |

Areas one and two are the plane's core. Area three uses it only on the input side, and its
generation and publishing half is a separate concern with a different threat profile. Area
four is how the team works, not a capability the plane provides.

Four consumer areas is the reason the plane publishes an ontology rather than a bespoke
export per consumer. Four point-to-point mappings become four things to keep in step, and
they will not stay in step.

## Ontology

The plane's interoperability contract is a semantic layer, not a file format. Consumers
interface with a defined object model of the acquisition domain rather than with nadra's
storage, its code, or each other's schemas.

The pattern is the Foundry-style Ontology: **Objects** as the domain's nouns, **Links** as
the relationships that make them traversable, and **Actions** as the only way state
changes. Engineers who know that pattern will recognise the shape immediately; engineers
who do not need only three ideas rather than a schema per consumer.

The upper vocabulary is **W3C PROV-O**, whose Entity, Activity and Agent classes and
`wasGeneratedBy`, `wasDerivedFrom`, `wasRevisionOf` and `wasAttributedTo` properties
already describe exactly what acquisition produces. Adopting it rather than inventing a
vocabulary means the model is interpretable outside this stack, and it applies the
reuse instinct to the semantic layer as well as to the libraries.

### Objects

| Object | PROV class | Meaning |
| --- | --- | --- |
| `Source` | Agent | A publisher or registry that produces content |
| `Determination` | Entity | A recorded judgement about a Source's terms: what may be retained, processed and redistributed, with the date it was made and the terms cited |
| `AcquisitionRun` | Activity | One batch of fetching, with its configuration and window |
| `Capture` | Entity | An immutable observation of a Source at a moment, carrying target URI, capture time and payload digest |
| `Derivation` | Activity | The reader turning a Capture into a Document |
| `Document` | Entity | Normalized immutable text with a content-derived identity |
| `Span` | Entity | A character range within a Document, the unit downstream labels attach to |
| `Operator` | Agent | The person accountable for a Determination or an approval |

Eight object types, closed by intent. A closed vocabulary is what makes the model
traversable and cheap; an open one becomes a second analysis problem.

### Links

```text
  Operator --wasAttributedTo(inv)--> Determination --governs--> Source
                                                                   ^
                                                                   | wasAttributedTo
  AcquisitionRun --wasAssociatedWith--> Operator                    |
        |                                                          |
        | wasGeneratedBy(inv)                                      |
        v                                                          |
     Capture ------------------------------------------------------+
        |
        | wasDerivedFrom(inv)   +--- wasRevisionOf ---+
        v                       v                     |
     Document -----------------------------------> Document
        ^
        | withinDocument
     Span
```

`wasRevisionOf` carries the supersession chain, which is why a changed upstream produces a
new Document rather than a rewrite: the previous version stays addressable and every Span
pointing into it keeps resolving.

### Actions

State changes only through Actions. An Action is not a function call: it is a declared
unit with four parts, and writing them down is what turns the security architecture from a
convention into something the model enforces.

| Part | What it declares |
| --- | --- |
| Parameters | The typed inputs the Action accepts, and nothing beyond them |
| Submission criteria | The conditions that must hold before it may run, evaluated against Object state rather than trusted from the caller |
| Edits | Exactly which Objects and Links it creates or relates. An Action that could touch anything is not an Action |
| Executor | The component permitted to run it. This is where the network and parsing partition lives |

| Action | Executor | Guard |
| --- | --- | --- |
| `RecordDetermination` | Operator | Requires a human agent. No automated agent may execute it |
| `CaptureSource` | Egress component | Refuses unless a current Determination permits retention |
| `DeriveDocument` | Reader component | Runs without network capability; refuses a Capture absent from the store |
| `ReviseDocument` | Reader component | Emits a new Document linked by `wasRevisionOf`. Cannot mutate the previous version |
| `ProjectCorpus` | Reader component | Refuses any Document whose Determination forbids the projection's distribution class |
| `ResolveProvenance` | Any reader | Read-only, offline |

No Action grants both network access and untrusted parsing. That partition is the
structural defence described in the threat model, expressed as permissions rather than as
prose.

**Propagation, and where this model departs from the pattern.** A Foundry-style Ontology
gets its single source of truth from write-back: an Action edits an Object and every
consumer sees the change. Here Objects are append-only by I4, because Spans are character
offsets and a rewrite would silently invalidate every label pointing into a Document. So
propagation happens by revision rather than by mutation: `ReviseDocument` adds a new
`Document` linked by `wasRevisionOf`, consumers follow the chain to the current version,
and the previous version stays addressable for anything already citing it. The single
source of truth property holds; the mechanism is a chain rather than an overwrite, and that
difference is deliberate rather than a limitation.

### Projections

A projection renders ontology Objects into the shape one consumer already reads. Consumers
do not learn nadra's internals and nadra does not learn theirs.

| Consumer | Projection |
| --- | --- |
| `loc-lm-bench` | Corpus directory plus per-document governance sidecars |
| OSINT and legal analysis | Objects and Links as records, with Spans preserved |
| Monitoring | Capture stream keyed on Source and time |
| Content input | Documents with attribution |
| Anything outside this stack | PROV-O serialization |

Adding a consumer adds a projection. It does not change an Object, a Link, or an Action.
That property is the whole point, and Slice A tests it rather than asserting it.

## Threat model

The plane sits where untrusted external text enters the system, so its threats are the
reason it is a separate service rather than a library inside each task.

**T1. Indirect prompt injection.** A court order, financial report or web page can carry
instructions aimed at any model that later reads it. This is the central 2026 agent threat:
retrieval systems, browsing agents, tool servers and summarising assistants all consume
attacker-controllable text. Acquisition is where that text arrives, so it is where the
structural defence belongs.

**T2. Supply-chain compromise through third-party collectors.** Parsing configurations,
plugins and agent skills can carry hooks that execute with user rights, including on
session-start events.

**T3. Secret leakage through context.** API keys printed to stdout on a connection error
enter a model's context and can be reproduced into generated code or output.

**T4. Silent source mutation.** An upstream page changes or disappears and every claim
resting on it becomes unverifiable. Not an attack, but the same effect on trust.

### Security architecture

**Two-plane split, enforced by Action permissions.** The component that reads untrusted
text has no network access; the component with network access never parses untrusted text.
`CaptureSource` belongs to the egress component and `DeriveDocument` to the reader, and
nothing holds both. This is the dual-model pattern that current work identifies as the most
reliable structural defence against indirect injection.

**Agents act only through Actions.** An automated agent never touches storage, code paths
or raw records. It reads validated Object states and executes guarded Actions, which is
where its permissions and validation live. An agent that can bypass an Action has escaped
the model, and that is a defect rather than a shortcut.

**Least privilege and an allowlist.** Acquisition runs against an explicit list of
permitted destinations and actions. No terminal execution without confirmation.

**Isolation.** Collectors run sandboxed. The current landscape has converged on three
primitives: microVMs such as Firecracker, giving each sandbox its own kernel on KVM at
roughly 125 ms boot; gVisor, whose user-space kernel intercepts syscalls at 10 to 30 per
cent I/O overhead; and hardened containers. Reported effect of sandboxing agent workloads
is around a 90 per cent reduction in security incidents versus unrestricted host access.
Choose per collector by whether it executes third-party code.

**Secrets never reach the reader.** Credentials belong to the egress component, are issued
from a secret manager, are short-lived, and are excluded from logs and error paths.

**Configuration is audited before it runs.** Any third-party collector configuration is
reviewed, by a person or by a second model acting as an adversary rather than a linter,
before first execution.

**Human-in-the-loop on final decisions.** `RecordDetermination` is executable only by a
human agent, and the plane takes no consequential action on its own output.

## Open-source reuse

Find best-of-breed open source, build the pipeline, get data quality right, and only then
analyse artifacts. ADOPT is the default choice; EVALUATE needs a bake-off against real
sources first.

### Semantic layer

| Need | Candidate | Note |
| --- | --- | --- |
| Provenance vocabulary | **W3C PROV-O** | ADOPT. Entity, Activity, Agent with `wasGeneratedBy`, `wasDerivedFrom`, `wasRevisionOf`, `wasAttributedTo`. A W3C recommendation beats a local vocabulary for anything crossing a boundary |
| Typed object model in code | **Pydantic** | ADOPT. The current direction is lightweight ontology as typed objects and typed actions validated against constraints, rather than heavyweight OWL behind a triplestore |
| PROV-O serialization | **provo** | EVALUATE. Implements the PROV-O classes and properties as Python classes with type-checked compliance |

No triplestore, no graph database. The ontology is typed objects in this repository,
serialized to PROV-O when it crosses a boundary. Eight object types do not need a query
engine.

### Acquisition and provenance

| Need | Candidate | Note |
| --- | --- | --- |
| Immutable capture format | **WARC** (ISO 28500) | ADOPT. Records the full request and response with headers, target URI, capture date and payload digest, which is the `Capture` object almost exactly |
| Index over captures | **CDX** | ADOPT |
| Read and write WARC from Python | **warcio** | ADOPT |
| High-fidelity crawling of dynamic pages | **Browsertrix Crawler** | ADOPT for JavaScript-rendered sources. Headless Chromium in Docker, writes WARC |
| Offline replay of a capture | **pywb** | ADOPT. This is what makes `ResolveProvenance` real: the page is replayed from the archive, not refetched |
| Crawl orchestration in Python | **Crawlee for Python** | EVALUATE. Has WARC support; the alternative is a thin scheduler over warcio |

### Text and document extraction

| Need | Candidate | Note |
| --- | --- | --- |
| Widest format coverage | **Apache Tika** | ADOPT as the fallback path. Used in government compliance monitoring and legal document indexing, which is this domain |
| Layout-aware parsing of scans and dense tables | **Docling** | EVALUATE. Best open-source AI parser, self-hosted, no per-page fee, wants GPU |
| Main-content extraction from HTML | **trafilatura** | EVALUATE against Browsertrix output for news and registry pages |

Boundary note: `loc-lm-bench` owns chunking. Nadra extracts far enough to emit a `Document`
and stops.

### Security controls

| Need | Candidate | Note |
| --- | --- | --- |
| Injection guardrails at the boundary | **LlamaFirewall**, **NeMo Guardrails**, **Guardrails AI** | EVALUATE. The Action partition is the structural defence; a guardrail is a second layer that must earn its latency with a measured catch rate |
| Sandboxing | **gVisor**, **Firecracker**, hardened containers | EVALUATE per collector by whether third-party code executes |
| Secret handling | secret manager plus short-lived tokens; **gitleaks** or **trufflehog** in CI | ADOPT the pattern; pick tools when the egress component exists |

### Ukrainian and domain sources

| Source | Note |
| --- | --- |
| **Unified State Register of Court Decisions, USRCD** (`reyestr.court.gov.ua`) | Over 126 million documents. Decisions appear after anonymisation, typically about three working days. Access terms have been contested, so the Determination matters here more than anywhere else |
| **court.gov.ua/opendata** | Official open data sets from the judiciary |
| **data.gov.ua** | National open data portal, includes the court register among its datasets |
| **Opendatabot** | Commercial API over the court register, company register and debtors register. Requires a sales agreement; evaluate against direct open-data access first |
| Defence and technology media | `militarnyi.com/uk/news`, `mod.gov.ua/news`, `armyinform.com.ua`, `braveinventors.com/invention`, `defence-ua.com`, `epravda.com.ua` |
| Bilingual | `united24media.com`, `mezha.net` |

### Sibling repositories

| Repo | Reuse |
| --- | --- |
| `loc-lm-bench` | Downstream consumer. Ukrainian model selection and tuning: gold sets, multi-annotator kappa adjudication, retrieval evaluation with paired verdicts, fine-tuning, host-fit serving. Nadra never duplicates any of it |
| `selfsuvis` | Reference for stream connectors, background processing, media and OCR pipelines, rolling-window state. Relevant to area two |
| `fl-op` | Reference for schema contracts and immutable decision-input snapshots. Its contract discipline is the closest existing analogue to the Object layer |

## Architecture

```text
   registries        documents        live feeds        media
   court, tax        web, PDF         news, streams     video, audio
        |                |                 |               |
        +----------------+--------+--------+---------------+
                                  |
        +-------------------------+--------------------------+
        |  EGRESS: holds credentials. Executes CaptureSource. |
        |  Never parses untrusted content.                    |
        +-------------------------+--------------------------+
                                  |
                        WARC store + CDX index
                          Capture objects
                                  |
        +-------------------------+--------------------------+
        |  READER: NO NETWORK, sandboxed. Executes            |
        |  DeriveDocument, ReviseDocument, ProjectCorpus.     |
        +-------------------------+--------------------------+
                                  |
                        ONTOLOGY: Objects, Links, Actions
                                  |
        +----------+--------------+--------------+-----------+
        |          |              |              |           |
    corpus     records with    capture       documents    PROV-O
   projection    spans          stream      with attrib.  export
        |          |              |              |           |
   loc-lm-bench  OSINT and    monitoring      content     outside
   model work    legal                         input      this stack
```

The trust boundary is the WARC store. Everything above it holds secrets and touches the
network. Everything below it is offline and sandboxed. The ontology sits below the boundary
and is the only thing consumers see.

## Design Invariants

- **I1. Nadra never trains, tunes, scores or serves a model.** That is `loc-lm-bench`.
- **I2. No component holds both network access and untrusted parsing.** Enforced by which
  component may execute which Action. Violating it collapses the primary defence against T1
  regardless of what guardrails sit alongside it.
- **I3. State changes only through Actions.** No consumer and no agent writes an Object
  directly. An agent that can bypass an Action has escaped the model.
- **I4. Document text is immutable once emitted.** Spans are character offsets into it, so a
  changed upstream produces a new Document linked by `wasRevisionOf`, never a rewrite.
- **I5. Consumers depend on the ontology, never on each other or on nadra's storage.** A new
  consumer is a new projection, not a change to Objects, Links or Actions.
- **I6. Provenance is captured at fetch time or not at all.** Licence, terms, capture time
  and payload digest cannot be reconstructed afterwards.
- **I7. Acquired material is retained and processed locally.** Acquisition is networked by
  nature, so this binds storage and processing, not whether the machine reaches the network.
- **I8. One capability enters the registry at a time**, with a declared falsification
  condition.

## Constraints

- Ukrainian with code-switching. The plane preserves text faithfully and records its
  language on the `Document`. It does not lemmatize, stem or index.
- Licence and terms are acquisition-time facts, recorded as a `Determination` with the date
  of determination. Court-register access terms have been contested, so this is not a
  formality.
- Personal data: court decisions are published after anonymisation, but derived artifacts
  can still re-identify through linkage. Any capability that joins records across sources
  needs its own review before it is specified.
- Lightweight, reuse-heavy stack. No Ray, Celery, Kubernetes, Airflow, MLflow tracking
  server, vector-database servers, or triplestores.
- No code reaches `src/` without a specification section, a capability registry row and a
  declared falsification condition. Runtime output lives under `DATA_DIR`.
- ASCII in source, filenames, identifiers, logs, commits and documentation. Object content
  and metadata values are UTF-8.

## Non-Goals

- Model training, tuning, evaluation, gold sets and serving.
- Retrieval, chunking, lemmatization and entity resolution over acquired content. The
  ontology describes the provenance of acquisition in a closed vocabulary of eight object
  types. It is not an analysis graph over people, companies or events named inside
  documents, and nadra never resolves those.
- Generation, synthesis and publishing, including the credentials they require.
- Agent frameworks and multi-agent orchestration as a dependency. Agentic behaviour inside
  the plane's own fetch path is not covered by this exclusion.
- Redistribution of acquired sources. Captures stay local; only digests, URIs, offsets and
  licence facts leave through a projection.
- Telegram as an acquisition platform, pending a threat-model determination against concrete
  criteria: official API availability, authentication model, auditability, retention terms,
  jurisdiction, and credential isolation.

## Current State

- **nadra**: foundation only. Three shipped capabilities, all infrastructure:
  `reproducible-environment`, `project-identity`, `documentation-integrity`. 609 lines of
  Python, all CLI and quality tooling. No product code and no acquisition capability.
- **loc-lm-bench**: shipped Ukrainian corpus-to-recommendation platform. Consumes local
  corpus directories. A source-wide search finds HTTP clients only for model downloads and
  Ollama endpoints, so it cannot acquire anything.
- **selfsuvis**, **fl-op**: available locally as reference implementations.
- Nothing anywhere in the stack acquires from the network with provenance, and nothing
  publishes a shared model that more than one consumer can read.

## Slice A: One Acquisition Run Through the Ontology

### Scope

Define the ontology, acquire from a named source set into a WARC store, derive Documents
through guarded Actions, and render two projections. Egress and reader are separate
processes from the first commit, because retrofitting I2 later means rewriting both.

Two projections rather than one is deliberate. One projection proves nothing about
decoupling; the second is what makes I5 falsifiable.

### Acceptance

VALID when:

- V1. Every Object validates against its typed schema, and every Link is one of the defined
  relations.
- V2. Every state change goes through an Action. A test that writes an Object directly
  fails.
- V3. The reader process runs with no network capability, shown by a test that fails when
  egress is reachable from it.
- V4. Every `Capture` carries target URI, capture time and payload digest.
- V5. Re-deriving from one `Capture` produces byte-identical text and the same `Document`
  identity.
- V6. No `Document` is projected whose `Determination` forbids that projection's
  distribution class.

GATE passes when:

- G1. The corpus projection is ingested by `loc-lm-bench` with every document reported ok
  and no hand-editing.
- G2. A second projection is rendered from the same Objects, and adding it required no
  change to any Object, Link or Action. This is I5 under test.
- G3. `ResolveProvenance` succeeds ten times out of ten: ten Documents sampled at random
  each resolve offline through `wasDerivedFrom` to the `Capture` behind them, with no
  network access.
- G4. An injection canary planted in a captured document reaches no component holding
  credentials, shown by a test that fails when the property is violated.

FAILED when:

- F1. Derived text is not reproducible from one `Capture`, which breaks I4.
- F2. The corpus projection needs hand-editing, which means the seam is not real.
- F3. The reader can reach the network under any tested configuration, which breaks I2.
- F4. The second projection cannot be added without changing an Object, Link or Action,
  which means the ontology is a rename of one consumer's schema rather than a model of the
  domain. This is the most informative failure available and it is cheap to reach.

### Effort

Roughly 2 to 3 weeks human, plus wall clock for the acquisition window. WARC, warcio and
pywb remove the immutable-store and replay work; PROV-O removes the vocabulary design.

## Required Changes in loc-lm-bench

To be raised in that repository through its own capability lifecycle, and held in
[the handoff plan](../impl/plan-loc-lm-bench.md). They keep the two services distinct:
nadra owns acquisition and provenance, `loc-lm-bench` owns Ukrainian model selection and
tuning.

- **LLB-1. Ontology provenance fields.** The governance field set carries no origin.
  Ingestion time records when that repository ingested rather than when the source was
  captured, and the source hash covers the local file rather than the captured bytes. Carry
  the projection's ontology identifiers through into chunk metadata and the gold-set
  provenance field, so a scored answer resolves to a `Capture`.
- **LLB-2. Corpus version bound to an `AcquisitionRun`**, so a gold set names the corpus
  version its Spans are valid against.
- **LLB-3. Revision semantics.** A changed upstream is a new `Document` linked by
  `wasRevisionOf`, never an in-place update, because Spans are offsets into the previous
  text.
- **LLB-4. Redistribution gate at export**, keyed on the `Determination` the projection
  carries. Access labels cover who may read, not what may be redistributed.

## Open Questions

1. Does `Span` need to be a first-class Object with its own identity, or is it a value type
   inside a Link? First-class costs storage and buys addressable citation. Decide when the
   second projection makes the cost visible.
2. Which sandbox primitive per collector: gVisor for the general case, a microVM where
   third-party code executes, or a hardened container where neither applies?
3. Direct open-data access to the court register, or the commercial API? Access terms have
   been contested, so this needs a determination and not an assumption.
4. Is a `Determination` per Source, or per Document at capture time? Per Source is cheaper,
   but terms change, so either way it carries a date.
5. Which guardrail library, if any, earns its place given that the Action partition already
   provides the structural defence? A guardrail that adds latency without a measured catch
   rate is not worth its dependency.
6. Which repository owns scheduling once acquisition is recurring? Nadra by I1, but
   recurrence is out of scope for Slice A.

## Dependencies

- A web backend that indexes Ukrainian, for discovery beyond the named source set. None is
  configured.
- The named source set with a `Determination` recorded for each.
- Docker, for Browsertrix Crawler.
- `loc-lm-bench` available as a local checkout for the corpus projection test.
- A specification amendment and capability registry rows before any code, per I8.

## Next Steps

1. Define the ontology as typed schemas with PROV-O alignment, before choosing tools, so
   tool choice does not dictate the model.
2. Bake off the acquisition stack against three real sources of different shape: a
   JavaScript-rendered news page, a court-register document, and a static feed.
3. Record a `Determination` for each source in the initial set.
4. Talk to four founders or CTOs at small deep-tech companies. One question: "walk me
   through the last time you decided whether to chase a programme, and what you actually
   read." No architectural decision resolves the demand question.
