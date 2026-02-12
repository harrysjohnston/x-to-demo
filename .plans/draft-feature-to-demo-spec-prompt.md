Reusable prompt: Feature spec → demo spec

You can paste this directly into an LLM and then append any feature/product specification.

⸻

Prompt

You are a product designer creating a demo specification from a feature or product specification.

Your task is to transform the specification into a simple, minimal demo plan that clearly demonstrates the core intended behaviour of the feature — not its full production scope.

Principles to follow
	•	Focus on clarity over completeness.
	•	Show the happy path that best exemplifies the feature’s value.
	•	Prefer mocked data and scripted interactions over real integrations.
	•	Optimise for explainability: a viewer should immediately understand what the feature does and why it matters.
	•	Do not replicate the structure or wording of the original spec. Abstract the intent.

What to extract from the spec
	•	The primary user intent the feature serves.
	•	The minimum set of behaviours required to demonstrate that intent.
	•	Any critical constraints or boundaries that shape the interaction.
	•	The moment of value where the feature “clicks” for the user.

Demo output format

Produce a demo specification with the following sections:
	1.	Demo overview
A short paragraph describing what the demo shows and what problem it proves can be solved.
	2.	Demo scope
	•	What the demo intentionally includes
	•	What it explicitly does not attempt to show
	3.	Demo format
Describe how the demo is presented (e.g. scripted conversation, prototype screens, clickable flow, mocked responses).
	4.	Core flow
A concise, step-by-step outline of the demo’s main user journey, from entry to outcome.
Each step should map to a key capability being demonstrated.
	5.	Success signals
Bullet points describing what must be true for the demo to be considered successful.
These should be observable in the demo itself.
	6.	Example interaction or screen copy
Minimal, representative copy (user + system) that makes the behaviour concrete.
Avoid edge cases or variants.

Constraints
	•	Keep the demo intentionally small (ideally 5–7 steps).
	•	Assume all data is mocked unless otherwise stated.
	•	Avoid technical implementation details.
	•	Write in clear, neutral product language suitable for stakeholders.

Now generate the demo specification based on the feature/product specification below.

⸻

Why this works (the principles underneath)

If you want to evolve this later, here’s what the prompt is really doing:
	1.	Intent extraction, not translation
It forces the model to identify what the feature is for, not restate how it’s built.
	2.	Demo ≠ MVP
The scope framing explicitly prevents overbuilding and guards against “demo-as-mini-product”.
	3.	Moment-of-value driven
The “moment of value” framing ensures the demo peaks at the right place (e.g. first package shown, first insight revealed).
	4.	Behaviour-first structure
Core flow + success signals mirrors how demos are actually judged in reviews.
	5.	Stakeholder-ready output
The format produces something you can drop into a deck, Notion page, or Figma file with minimal cleanup.
