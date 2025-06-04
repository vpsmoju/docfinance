# Install Python dependencies using Python 3.12
python3.12 -m pip install -r requirements.txt

# Collect static files using Python 3.12
python3.12 manage.py collectstatic --noinput --clear
