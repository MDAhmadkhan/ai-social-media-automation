# Installation Guide

## Ubuntu VPS Deployment

1. Install Docker and Compose.

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

2. Configure environment.

```bash
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set `JWT_SECRET`, `ENCRYPTION_KEY`, `PUBLIC_BASE_URL`, `FRONTEND_BASE_URL`, `ALLOWED_ORIGINS`, and at least one AI provider key.

3. Start services.

```bash
docker compose up -d --build
docker compose logs -f backend worker scheduler
```

4. Point DNS at the VPS and replace `server_name _;` in `deploy/nginx/default.conf` with your domain.

5. Add TLS with Certbot or your preferred certificate manager.

## Platform Tokens

Connect platform accounts from the dashboard. Tokens are encrypted before storage. Each provider still requires the correct OAuth scopes from its own developer console:

- Facebook Pages and Instagram Business use Meta Graph API page and media publishing permissions.
- LinkedIn Pages use organization posting permissions.
- X/Twitter uses OAuth 2 bearer access for tweet publishing.
- Threads uses Threads Graph API publishing.
- Pinterest requires a board ID in account metadata.
- Telegram requires a bot token and channel/chat ID.

## Operating Jobs

The scheduler queues website scans every 10 minutes and publishing checks every minute. Celery workers execute those jobs through Redis.

## Backups

Back up MongoDB volumes and the `storage` directory. If S3-compatible storage is enabled in a future adapter configuration, back up the bucket according to your provider policy.
