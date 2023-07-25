FROM python:3-slim
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# COPY ./orders .


# ENTRYPOINT ["/code/entrypoint.sh"]
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "stocks_products.wsgi:application"]