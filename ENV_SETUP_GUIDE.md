# Environment Variables Configuration Guide for AMRUT Chatbot

This guide explains all the environment variables needed for the AMRUT Chatbot, including how to obtain the required secrets.

---

## 🔹 Vector Database Configuration

### Option 1: Using Weaviate (Self-Hosted - Recommended)

```bash
# Vector Database Selection
VECTOR_DB_TYPE=weaviate

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=  # Leave empty for local instances
WEAVIATE_COLLECTION_NAME=AmrutChatbotDocs
```

**How to set up Weaviate:**

1. **Local Setup (Docker - No API Key Needed)**
   ```bash
   docker run -d \
     -p 8080:8080 \
     -p 50051:50051 \
     --name weaviate \
     semitechnologies/weaviate:latest
   ```
   - ✅ No API key required
   - ✅ Free to use
   - ✅ Runs on your machine
   - Set `WEAVIATE_URL=http://localhost:8080`
   - Leave `WEAVIATE_API_KEY` empty

2. **Cloud Setup (Weaviate Cloud Services)**
   - Go to: https://console.weaviate.cloud/
   - Sign up for a free account
   - Create a new cluster
   - Copy the cluster URL → Set as `WEAVIATE_URL`
   - Copy the API key → Set as `WEAVIATE_API_KEY`

---

### Option 2: Using Pinecone (Cloud-Hosted)

```bash
# Vector Database Selection
VECTOR_DB_TYPE=pinecone

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_index_name
PINECONE_REGION=us-east-1
PINECONE_HOST=your_pinecone_host
```

**How to get Pinecone credentials:**

1. Go to: https://www.pinecone.io/
2. Sign up or log in
3. Navigate to "API Keys" section
4. Copy your API key → Set as `PINECONE_API_KEY`
5. Create an index in the dashboard
6. Copy the index name → Set as `PINECONE_INDEX_NAME`
7. Note the region (e.g., us-east-1) → Set as `PINECONE_REGION`
8. Find the host URL in index details → Set as `PINECONE_HOST`

---

## 🔹 Google Gemini API (Required for AI)

```bash
GEMINI_API_KEY=your_google_gemini_api_key
```

**How to get Gemini API key:**

1. Go to: https://makersuite.google.com/app/apikey
   - OR: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key → Set as `GEMINI_API_KEY`

**Note:** Free tier includes:
- 60 requests per minute
- 1,500 requests per day

---

## 🔹 WhatsApp Integration (Optional)

```bash
WA_ACCESS_TOKEN=your_whatsapp_access_token
WA_PHONE_NUMBER_ID=your_phone_number_id
```

**How to get WhatsApp credentials:**

1. Go to: https://developers.facebook.com/
2. Create a new app or select existing app
3. Add "WhatsApp" product
4. Navigate to WhatsApp → Getting Started
5. Copy the temporary access token → Set as `WA_ACCESS_TOKEN`
6. Copy the Phone Number ID → Set as `WA_PHONE_NUMBER_ID`

**For production:** Generate a permanent access token from the App Dashboard

---

## 🔹 Guardrails API (Optional)

```bash
GUARDRAILS_API_KEY=your_guardrails_api_key
```

**How to get Guardrails API key:**

1. Go to: https://www.guardrailsai.com/
2. Sign up for an account
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the key → Set as `GUARDRAILS_API_KEY`

---

## 🔹 Supabase Database (Optional)

```bash
SUPABASE_DATABASE_URI=postgresql://user:password@host:port/database
SUPABASE_DB_HOST=your_supabase_host
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=your_username
SUPABASE_DB_PASSWORD=your_password
```

**How to get Supabase credentials:**

1. Go to: https://supabase.com/
2. Create a new project
3. Navigate to Settings → Database
4. Find "Connection String" section
5. Copy connection details:
   - Host → Set as `SUPABASE_DB_HOST`
   - Port → Set as `SUPABASE_DB_PORT` (usually 5432)
   - Database → Set as `SUPABASE_DB_NAME`
   - User → Set as `SUPABASE_DB_USER`
   - Password → Set as `SUPABASE_DB_PASSWORD`
   - Full URI → Set as `SUPABASE_DATABASE_URI`

---

## 🔹 OpenWeather API (Optional)

```bash
OPENWEATHER_API_KEY=your_openweather_api_key
```

**How to get OpenWeather API key:**

1. Go to: https://openweathermap.org/api
2. Sign up for a free account
3. Navigate to API Keys section
4. Copy your API key → Set as `OPENWEATHER_API_KEY`

**Note:** Free tier includes 60 calls/minute

---

## 🔹 Other Configuration

```bash
ORGANIZATION_NAME=YourOrganizationName
NAMESPACE=default_namespace
```

- `ORGANIZATION_NAME`: Your organization or project name
- `NAMESPACE`: Default namespace for document organization (can be any string)

---

## ✅ Minimal Setup (Quick Start)

For testing the Weaviate integration, you only need:

```bash
# Required
GEMINI_API_KEY=your_google_gemini_api_key

# Vector Database (Choose one)
VECTOR_DB_TYPE=weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=  # Leave empty for local Docker setup
WEAVIATE_COLLECTION_NAME=AmrutChatbotDocs

# Optional
ORGANIZATION_NAME=AMRUT
NAMESPACE=default
```

---

## 📋 Complete .env Template

```bash
# ============================================
# AMRUT Chatbot Environment Variables
# ============================================

# Google Gemini API (Required)
GEMINI_API_KEY=

# Vector Database Selection (Required)
VECTOR_DB_TYPE=weaviate  # Options: "weaviate" or "pinecone"

# Weaviate Configuration (if VECTOR_DB_TYPE=weaviate)
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
WEAVIATE_COLLECTION_NAME=AmrutChatbotDocs

# Pinecone Configuration (if VECTOR_DB_TYPE=pinecone)
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
PINECONE_REGION=
PINECONE_HOST=

# WhatsApp Integration (Optional)
WA_ACCESS_TOKEN=
WA_PHONE_NUMBER_ID=

# Guardrails (Optional)
GUARDRAILS_API_KEY=

# Supabase Database (Optional)
SUPABASE_DATABASE_URI=
SUPABASE_DB_HOST=
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=
SUPABASE_DB_PASSWORD=

# OpenWeather API (Optional)
OPENWEATHER_API_KEY=

# General Configuration
ORGANIZATION_NAME=AMRUT
NAMESPACE=default
```

---

## 🚀 Quick Start Steps

1. **Copy the template above** into your `.env` file
2. **Get Gemini API key** (Required): https://makersuite.google.com/app/apikey
3. **Start Weaviate** (Recommended):
   ```bash
   docker run -d -p 8080:8080 -p 50051:50051 --name weaviate semitechnologies/weaviate:latest
   ```
4. **Test the setup**:
   ```bash
   python examples/vector_db_weaviate_example.py
   ```

---

## 🔒 Security Best Practices

- ✅ Never commit `.env` file to version control
- ✅ Add `.env` to `.gitignore`
- ✅ Use different API keys for development and production
- ✅ Rotate API keys periodically
- ✅ Keep production credentials in secure vault services

---

## 🆘 Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'weaviate'`
- **Solution:** Run `pip install weaviate-client==4.9.3`

**Issue:** `Connection refused` to Weaviate
- **Solution:** Make sure Docker container is running: `docker ps | grep weaviate`

**Issue:** `Invalid API key` for Gemini
- **Solution:** Regenerate key at https://makersuite.google.com/app/apikey

**Issue:** Pinecone errors
- **Solution:** Verify API key and index name in Pinecone dashboard
