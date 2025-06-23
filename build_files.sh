#!/bin/bash
set -e

echo "🐍 Python version:"
/python312/bin/python --version

echo "🚀 Iniciando processo de build do Django..."

echo "📦 Instalando dependências..."
/python312/bin/pip install -r requirements.txt

echo "🗂️ Coletando arquivos estáticos..."
/python312/bin/python manage.py collectstatic --noinput

echo "🛠️ Aplicando migrações..."
/python312/bin/python manage.py migrate

echo "✅ Build finalizado com sucesso!"
