from pathlib import Path
from openai import AzureOpenAI, get_bearer_token_provider
from azure.identity import DefaultAzureCredential

# --- Azure OpenAI setup ---
endpoint = "https://<resource-name>.openai.azure.com/openai/v1/"
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)
client = AzureOpenAI(
    base_url=endpoint,
    azure_ad_token_provider=token_provider,
    api_version="preview",
)

# --- Create a response that generates a file via Code Interpreter ---
instructions = "You write and run Python code to answer the question."
prompt = "Create a file named test.txt with the text 'hello world'."

print("Creating response...")
response = client.responses.create(
    model="gpt-4o",
    tools=[{"type": "code_interpreter", "container": {"type": "auto"}}],
    instructions=instructions,
    input=prompt,
)

print("\nFull response.output:")
print(response.output)

# --- Parse file references from annotations ---
outdir = Path("downloads")
outdir.mkdir(exist_ok=True)

files = []
for item in response.output:
    for block in getattr(item, "content", []):
        for ann in getattr(block, "annotations", []) or []:
            if getattr(ann, "file_id", None):
                container_id = getattr(ann, "container_id", None)
                file_id = getattr(ann, "file_id", None)
                filename = getattr(ann, "filename", None)
                print(f"Found file: filename={filename!r}, file_id={file_id!r}, container_id={container_id!r}")
                files.append((container_id, file_id, filename))

if not files:
    raise RuntimeError("No files found in annotations.")

# --- Download each file ---
for container_id, file_id, filename in files:
    print(f"Downloading file_id={file_id} from container_id={container_id}...")
    obj = client.containers.files.content.retrieve(
        container_id=container_id,
        file_id=file_id,
    )
    data = getattr(obj, "content", None)
    name = (filename or getattr(obj, "filename", None) or f"{file_id}.bin")
    path = outdir / Path(name).name  # keep filename safe
    if not data:
        raise RuntimeError(f"Empty content for file_id={file_id}")
    with open(path, "wb") as f:
        f.write(data)
    print(f"Saved: {path.resolve()}")
