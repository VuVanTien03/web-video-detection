FROM python:3.9

WORKDIR /app

# Cài đặt ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Cài đặt dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn
COPY ./app /app

# Tạo thư mục uploads và processed
RUN mkdir -p /app/uploads /app/processed

# Chạy ứng dụng
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
