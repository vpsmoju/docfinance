# Use uma imagem base oficial do Python
FROM python:3.12-slim

# Define usuário não-root para OpenShift
USER 1001

# Define o diretório de trabalho
WORKDIR /app

# Copia os requisitos primeiro para aproveitar o cache
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput

# Expõe a porta
EXPOSE 8000

# Comando para iniciar
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]