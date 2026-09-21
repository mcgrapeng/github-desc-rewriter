#!/usr/bin/env python3
"""Batch PATCH GitHub repo descriptions from a JSON dict.

Usage:
    python3 apply_descs.py \\
        --repos /tmp/repos.json \\
        --new-descs /tmp/new_descs.json \\
        --owner mcgrapeng [--dry-run] [--token <ghp_xxx>]

Reads:
  - repos.json     : output of list_repos.py (for cross-checking names)
  - new_descs.json : {repo_name: new_description, ...}

Behavior:
  - Skips repos where current == new (no API call)
  - Truncates descriptions > 350 chars with a warning
  - Replaces \\n with ' / ' (GitHub API rejects newlines)
  - Retries 429/5xx with exponential backoff
  - --dry-run prints what would change without calling API
"""
import argparse, json, urllib.request, urllib.error, subprocess, base64, sys, time

MAX_LEN = 350


def get_token() -> str:
    raw = subprocess.check_output(
        ['security', 'find-generic-password', '-s', 'gh:github.com', '-w']
    ).decode().strip()
    if raw.startswith('go-keyring-base64:'):
        return base64.b64decode(raw.split(':', 1)[1]).decode()
    return raw


def sanitize(desc: str) -> str:
    """Strip control chars + truncate to MAX_LEN."""
    # remove newlines, tabs, control chars
    bad = ''.join(chr(c) for c in range(32) if c not in (9,)) + chr(127)
    for ch in bad:
        desc = desc.replace(ch, ' ')
    if len(desc) > MAX_LEN:
        desc = desc[: MAX_LEN - 1] + '…'
    return desc.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repos', required=True, help='output of list_repos.py')
    ap.add_argument('--new-descs', required=True, help='{name: desc, ...}')
    ap.add_argument('--owner', required=True)
    ap.add_argument('--token', default=None)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=0, help='max repos to update (0 = all)')
    args = ap.parse_args()

    repos = json.load(open(args.repos))
    new_descs = json.load(open(args.new_descs))
    valid_names = {r['name'] for r in repos}
    cur_by_name = {r['name']: (r.get('description') or '') for r in repos}

    unknown = [k for k in new_descs if k not in valid_names]
    if unknown:
        print(f'⚠️  {len(unknown)} keys in new-descs are not real repos (skipped):')
        for k in unknown[:10]:
            print(f'    - {k}')
        if len(unknown) > 10:
            print(f'    ... +{len(unknown) - 10} more')

    items = [(k, sanitize(v)) for k, v in new_descs.items() if k in valid_names]
    items = [(k, v) for k, v in items if v != cur_by_name.get(k, '')]

    truncated = [(k, len(v)) for k, v in items if len(v) > MAX_LEN]

    print(f'Repos to update: {len(items)}')
    print(f'Skipped (unchanged): {len(new_descs) - len(items)}')
    if truncated:
        print(f'⚠️  Truncated to {MAX_LEN} chars: {len(truncated)}')

    if args.dry_run:
        print('\n--- DRY RUN (no API calls) ---')
        for k, v in items[:10]:
            old = cur_by_name.get(k, '')
            print(f'\n[{k}]')
            print(f'  OLD: {old[:100]}')
            print(f'  NEW: {v[:100]}')
        if len(items) > 10:
            print(f'\n... +{len(items) - 10} more (not shown)')
        print('\n--dry-run specified, no PATCH sent.')
        return

    if args.limit > 0:
        items = items[: args.limit]
        print(f'Limiting to first {len(items)} updates')

    token = args.token or get_token()
    api = 'https://api.github.com'

    success = fail = unchanged = 0
    results = []
    for i, (name, desc) in enumerate(items, 1):
        url = f'{api}/repos/{args.owner}/{name}'
        data = json.dumps({'description': desc}).encode()
        req = urllib.request.Request(url, data=data, method='PATCH', headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'User-Agent': 'github-desc-rewriter',
        })
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    success += 1
                    results.append((name, 'OK'))
                    break
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:120]
                if e.code in (429, 500, 502, 503):
                    time.sleep(2 ** attempt)
                    continue
                elif e.code == 422:
                    fail += 1
                    results.append((name, f'422 {body}'))
                    break
                else:
                    fail += 1
                    results.append((name, f'{e.code} {body}'))
                    break
            except Exception as e:
                time.sleep(1)
        else:
            fail += 1
            results.append((name, 'TIMEOUT'))

        if i % 25 == 0:
            print(f'  [{i}/{len(items)}] {success} ok, {fail} fail')
            time.sleep(0.3)

    print(f'\n✓ Done: {success} updated, {fail} failed, {unchanged} unchanged')

    if fail:
        print('\nFailures:')
        for n, s in results:
            if s != 'OK':
                print(f'  {n}: {s}')

    json.dump(results, open('/tmp/github-desc/last_results.json', 'w'),
              ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
