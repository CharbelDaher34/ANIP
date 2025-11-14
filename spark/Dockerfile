FROM apache/spark:4.0.0

USER root

# Install uv from official image
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

# Install Python 3.12 to match Airflow
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --set python3 /usr/bin/python3.12

# Copy package files for caching
COPY pyproject.toml setup.py /opt/anip/
COPY src/ /opt/anip/src/

# Install anip package with ML extras
WORKDIR /opt/anip
RUN uv pip install --system --python python3.12 --reinstall-package blinker -e ".[ml]" && \
    python3.12 -c "import mlflow; print('✅ MLflow installed')" && \
    python3.12 -c "import sklearn; print('✅ scikit-learn installed')"

USER spark

# Set Python 3.12 for Spark workers
ENV PYSPARK_PYTHON=python3.12
ENV PYSPARK_DRIVER_PYTHON=python3.12

# Set PYTHONPATH for Spark
ENV PYTHONPATH="/opt/anip:${PYTHONPATH}"

