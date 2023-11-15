from langchain.llms import LlamaCpp

def get_llm():
    llm = LlamaCpp(
        model_path="./model/mistral-7b-instruct-v0.1.Q5_K_M.gguf",
        temperature=0,
        max_tokens=8192,
        use_mmap=True,
        use_mlock=False,
        n_ctx=1024,
        n_gpu_layers=30,
        n_batch=512,
        verbose=True)
    return llm