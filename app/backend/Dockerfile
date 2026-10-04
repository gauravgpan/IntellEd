FROM python:3.12-slim

WORKDIR /app

# No system MySQL client libs needed: requirements.txt uses PyMySQL, a
# pure-Python driver (registered as MySQLdb in config/__init__.py).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
