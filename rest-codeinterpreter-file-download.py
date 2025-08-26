from pathlib import Path
import json
import requests
from openai import get_bearer_token_provider
from azure.identity import DefaultAzureCredential

# --- Azure OpenAI setup ---
endpoint = "https://<resource-name>.openai.azure.com/openai/v1/"
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

# --- Create a response that generates a file via Code Interpreter (REST) ---
instructions = "You write and run Python code to answer the question."
prompt = "Create a file named test.txt with the text 'hello world'."

print("Creating response via REST...")
headers = {"Authorization": f"Bearer {token_provider()}", "Content-Type": "application/json"}
params = {"api-version": "preview"}

resp = requests.post(
    f"{endpoint}responses",
    headers=headers,
    params=params,
    json={
        "model": "gpt-4o",
        "tools": [{"type": "code_interpreter", "container": {"type": "auto"}}],
        "instructions": instructions,
        "input": prompt,
    },
    timeout=60,
)

if resp.status_code != 200:
    raise RuntimeError(f"Responses API failed: {resp.status_code} - {resp.text}")

payload = resp.json()
print("\nFull response.output:")
print(json.dumps(payload.get("output"), indent=2))

# --- Parse file references from annotations ---
outdir = Path("downloads")
outdir.mkdir(exist_ok=True)

files = []
for item in payload.get("output", []) or []:
    for block in item.get("content", []) or []:
        for ann in block.get("annotations", []) or []:
            file_id = ann.get("file_id")
            if file_id:
                container_id = ann.get("container_id")
                filename = ann.get("filename")
                print(f"Found file: filename={filename!r}, file_id={file_id!r}, container_id={container_id!r}")
                files.append({"container_id": container_id, "file_id": file_id, "filename": filename})

if not files:
    raise RuntimeError("No files found in annotations.")

# --- Download each file via REST ---
for file in files:
    container_id = file["container_id"]
    file_id = file["file_id"]
    filename = file["filename"] or f"{file_id}.bin"

    url = f"{endpoint}containers/{container_id}/files/{file_id}/content"
    print(f"Downloading file_id={file_id} from container_id={container_id}...")

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            path = outdir / Path(filename).name  # keep filename safe
            with open(path, "wb") as f:
                f.write(r.content)
            print(f"Saved: {path.resolve()}")
        else:
            print(f"Failed to download {filename}, status code: {r.status_code}")
    except Exception as e:
        print(f"Exception while downloading {filename}: {e}")
