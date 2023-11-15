import requests
import os

def is_directory_empty(directory_path='./model/'):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return len(os.listdir(directory_path)) == 0

def download_llm(url='https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q5_K_M.gguf', local_filename='./model/mistral-7b-instruct-v0.1.Q5_K_M.gguf'):
    response = requests.get(url, stream=True)
    with open(local_filename, 'wb') as output_file:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk:
                output_file.write(chunk)
