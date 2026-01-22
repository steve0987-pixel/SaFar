# Railway Deployment Guide

This guide will help you deploy the SaFar AI Travel Assistant to [Railway](https://railway.app/).

## Prerequisites

- [x] Node.js & npm (Verified: Node v24.12.0)
- [ ] Railway CLI
- [ ] Railway Account

## Step 1: Install Railway CLI

Since you have Node.js installed, run the following command to install the Railway CLI globally:

```bash
npm install -g @railway/cli
```

## Step 2: Login to Railway

Authenticate with your Railway account:

```bash
railway login
```

This will open your browser to verify the login.

## Step 3: Initialize Project

Link your local code to a Railway project:

```bash
railway init
```

- Select **"Empty Project"** (or select an existing one if you have checking).
- Give it a name (e.g., `safar-assistant`).

## Step 4: Configure Environment Variables

Your `.env` file contains sensitive keys. You need to upload these to Railway.
You can do this via the [Railway Dashboard](https://railway.app/dashboard) or using the CLI.

**Required Variables:**
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `GROQ_API_KEY`
- `GROQ_MODEL`
- `EMBEDDING_MODEL`
- `DEFAULT_LANGUAGE`

To set them via CLI (example):
```bash
railway variables --set OPENAI_API_KEY=your_key_here
```

## Step 5: Deploy

Once configured, deploy your application:

```bash
railway up
```

Railway will build the Docker container using the `Dockerfile` and start the service based on `railway.json`.

## Utility Commands

- `railway status`: Check deployment status
- `railway logs`: View live logs
- `railway open`: Open the deployed app in browser
