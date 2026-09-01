# Nadra Specification

## Purpose

Nadra is a secure, AI-driven automation architecture that integrates specialized agents for data
processing, real-time monitoring, and content creation while implementing rigorous,
security-by-design protocols to mitigate cyber threats.

This specification is living. Nadra's complete domain design will be supplied later. Until then,
the repository specifies only its development foundation and project identity; intended domain
areas are not treated as available capabilities or implementation-ready requirements.

A product need discovered during implementation expands this document through
[Extending This Specification](#extending-this-specification). Behavior that has no specification,
boundary, or evaluation remains outside the product until those are declared.

## Design principles

The trust chain is:

```text
domain problem -> bounded capability -> evaluation -> forward task
               -> code and tests -> current-state documentation
```

The product specification answers what and why. The plan answers what remains. Current-state pages
answer what exists. CI checks the joins so completion is a state transition, not a status note.

Security-sensitive behavior must be specified with explicit trust boundaries, failure handling,
and acceptance signals before implementation. The high-level security-by-design direction does not
substitute for those capability-level contracts.

## Scope

The current Nadra foundation includes:

- a Python 3.12+ `src` layout with an importable `nadra` package and CLI;
- locked `uv` dependency management and Make entrypoints;
- deterministic tests, formatting, linting, typing, coverage, complexity, shell, and docs checks;
- GitHub Actions using the same CI entrypoint as local development;
- shared instructions for Codex, Claude, Gemini, and Cursor;
- a living capability registry and forward-plan/current-state lifecycle.

Nadra's stated direction includes specialized agents for data processing, real-time monitoring, and
content creation within a security-by-design architecture. The first two product capabilities are
specified below: an [acquisition ontology](#acquisition-ontology) that gives every consumer one
shared model to interface with, and [evidence acquisition](#evidence-acquisition), which covers
capture, provenance, and the trust boundary at which external text enters the system.

The rest of that direction remains unspecified. Orchestration, models, interfaces, persistence,
deployment, and operational acceptance for the analysis, monitoring, and content areas are not
chosen here, and must enter through their own specified capabilities before product code or plan
tasks are added.

## Architecture

The architecture currently implemented is the project foundation:

```text
Make and GitHub Actions
        |
        +-> package and CLI under src/nadra/
        +-> mirrored tests under tests/
        +-> quality checks under src/nadra/quality/
        `-> design -> plan -> current documentation lifecycle
```

Production behavior belongs below `src/nadra/`. CLI parsing stays at the boundary and domain logic
moves to focused modules. Runtime artifacts resolve from `DATA_DIR` and never enter source packages.
The eventual domain architecture remains intentionally unspecified until the full design is
provided.

## Reproducible environment

The environment is created from `pyproject.toml` and committed `uv.lock`. Local development and
GitHub Actions both call Make targets and use the same locked development extra. Tool caches follow
`DATA_DIR`; the shared environment helper chooses `UV_LINK_MODE=copy` only when uv's cache and the
checkout live on different filesystems.

Boundary: the repository controls Python dependencies and checks. It does not install system
packages, provision external services, or guarantee reproducibility for undeclared tools.

Evaluation: a fresh checkout reaches `make bootstrap` and `make ci` without manual repair. A
negative result names the missing command, stale lock, unsupported interpreter, or failing gate
rather than silently changing the environment contract.

## Project identity

The `nadra` package exposes typed distribution, import-package, and version metadata. The
`nadra info` command provides a minimal installed-path smoke test and a stable seam for Nadra's
future product interfaces.

Boundary: the command reports identity only. It does not define configuration, service health,
deployment readiness, security posture, or product-domain behavior.

Evaluation: package import and CLI tests verify the `nadra` identity, while the build target
produces both source and wheel distributions. A negative result retains the minimal identity seam
and records why a proposed product interface is not ready.

## Documentation and planning integrity

`AGENTS.md` is the canonical contributor policy; tool-specific files are adapters. The product
specification, forward plan, and current-state tree have distinct ownership. Repository checks
validate relative links and anchors, capability registration, task metadata, lane-appropriate
statuses, group ordering, and forward-only plan language.

Boundary: these checks establish structural agreement. They do not decide which capability is
valuable, whether an evaluation threshold is ambitious enough, or whether a human judgment is
correct.

Evaluation: synthetic tests reproduce broken links, unknown capabilities, missing task fields,
wrong task lanes, and invalid ordering; the repository tree passes the same checks. A negative
result blocks the change and points to the documents that disagree.

## Acquisition ontology

Consumers of acquired evidence interface with a defined object model of the acquisition domain
rather than with Nadra's storage, its code, or one another's schemas. Without it, each consumer
needs a bespoke export and every change to one of them is a change to Nadra.

The model has three parts. **Objects** are the domain's nouns: source, determination, acquisition
run, capture, derivation, document, span, and operator. **Links** are the defined relationships
between them, which make the model traversable rather than a bag of records. **Actions** are the
only way state changes; each declares its typed parameters, the submission criteria evaluated
against object state before it may run, the exact objects and links it edits, and the single
component permitted to execute it.

The upper vocabulary is the W3C provenance ontology, whose entity, activity, and agent classes and
derivation, generation, revision, and attribution properties already describe what acquisition
produces. Adopting a published vocabulary rather than inventing one keeps the model interpretable
outside this repository.

Two properties follow from the object model and are load-bearing elsewhere. Objects are append-only:
a changed upstream produces a new document linked as a revision rather than a rewrite, because
downstream labels are character offsets into document text and a rewrite would silently invalidate
them. And no action grants both network access and the parsing of untrusted content, which is where
the security boundary is enforced rather than described.

A consumer is served by a projection, which renders objects into the shape that consumer already
reads. Adding a consumer adds a projection.

**Boundary.** The ontology describes the provenance of acquisition in a closed vocabulary. It is not
an analysis graph over people, companies, or events named inside acquired documents, and Nadra
resolves no such entities. It is not a query engine, a triplestore, or a graph database. It does not
model anything downstream of the handoff.

**Evaluation.** The capability is known to work when all of the following hold:

- every object validates against its typed schema and every link is one of the defined relations;
- every state change passes through an action, shown by a check that fails when an object is written
  directly;
- two distinct projections are rendered from the same objects, and adding the second required no
  change to any object, link, or action;
- the model serializes to the published provenance vocabulary and reads back with its links intact.

**Valid negative result.** The second projection cannot be added without changing an object, a link,
or an action. That outcome means the model is a rename of one consumer's schema rather than a model
of the domain, and it returns the capability to specification. It is the cheapest informative failure
available and is reached early by design.

## Evidence acquisition

Nadra acquires external sources into an immutable capture store and derives documents published
through the [acquisition ontology](#acquisition-ontology). Acquisition is the point at which text an
attacker may control enters the system, so this capability owns the trust boundary as well as the
transfer.

The capability has three parts:

- **Capture.** An egress component holds credentials, fetches, and writes WARC records carrying
  target URI, capture date, and payload digest, together with an index over them. It does not parse
  captured content.
- **Derivation.** A reader component with no network capability reads the capture store and emits
  normalized document text plus a per-document metadata sidecar. Normalized text is immutable once
  emitted; a changed upstream yields a new document identity rather than a rewrite, because
  downstream labels are character offsets into that text.
- **Handoff.** The derived corpus directory is consumed by a downstream corpus consumer without
  hand-editing.

The split between capture and derivation is a security requirement, not an implementation
preference. The component that reads untrusted text has no network access, and the component with
network access never parses untrusted text. This is the structural defence against instructions
hidden inside an acquired document, and no guardrail substitutes for it.

**Boundary.** This capability does not train, tune, score, or serve models. It does not chunk,
retrieve, lemmatize, resolve entities, or build graphs. It does not generate, synthesize, or
publish, and it holds none of the credentials those need. It does not redistribute captured
sources. It does not schedule recurring acquisition; recurrence is a later capability.

**Evaluation.** The capability is known to work when all of the following hold:

- downstream corpus ingest completes with every document reported ok and no hand-editing;
- a provenance round trip succeeds ten times out of ten: ten documents sampled from the ingested
  corpus each resolve, offline and without network access, from the corpus document back through
  the capture store to the capture that produced it;
- an injection canary planted in a captured document reaches no component holding credentials,
  shown by a test that fails when the property is violated;
- re-deriving from one capture yields byte-identical text and the same document identity.

**Valid negative result.** Either the reader cannot be isolated from the network on the target
platform at acceptable operational cost, or derived text cannot be made reproducible from a
capture. Either outcome returns the capability to specification rather than being worked around,
and is recorded as a negative result rather than a failure.

## Capability Registry

Every product capability appears here exactly once. Status is `planned` when the capability is
specified and has open plan work, or `shipped` when current-state documentation describes its
available implementation. A shipped capability may still have optional extension work.

Row order is the implementation line. Hard dependencies come first, then work that changes another
capability's evaluation inputs, then required work before capabilities with only optional work, then
upstream before downstream.

| # | Capability | Status | How it is evaluated | Implementation |
| --- | --- | --- | --- | --- |
| 1 | `reproducible-environment` | shipped | A fresh locked environment reaches the complete CI gate without manual repair | [Developer tooling](../impl/current/developer-tooling.md) |
| 2 | `project-identity` | shipped | Import, CLI, and distribution-build tests agree on the Nadra identity | [Product core](../impl/current/product-core.md) |
| 3 | `documentation-integrity` | shipped | Link, registry-plan, task-lane, metadata, ordering, and forward-language checks pass over fixtures and the repository tree | [Governance](../impl/current/governance.md) |
| 4 | `acquisition-ontology` | planned | Every object validates against its typed schema and every link is a defined relation; a direct object write fails; two projections render from the same objects and the second required no change to any object, link, or action; the model round-trips through the published provenance vocabulary | [Forward plan](../impl/plan.md) |
| 5 | `evidence-acquisition` | planned | Downstream corpus ingest completes with no hand-editing; a ten-of-ten offline provenance round trip from document to capture; a planted injection canary reaches no credential-holding component; re-derivation from one capture is byte-identical | [Forward plan](../impl/plan.md) |

## Extending This Specification

A capability gap is a product discovery, not an automatic refusal and not permission for silent
scope growth. Use this lifecycle in order:

1. State the problem in operator or domain terms.
2. Amend the owning section of this specification, including what the capability does not do.
3. Declare the measurement, acceptance signal, and valid negative result before implementation.
4. Add a `planned` registry row with that evaluation.
5. Put tasks under the capability in the implementation line; every task declares `Serves`.
6. Build and evaluate, document available behavior under current state, remove finished plan scope,
   and change the registry row to `shipped` with its implementation link.

When implementation reveals that an existing capability has the wrong boundary, update its section
instead of creating an implementation workaround that the specification cannot explain.

## Specification and plan integrity

The registry and [implementation plan](../impl/plan.md) are two views of one product. The executable
contract requires:

- every task serves a registered capability and sits in its capability group;
- every capability declares an evaluation;
- every planned capability has at least one open task;
- every shipped capability links to current-state documentation;
- groups follow registry order in each task lane;
- every task declares the required outcome, boundary, execution, and acceptance fields;
- lane statuses match whether an agent can finish independently or a human action gates acceptance;
- required tasks precede optional refinements within a capability.

The check is structural by design. Product priority changes are made by editing the registry order,
not by adding heuristics to the checker.

## Success criteria

The current foundation succeeds when contributors can create the locked environment, import and run
the Nadra package, execute the complete quality gate, and use supported coding agents without
duplicating project policy. A maintainer can determine what Nadra currently promises, what work
remains, which task is next in each lane, what behavior exists, and how every registered capability
is evaluated from repository files alone.

Future product success criteria will be added with the full design and its capability-level
evaluations; this foundation does not infer them from the project description.
