# temperans

Trajectory intelligence for human–agent–tool interactions.

`temperans` maintains persistent trajectories across conversations, agents, and
tools, and computes structural signals over them — duplicated tool calls, tool
thrash, failure and recovery runs, and agent handoffs.

> **Alpha.** The public API covers event ingestion and trajectory assembly.
> Behavioral perception (classifying turns as repair, resistance, and similar) is
> under active research and is **not** part of the public API. See
> [ENGINEERING.md](ENGINEERING.md) for current defects and roadmap.

## Install

```bash
pip install temperans
```

## Quickstart

```python
from temperans import TrajectoryStore

store = TrajectoryStore("temperans.db")
trace = store.trace(user_id="u_1", trajectory_id="t_1")

trace.human("the refund still hasn't arrived")
trace.agent("let me check that", actor_id="support-agent")
trace.tool("lookup_refund", status="failed")
trace.tool("lookup_refund", status="failed")

print(trace.state().to_dict())
# {'event_count': 4, 'tool_failures': 2, 'duplicate_tool_calls': 1, ...}
```

## What it computes

All signals below are deterministic counts over the event sequence. No model, no
labels, no inference.

| Signal | Meaning |
|---|---|
| `duplicate_tool_calls` | Same tool invoked with the same arguments again |
| `cross_agent_duplicate_actions` | Duplicate work across different agents |
| `tool_switches` | Consecutive calls to different tools |
| `tool_failures` | Failed tool events |
| `consecutive_tool_failures` | Failure run length since the last success |
| `recovery_count` | Recoveries from an unresolved state |
| `agent_handoffs` | Changes of acting agent |

## Status

| call | State |
|---|---|
| Event model, trajectory assembly, SQLite store | Working, alpha |
| Structural signals | Working, deterministic |
| Thread resolution | Alpha; see ENGINEERING.md §2.5 |
| Behavioral perception | Research; not exported |

## License

Apache-2.0
