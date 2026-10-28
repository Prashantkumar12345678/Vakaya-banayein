# -*- coding: utf-8 -*-
"""Drop CSS that can never match anything in this game.

    python _tools/prune_css.py IN.html OUT.html

A selector is DEAD when it names a class or id that appears nowhere in the page's markup, its
JavaScript or the card - every class the engine ever adds is spelled somewhere in that text. Names
built at runtime ("fw-hand-" + side, `thm-${theme}`) are covered by treating every literal that ends
in "-" or "_" right before a quote or ${ as a PREFIX: any class starting with it stays.
Classes inside :not() are ignored (":not(.never)" matches everything), and :is/:where/:has lists
keep the selector alive (cheap to keep, costly to get wrong).
  - a rule loses its dead selectors; a rule with none left goes, with the comment block above it
  - @media / @supports blocks are pruned inside and dropped when empty
  - @keyframes no surviving CSS or JS names are dropped
  - custom properties (--x) that nothing reads with var(--x) or sets from JS are dropped
Prints what it removed; OUT is written only if the result still parses.
"""
import io, re, sys
import tinycss2

sys.stdout.reconfigure(encoding="utf-8")
IN, OUT = sys.argv[1], sys.argv[2]
h = io.open(IN, encoding="utf-8", newline="").read()
STYLE = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.S)
styles = [(m.start(2), m.end(2), m.group(2)) for m in STYLE.finditer(h)]
other = STYLE.sub("", h)                          # markup + scripts + card
words = set(re.findall(r"[A-Za-z_][\w-]*", other))
prefixes = set(re.findall(r"([A-Za-z][\w-]*[-_])(?=[\"'`]|\$\{)", other))
stats = {"selectors": 0, "rules": 0, "keyframes": 0, "props": 0, "media": 0}
removed_names = []


def known(name):
    return name in words or any(name.startswith(p) for p in prefixes)


def strip_fn(sel, fn):
    out, i = "", 0
    while True:
        j = sel.find(":" + fn + "(", i)
        if j < 0: return out + sel[i:]
        out += sel[i:j]; k = j + len(fn) + 2; d = 1
        while d and k < len(sel):
            d += {"(": 1, ")": -1}.get(sel[k], 0); k += 1
        i = k


def alive(sel):
    s = re.sub(r"\[[^\]]*\]", "", sel)                       # attribute selectors carry values, not names
    if re.search(r":(is|where|has)\(", s): return True
    s = strip_fn(s, "not")
    s = re.sub(r"::?[\w-]+(\([^)]*\))?", "", s)              # pseudo-classes / elements
    names = re.findall(r"[.#](-?[A-Za-z_][\w-]*)", s)
    return all(known(n) for n in names)


def split_top(prelude):
    parts, d, cur = [], 0, ""
    for ch in prelude:
        if ch == "(": d += 1
        elif ch == ")": d -= 1
        if ch == "," and d == 0: parts.append(cur); cur = ""
        else: cur += ch
    parts.append(cur)
    return parts


def prune(nodes):
    out = []
    for n in nodes:
        if n.type == "qualified-rule":
            pre = tinycss2.serialize(n.prelude)
            sels = split_top(pre)
            keep = [s for s in sels if alive(s.strip())]
            stats["selectors"] += len(sels) - len(keep)
            if not keep:
                stats["rules"] += 1; removed_names.append(pre.strip()[:70])
                while out and (out[-1].type == "whitespace" or out[-1].type == "comment"):
                    out.pop()                                  # its comment goes with it
                out.append(tinycss2.ast.WhitespaceToken(0, 0, "\n"))
                continue
            if len(keep) != len(sels):
                lead = re.match(r"\s*", pre).group(0); tail = re.search(r"\s*$", pre).group(0)
                n.prelude = tinycss2.parse_component_value_list(lead + ",".join(k for k in keep).strip() + tail)
            out.append(n)
        elif n.type == "at-rule" and n.lower_at_keyword in ("media", "supports") and n.content is not None:
            inner = prune(tinycss2.parse_rule_list(n.content, skip_comments=False, skip_whitespace=False))
            if not any(x.type in ("qualified-rule", "at-rule") for x in inner):
                stats["media"] += 1
                while out and out[-1].type in ("whitespace", "comment"): out.pop()
                out.append(tinycss2.ast.WhitespaceToken(0, 0, "\n"))
                continue
            n.content = tinycss2.parse_component_value_list(tinycss2.serialize(inner))
            out.append(n)
        else:
            out.append(n)
    return out


new_css = []
for a, b, css in styles:
    nodes = tinycss2.parse_stylesheet(css, skip_comments=False, skip_whitespace=False)
    new_css.append(tinycss2.serialize(prune(nodes)))

# ---- keyframes nobody plays
all_css = "\n".join(new_css)
anim_text = " ".join(re.findall(r"animation(?:-name)?\s*:([^;}]*)", all_css)) + " " + other
def drop_kf(css):
    def rep(m):
        name = m.group(1)
        if re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", anim_text): return m.group(0)
        stats["keyframes"] += 1; removed_names.append("@keyframes " + name); return ""
    nodes = tinycss2.parse_stylesheet(css, skip_comments=False, skip_whitespace=False)
    out = []
    for n in nodes:
        if n.type == "at-rule" and n.lower_at_keyword in ("keyframes", "-webkit-keyframes"):
            name = tinycss2.serialize(n.prelude).strip()
            if not re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", anim_text):
                stats["keyframes"] += 1; removed_names.append("@keyframes " + name)
                while out and out[-1].type in ("whitespace", "comment"): out.pop()
                out.append(tinycss2.ast.WhitespaceToken(0, 0, "\n")); continue
        out.append(n)
    return tinycss2.serialize(out)
new_css = [drop_kf(c) for c in new_css]

# ---- custom properties nobody reads
all_css = "\n".join(new_css)
defined = set(re.findall(r"(?<![\w-])(--[\w-]+)\s*:", all_css))
read = set(re.findall(r"var\(\s*(--[\w-]+)", all_css + other)) | set(re.findall(r"[\"'`](--[\w-]+)[\"'`]", other))
dead_props = sorted(p for p in defined if p not in read)
for p in dead_props:
    for i, c in enumerate(new_css):
        c2, k = re.subn(r"(?<![\w-])" + re.escape(p) + r"\s*:[^;{}]*;?", "", c)
        stats["props"] += k; new_css[i] = c2
removed_names += ["prop " + p for p in dead_props]

# ---- write back (styles replaced from the end so offsets hold)
for (a, b, _), c in sorted(zip(styles, new_css), key=lambda t: -t[0][0]):
    h = h[:a] + c + h[b:]
for c in new_css:   # must still parse cleanly
    for n in tinycss2.parse_stylesheet(c):
        assert n.type != "error", n
io.open(OUT, "w", encoding="utf-8", newline="").write(h)
print(stats)
print("CSS chars %d -> %d" % (sum(len(s[2]) for s in styles), sum(len(c) for c in new_css)))
for x in removed_names[:40]: print("  -", x)
print("  ... %d removed in all" % len(removed_names))
