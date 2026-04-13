"""Template dataclass and zero-dependency mini template engine.

The engine supports:
  {{variable}}                  — variable substitution
  {% if condition %}            — conditional block
  {% elif condition %}          — else-if branch
  {% else %}                    — else branch
  {% endif %}                   — end conditional
  {% for item in list %}        — iteration
  {% endfor %}                  — end iteration

Condition operators:
  truthiness:   {% if hipaa %}
  equality:     {% if preset == "government" %}
  inequality:   {% if preset != "government" %}
  membership:   {% if "hipaa" in compliance %}

No arbitrary Python eval — intentionally limited for security.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ── DocumentTemplate ──────────────────────────────────────────────────────

@dataclass
class DocumentTemplate:
    """Metadata + body for a scaffold-able document template."""

    template_id: str                    # unique slug: "strategic-plan"
    display_name: str                   # human-readable: "Strategic Plan"
    preset: str                         # "business", "universal", "security", etc.
    description: str
    suggested_tags: list[str] = field(default_factory=list)
    suggested_folder: str = ""          # relative to docs root
    typical_cross_refs: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    recommended_with: list[str] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    body: str = ""                      # raw markdown body with {{variables}}

    @classmethod
    def from_string(cls, text: str, preset: str = "universal") -> "DocumentTemplate":
        """Parse a template file (YAML frontmatter + markdown body)."""
        frontmatter, body = _split_frontmatter(text)
        return cls(
            template_id=frontmatter.get("template_id", ""),
            display_name=frontmatter.get("display_name", ""),
            preset=frontmatter.get("preset", preset),
            description=frontmatter.get("description", ""),
            suggested_tags=frontmatter.get("suggested_tags", []),
            suggested_folder=frontmatter.get("suggested_folder", ""),
            typical_cross_refs=frontmatter.get("typical_cross_refs", []),
            requires=frontmatter.get("requires", []),
            recommended_with=frontmatter.get("recommended_with", []),
            sections=frontmatter.get("sections", []),
            body=body,
        )

    @classmethod
    def from_file(cls, path: str, preset: str = "universal") -> "DocumentTemplate":
        """Load a template from a file path."""
        from pathlib import Path
        text = Path(path).read_text(encoding="utf-8")
        return cls.from_string(text, preset=preset)

    def render(self, context: dict[str, Any]) -> str:
        """Render the template body with the given context dict."""
        return render_template(self.body, context)


# ── Frontmatter parser ────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from markdown body. Returns ({}, text) if no frontmatter."""
    import yaml
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw_yaml = m.group(1)
    body = text[m.end():]
    try:
        fm = yaml.safe_load(raw_yaml) or {}
    except Exception:
        fm = {}
    return fm, body


# ── Mini template engine ──────────────────────────────────────────────────

# Tag patterns
_TAG_RE = re.compile(r"\{%\s*(.*?)\s*%\}")
_VAR_RE = re.compile(r"\{\{(\s*[\w.]+\s*)\}\}")

# Directive patterns (applied to stripped tag content)
_IF_RE = re.compile(r"^if\s+(.+)$")
_ELIF_RE = re.compile(r"^elif\s+(.+)$")
_ELSE_RE = re.compile(r"^else$")
_ENDIF_RE = re.compile(r"^endif$")
_FOR_RE = re.compile(r"^for\s+(\w+)\s+in\s+(\w+)$")
_ENDFOR_RE = re.compile(r"^endfor$")


def render_template(template: str, context: dict[str, Any]) -> str:
    """Render a template string with variable substitution and control flow."""
    tokens = _tokenize(template)
    ast = _parse_tokens(tokens)
    return _evaluate(ast, context)


def _tokenize(template: str) -> list[tuple[str, str]]:
    """Split template into a list of (type, value) tokens.

    Types: 'text', 'var', 'tag'
    """
    tokens: list[tuple[str, str]] = []
    pos = 0
    # Combined pattern: match {% ... %} or {{ ... }}
    combined = re.compile(r"(\{%\s*.*?\s*%\}|\{\{.*?\}\})")
    for m in combined.finditer(template):
        start, end = m.span()
        if start > pos:
            tokens.append(("text", template[pos:start]))
        raw = m.group(0)
        if raw.startswith("{%"):
            # Strip {% and %}
            inner = raw[2:-2].strip()
            tokens.append(("tag", inner))
        else:
            # Strip {{ and }}
            inner = raw[2:-2].strip()
            tokens.append(("var", inner))
        pos = end
    if pos < len(template):
        tokens.append(("text", template[pos:]))
    return tokens


# AST node types
# ("text", value)
# ("var", name)
# ("if", [(condition_str, [nodes]), ...])   — branches list; "else" has condition None
# ("for", var_name, list_name, [nodes])

def _parse_tokens(tokens: list[tuple[str, str]]) -> list[tuple]:
    """Parse flat token list into a nested AST."""
    ast, remaining = _parse_block(tokens, stop_tags=set())
    return ast


def _parse_block(
    tokens: list[tuple[str, str]],
    stop_tags: set[str],
) -> tuple[list[tuple], list[tuple[str, str]]]:
    """Parse tokens until a stop tag or end-of-input. Returns (nodes, remaining_tokens)."""
    nodes: list[tuple] = []
    while tokens:
        typ, val = tokens[0]

        if typ == "text":
            nodes.append(("text", val))
            tokens = tokens[1:]
        elif typ == "var":
            nodes.append(("var", val))
            tokens = tokens[1:]
        elif typ == "tag":
            # Check if this is a stop tag
            if any(val.startswith(s) or val == s for s in stop_tags):
                break

            m_if = _IF_RE.match(val)
            if m_if:
                tokens = tokens[1:]
                node, tokens = _parse_if(m_if.group(1), tokens)
                nodes.append(node)
                continue

            m_for = _FOR_RE.match(val)
            if m_for:
                tokens = tokens[1:]
                node, tokens = _parse_for(m_for.group(1), m_for.group(2), tokens)
                nodes.append(node)
                continue

            # Unknown tag — treat as text
            nodes.append(("text", "{%" + val + "%}"))
            tokens = tokens[1:]
        else:
            tokens = tokens[1:]

    return nodes, tokens


def _parse_if(
    condition: str,
    tokens: list[tuple[str, str]],
) -> tuple[tuple, list[tuple[str, str]]]:
    """Parse an if/elif/else/endif block."""
    branches: list[tuple[str | None, list[tuple]]] = []

    # Parse the 'if' body
    body, tokens = _parse_block(tokens, stop_tags={"elif", "else", "endif"})
    branches.append((condition, body))

    while tokens:
        typ, val = tokens[0]
        if typ != "tag":
            break

        if val == "endif":
            tokens = tokens[1:]
            break

        m_elif = _ELIF_RE.match(val)
        if m_elif:
            tokens = tokens[1:]
            body, tokens = _parse_block(tokens, stop_tags={"elif", "else", "endif"})
            branches.append((m_elif.group(1), body))
            continue

        if val == "else":
            tokens = tokens[1:]
            body, tokens = _parse_block(tokens, stop_tags={"endif"})
            branches.append((None, body))
            # Consume endif
            if tokens and tokens[0] == ("tag", "endif"):
                tokens = tokens[1:]
            break

        break

    return ("if", branches), tokens


def _parse_for(
    var_name: str,
    list_name: str,
    tokens: list[tuple[str, str]],
) -> tuple[tuple, list[tuple[str, str]]]:
    """Parse a for/endfor block."""
    body, tokens = _parse_block(tokens, stop_tags={"endfor"})
    if tokens and tokens[0] == ("tag", "endfor"):
        tokens = tokens[1:]
    return ("for", var_name, list_name, body), tokens


def _evaluate(nodes: list[tuple], context: dict[str, Any]) -> str:
    """Evaluate AST nodes against a context dict, producing the final string."""
    parts: list[str] = []
    for node in nodes:
        kind = node[0]
        if kind == "text":
            parts.append(node[1])
        elif kind == "var":
            name = node[1]
            val = context.get(name, "")
            parts.append(str(val))
        elif kind == "if":
            branches = node[1]
            for cond, body in branches:
                if cond is None or _eval_condition(cond, context):
                    parts.append(_evaluate(body, context))
                    break
        elif kind == "for":
            _, var_name, list_name, body = node
            iterable = context.get(list_name, [])
            if isinstance(iterable, (list, tuple)):
                for item in iterable:
                    sub_ctx = {**context, var_name: item}
                    parts.append(_evaluate(body, sub_ctx))
    return "".join(parts)


_MAX_CONDITION_DEPTH = 20


def _eval_condition(condition: str, context: dict[str, Any], _depth: int = 0) -> bool:
    """Evaluate a condition string against the context.

    Supported forms:
      truthiness:    "hipaa"             → bool(context.get("hipaa"))
      equality:      'preset == "gov"'   → context["preset"] == "gov"
      inequality:    'preset != "gov"'   → context["preset"] != "gov"
      membership:    '"hipaa" in compliance' → "hipaa" in context["compliance"]
      or combinator: 'cond1 or cond2'    → eval(cond1) or eval(cond2)
      and combinator:'cond1 and cond2'   → eval(cond1) and eval(cond2)
      not operator:  'not hipaa'         → not bool(context.get("hipaa"))
    """
    if _depth > _MAX_CONDITION_DEPTH:
        return False
    condition = condition.strip()

    # Handle 'or' (lower precedence than 'and')
    # Split on ' or ' but not inside quotes
    or_parts = _split_logical(condition, " or ")
    if len(or_parts) > 1:
        return any(_eval_condition(p, context, _depth + 1) for p in or_parts)

    # Handle 'and'
    and_parts = _split_logical(condition, " and ")
    if len(and_parts) > 1:
        return all(_eval_condition(p, context, _depth + 1) for p in and_parts)

    # Handle 'not'
    if condition.startswith("not "):
        return not _eval_condition(condition[4:], context, _depth + 1)

    # Handle 'in' membership: "value" in variable
    in_match = re.match(r'^"([^"]+)"\s+in\s+(\w+)$', condition)
    if in_match:
        needle = in_match.group(1)
        haystack_name = in_match.group(2)
        haystack = context.get(haystack_name, [])
        if isinstance(haystack, (list, tuple, set, frozenset)):
            return needle in haystack
        if isinstance(haystack, str):
            return needle in haystack
        return False

    # Handle equality: variable == "value"
    eq_match = re.match(r'^(\w+)\s*==\s*"([^"]*)"$', condition)
    if eq_match:
        var_name = eq_match.group(1)
        expected = eq_match.group(2)
        return str(context.get(var_name, "")) == expected

    # Handle inequality: variable != "value"
    neq_match = re.match(r'^(\w+)\s*!=\s*"([^"]*)"$', condition)
    if neq_match:
        var_name = neq_match.group(1)
        expected = neq_match.group(2)
        return str(context.get(var_name, "")) != expected

    # Truthiness: bare variable name
    return bool(context.get(condition, False))


def _split_logical(condition: str, operator: str) -> list[str]:
    """Split condition on a logical operator, respecting quoted strings."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    i = 0
    while i < len(condition):
        ch = condition[i]
        if ch == '"':
            depth = 1 - depth  # toggle inside/outside quotes
            current.append(ch)
            i += 1
        elif depth == 0 and condition[i:i + len(operator)] == operator:
            parts.append("".join(current).strip())
            current = []
            i += len(operator)
        else:
            current.append(ch)
            i += 1
    remaining = "".join(current).strip()
    if remaining:
        parts.append(remaining)
    return parts
