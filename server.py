from mcp.server.fastmcp import FastMCP
import pandas as pd
import datetime
import os

from lib.jira import JiraClient


from dotenv import load_dotenv

load_dotenv()


mcp = FastMCP("jira")

SHOW_COLUMNS = [
    'project.name',
    'summary',
    'status.name',
    'assignee.displayName',
    'issuetype.name',
    'timespent.hr',
    'timeestimate.hr',
    'created.date',
    'updated.date',
]


@mcp.tool()
def list_tasks_for_assignee(assignee: str, created_after: str, num_pages: int = 10) -> str:
    today = datetime.date.today()
    created_after_date = datetime.datetime.strptime(created_after, "%Y-%m-%d").date()
    days = (today - created_after_date).days

    client = JiraClient(
        url=os.environ.get("JIRA_URL", ""),
        email=os.environ.get("JIRA_EMAIL", ""),
        token=os.environ.get("JIRA_TOKEN", ""),
    )

    client.set_query_params(task_types=None, assignees=[assignee])

    df = client.query_tasks(num_pages=num_pages, page_size=200, days=days)
    df = df[df['assignee.displayName'] == assignee].reset_index(drop=True)
    df = df[SHOW_COLUMNS]

    return df.to_markdown()


if __name__ == "__main__":
    # mcp.run(transport='stdio')
    mcp.run()

