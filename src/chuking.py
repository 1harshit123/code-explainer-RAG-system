"""
repo_chunker.py
---------------
Drop-in replacement for your AST dump script.
Input  : a cloned GitHub repo path
Output : chunks.json  — list of RAG-ready chunk dicts, one per function/class
"""



from tree_sitter import Language, Parser
import tree_sitter_python
import json
import os
from pathlib import Path


# ── 1. Parser setup ──────────────────────────────────────────────────────────

PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)

with open("demo.py", "r", encoding="utf-8") as f:
        source_code = f.read()
# ── 2. Core extractor ────────────────────────────────────────────────────────

def extract_chunks(source_code: str, filepath: str) -> list[dict]:
    """
    Walk the AST of one Python file.
    Returns one chunk dict per function_definition or class_definition.
    """
    src_bytes = source_code.encode("utf-8")
    tree = parser.parse(src_bytes)

    chunks = []
    _walk(tree.root_node, src_bytes, filepath, chunks, parent_class=None)
    return chunks


def _walk(node, src_bytes: bytes, filepath: str, chunks: list, parent_class: str | None):
    if node.type in ("function_definition", "class_definition"):
        chunk = _build_chunk(node, src_bytes, filepath, parent_class)
        chunks.append(chunk)

        # recurse into classes to also capture their methods
        if node.type == "class_definition":
            for child in node.children:
                _walk(child, src_bytes, filepath, chunks, parent_class=chunk["name"])
        # don't recurse into functions (nested functions are rare, skip for now)
        return

    for child in node.children:
        _walk(child, src_bytes, filepath, chunks, parent_class)


def _build_chunk(node, src_bytes: bytes, filepath: str, parent_class: str | None) -> dict:
    raw_source = src_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")

    name        = _get_name(node, src_bytes)
    signature   = _get_signature(node, src_bytes)
    docstring   = _get_docstring(node, src_bytes)
    calls       = _get_calls(node, src_bytes)
    decorators  = _get_decorators(node, src_bytes)

    # what gets embedded — plain English-friendly, no AST noise
    embed_text = _build_embed_text(
        name, signature, docstring, calls, decorators,
        filepath, parent_class, raw_source
    )

    return {
        "id":           f"{filepath}::{name}",
        "name":         name,
        "type":         "function" if node.type == "function_definition" else "class",
        "parent_class": parent_class,
        "filepath":     filepath,
        "start_line":   node.start_point[0] + 1,
        "end_line":     node.end_point[0] + 1,
        "signature":    signature,
        "docstring":    docstring,
        "decorators":   decorators,
        "calls":        calls,
        "source":       raw_source,
        "embed_text":   embed_text,   # <-- this is what you pass to the embedder
    }


# ── 3. Text format for embedding ─────────────────────────────────────────────

def _build_embed_text(name, signature, docstring, calls, decorators,
                      filepath, parent_class, raw_source) -> str:
    parts = []
    parts.append(f"File: {filepath}")
    if parent_class:
        parts.append(f"Class: {parent_class}")
    parts.append(f"Name: {name}")
    parts.append(f"Signature: {signature}")
    if decorators:
        parts.append(f"Decorators: {', '.join(decorators)}")
    if docstring:
        parts.append(f"Description: {docstring}")
    if calls:
        parts.append(f"Calls: {', '.join(calls[:15])}")  # cap at 15
    parts.append(f"\nSource code:\n{raw_source}")
    return "\n".join(parts)


# ── 4. AST helpers ───────────────────────────────────────────────────────────

def _get_name(node, src_bytes: bytes) -> str:
    for child in node.children:
        if child.type == "identifier":
            return src_bytes[child.start_byte:child.end_byte].decode("utf-8")
    return "unknown"


def _get_signature(node, src_bytes: bytes) -> str:
    """First line of the definition up to and including the colon."""
    raw = src_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
    first_line = raw.split("\n")[0].strip()
    return first_line


def _get_docstring(node, src_bytes: bytes) -> str:
    """First string literal inside the function/class body, if any."""
    body = None
    for child in node.children:
        if child.type == "block":
            body = child
            break
    if not body:
        return ""
    for child in body.children:
        if child.type == "expression_statement":
            for sub in child.children:
                if sub.type == "string":
                    raw = src_bytes[sub.start_byte:sub.end_byte].decode("utf-8", errors="ignore")
                    # strip quotes
                    return raw.strip('"""').strip("'''").strip('"').strip("'").strip()
    return ""


def _get_calls(node, src_bytes: bytes) -> list[str]:
    """All function call names inside this node."""
    calls = set()
    _collect_calls(node, src_bytes, calls)
    return sorted(calls)


def _collect_calls(node, src_bytes: bytes, calls: set):
    if node.type == "call":
        func_node = node.children[0] if node.children else None
        if func_node:
            name = src_bytes[func_node.start_byte:func_node.end_byte].decode("utf-8", errors="ignore")
            # keep it short — drop long attribute chains
            if len(name) < 60:
                calls.add(name)
    for child in node.children:
        _collect_calls(child, src_bytes, calls)


def _get_decorators(node, src_bytes: bytes) -> list[str]:
    decorators = []
    for child in node.children:
        if child.type == "decorator":
            raw = src_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="ignore")
            decorators.append(raw.strip())
    return decorators


# ── 5. Repo walker ───────────────────────────────────────────────────────────

def process_repo(repo_path: str) -> list[dict]:
    """Walk every .py file in the repo and return all chunks."""
    all_chunks = []
    repo_root = Path(repo_path)

    for py_file in repo_root.rglob("*.py"):
        # skip venv / test / migration folders
        parts = py_file.parts
        if any(p in parts for p in ("venv", ".venv", "env", "node_modules", "migrations", "__pycache__")):
            continue

        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            rel_path = str(py_file.relative_to(repo_root))
            chunks = extract_chunks(source, rel_path)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  Skipped {py_file}: {e}")

    return all_chunks


# ── 6. Main ──────────────────────────────────────────────────────────────────

def chuking():
    import sys
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"Processing repo: {repo_path}")
    chunks = process_repo(repo_path)
    print(f"Extracted {len(chunks)} chunks")

    out_path = "chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Saved to {out_path}")

    # quick preview
    if chunks:
        print("\n── Sample chunk (embed_text field) ──")
        print(chunks[0]["embed_text"][:600])

# Exporting chuking function
