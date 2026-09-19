---
name: implementation-detail
description: Summarize the engineering and operational decisions that make an implemented software product buildable, deployable, and operable. Use after design and implementation phases; keep the output brief and evidence-driven.
compatibility: opencode
---

# Implementation Detail Reverse-Engineering Skill

## Objective

Document the practical concerns that sit between a completed software design/implementation and a usable delivered application.

This is a supplementary engineering artifact, not a separate SDLC lifecycle phase and not a replacement for High-Level Design, Low-Level Design, Technology Architecture, or Testing Harness.

The central question is:

> Once the product has been implemented, what additional engineering decisions, configuration, and delivery mechanics are required to build, deploy, operate, and evolve it?

This phase is intentionally brief. Many repositories will have few or no material implementation concerns. That is a valid result.

## Scope

Inspect only material concerns that affect turning the implemented product into a running, deliverable system:

- build/package requirements;
- runtime and environment configuration;
- deployment approach;
- CI/CD or release automation, when evidenced;
- database/schema migration mechanics, when applicable;
- environment promotion or release considerations;
- startup/hosting/runtime configuration that is not already adequately covered by architecture/design;
- operational prerequisites, health/observability hooks, or rollback considerations when materially relevant;
- implementation constraints or technical debt that materially affect delivery.

Do not repeat:

- business purpose or requirements;
- technology-stack description already covered by Technology Architecture;
- logical/component design from High-Level Design;
- classes, functions, algorithms, or detailed code structure from Low-Level Design;
- detailed behavioral test analysis from Testing Harness.

Do not invent operational mechanisms that are not evidenced.

## Investigation Strategy

Start from deterministic repository intelligence and the available phase research.

Select only the few concerns that materially affect delivery. Prefer targeted inspection of:

1. build/package configuration;
2. deployment/runtime configuration;
3. CI/CD or release automation;
4. database migration or environment initialization mechanisms;
5. operational prerequisites or release constraints.

Do not perform an exhaustive repository audit.

Where a concern is not applicable or not established, record it briefly as `N/A` or `Not established by the repository`.

## Evidence Rules

Support material claims with repository evidence.

Prefer:

1. executable configuration and scripts;
2. deployment/runtime manifests;
3. package/build configuration;
4. CI/CD workflows;
5. tests or commands that demonstrate the mechanism;
6. repository documentation confirmed by implementation.

Distinguish what is implemented from what is merely documented or intended.

Never expose credentials or secret values.

## Required Questions

Answer only the questions relevant to the repository:

- How is the implemented product built or packaged?
- What configuration/environment setup is required to run it?
- How is it deployed or released?
- Is CI/CD present, absent, partial, or externally implied?
- Are database/schema migrations part of delivery?
- Are there environment-specific deployment concerns?
- What operational prerequisites or limitations materially affect delivery?
- What important implementation/delivery concerns remain unresolved?

## Output Style

Keep the final document concise. Prefer a short table or compact sections over exhaustive prose.

A useful target is a brief engineering note, not a detailed implementation manual.

Do not force every heading to contain detail. Omit sections that are genuinely not applicable, but state material `N/A` or `Not established` items when they clarify the delivery picture.

Do not recommend redesign merely because a conventional mechanism is absent.

## Verification Gate

Before finishing:

- material claims are supported by current repository evidence;
- implementation concerns are separated from design/code details already covered elsewhere;
- absent mechanisms are not invented;
- the document is concise and focused on build, deployment, configuration, migration, and operational delivery concerns;
- secrets are not exposed.
