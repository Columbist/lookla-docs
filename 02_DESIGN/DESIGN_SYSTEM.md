---
title: Design System
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 02_DESIGN/COMPONENT_LIBRARY.md
  - 02_DESIGN/BRAND_GUIDELINES.md
  - 06_ENGINEERING/AUDIT.md
implementation_status: N/A — awaiting approval
---

# Design System
**Lookla Beauty Marketplace**

> **DRAFT — awaiting approved product decisions.**  
> The Design System is the single source of truth for visual and interaction design.  
> No UI redesign or new component implementation begins before this document is Approved.

---

## Purpose

The Design System defines the visual language, spacing, typography, color, and interaction patterns used across all Lookla surfaces (web, iOS, Android, partner app).

It is the contract between design and engineering. Every UI component must trace back to a token or pattern defined here.

---

## Current State (from Engineering Audit)

The current implementation uses Tailwind CSS utility classes exclusively.  
No formal design system or component library exists.  
The de facto visual language is:

- **Primary color:** pink-600 (#db2777)
- **Background:** gray-50, white
- **Text:** gray-900 (headings), gray-500 (secondary), gray-400 (meta)
- **Success:** green-500
- **Danger:** red-500
- **Border radius:** rounded-xl (cards), rounded-lg (inputs, buttons)
- **Card border:** border-gray-100
- **Typography:** system fonts, sizes via Tailwind scale

This is an observed implementation state, not an approved design specification.

---

## Sections (awaiting approval)

### 1. Design Tokens

_[Colors, spacing, typography, shadows, border radius — awaiting approval]_

### 2. Typography Scale

_[Awaiting approval]_

### 3. Color System

_[Awaiting approval]_

### 4. Spacing System

_[Awaiting approval]_

### 5. Grid and Layout

_[Awaiting approval]_

### 6. Breakpoints

_[Awaiting approval]_

### 7. Motion and Animation

_[Awaiting approval]_

### 8. Iconography

_[Awaiting approval]_

---

*Last updated: 2026-07-09*
