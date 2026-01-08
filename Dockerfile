# Use uma imagem base oficial do Python
FROM python:3.12-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para compilar pacotes Python (ex: psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia todo o código para o container
COPY . .

# Instala as dependências a partir do pyproject.toml
RUN pip install --no-cache-dir .

# Expõe a porta
EXPOSE 8000

# Comando para iniciar
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
