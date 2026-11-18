# Specification Quality Checklist: Línea de tiempo

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-17
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

- La spec no nombra estructuras, clases ni módulos (constitución, principio VII). Las menciones a partida.log, --replay, --hasta, --checkpoint-cada, --bench, el archivo de partida y la tecla H son parte del contrato del juego definido por el enunciado, no detalles de implementación. "Punto de control" y "cambio registrado" son conceptos del enunciado (§3.6), no estructuras.
- Los 6 escenarios obligatorios del Apéndice B están en US1 (1, 2 y 3), US2 (1), US3 (1) y US4 (2). SC-001 cuenta 28 escenarios (8 + 5 + 5 + 3 + 4 + 3).
- Depende de la feature 002 (conocimiento del jugador reversible y formato 3) y de las reglas de la primera parte para el reloj, la agenda, el pergamino y el guardado.
- Supuestos candidatos a confirmar con `/speckit-clarify`: que `--replay … --hasta t` muestre la historia tal como quedó con los pergaminos aplicados (FR-014); que H detenga un viaje «ir a» en curso antes de abrir la consulta, como excepción a la regla de la feature 002 (FR-017); y desde qué instante figura en la línea de tiempo un pergamino recogido dentro de un tramo revertido (regla D50 de la primera parte).
- Corrección del 2026-11-17 (fase specify): la referencia de SC-002 y de las pruebas independientes de US1 y US3 es reproducir solo las acciones que siguen existiendo, no la partida tal como se jugó; FR-017 explica la excepción de H a la regla de la feature 002. Todos los ítems siguen cumpliéndose.
- Clarify del 2026-11-17 (3 preguntas): --replay … --hasta muestra la historia tal como quedó con los pergaminos aplicados (FR-014); H detiene un viaje «ir a» como excepción a la regla de la feature 002 (FR-017); un pergamino recogido dentro de un tramo revertido figura desde el reloj actual (FR-008, escenario 5 de US2). Todos los ítems siguen cumpliéndose (16/16).
- Corrección del 2026-11-17 (hallazgo del plan, research R6): la referencia de SC-002 y de las pruebas independientes de US1 y US3 pasa a ser el estado que la partida real tuvo en ese instante de la historia que quedó (resúmenes capturados en vivo en cada decisión, quitando los de las acciones revertidas). Reproducir solo las acciones que quedaron no reproduce el pergamino gastado (FR-008) ni la regla D50. Todos los ítems siguen cumpliéndose (16/16).
