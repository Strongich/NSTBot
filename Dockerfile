FROM python:3.11 AS bot
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04
ENV TOKEN=${TOKEN}

RUN apt-get update && apt-get install -y libpq-dev build-essential
RUN apt-get install -y python3.11 python3-pip python3-dev build-essential python3-venv
RUN pip install --upgrade pip
WORKDIR /app
COPY . /app
RUN chmod +x /app/src/bot.py
# Seting the Assistant to GPU, if it's possible
RUN CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
RUN pip install --no-cache-dir -r requirements.txt

CMD python3 src/bot.py
