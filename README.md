# Azure OpenAI — Responses API + Code Interpreter: download a generated file

This tiny demo shows how to:
1) Ask the **Responses API** (with **Code Interpreter**) to create a file in a sandboxed container.
2) Parse the **annotations** returned by the assistant message to find `container_id`, `file_id`, and `filename`.
3) **Download** the file to your local `./downloads/` folder.

**What’s included**
- `demo_code_interpreter_download.py` — one clean, runnable script with step-by-step console output.
- `demo_code_interpreter_download.ipynb` — a Jupyter version split into cells to visualize each phase.
- `downloads/` — where files will be saved (gitignored).

---

## Prereqs

- Python 3.9+
- Packages:
~~~
pip install --upgrade openai azure-identity
~~~

> The script uses **Microsoft Entra ID** via `DefaultAzureCredential()` by default. There’s a one-line toggle at the top to switch to **API key** if you prefer.

---

## Quick start (script)

1) Open `demo_code_interpreter_download.py` and set these constants at the top:
   - `ENDPOINT` (e.g., `https://<resource-name>.openai.azure.com/openai/v1/`)
   - `API_VERSION` (e.g., `preview`)
   - `DEPLOYMENT` (your model deployment name, e.g., `gpt-4o`)

2) Run:
~~~
python demo_code_interpreter_download.py
~~~

You should see step numbers like `[1/5]`, a table of discovered files, and the final local path. The script asks the model to create a `test.txt` file containing `hello world` and then downloads it to `./downloads/test.txt`.

---

## Notebook option

Start Jupyter and open the notebook:
~~~
jupyter lab
~~~

Then run `demo_code_interpreter_download.ipynb` top-to-bottom to see the same flow in cells.

---

## How it works (short version)

1) Create a Response with:
   - `tools=[{"type":"code_interpreter","container":{"type":"auto"}}]`
   - An instruction that writes a file (e.g., `test.txt`).

2) Inspect the assistant message’s **annotations** to capture:
   - `container_id`
   - `file_id`
   - `filename`

3) Call the container file APIs to **retrieve** and **save** the file locally.

---

## Official docs

Azure AI Foundry — Responses API (Code Interpreter section):  
https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses?tabs=python-secure#code-interpreter

---

## Common hiccups

- **“No files found in annotations.”** Ensure your instruction actually writes a file. Re-run and inspect the notebook cell that prints the annotations.
- **“404/expired container.”** Containers are ephemeral. Re-run the response request if the container has expired.
- **Auth issues.** Confirm your environment works with `DefaultAzureCredential()` (e.g., VS Code sign-in, Azure CLI login). You can also flip the toggle to API-key mode in the script.
