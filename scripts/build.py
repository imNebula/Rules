from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import os
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "domains.txt"
OUT = ROOT / "dist"
IMPORT_TIMEOUT = 20

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
GROUP_RE = re.compile(r"^[a-z0-9_-]+$")
IMPORT_RE = re.compile(r"^@(?:(auto|list|yaml)\s+)?(.+)$", re.IGNORECASE)
KEYWORD_RE = re.compile(r"^[^,\s#]+$")
GITHUB_RE = re.compile(
    r"^(?:https?://[^/\s]+/|git@[^:\s]+:)([^/\s]+)/([^/\s]+?)(?:\.git)?/?$"
)


def strip_inline_comment(value: str) -> str:
    if "#" in value:
        value = value.split("#", 1)[0]
    return value.strip()


def normalize_domain(raw: str):
    s = strip_inline_comment(raw)
    if not s:
        return None

    exact = s.startswith("=")
    if exact:
        s = s[1:].strip()

    if "://" in s:
        parsed = urlparse(s)
        s = parsed.hostname or s

    s = s.strip().lower().rstrip(".")
    s = s.split("/", 1)[0]

    if s.startswith("*."):
        s = s[2:]
    if s.startswith("."):
        s = s[1:]

    try:
        s = s.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError(f"Invalid IDN domain: {raw}") from exc

    if not DOMAIN_RE.match(s):
        raise ValueError(f"Invalid domain: {raw}")

    return ("exact" if exact else "suffix", s)


def normalize_rule_token(raw: str, plain_mode: str = "suffix"):
    s = strip_inline_comment(raw)
    if not s:
        return None

    upper = s.upper()
    if upper.startswith("DOMAIN-SUFFIX,"):
        return normalize_domain(s.split(",", 1)[1].strip())
    if upper.startswith("DOMAIN,"):
        return normalize_domain("=" + s.split(",", 1)[1].strip())
    if upper.startswith("DOMAIN-KEYWORD,"):
        keyword = s.split(",", 1)[1].strip().lower()
        if not KEYWORD_RE.match(keyword):
            raise ValueError(f"Invalid DOMAIN-KEYWORD rule: {raw}")
        return ("keyword", keyword)
    if upper.startswith("HOST-SUFFIX,"):
        return normalize_domain(s.split(",", 1)[1].strip())
    if upper.startswith("HOST,"):
        return normalize_domain("=" + s.split(",", 1)[1].strip())
    if s.startswith("+."):
        return normalize_domain(s[1:])
    if s.startswith("."):
        return normalize_domain(s)
    if s.startswith("="):
        return normalize_domain(s)
    if plain_mode == "exact":
        return normalize_domain("=" + s)

    return normalize_domain(s)


def infer_import_format(source: str, declared: str):
    if declared and declared != "auto":
        return declared

    lower = source.lower()
    if lower.endswith((".yaml", ".yml")):
        return "yaml"
    return "list"


def read_import_source(source: str) -> str:
    if "://" in source:
        request = Request(source, headers={"User-Agent": "custom-rules-builder/1.0"})
        with urlopen(request, timeout=IMPORT_TIMEOUT) as response:
            return response.read().decode("utf-8-sig")

    path = Path(source)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path.read_text(encoding="utf-8-sig")


def parse_import_lines(text: str, fmt: str, origin: str):
    items = []
    plain_mode = "exact"

    for line_no, raw_line in enumerate(text.splitlines(), 1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if fmt == "yaml":
            if stripped == "payload:":
                continue
            if not stripped.startswith("-"):
                continue
            token = stripped[1:].strip()
            if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
                token = token[1:-1]
        else:
            token = stripped

        item = normalize_rule_token(token, plain_mode=plain_mode)
        if item:
            items.append((item, f"{origin}:{line_no}"))

    return items


def parse_import(target: str, declared_format: str):
    fmt = infer_import_format(target, declared_format)
    text = read_import_source(target)
    return parse_import_lines(text, fmt, target)


def ensure_unique(entries):
    seen = {}
    duplicates = {}

    for entry in entries:
        key = entry["item"]
        if key in seen:
            duplicates.setdefault(key, [seen[key]]).append(entry)
        else:
            seen[key] = entry

    if not duplicates:
        return

    lines = ["Duplicate rules found:"]
    for (kind, domain), matches in sorted(duplicates.items(), key=lambda x: (x[0][1], x[0][0])):
        rendered = f"{kind}:{domain}"
        lines.append(f"- {rendered}")
        for match in matches:
            lines.append(f"  group={match['group']} source={match['source']}")
    raise ValueError("\n".join(lines))


def parse_domains():
    groups = {}
    entries = []
    current = "custom"

    for line_no, raw_line in enumerate(SRC.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip().lower()
            if not GROUP_RE.match(current):
                raise ValueError(f"Invalid group name at line {line_no}: {current}")
            groups.setdefault(current, [])
            continue

        import_match = IMPORT_RE.match(line)
        if import_match:
            import_format = (import_match.group(1) or "auto").lower()
            import_target = import_match.group(2).strip()
            if not import_target:
                raise ValueError(f"Missing import target at line {line_no}")

            for item, source in parse_import(import_target, import_format):
                entry = {"group": current, "item": item, "source": source}
                groups.setdefault(current, []).append(item)
                entries.append(entry)
            continue

        item = normalize_domain(line)
        if item:
            groups.setdefault(current, []).append(item)
            entries.append({"group": current, "item": item, "source": f"{SRC.name}:{line_no}"})

    ensure_unique(entries)

    result = {}
    for group, items in groups.items():
        normalized = sorted(items, key=lambda x: (x[1], x[0]))
        if normalized:
            result[group] = normalized
    return result


def base_url():
    configured = (
        os.environ.get("RULES_BASE_URL", "").strip()
        or os.environ.get("PAGES_BASE_URL", "").strip()
    ).rstrip("/")
    if configured:
        return configured

    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    branch = os.environ.get("GITHUB_REF_NAME", "").strip() or git_output(
        "branch", "--show-current"
    )
    if "/" not in repo:
        repo = github_repo_from_origin()

    if "/" in repo and branch:
        return f"https://raw.githubusercontent.com/{repo}/{branch}/dist"

    return "https://<user>.github.io/<repo>"


def git_output(*args):
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def github_repo_from_origin():
    origin = git_output("config", "--get", "remote.origin.url")
    match = GITHUB_RE.search(origin)
    if not match:
        return ""
    return f"{match.group(1)}/{match.group(2)}"


def yaml_quote(value):
    return "'" + value.replace("'", "''") + "'"


def mihomo_domain_value(kind, domain):
    return domain if kind == "exact" else f"+.{domain}"


def classical_rule_value(kind, domain):
    if kind == "exact":
        return f"DOMAIN,{domain}"
    if kind == "suffix":
        return f"DOMAIN-SUFFIX,{domain}"
    if kind == "keyword":
        return f"DOMAIN-KEYWORD,{domain}"
    raise ValueError(f"Unsupported rule kind: {kind}")


def surge_domain_set_value(kind, domain):
    if kind == "keyword":
        return None
    return domain if kind == "exact" else f".{domain}"


def surge_rule_set_value(kind, domain):
    return classical_rule_value(kind, domain)


def write_files(groups):
    if OUT.exists():
        shutil.rmtree(OUT)

    (OUT / "mihomo").mkdir(parents=True)
    (OUT / "mihomo" / "domain").mkdir(parents=True)
    (OUT / "surge" / "domain-set").mkdir(parents=True)
    (OUT / "surge" / "rule-set").mkdir(parents=True)
    (OUT / "snippets").mkdir(parents=True)

    root_url = base_url()
    mihomo_snippet = ["rule-providers:"]
    mihomo_domain_snippet = ["rule-providers:"]
    mihomo_rules = ["rules:"]
    mihomo_domain_rules = ["rules:"]
    surge_domain_set_lines = ["[Rule]"]
    surge_rule_set_lines = ["[Rule]"]

    for group, items in groups.items():
        mihomo_payload = [classical_rule_value(k, d) for k, d in items]
        mihomo_domain_payload = [
            mihomo_domain_value(k, d) for k, d in items if k in {"exact", "suffix"}
        ]
        surge_domain_set = [
            x for x in (surge_domain_set_value(k, d) for k, d in items) if x
        ]
        surge_rule_set = [surge_rule_set_value(k, d) for k, d in items]

        (OUT / "mihomo" / f"{group}.yaml").write_text(
            "payload:\n" + "\n".join(f"  - {yaml_quote(x)}" for x in mihomo_payload) + "\n",
            encoding="utf-8",
        )
        (OUT / "mihomo" / f"{group}.list").write_text(
            "\n".join(mihomo_payload) + "\n",
            encoding="utf-8",
        )
        (OUT / "mihomo" / "domain" / f"{group}.yaml").write_text(
            "payload:\n"
            + "\n".join(f"  - {yaml_quote(x)}" for x in mihomo_domain_payload)
            + "\n",
            encoding="utf-8",
        )
        (OUT / "mihomo" / "domain" / f"{group}.list").write_text(
            "\n".join(mihomo_domain_payload) + "\n",
            encoding="utf-8",
        )
        (OUT / "surge" / "domain-set" / f"{group}.txt").write_text(
            "\n".join(surge_domain_set) + "\n",
            encoding="utf-8",
        )
        (OUT / "surge" / "rule-set" / f"{group}.list").write_text(
            "\n".join(surge_rule_set) + "\n",
            encoding="utf-8",
        )

        policy = group.upper()

        mihomo_snippet += [
            f"  {group}:",
            "    type: http",
            "    behavior: classical",
            "    format: yaml",
            f"    url: {yaml_quote(f'{root_url}/mihomo/{group}.yaml')}",
            f"    path: ./ruleset/{group}.yaml",
            "    interval: 86400",
        ]
        mihomo_rules.append(f"  - RULE-SET,{group},{policy}")
        mihomo_domain_snippet += [
            f"  {group}:",
            "    type: http",
            "    behavior: domain",
            "    format: yaml",
            f"    url: {yaml_quote(f'{root_url}/mihomo/domain/{group}.yaml')}",
            f"    path: ./ruleset/{group}-domain.yaml",
            "    interval: 86400",
        ]
        mihomo_domain_rules.append(f"  - RULE-SET,{group},{policy}")
        surge_domain_set_lines.append(
            f"DOMAIN-SET,{root_url}/surge/domain-set/{group}.txt,{policy},extended-matching"
        )
        surge_rule_set_lines.append(
            f"RULE-SET,{root_url}/surge/rule-set/{group}.list,{policy}"
        )

    mihomo_rules.append("  - MATCH,PROXY")
    mihomo_domain_rules.append("  - MATCH,PROXY")
    surge_domain_set_lines.append("FINAL,PROXY")
    surge_rule_set_lines.append("FINAL,PROXY")

    (OUT / "snippets" / "mihomo.yaml").write_text(
        "\n".join(mihomo_snippet) + "\n\n" + "\n".join(mihomo_rules) + "\n",
        encoding="utf-8",
    )
    (OUT / "snippets" / "mihomo-domain.yaml").write_text(
        "\n".join(mihomo_domain_snippet) + "\n\n" + "\n".join(mihomo_domain_rules) + "\n",
        encoding="utf-8",
    )
    (OUT / "snippets" / "surge.conf").write_text(
        "\n".join(surge_domain_set_lines) + "\n",
        encoding="utf-8",
    )
    (OUT / "snippets" / "surge-rule-set.conf").write_text(
        "\n".join(surge_rule_set_lines) + "\n",
        encoding="utf-8",
    )


def main():
    groups = parse_domains()
    if not groups:
        raise SystemExit("No domains found in domains.txt")
    write_files(groups)
    print(f"Generated {sum(len(v) for v in groups.values())} rules in {len(groups)} groups.")


if __name__ == "__main__":
    main()
