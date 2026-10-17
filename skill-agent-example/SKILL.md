---
name: example
title: Example
routing_description: >
  TODO: what this agent answers, the phrases a user would use ('...', '...'), what to
  pass in, what comes back, and which other agent to use instead for neighbouring questions.
requires: [warehouse]
capabilities:
  - database_tools: { provider: warehouse, row_limit: 50, show_rows: 20 }
  - ask_user
examples:
  - TODO: a prompt as the user would type it
  - TODO: another
settings:
  provider: { type: string, title: Database provider, default: warehouse }
max_iters: 6
---
TODO: the persona. What the agent answers, the domain facts it should know (tables,
definitions), what the user already sees (so the result is a short summary with the key
numbers and the dataset id), and what to do when something is missing. Never invent data.
