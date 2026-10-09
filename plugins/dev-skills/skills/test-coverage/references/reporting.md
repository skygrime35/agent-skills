# Reporting — statuses, verdicts, templates, journal

## 1. Statuses are never collapsed

Coverage has six outcomes and reports keep all six apart — each confusion has a cost:

| Status | Meaning | If confused with `covered`… |
|---|---|---|
| covered | ≥1 living test asserts the scenario's `expected_outcome` | — |
| partial | a test touches the feature but not this outcome | the outcome regresses green |
| missing | no test | the gap disappears from view |
| waived | conscious human decision (`accepted_risks`) | fine — but it must stay visible in audits |
| gated | runnable only via `/full-test` (preprod) | "tested" claimed for something never run here |
| bug-found | a written test proved the outcome wrong | a known bug reads as covered behavior |

Speed levers likewise have five outcomes kept apart — **appliqué / refusé (raison + preuve) / non proposé / non vérifiable / hors périmètre** — a refused lever is never folded into « non proposé » (it is a measured fact, not a choice). Check results likewise: **PASS / FAIL / WAIVED / BLIND SPOT** — a check that could not run is a BLIND SPOT, never a PASS. Waived items are counted in one quiet footer line (« N risques assumés — détail au prochain audit »), never itemized outside audit.

## 2. Verdict wording

Always **green on what ran**. Coverage numbers always carry their denominator *and* its delta: « 148/214 scénarios couverts (inventaire : +9 scénarios depuis le dernier audit) » — a percentage alone hides both the inventory's size and the fact that a growing inventory can make coverage *drop* while the suite improved. The Blind spots section states **what each absence means**, not merely that it exists (« passe dynamique non exécutée : les features visibles uniquement à l'exécution sont absentes de l'inventaire — l'exhaustivité revendiquée ne porte que sur le code »).

## 3. Build report skeleton

```markdown
# Build de couverture — <PROJET> — <YYYY-MM-DD> (SHA <SHORTSHA>)
Audit consommé : <path> (SHA <AUDIT_SHA>) · Gate : <go all | go partiel (groupes listés) | narrowed by --gaps=…>
## Synthèse            <tests écrits / scénarios couverts (dénominateur) / bugs découverts / baseline vs final>
## Tests écrits        <par fichier : scénarios, framework, vert local o/n>
## Bugs découverts     <chaque TC-BUG : repro exacte, observé vs attendu, où est le skip annoté>
## Non-régression      <diff vs baseline B2 ; casses réparées (fixtures) ; échecs pré-existants inchangés>
## Gaps restants       <scénarios encore missing/partial + pourquoi (refusés au gate, costly non confirmés)>
## Gated → /full-test  <scénarios écrits non exécutés ici, avec la variable d'env cible>
## Verdict             « Vert sur ce qui a tourné » + la phrase honnête sur le reste
```

The audit report skeleton lives in `audit-grid.md` §2; the trailer contract in `inventory-schema.md` §4; the speed report skeleton and its `levers:` trailer in `speed.md` §6.

## 4. Journal

`.claude/test-coverage/journal.md`, one line per completed step: `<ISO date> <mode> <phase/wave> <fact>` — facts, not narration (« B4 wave 2 : 6/6 fichiers verts », « audit wave 5 : DOM-03 mappé, 41 scénarios »). Written by the main loop only; `verify` and `--dry-run` never write it (a `speed --dry-run` that measured a baseline records that single fact in the baseline JSON's `notes`, not in the journal). Its purpose is resumability: the resume check (Phase 0.1) must be able to reconstruct exactly which test files are done, which wave was in flight, and which gate answers were already given — a `go all` on 100+ tests that crashes at file 60 resumes at file 61, it does not re-ask the gate.
