# Model reference

The facts the `agents` and `doctrine` scopes rely on when choosing models and efforts. **Dated, not timeless**: Phase 0 refreshes them (probe D11) before anything is written. A stale table is a blind spot, never a silent default.

Verified: **2026-10-07**, against the official pages listed at the end.

## Lineup

| Alias | Current model | Input / output per MTok | Cache read | 5m cache write | Default effort | Efforts accepted |
|---|---|---|---|---|---|---|
| `fable` | Claude Fable 5.1 | $10 / $50 | $0.25 | $12.50 | high | low to max |
| `opus` | Claude Opus 5.5 | $4 / $20 | $0.20 | $5 | medium | low to max |
| `sonnet` | Claude Sonnet 5.5 | $2 / $10 | $0.20 (the pricing text also states $0.10; the table value is used) | $2.50 | high | low to max |
| `haiku` | Claude Haiku 5.5 | $0.10 / $0.50 up to 100k prompt tokens, $0.50 / $2.50 above | $0.01, $0.05 above 100k | $0.125, $0.625 above 100k | medium | low to max |

All four: 1M context, 128k output, adaptive thinking.

## Tiers used by this skill

- **`{LOW}`** = `haiku`. Bottom tier, inside the matrix since Haiku 5.5 accepts the effort parameter.
- **`{MID}`** = `sonnet`. The workhorse.
- **`{TOP}`** = `opus`. Real reasoning.
- **Above the matrix**: `fable`. Listed in the ladder when available, never given an agent type: at 2.5x the top tier's price, it is chosen per invocation and justified, not made routine.

Q1.1 prunes these to what is actually available. A missing tier is dropped, never faked.

## Measured facts that shape the doctrine

1. **Agent loops are context-bound, not output-bound.** On the reference machine, over 30 days, more than 95% of subagent spend was cache reads and cache writes. Cost per run is roughly calls per run x context per call x cache price. The two real levers are therefore the model's cache price and the number of turns, which effort drives.
2. **High effort on a cheaper model is not cheap.** Measured cost per run on the reference machine: mid tier at high effort $7.4, top tier at medium effort $10.0, top tier at xhigh $31.8. Mid at high saved 25% over top at medium while reasoning less. This is why the matrix has no `{MID}-deep` and why `{TOP}-deep` runs at high, not xhigh.
3. **The bottom tier is the large saving.** Haiku 5.5 reads cache 20x cheaper than Opus 5.5 and Sonnet 5.5 under 100k prompt tokens, 4x above.
4. **Haiku 5.5 trails Sonnet 5.5 on open-ended coding** (FrontierCode 46.4% vs 52.1%). Anthropic positions it as a subagent for coding work, not as a designer. Bottom-tier types therefore take briefed implementation by default, and open design goes one rung up.
5. **Per-model effort guidance** (official): Haiku 5.5, start at medium, use low for short simple tasks (at low it skips searches and checks more often in long agent prompts), high for longer agent tasks. Sonnet 5.5, medium for well-specified agentic coding, high for harder or longer ones. Opus 5.5, medium is the default and the usual starting point. xhigh and max only where measured gains justify them.

## Practice the doctrine follows

Consensus across Anthropic's engineering write-up, the Claude Code documentation, and published orchestration setups:

- A capable orchestrator directs cheaper workers. Anthropic's research system (Opus lead, Sonnet subagents) beat a single Opus agent by 90.2%.
- **Route first, escalate second.** Cascades cut cost 85-98% at equal quality, but only when most tasks resolve at the tier first chosen, and only when the escalation gate is an **objective check**. A model's self-reported confidence fails exactly on the cases that need escalation.
- Verifying is cheaper than producing: a bottom-tier reviewer can check a mid-tier result.
- **Brief quality is the first lever.** Vague delegation causes misreads and duplicated work, more so on small models.
- Scale the number of agents to the task. Over-spawning was an observed failure mode, and coding parallelizes less than research.
- Override the built-ins that silently inherit the session model: a user agent named `Explore` with `model: haiku` replaces the built-in; `CLAUDE_CODE_SUBAGENT_MODEL` sets the model of `general-purpose` and of any custom agent without a `model` field.

## Claude Code facts

- Frontmatter `model` accepts `haiku`, `sonnet`, `opus`, `fable`, a full model ID, or `inherit`.
- **Aliases lag new releases.** Observed 2026-10-07 on Claude Code 2.1.289: `haiku` still resolved to Claude Haiku 4.5 on Haiku 5.5's release day (10x the price, no effort support). The full ID `claude-haiku-5-5` resolved correctly, with an `unrecognized_model` warning from the harness, meaning its local model table did not know the model yet. Phase 4's resolution dispatch is what catches this. When an alias resolves to an older model, write the full ID, record it in `quirks`, and switch back to the alias once a harness update makes the alias resolve correctly.
- `effort` accepts `low`, `medium`, `high`, `xhigh`, `max`; the levels available depend on the model.
- `maxTurns` caps agentic turns. On reaching it, the output comes back marked partial and the agent can be resumed (Claude Code v2.1.246 or later).
- Subagent model resolution order: per-invocation `model` parameter, then frontmatter `model`, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's model. `Plan` inherits the main model unless `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`.
- `color` accepts `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`.
- The `name` field does not have to match the filename; this skill still requires it as a convention (O6.1).

## Sources

- https://platform.claude.com/docs/en/about-claude/models/overview
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/build-with-claude/effort
- https://platform.claude.com/docs/en/models/haiku-5-5/overview
- https://www.anthropic.com/claude-haiku-5-5
- https://code.claude.com/docs/en/sub-agents
- https://www.anthropic.com/engineering/multi-agent-research-system
