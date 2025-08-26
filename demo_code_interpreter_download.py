#!/usr/bin/env python3
"""
Demo: Responses API + Code Interpreter (Azure OpenAI)
- Creates a file in a sandboxed container via Code Interpreter.
- Parses annotations to find container_id/file_id/filename.
- Downloads the file to ./downloads/

Requires:
  pip install --upgrade openai azure-identity
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

from openai import AzureOpenAI, get_bearer_token_provider  # type: ignore
from azure.identity import DefaultAzureCredential  # type: ignore

# ---------------------------
# Configuration (edit me)
# ---------------------------
ENDPOINT = "https://<resource-name>.openai.azure.com/openai/v1/"
API_VERSION = "preview"
DEPLOYMENT = "gpt-4o"

# Auth mode: Entra ID (recommended) by default. Flip to True to use API key.
USE_API_KEY = False
AZURE_OPENAI_API_KEY = "<paste-api-key-here-if-you-switch-to-key-mode>"
SCOPE = "https://cognitiveservices.azure.com/.default"

DOWNLOAD_DIR = Path("./downloads")


def print_step(i: int, total: int, msg: str) -> None:
    print(f"[{i}/{total}] {msg}")


def print_kv(key: str, value: Any) -> None:
    print(f"  - {key}: {value}")


def get_client() -> AzureOpenAI:
    if USE_API_KEY:
        print("Auth: API key mode")
        return AzureOpenAI(base_url=ENDPOINT, api_key=AZURE_OPENAI_API_KEY, api_version=API_VERSION)
    print("Auth: Microsoft Entra ID (DefaultAzureCredential)")
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), SCOPE)
    return AzureOpenAI(base_url=ENDPOINT, azure_ad_token_provider=token_provider, api_version=API_VERSION)


def collect_file_annotations(obj: Any) -> List[Dict[str, Any]]:
    """Recursively search for dict-like annotations containing file metadata.
    Returns a list of dicts with keys: filename, file_id, container_id.
    """
    results: List[Dict[str, Any]] = []

    def walk(x: Any) -> None:
        # Dict branch
        if isinstance(x, dict):
            if "file_id" in x:
                results.append({
                    "filename": x.get("filename") or x.get("path") or "unknown",
                    "file_id": x.get("file_id"),
                    "container_id": x.get("container_id"),
                })
            for v in x.values():
                walk(v)
            return

        # Iterable branch
        if isinstance(x, (list, tuple, set)):
            for v in x:
                walk(v)
            return

        # Object branch
        for attr in ("annotations", "content", "output", "message", "messages"):
            if hasattr(x, attr):
                try:
                    walk(getattr(x, attr))
                except Exception:
                    pass

        # Some SDK objects expose __dict__
        if hasattr(x, "__dict__"):
            try:
                walk(vars(x))
            except Exception:
                pass

    walk(obj)

    # Deduplicate by file_id
    seen = set()
    dedup: List[Dict[str, Any]] = []
    for r in results:
        fid = r.get("file_id")
        if fid and fid not in seen:
            seen.add(fid)
            dedup.append(r)
    return dedup


def print_table(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print("  (no rows)")
        return
    headers = ["filename", "file_id", "container_id"]
    widths = {h: max(len(h), max(len(str(r.get(h, ''))) for r in rows)) for h in headers}
    def fmt_row(r: Dict[str, Any]) -> str:
        return " | ".join(str(r.get(h, "")).ljust(widths[h]) for h in headers)
    print(fmt_row({h: h for h in headers}))
    print("-+-".join("-" * widths[h] for h in headers))
    for r in rows:
        print(fmt_row(r))


def main() -> None:
    total_steps = 5

    print_step(1, total_steps, "Initialize client and show config")
    print_kv("Endpoint", ENDPOINT)
    print_kv("API version", API_VERSION)
    print_kv("Deployment", DEPLOYMENT)
    client = get_client()

    print_step(2, total_steps, "Create response (Code Interpreter: auto container)")
    instructions = (
        "You are a personal assistant that writes and runs code using the Python tool to answer the question."
    )
    try:
        response = client.responses.create(
            model=DEPLOYMENT,
            tools=[{"type": "code_interpreter", "container": {"type": "auto"}}],
            instructions=instructions,
            input="Please use the Python tool to create a file called test.txt and write the word 'hello world' to it.",
        )
    except Exception as e:
        print(f"   ❌ Failed to create response: {e}")
        sys.exit(1)

    # Basic response summary (best-effort – fields vary by SDK version)
    resp_id = getattr(response, "id", None) or "<unknown>"
    print_kv("Response ID", resp_id)

    # The SDK often provides consolidated text via 'output_text'
    output_text = getattr(response, "output_text", None)
    if output_text:
        preview = (output_text[:120] + "...") if len(output_text) > 120 else output_text
        print_kv("Assistant says", preview)

    print_step(3, total_steps, "Scan annotations for created files")
    files = collect_file_annotations(response.output)
    if not files:
        print("   ❌ No files found in annotations. Re-run or inspect the response in the notebook.")
        sys.exit(1)

    print_table(files)

    print_step(4, total_steps, "Retrieve file content and save to ./downloads")
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    for fmeta in files:
        filename = fmeta.get("filename") or "unnamed.bin"
        file_id = fmeta.get("file_id")
        container_id = fmeta.get("container_id")
        if not (file_id and container_id):
            print(f"   ⚠️  Skipping missing metadata: {fmeta}")
            continue

        try:
            retrieved = client.containers.files.content.retrieve(
                container_id=container_id,
                file_id=file_id,
            )
        except Exception as e:
            print(f"   ❌ Failed to retrieve file content for {filename}: {e}")
            continue

        # Resolve bytes payload
        data = None
        for attr in ("content", "body", "data"):
            if hasattr(retrieved, attr):
                data = getattr(retrieved, attr)
                break
        if data is None:
            # Some SDKs can return raw bytes already
            if isinstance(retrieved, (bytes, bytearray)):
                data = bytes(retrieved)
            else:
                print(f"   ❌ Could not locate bytes on retrieved object for {filename}.")
                continue

        out_path = DOWNLOAD_DIR / filename
        try:
            with open(out_path, "wb") as fh:
                fh.write(data)
        except Exception as e:
            print(f"   ❌ Failed to write file {out_path}: {e}")
            continue

        print(f"   ✅ Saved: {out_path.resolve()}  ({len(data)} bytes)")

    print_step(5, total_steps, "Quick verification")
    for p in DOWNLOAD_DIR.glob("*"):
        try:
            if p.suffix.lower() in {".txt", ".csv", ".md"} and p.stat().st_size < 1024 * 64:
                first_line = p.read_text(errors="replace").splitlines()[0] if p.read_text(errors="replace") else ""
                print(f"   {p.name}: '{first_line[:80]}'")
            else:
                print(f"   {p.name}: {p.stat().st_size} bytes")
        except Exception as e:
            print(f"   ⚠️  Could not read {p.name}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
