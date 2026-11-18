# Specification Quality Checklist: Niebla de guerra e «ir a»

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-15
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- La spec no nombra estructuras, clases ni módulos (constitución, principio VII). Las menciones a partida.log, --replay, --bench y al archivo de partida son parte del contrato del juego definido por el enunciado, no detalles de implementación.
- Los 6 escenarios obligatorios del Apéndice B están en US3 (1, 2, 3), US4 (1) y US5 (1, 2). SC-001 cuenta 32 escenarios (6 + 3 + 12 + 4 + 5 + 2), con el escenario 11 de US3 (vecinas 9 y 10, ids comparados como números).
- Clarify del 2026-11-15 (5 preguntas): puertas de vecinas exploradas con la antorcha "no observada"; el veneno detiene el viaje; un enemigo errante que llega solo lo detiene si causa daño; archivo de formato anterior incompatible, sin migración (FR-013); destino de «ir a» elegido en el panel del mapa conocido con flechas y Enter (FR-035). Todos los ítems siguen cumpliéndose (16/16).
- Corrección del 2026-11-15 (fase specify): ids de sala comparados como números (FR-020), referencias §3.3, §3.4, §5.3, §6.1, §6.3 y §7.3, y pergamino durante un viaje en curso sin interrumpirlo antes (FR-024, FR-029); la interrupción manual (FR-028) queda como opción adicional. Todos los ítems siguen cumpliéndose.
- Enmienda del 2026-11-15 (implementación): FR-036 (pausa de presentación de alrededor de 0,15 s entre pasos de «ir a» en la ventana, sin efecto en el tiempo del juego ni fuera de la ventana) y escenario 12 de US3. Todos los ítems siguen cumpliéndose.
- Enmienda del 2026-11-16 (prueba en la ventana): FR-037 (con el mapa abierto, R, A, U, Q y S cierran el mapa antes de abrir su selección; ESC no lo reabre) y escenario 6 de US1. Todos los ítems siguen cumpliéndose.
- Enmienda del 2026-11-17 (prueba en la ventana): la pausa de FR-036 y del escenario 12 de US3 pasa de alrededor de 0,15 s a alrededor de 0,5 s, porque con 0,15 s no alcanzaba el tiempo para apretar I o P a mitad de un viaje. Todos los ítems siguen cumpliéndose.
