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


TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)


def format_result(df) -> str | list[str] | list[dict]:
    # return df.to_markdown()
    # return df.to_json(orient="records")
    return df['summary'].to_list()


@mcp.tool()
def list_tasks_for_assignee(
    assignee: str, created_after: str, num_pages: int = 10
) -> str | list[str] | list[dict]:
    today = datetime.date.today()
    created_after_date = datetime.datetime.strptime(created_after, "%Y-%m-%d").date()
    days = (today - created_after_date).days

    file_path = os.path.join(
        TMP_DIR, f"{today.strftime("%Y%m%d")}_jira_tasks_{assignee}_created_{created_after}.csv"
    )

    # load data from temporary file if it exists
    # TODO: fix mcp tool bug in claude, but not cursor?
    if os.path.exists(file_path):
        print(f"File already exists: {file_path}")
        df = pd.read_csv(file_path)
    else:
        client = JiraClient(
            url=os.environ.get("JIRA_URL", ""),
            email=os.environ.get("JIRA_EMAIL", ""),
            token=os.environ.get("JIRA_TOKEN", ""),
        )

        client.set_query_params(task_types=None, assignees=[assignee])
        df = client.query_tasks(num_pages=num_pages, page_size=200, days=days)
        df.to_csv(file_path, index=False)
        print(f"Saved to {file_path}")

    # df = df[df['assignee.displayName'] == assignee].reset_index(drop=True)
    df = df[SHOW_COLUMNS]
    return format_result(df)


if __name__ == "__main__":
    # mcp.run(transport='stdio')
    mcp.run()
