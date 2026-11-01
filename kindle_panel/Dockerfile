FROM python:3.13-alpine
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
COPY server.py ui.py icons.py mdi-icons.json mdi-icons-source.json ha_dashboard.py live.js panel.js ICON-LICENSE.txt /app/
EXPOSE 8080 8099
CMD ["python3", "-u", "/app/server.py"]
