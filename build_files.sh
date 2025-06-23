#!/bin/bash

# Encerra o script se qualquer comando falhar
set -e

# Exibe a versão do Python em uso (debug)
echo "🐍 Python version:"
python --version || python3 --version

# Mensagem de início do build
echo "🚀 Iniciando processo de build do Django..."

# Instala as dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Coleta dos arquivos estáticos
echo "🗂️ Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Executa as migrações do banco de dados
echo "🛠️ Aplicando migrações..."
python manage.py migrate

# Fim
echo "✅ Build finalizado com sucesso!"
