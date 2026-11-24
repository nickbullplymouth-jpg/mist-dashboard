# Juniper Mist Organization Stats & Ops Dashboard

Real-time monitoring and statistics web dashboard for Juniper Mist Cloud, configured for the **EU region (`api.eu.mist.com`)**.

---

## 🚀 Quick Setup Locally

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in:
   ```ini
   MIST_HOST=api.eu.mist.com
   MIST_API_TOKEN=your_token_here
   MIST_ORG_ID=your_org_id_here
   PORT=8000
   ```

2. **Install & Run**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Or on Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```
   Open `http://localhost:8000` in your browser.

---

## ☁️ Deploying to AWS Amazon Linux (`18.132.47.78`)

### Option A: Direct SSH & Git Pull (Recommended)

1. **Push this repo to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Mist Org Dashboard"
   git branch -M main
   git remote add origin https://github.com/nickbullplymouth-jpg/<your-repo-name>.git
   git push -u origin main
   ```

2. **SSH into your AWS instance**:
   ```bash
   ssh -i /path/to/your-key.pem ec2-user@18.132.47.78
   ```

3. **Clone & Run the Setup Script**:
   ```bash
   git clone https://github.com/nickbullplymouth-jpg/<your-repo-name>.git mist-dashboard
   cd mist-dashboard
   cp .env.example .env
   nano .env  # Add your MIST_API_TOKEN and MIST_ORG_ID
   chmod +x deploy_amazon_linux.sh
   ./deploy_amazon_linux.sh
   ```

### Option B: Docker Compose

```bash
docker compose up -d --build
```

---

## 🔒 Security Group Note
Make sure the **Security Group** attached to your AWS EC2 instance (`18.132.47.78`) has an **Inbound Rule** allowing TCP port `8000` (or port `80` if mapped) from your IP.
