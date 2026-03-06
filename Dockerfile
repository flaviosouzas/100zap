FROM python:3.11-slim

WORKDIR /app

# Instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do bot
COPY botdocker.py .

# Comando para rodar (ajustado para o nome do seu arquivo)
CMD ["python", "botdocker.py"]