# Chapter 4 — Memory and the Map: MCP + Memory Bank

## Quest brief

A Council without memory is a Council that re-introduces itself every session. In this chapter you give the Steward two new powers: **short-term CRM awareness** via the Model Context Protocol (MCP), and **long-term customer memory** via the Agent Memory Bank. By the end, the Steward knows that u-megacorp had a billing dispute in February before it even reads the Megaticket.

**Plain English:** MCP lets your agent call external systems (like a CRM) as tools. Memory Bank is a managed store for facts that should persist across sessions. This chapter adds both.

---

## Files in this chapter

| File | What it does |
|---|---|
| `mcp_server.py` | Fake CRM server exposing 3 tools over MCP stdio |
| `memory_wiring.py` | Memory Bank API wrapper + session ID mapper |
| `run_with_mcp.py` | Updated Steward that calls the CRM before/after processing |

---

## Part 1 — MCP: The CRM connection

### Start the MCP server

In a separate terminal:

```bash
python chapter_04_memory_and_mcp/mcp_server.py
```

You'll see: `ContosoCloud CRM MCP server starting on stdio…`

### Run the Council with CRM access

In your main terminal:

```bash
python chapter_04_memory_and_mcp/run_with_mcp.py
```

### What the Steward gains

Before the Megaticket workflow, the Steward now calls:

```
get_ticket_history("T-megaticket-001")
```

Which returns the prior history (the Feb cancellation context). This flows
into the Loremaster query and the Envoy's tone — the Envoy knows to reference
the February cancellation confirmation proactively.

After the workflow:

```
update_ticket_status("T-megaticket-001", "IN_PROGRESS", "Draft sent to human review — CRITICAL priority")
```

### The three CRM tools

| Tool | Purpose |
|---|---|
| `get_ticket_history` | Full history for a ticket_id |
| `update_ticket_status` | Write a status + note back to the CRM |
| `list_open_tickets` | All OPEN / IN_PROGRESS tickets (used in Chapter 7) |

---

## Part 2 — Memory Bank: Cross-session customer memory

### What it does

Agent Memory Bank stores facts that should survive across completely separate
sessions. For example:
- u-alice prefers email resolution over the portal
- u-megacorp had a billing credit in February 2026

The Steward can recall these before processing a new ticket — even if it's a
brand-new ADK session with no prior context.

### Run the memory demo

```bash
python chapter_04_memory_and_mcp/memory_wiring.py
```

> **Important:** If you're running before the Memory Bank Python SDK ships,
> the script runs in mock mode and prints what *would* be stored. The API surface
> is illustrative — verify the exact method names against the Agent Platform release
> notes before deploying.

### Session ID mapping

The `SessionMapper` class in `memory_wiring.py` solves a practical problem:
ADK uses its own session IDs, but your CRM uses ticket IDs. The mapper keeps them
in sync so you can resume an agent session from a CRM webhook.

---

## How MCP tools differ from regular tools

| Regular `FunctionTool` | MCP `MCPToolset` |
|---|---|
| Python function in the same process | External process / server |
| Schema defined by Python type hints | Schema defined by the MCP server |
| Ideal for stateless transforms | Ideal for external system integration |
| No transport layer | stdio or HTTP transport |

---

## Exercises

1. Add a fourth MCP tool: `search_customer_by_email`. What does the server code look like?
2. Modify the Steward instruction to skip `get_ticket_history` for NEW tickets (where history is empty). Why might you want this?
3. What happens if the MCP server isn't running when `run_with_mcp.py` starts? How would you handle that gracefully?

---

## Checkpoint

- [ ] `mcp_server.py` starts without errors
- [ ] `run_with_mcp.py` loads 3 MCP tools successfully
- [ ] The Steward references previous ticket history in its response
- [ ] `update_ticket_status` is called at the end of the workflow

---

**Next:** [Chapter 5 — Trial by Fire: Evaluation and Testing](../chapter_05_trial_by_fire/README.md)
