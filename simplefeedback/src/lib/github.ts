export async function createGitHubIssue(params: {
  token: string;
  repo: string;
  title: string;
  body: string;
  labels?: string[];
}): Promise<string> {
  const { token, repo, title, body, labels } = params;

  const response = await fetch(
    `https://api.github.com/repos/${repo}/issues`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "application/vnd.github+json",
      },
      body: JSON.stringify({ title, body, labels }),
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`GitHub API error: ${error}`);
  }

  const data = await response.json();
  return data.html_url;
}
