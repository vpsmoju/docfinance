#!/bin/bash
set -e

echo "🐍 Python version:"
python3 --version

echo "🚀 Iniciando processo de build do Django..."
echo "📦 Instalando dependências..."
pip3 install -r requirements.txt

echo "🗂️ Coletando arquivos estáticos..."
python3 manage.py collectstatic --noinput

echo "🛠️ Aplicando migrações..."
python3 manage.py migrate

echo "✅ Build finalizado com sucesso!"
