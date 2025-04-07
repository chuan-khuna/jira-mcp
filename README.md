# Jira MCP Server

- query tasks for assignees

## MCP setting

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["--directory", "/path/to/project/", "run", "server.py"]
    }
  }
}
```

## development

```bash
uv run mcp dev server.py
```

## Usage

example prompt

```txt

Summarise tasks for `<assignee>` from `<date>`, limit pagination to 10 pages.

Summarise it for resume
```
