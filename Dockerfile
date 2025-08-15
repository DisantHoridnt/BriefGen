FROM public.ecr.aws/debian/debian:bookworm-slim

# Minimal build tools for wheels if needed later
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip ca-certificates build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV TZ=Asia/Kolkata
ENV PORT=8000
EXPOSE 8000

RUN mkdir -p /data
ENV BRIEFGEN_DB=/data/briefgen.db

CMD ["python", "-m", "uvicorn", "BriefGenBackend.main:app", "--host", "0.0.0.0", "--port", "8000"]