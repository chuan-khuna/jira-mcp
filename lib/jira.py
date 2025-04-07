import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
from tqdm import tqdm


class JiraClient:
    def __init__(self, url: str, email: str, token: str):
        self.email = email
        self.token = token
        self.url = url
        self.http_auth = HTTPBasicAuth(self.email, self.token)

        self.filtered_columns = [
            "project.name",
            "key",
            "status.name",
            "issuetype.name",
            "assignee.displayName",
            "priority.name",
            "customfield_10016",
            "created",
            "updated",
            "duedate",
            "timeestimate",
            "aggregatetimeestimate",
            "timeoriginalestimate",
            "aggregatetimeoriginalestimate",
            "timespent",
            "aggregatetimespent",
            "summary",
        ]

        self.task_types: list[str] | None = None
        self.assignees: list[str] | None = None

    def set_query_params(
        self, task_types: list[str] | None = None, assignees: list[str] | None = None
    ):
        """Set jql query parameters.

        `None` means no filters.
        """
        self.task_types = task_types
        self.assignees = assignees

    def _build_jql_query_string(self, days: int) -> str:

        task_types = self.task_types if self.task_types is not None else []
        assignees = self.assignees if self.assignees is not None else []

        task_tuple = ', '.join(task_types)
        task_condition = f'AND issuetype in ({task_tuple})' if task_types else ''

        assignee_tuple = ', '.join(map(lambda x: f'"{x}"', assignees))
        assignee_condition = f'AND assignee in ({assignee_tuple})' if assignees else ''

        jql_string = (
            f'created >= -{days}d {task_condition} {assignee_condition} order by created DESC'
        )
        return jql_string

    def _paginated_query(self, days: int, skip: int, limit: int) -> None | pd.DataFrame:
        headers = {"Accept": "application/json"}
        query = {'jql': self._build_jql_query_string(days), 'startAt': skip, 'maxResults': limit}

        response = requests.request(
            "GET", self.url, headers=headers, params=query, auth=self.http_auth, timeout=5
        )

        data = json.loads(response.text)
        issues = data.get('issues', [])

        if len(issues) == 0:
            print("[paginated query] No issues found")
            return None

        df = pd.DataFrame(issues)
        df = df.join(pd.json_normalize(df['fields']))

        try:
            return df[self.filtered_columns]
        except KeyError as e:
            print(f"[paginated query] Error while filtering columns from Jira response: {e}")
            return None

    def _process_time_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        time_cols = [
            "timeestimate",
            "aggregatetimeestimate",
            "timeoriginalestimate",
            "aggregatetimeoriginalestimate",
            "timespent",
            "aggregatetimespent",
        ]

        for col in time_cols:
            df[col + '.hr'] = df[col] / 3600
            df[col + '.days'] = df[col] / (3600 * 8)

            df[col + '.hr'] = df[col + '.hr'].round(2)
            df[col + '.days'] = df[col + '.days'].round(1)

        return df

    def query_tasks(self, num_pages: int, page_size: int, days: int) -> pd.DataFrame:
        dfs = []
        for page in tqdm(range(num_pages), desc="Fetching pages"):
            skip = page * page_size
            df = self._paginated_query(days, skip=skip, limit=page_size)

            if df is not None:
                dfs.append(df)
            else:
                print(f"No more issues found or an error occurs after page {page}.")
                break

        df = pd.concat(dfs, ignore_index=True)

        df['created'] = pd.to_datetime(df['created'])
        df['updated'] = pd.to_datetime(df['updated'])

        df['created.date'] = df['created'].dt.date
        df['updated.date'] = df['updated'].dt.date

        df = self._process_time_columns(df)

        return df
