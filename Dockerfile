# Use uma imagem base oficial do Python
FROM python:3.12-slim

# Define diretório de trabalho
WORKDIR /app

# Copia os requisitos primeiro para aproveitar o cache
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Expõe a porta
EXPOSE 8000

# Comando para iniciar (desenvolvimento)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
