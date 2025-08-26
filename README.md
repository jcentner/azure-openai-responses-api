# Downloading files from Azure OpenAI Responses API (Code Interpreter) — Python

A simple example that creates a response with the Code Interpreter tool and downloads all files produced by that run.

Reference documentation: [Azure OpenAI Responses API - Code Interpreter](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses?tabs=python-secure#code-interpreter)

## Requirements
- Python 3.9+
- Azure subscription with an Azure OpenAI resource
- Auth via `DefaultAzureCredential` (e.g., `az login`, Managed Identity, etc.) or replace the token provider with an api-key in the client setup.
- Python packages:
~~~
pip install openai azure-identity
~~~

## Configure
Edit the script and set your endpoint:
~~~
endpoint = "https://<resource-name>.openai.azure.com/openai/v1/"
~~~

## Run
~~~
python simple-code-interpreter-file-download.py
~~~

## What you’ll see (example)
~~~
Creating response...

Full response.output:
[ ... trimmed SDK objects ... ]

Found file: filename='test.txt', file_id='file_abc123', container_id='ctr_xyz789'
Downloading file_id=file_abc123 from container_id=ctr_xyz789...
Saved: /path/to/repo/downloads/test.txt
~~~

## Where files go
Files are written to a local `downloads/` folder next to the script. If multiple files are produced, each is downloaded.

## How it works (very briefly)
1. Creates a `responses.create(...)` call with the `code_interpreter` tool.
2. Reads `response.output[*].content[*].annotations[*]` to collect `(container_id, file_id, filename)`.
3. Retrieves bytes via `client.containers.files.content.retrieve(...)`.
4. Writes to `downloads/<filename>`.

## Troubleshooting
- **“No files found in annotations.”**
  Ensure your prompt actually **writes a file** in Code Interpreter and that the selected model supports the tool.
- **Auth issues**
  Verify `az login` or your Managed Identity is available to `DefaultAzureCredential`.
