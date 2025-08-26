# Full example: downloading file from Response API Code Interpreter

from openai import AzureOpenAI  
from pathlib import Path  

# Define the Azure OpenAI endpoint and auth
endpoint = "https://<resource-name>.openai.azure.com/openai/v1/" 

# Initialise token provider
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

# Initialize the AzureOpenAI client 
client = AzureOpenAI(  
    base_url=endpoint,  
    azure_ad_token_provider = token_provider,
    api_version="preview"  
)  


# Define the instructions for the AI model  
instructions = "You are a personal assistant that writes and runs code using the Python tool to answer the question."  

# Create a response using the client  
try:  
    response = client.responses.create(  
        model="gpt-4o",  
        tools=[  
            {  
                "type": "code_interpreter",  
                "container": {"type": "auto"}  
            }  
        ],  
        instructions=instructions,  
        input="Please use the Python tool to create a file called test.txt and write the word 'hello world' to it.",  
    )  
except Exception as e:  
    raise RuntimeError(f"Failed to create response: {e}")  

print(response.output)

print("\nWorking on file download...")

container_id = None
file_id = None
filename = None

for output_item in response.output:
    if hasattr(output_item, 'content'):
        for content_block in output_item.content:
            if hasattr(content_block, 'annotations') and content_block.annotations:
                for annotation in content_block.annotations:
                    if hasattr(annotation, 'file_id'):
                        container_id = getattr(annotation, 'container_id', None)
                        file_id = getattr(annotation, 'file_id', None) 
                        filename = getattr(annotation, 'filename', None)
                        break

if not file_id:
    print("   ❌ No files found in annotations")

# Validate extracted information  
if not container_id or not file_id or not filename:  
    raise ValueError("Invalid container or file information.")  

# Retrieve the file info from the container  
try:  
    file_retrieved = client.containers.files.list(  
        container_id=container_id
    )  
except Exception as e:  
    raise RuntimeError(f"Failed to retrieve file content: {e}")  

# Retrieve the file content from the container  
try:  
    file_retrieved = client.containers.files.content.retrieve(  
        container_id=container_id,  
        file_id=file_id  
    )  
except Exception as e:  
    raise RuntimeError(f"Failed to retrieve file content: {e}")  

# Ensure the file content is retrieved  
if not file_retrieved or not file_retrieved.content:  
    raise ValueError("File content could not be retrieved.")  

# Create a directory for downloads if it doesn't exist  
download_dir = Path("./downloads")  
download_dir.mkdir(exist_ok=True)  

# Define the file path for saving the retrieved file  
file_path = download_dir / filename  

# Save the retrieved file content to the specified path  
try:  
    with open(file_path, 'wb') as f:  
        f.write(file_retrieved.content)  
except Exception as e:  
    raise RuntimeError(f"Failed to write file content: {e}")  

print(f"File '{filename}' has been successfully downloaded to '{file_path}'.")  
