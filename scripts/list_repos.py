#!/usr/bin/env python3
"""List all repos for a GitHub owner with current metadata.

Usage:
    python3 list_repos.py --owner mcgrapeng [--out /tmp/repos.json]

Output JSON: list of {name, description, language, topics, stars, updated_at, html_url}
"""
import argparse, json, urllib.request, urllib.error, os, sys, time


def _load_dotenv() -> None:
    here = os.path.dirname(os.path.realpath(__file__))
    env_path = os.path.normpath(os.path.join(here, '..', '.env'))
    if not os.path.isfile(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
                v = v[1:-1]
            os.environ.setdefault(k, v)


_load_dotenv()


def get_token() -> str:
    tok = os.environ.get('GITHUB_TOKEN')
    if not tok:
        raise RuntimeError(
            'GITHUB_TOKEN env var is required.\n'
            '  export GITHUB_TOKEN=ghp_xxx   # classic PAT, scope: repo (read+write)'
        )
    return tok


def gh_get(url: str, token: str, max_pages: int = 20) -> list:
    out = []
    for page in range(1, max_pages + 1):
        u = f'{url}?per_page=100&page={page}&sort=updated'
        req = urllib.request.Request(u, headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'github-desc-rewriter',
        })
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read())
                    if not data:
                        return out
                    out.extend(data)
                    break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503):
                    time.sleep(2 ** attempt)
                    continue
                raise
        else:
            raise RuntimeError(f'failed after 3 retries: {u}')
        if len(data) < 100:
            return out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owner', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--token', default=None)
    args = ap.parse_args()

    token = args.token or get_token()
    raw = gh_get(f'https://api.github.com/users/{args.owner}/repos', token)
    repos = []
    for r in raw:
        repos.append({
            'name': r['name'],
            'description': r.get('description') or '',
            'language': r.get('language') or '',
            'topics': r.get('topics') or [],
            'stars': r.get('stargazers_count', 0),
            'updated_at': r.get('updated_at', ''),
            'html_url': r.get('html_url', ''),
        })

    if args.out:
        with open(args.out, 'w') as f:
            json.dump(repos, f, ensure_ascii=False, indent=2)
        print(f'Wrote {len(repos)} repos to {args.out}')
    else:
        json.dump(repos, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
