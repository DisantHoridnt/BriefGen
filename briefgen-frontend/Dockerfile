# Works around Docker Hub/GHCR pull failures: only uses Debian mirrors
FROM public.ecr.aws/debian/debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm ca-certificates git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# optional: speed up installs if you have a lock file
COPY package*.json ./
RUN npm install

COPY . .
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0"]
