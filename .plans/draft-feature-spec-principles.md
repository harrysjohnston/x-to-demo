🧭 Core Principles for an SDD-Ready Feature Spec

1️⃣ Intent Before Implementation

Principle: The spec must clearly define why the feature exists before describing how it works.

A good SDD spec:
	•	States the user outcome in plain language.
	•	Defines the business objective.
	•	Clarifies the problem being solved.
	•	Separates intent from technical implementation.

Test: Could someone implement this correctly without knowing your internal architecture?

⸻

2️⃣ Behavioral Clarity Over Narrative Ambiguity

Principle: Define observable behaviors, not vague descriptions.

Instead of:

“The system should intelligently recommend experiences.”

Specify:
	•	Inputs
	•	Outputs
	•	Preconditions
	•	Postconditions
	•	Error states

Use structured formats such as:
	•	Given / When / Then
	•	Explicit acceptance criteria
	•	Input/output tables

Test: Can we objectively verify whether the behavior occurred?

⸻

3️⃣ Specifications as the Source of Truth

Principle: The spec is the authoritative representation of feature intent — not the code.

This means:
	•	Specs are version-controlled.
	•	Code derives from the spec.
	•	Tests derive from the spec.
	•	Documentation derives from the spec.

The spec is not a summary of what was built — it dictates what must be built.

Test: If implementation and spec conflict, which wins? (It should be the spec.)

⸻

4️⃣ Structured, Machine-Interpretable Format

Principle: Specs should be structured enough to drive automation.

Include:
	•	Defined schemas
	•	Interface contracts
	•	Explicit constraints
	•	Typed inputs and outputs
	•	Enumerated states
	•	Measurable criteria

This allows:
	•	AI agents to generate code
	•	Automatic test generation
	•	API scaffolding
	•	Mock environments

Test: Could an AI reliably generate a prototype from this spec without guessing?

⸻

5️⃣ Explicit Constraints & Invariants

Principle: State what must always be true.

Examples:
	•	Pricing rules
	•	Eligibility constraints
	•	Data validation rules
	•	Regulatory requirements
	•	Performance thresholds

These invariants:
	•	Prevent drift
	•	Enable validation tooling
	•	Protect architecture integrity

Test: Are constraints written clearly enough to detect violations automatically?

⸻

6️⃣ Iterative, Living Document

Principle: Specs evolve with discovery — they are not frozen upfront design.

An SDD spec:
	•	Is updated as assumptions change.
	•	Tracks decisions and revisions.
	•	Reflects validated learning.
	•	Supports rapid iteration.

Avoid:
	•	Big Design Up Front rigidity.
	•	Static documentation that becomes stale.

Test: Does your workflow encourage spec updates alongside code changes?

⸻

7️⃣ Shared Cross-Functional Artifact

Principle: The spec must be readable and meaningful to product, design, engineering, and AI systems.

Include:
	•	User personas
	•	UX implications
	•	Business metrics
	•	Technical interfaces

The spec bridges:
Business ↔ UX ↔ Engineering ↔ AI agents

Test: Can a product manager, designer, and engineer all validate this document?

⸻

8️⃣ Testability by Construction

Principle: Acceptance criteria should be directly derivable into tests.

Each major behavior should:
	•	Have clear success conditions
	•	Define edge cases
	•	Include failure states

Specs should eliminate “interpretive” testing.

Test: Could QA generate a test suite purely from this spec?

⸻

9️⃣ Metrics & Measurable Outcomes

Principle: Define how success will be measured.

Include:
	•	Behavioral success indicators
	•	Performance benchmarks
	•	Business KPIs
	•	User impact metrics

Without measurable outcomes, intent cannot be validated.

Test: Is there a measurable definition of “done” beyond “it works”?

⸻

🔟 Separation of Experience, Policy, and Implementation

Principle: Clearly separate:
	•	User experience behavior
	•	Business rules/policy
	•	Technical execution details

This enables:
	•	Independent evolution
	•	AI interpretation
	•	Clean architecture
	•	Reduced coupling

Test: Can policy change without rewriting the entire feature description?

⸻

🧠 What an SDD-Ready Feature Spec Must Contain

At minimum, a strong SDD feature spec should include:
	1.	Feature Intent
	•	Problem statement
	•	Target persona
	•	Desired outcome
	2.	External Behavior
	•	Inputs
	•	Outputs
	•	User interactions
	•	API contracts (if applicable)
	3.	Acceptance Criteria
	•	Given / When / Then scenarios
	•	Edge cases
	•	Failure cases
	4.	Constraints & Invariants
	•	Rules that must always hold
	•	Compliance or business logic
	5.	Success Metrics
	•	Quantitative definitions of success
	6.	Versioning & Change Log
	•	Assumptions
	•	Decisions
	•	Iteration history

⸻

🏗 High-Level Meta-Principle

Spec-Driven Development works when:

The spec is precise enough to execute,
but flexible enough to evolve.

⸻

🧩 In One Sentence

A good SDD feature spec is:

A structured, versioned, behaviorally precise representation of intent that humans and machines can both reliably execute against.
