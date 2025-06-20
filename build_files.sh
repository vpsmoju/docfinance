#!/bin/bash

# Instalar dependências
pip install -r requirements.txt

# Coletar arquivos estáticos
python manage.py collectstatic --noinput --clear

# Executar migrações do banco de dados
python manage.py migrate
