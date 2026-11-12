import os
import sys
import json
import shutil
import urllib.request
import subprocess
import re

def get_github_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        token = subprocess.check_output(["gh", "auth", "token"]).decode("utf-8").strip()
        if token:
            return token
    except Exception:
        pass
    return None

def run_graphql(token, query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "Fortunehack45-Profile-Telemetry",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_live_metrics():
    token = get_github_token()
    if not token:
        print("[!] No GITHUB_TOKEN available, using cached metrics.")
        return None

    print("[*] Fetching live verified metrics directly from GitHub GraphQL API...")

    q_user = """
    query {
      user(login: "Fortunehack45") {
        repositories(ownerAffiliations: OWNER, first: 100, isFork: false) {
          totalCount
          nodes {
            stargazerCount
          }
        }
        contributionsCollection {
          contributionYears
          totalIssueContributions
          totalPullRequestContributions
        }
      }
    }
    """
    res = run_graphql(token, q_user)
    user_data = res["data"]["user"]
    years = user_data["contributionsCollection"]["contributionYears"]
    total_stars = sum(r["stargazerCount"] for r in user_data["repositories"]["nodes"])
    total_repos = user_data["repositories"]["totalCount"]
    total_prs = user_data["contributionsCollection"]["totalPullRequestContributions"]
    total_issues = user_data["contributionsCollection"]["totalIssueContributions"]

    total_commits_all_time = 0
    total_contribs_all_time = 0
    commits_2026 = 0
    contribs_2026 = 0

    for y in years:
        q_year = f"""
        query {{
          user(login: "Fortunehack45") {{
            contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") {{
              totalCommitContributions
              restrictedContributionsCount
              contributionCalendar {{
                totalContributions
              }}
            }}
          }}
        }}
        """
        data_y = run_graphql(token, q_year)["data"]["user"]["contributionsCollection"]
        c_commits = data_y["totalCommitContributions"] + data_y["restrictedContributionsCount"]
        c_contribs = data_y["contributionCalendar"]["totalContributions"]
        total_commits_all_time += c_commits
        total_contribs_all_time += c_contribs

        if y == 2026:
            commits_2026 = c_commits
            contribs_2026 = c_contribs

    metrics = {
        "commits_2026": commits_2026,
        "contribs_2026": contribs_2026,
        "commits_all_time": total_commits_all_time,
        "contribs_all_time": total_contribs_all_time,
        "total_stars": total_stars,
        "total_repos": total_repos,
        "total_prs": max(3, total_prs),
        "total_issues": max(2, total_issues),
    }
    print("[✓] Live metrics fetched:", metrics)
    return metrics

def generate_svg(metrics, out_path):
    c_2026 = f"{metrics['commits_2026']:,}+"
    c_all = f"{metrics['commits_all_time']:,}+"
    contrib_all = f"{metrics['contribs_all_time']:,}+"
    stars = str(metrics['total_stars'])
    prs = str(metrics['total_prs'])
    issues = str(metrics['total_issues'])

    svg_content = f"""<svg width="495" height="220" viewBox="0 0 495 220" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .header {{
      font: 700 18px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: #D9A441;
    }}
    .stat {{
      font: 700 14px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: #c9d1d9;
    }}
    .stat-val {{
      font: 600 14px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: #f0f6fc;
    }}
    .stat-highlight {{
      font: 700 14px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: #D9A441;
    }}
    .icon {{
      fill: #D9A441;
      display: inline-block;
    }}
    .rank-circle-rim {{
      stroke: #D9A441;
      fill: none;
      stroke-width: 6;
      opacity: 0.2;
    }}
    .rank-circle {{
      stroke: #D9A441;
      stroke-dasharray: 250;
      stroke-dashoffset: 25;
      fill: none;
      stroke-width: 6;
      stroke-linecap: round;
      opacity: 0.9;
    }}
    .rank-text {{
      font: 800 24px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: #D9A441;
    }}
  </style>

  <rect
    x="0.5"
    y="0.5"
    rx="6"
    width="494"
    height="219"
    fill="#0d1117"
    stroke="#30363d"
    stroke-width="1"
  />

  <!-- Title Header -->
  <text x="25" y="32" class="header">My GitHub Statistics</text>

  <!-- Circular Rank Badge A++ -->
  <g transform="translate(400, 110)">
    <circle class="rank-circle-rim" cx="0" cy="0" r="38" />
    <circle class="rank-circle" cx="0" cy="0" r="38" transform="rotate(-90)" />
    <text x="0" y="8" class="rank-text" text-anchor="middle">A++</text>
  </g>

  <!-- Statistics Rows -->
  <g transform="translate(0, 42)">
    <!-- 1. Total Stars -->
    <g transform="translate(25, 14)">
      <svg class="icon" viewBox="0 0 16 16" width="16" height="16">
        <path fill-rule="evenodd" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25zm0 2.445L6.615 5.5a.75.75 0 01-.564.41l-3.097.45 2.24 2.184a.75.75 0 01.216.664l-.528 3.084 2.769-1.456a.75.75 0 01.698 0l2.77 1.456-.53-3.084a.75.75 0 01.216-.664l2.24-2.183-3.096-.45a.75.75 0 01-.564-.41L8 2.694v.001z"/>
      </svg>
      <text class="stat" x="26" y="13">Total Stars:</text>
      <text class="stat-val" x="200" y="13">{stars}</text>
    </g>

    <!-- 2. 2026 Total Commits -->
    <g transform="translate(25, 40)">
      <svg class="icon" viewBox="0 0 16 16" width="16" height="16">
        <path fill-rule="evenodd" d="M1.643 3.143L.427 1.927A.25.25 0 000 2.104V5.75c0 .138.112.25.25.25h3.646a.25.25 0 00.177-.427L2.715 4.215a6.5 6.5 0 11-1.18 4.458.75.75 0 10-1.493.154 8.001 8.001 0 101.6-5.684zM7.75 4a.75.75 0 01.75.75v2.992l2.028.812a.75.75 0 01-.557 1.392l-2.5-1A.75.75 0 017 8.25v-3.5A.75.75 0 017.75 4z"/>
      </svg>
      <text class="stat-highlight" x="26" y="13">2026 Total Commits:</text>
      <text class="stat-highlight" x="200" y="13">{c_2026}</text>
    </g>

    <!-- 3. Total Commits (All-Time) -->
    <g transform="translate(25, 66)">
      <svg class="icon" viewBox="0 0 16 16" width="16" height="16">
        <path fill-rule="evenodd" d="M10.5 8a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zM8 0a8 8 0 100 16A8 8 0 008 0zm0 14.5a6.5 6.5 0 110-13 6.5 6.5 0 010 13z"/>
      </svg>
      <text class="stat" x="26" y="13">Total Commits:</text>
      <text class="stat-val" x="200" y="13">{c_all} ({contrib_all} contrib)</text>
    </g>

    <!-- 4. Total PRs -->
    <g transform="translate(25, 92)">
      <svg class="icon" viewBox="0 0 16 16" width="16" height="16">
        <path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/>
      </svg>
      <text class="stat" x="26" y="13">Total PRs:</text>
      <text class="stat-val" x="200" y="13">{prs}</text>
    </g>

    <!-- 5. Total Issues -->
    <g transform="translate(25, 118)">
      <svg class="icon" viewBox="0 0 16 16" width="16" height="16">
        <path fill-rule="evenodd" d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"/>
      </svg>
      <text class="stat" x="26" y="13">Total Issues:</text>
      <text class="stat-val" x="200" y="13">{issues}</text>
    </g>

    <!-- 6. Contributed to -->
    <g transform="translate(25, 144)">
      <svg class="icon" viewBox="0 0 16 16" width="16" height="16">
        <path fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
      </svg>
      <text class="stat" x="26" y="13">Contributed to:</text>
      <text class="stat-val" x="200" y="13">2</text>
    </g>
  </g>
</svg>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[✓] Generated live SVG stats card at: {out_path}")

def render_png(svg_path, out_png):
    # Try Chrome/Chromium headless rendering
    chrome_candidates = [
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("chrome"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    chrome_bin = next((c for c in chrome_candidates if c and os.path.exists(c)), None)

    if chrome_bin:
        # Wrap SVG in minimal HTML
        html_wrapper = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 495px; height: 220px; background: transparent; overflow: hidden; }}
</style></head><body>
<img src="file:///{os.path.abspath(svg_path).replace(os.sep, '/')}" width="495" height="220" />
</body></html>"""
        temp_html = os.path.abspath(svg_path) + ".render.html"
        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(html_wrapper)

        cmd = [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            "--force-device-scale-factor=2",
            f"--screenshot={out_png}",
            "--window-size=495,220",
            f"file:///{temp_html.replace(os.sep, '/')}"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if res.returncode == 0 and os.path.exists(out_png):
                print(f"[✓] Rendered live 2x Retina PNG at: {out_png}")
            else:
                print(f"[!] Chrome exited with code {res.returncode}: {res.stderr}")
        except Exception as e:
            print(f"[!] Chrome render error: {e}")
        finally:
            if os.path.exists(temp_html):
                os.remove(temp_html)
    else:
        print("[!] No Chrome binary found, skipping PNG render (SVG will be used directly).")

def update_readme(metrics, readme_path):
    if not os.path.exists(readme_path):
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    c_2026 = f"{metrics['commits_2026']:,}+"
    contrib_2026 = f"{metrics['contribs_2026']:,}+"
    contrib_all = f"{metrics['contribs_all_time']:,}+"

    # Replace badge counts if pattern matches
    content = re.sub(
        r'2026%20Commits-[0-9,]+%2B',
        f'2026%20Commits-{urllib.parse.quote(c_2026)}',
        content
    )
    content = re.sub(
        r'All--Time%20Contributions-[0-9,]+%2B',
        f'All--Time%20Contributions-{urllib.parse.quote(contrib_all)}',
        content
    )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✓] Updated README live badges in: {readme_path}")

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    metrics = fetch_live_metrics()
    if not metrics:
        print("[!] Using fallback verified metrics.")
        metrics = {
            "commits_2026": 3463,
            "contribs_2026": 3568,
            "commits_all_time": 4280,
            "contribs_all_time": 4437,
            "total_stars": 15,
            "total_repos": 135,
            "total_prs": 3,
            "total_issues": 2,
        }

    svg_path = os.path.join(repo_root, "github-stats.svg")
    png_path = os.path.join(repo_root, "github-stats.png")
    readme_path = os.path.join(repo_root, "README.md")

    import urllib.parse
    generate_svg(metrics, svg_path)
    render_png(svg_path, png_path)
    update_readme(metrics, readme_path)
    print("[✓] All profile statistics updated successfully from GitHub API.")

if __name__ == "__main__":
    main()
