# Downloading files from Azure OpenAI Responses API (Code Interpreter) — Python

Simple examples (REST API, openai python SDK) that create a response with the Code Interpreter tool and download all files produced by that run.

Reference documentation: [Azure OpenAI Responses API - Code Interpreter](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses?tabs=python-secure#code-interpreter)


## Requirements
- Python 3.9+
- Azure subscription with an Azure OpenAI resource
- Auth via `DefaultAzureCredential` (e.g., `az login`, Managed Identity, etc.); alternatively, replace the token provider with an api-key to your resource.
- Python packages:
~~~
pip install requests openai azure-identity
~~~

## Configure
Edit each script and set your endpoint:
~~~
endpoint = "https://<resource-name>.openai.azure.com/openai/v1/"
~~~

## Run
SDK sample:
~~~
python sdk-codeinterpreter-file-download.py
~~~

REST sample:
~~~
python rest-codeinterpreter-file-download.py
~~~

## What you’ll see (example)
~~~
Creating response...

Full response.output:
[ ... trimmed SDK/REST objects ... ]

Found file: filename='test.txt', file_id='file_abc123', container_id='ctr_xyz789'
Downloading file_id=file_abc123 from container_id=ctr_xyz789...
Saved: /path/to/repo/downloads/test.txt
~~~

## Where files go
Files are written to a local `downloads/` folder next to the script. If multiple files are produced, each is downloaded.

## How it works (very briefly)
**SDK path**
1. `client.responses.create(...)` with the `code_interpreter` tool.
2. Read `response.output[*].content[*].annotations[*]` for `(container_id, file_id, filename)`.
3. `client.containers.files.content.retrieve(...)` to get bytes.
4. Write to `downloads/<filename>`.

**REST path**
1. `POST {endpoint}responses?api-version=preview` with body specifying `model`, `tools`, `instructions`, and `input`.
2. Parse `output[*].content[*].annotations[*]` for `(container_id, file_id, filename)`.
3. `GET {endpoint}containers/{container_id}/files/{file_id}/content?api-version=preview` for bytes.
4. Write to `downloads/<filename>`.

## Troubleshooting
- **“No files found in annotations.”**
  Ensure your prompt actually **writes a file** in Code Interpreter and that the selected model supports the tool.
- **Auth issues**
  Verify `az login` or your Managed Identity is available to `DefaultAzureCredential`. For REST, ensure the `Authorization: Bearer <token>` header is present and you pass `api-version=preview` on both the POST and GET.
