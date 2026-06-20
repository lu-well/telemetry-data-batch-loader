FROM python:3.11-slim

# install connector for MySQL
RUN pip install --no-cache-dir mysql-connector-python pandas numpy

# set working directory
WORKDIR /app

# copy files to container
COPY . /app

# run python app
CMD ["python", "batch_uploads.py"]
