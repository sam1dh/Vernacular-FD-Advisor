# 🏦 FD सलाहकार — Vernacular FD Advisor

> **Hackathon Project** | Financial inclusion for rural India through vernacular AI-powered Fixed Deposit guidance

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://your-vercel-url.vercel.app)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite)](https://vitejs.dev)

---

## 📽️ Demo Video

<!-- ═══════════════════════════════════════════════════════════════
     PASTE YOUR DEMO VIDEO LINK OR EMBED HERE
     Example: [![Demo Video](thumbnail.png)](https://youtube.com/your-video)
     Or embed: <video src="demo.mp4" controls width="100%" />
     ═══════════════════════════════════════════════════════════════ -->

> 🎬 *[Video placeholder — add your demo link here]*

---

## 📸 Screenshots

<!-- ═══════════════════════════════════════════════════════════════
     ADD YOUR SCREENSHOTS BELOW
     Recommended: 3–4 images showing different tabs/flows
     Format: ![Alt Text](./screenshots/filename.png)
     ═══════════════════════════════════════════════════════════════ -->

| FD Compare Tab | AI Chat (Hindi) | Calculator |
|:-:|:-:|:-:|
| ![FD List](./screenshots/fd-list.png) | ![Chat UI](./screenshots/chat-hindi.png) | ![Calculator](./screenshots/calculator.png) |

> 📷 *[Screenshot placeholders — add your images to a `/screenshots` folder]*

---

## 🎯 The Problem We Solve

A person in Gorakhpur sees **"Suryoday Small Finance Bank — 8.50% p.a. — 12M tenor"** and has no idea what it means. They don't know:
- What "p.a." means
- Whether a Small Finance Bank is safe
- How much money they'll actually get at the end

**FD सलाहकार** solves this by explaining everything in plain Hindi, Tamil, or Telugu — the way a trusted friend would.

---

## ✨ Features

### 💬 Vernacular AI Advisor
- Powered by **Claude (Anthropic API)** with language-specific system prompts
- Responds in simple, everyday Hindi / Tamil / Telugu
- Explains jargon like "p.a.", "tenor", "DICGC", "compounding" with ₹ examples
- Context-aware: links to the specific FD the user is viewing

### 🏦 FD Comparison Table
- 15 real Indian banks: SBI, HDFC, Suryoday SFB, Ujjivan SFB, and more
- Filter by: Government / Private / Small Finance / High Rate / Safest
- Sort by: Interest Rate / Safety / Minimum Amount
- One-tap "Ask AI" to open the chat pre-loaded with that bank's context

### 🧮 FD Calculator
- Interactive sliders for principal (₹1K–₹5L), tenor (3–60 months), rate (4–10%)
- Monthly / Quarterly / Yearly compounding
- Visual growth bar showing principal vs. interest split
- Jargon pill buttons — tap any term to instantly ask the AI advisor

### ✅ Booking Flow
- Step-by-step guided form to "open" an FD (demo mode)
- Pre-filled when arriving from an FD card's "Book Now" button
- Confirmation screen with summary

### 🌐 3-Language Support
- **Hindi (हिन्दी)** — primary target (UP, Bihar, MP)
- **Tamil (தமிழ்)** — South India coverage
- **Telugu (తెలుగు)** — Andhra/Telangana
- Instant language switching via header toggle

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              React + Vite Frontend           │
│                                             │
│  App.jsx ──► FDList ──► FDCard             │
│           ──► ChatUI ──► useChat hook       │
│           ──► Calculator                   │
│           ──► BookingFlow                  │
└───────────────────┬─────────────────────────┘
                    │ HTTP POST /api/chat
┌───────────────────▼─────────────────────────┐
│           Express.js Backend (Node)          │
│                                             │
│  server.js ──► Language prompt selector    │
│             ──► FD context injector        │
│             ──► OpenRouter / Anthropic API  │
└─────────────────────────────────────────────┘
```

**Key files:**

| File | Purpose |
|---|---|
| `src/App.jsx` | Root — tab routing, language state, FD context passing |
| `src/components/ChatUI.jsx` | Chat interface with jargon pills & quick questions |
| `src/components/FDList.jsx` | Filterable/sortable FD card grid |
| `src/components/FDCard.jsx` | Individual FD card with maturity estimate |
| `src/components/Calculator.jsx` | FD maturity calculator with visual bar |
| `src/components/BookingFlow.jsx` | Multi-step FD opening form |
| `src/api/gemini.js` | API client + quick questions + jargon config |
| `src/hooks/useChat.js` | Chat state, message history, API calls |
| `src/data/fds.json` | FD data for 15 banks |
| `server.js` | Express backend — language prompts & AI proxy |

---

## 🚀 Local Development Setup

### Prerequisites

- Node.js 18+ (`node --version`)
- npm 9+ (`npm --version`)
- An API key from [OpenRouter](https://openrouter.ai) (free tier available) **OR** [Anthropic](https://console.anthropic.com)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/fd-advisor.git
cd fd-advisor
```

### 2. Set up the Backend

```bash
cd backend          # or wherever your server.js lives
npm install
```

Create a `.env` file in the backend folder:

```env
# .env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PORT=3001
APP_URL=http://localhost:5173
```

> 💡 **Free API option:** Sign up at [openrouter.ai](https://openrouter.ai) and use model `mistralai/mistral-7b-instruct:free` — no credits needed.

Start the backend:

```bash
npm run dev
# Server running → http://localhost:3001
```

### 3. Set up the Frontend

Open a new terminal:

```bash
cd frontend         # or wherever your src/ folder lives
npm install
```

Create a `.env` file in the frontend folder:

```env
# .env
VITE_API_URL=http://localhost:3001
```

Start the frontend:

```bash
npm run dev
# App running → http://localhost:5173
```

### 4. Open the app

Visit **http://localhost:5173** in your browser. You should see the FD सलाहकार app in Hindi by default.

---

## ☁️ Deployment Guide

### Option A: Vercel (Recommended — Free, 5 minutes)

Vercel can host both the frontend and the backend as serverless functions.

#### Step 1 — Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

#### Step 2 — Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repository
3. Set the **Root Directory** to your frontend folder (e.g., `frontend/`)
4. Vercel auto-detects Vite — click **Deploy**
5. Add Environment Variable:
   - Key: `VITE_API_URL`
   - Value: `https://your-backend-url.vercel.app` *(set after backend deploy)*

#### Step 3 — Deploy Backend to Vercel

1. In the same project or a new one, set Root Directory to `backend/`
2. Add Environment Variables:
   - `OPENROUTER_API_KEY` = your API key
   - `APP_URL` = your frontend Vercel URL
3. Deploy

> ⚠️ **Important:** Update `VITE_API_URL` in the frontend's Vercel env to point to the deployed backend URL, then redeploy frontend.

---

### Option B: Render (Free Tier — Easier for Express backend)

#### Backend on Render

1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect your GitHub repo, set root to `backend/`
3. Build command: `npm install`
4. Start command: `node server.js`
5. Add env vars: `OPENROUTER_API_KEY`, `PORT=3001`
6. Deploy → copy the public URL (e.g., `https://fd-advisor-api.onrender.com`)

#### Frontend on Vercel (same as Option A Step 2)

Set `VITE_API_URL=https://fd-advisor-api.onrender.com`

---

### Option C: Railway (Simplest full-stack)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Set environment variables in the Railway dashboard.

---

### CORS Note for Production

When both frontend and backend are deployed, update `server.js` to allow your Vercel domain:

```js
app.use(cors({
  origin: ['https://your-app.vercel.app', 'http://localhost:5173']
}))
```

---

## 🔑 Environment Variables Reference

### Backend (`server.js`)

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ Yes | Your OpenRouter or Anthropic API key |
| `PORT` | No | Port for Express server (default: 3001) |
| `APP_URL` | No | Frontend URL for CORS/referrer header |

### Frontend (`vite`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ✅ Yes | Backend URL (e.g., `http://localhost:3001`) |

---

## 🧠 AI Prompt Design

The system prompt is the heart of the vernacular experience. Key principles:

```
You are a beginner-friendly FD advisor for users in India.
- Reply in simple Hindi (no English jargon)
- Keep answers SHORT (max 2–3 lines)
- Use simple words: "paisa", "kamai", "lock", "nikalna"
- Always give a ₹ example
- NEVER say "best hai" or give recommendations
- Be factual and neutral
```

**FD context injection:** When a user taps "Ask AI" on an FD card, the card's data (bank name, rate, tenor, DICGC status) is appended to the system prompt so Claude answers about *that specific FD*.

---

## 📊 Data Sources

FD interest rates in `src/data/fds.json` are based on **April 2025** published rates. Always verify with the bank before investing.

Banks included: Suryoday SFB, Ujjivan SFB, Jana SFB, Equitas SFB, AU SFB, IDFC First, Yes Bank, RBL Bank, Kotak Mahindra, HDFC Bank, ICICI Bank, Axis Bank, SBI, PNB, Bank of Baroda.

---

## 🗺️ Roadmap (Post-Hackathon)

- [ ] Add Tamil language prompts to backend
- [ ] Voice input using Web Speech API (for low-literacy users)
- [ ] Real-time rate updates via bank APIs / web scraping
- [ ] WhatsApp Bot integration (most accessible channel in rural India)
- [ ] Offline mode with service workers (poor connectivity areas)
- [ ] Flutter mobile app (for Android-first rural users)

---

## 👥 Team

<!-- ═══════════════════════════════════════════════════════════════
     ADD YOUR TEAM MEMBER NAMES, ROLES, AND LINKS
     ═══════════════════════════════════════════════════════════════ -->

| Name | Role | GitHub |
|---|---|---|
| [Your Name] | Full Stack + AI | [@username](https://github.com/username) |
| [Teammate 2] | UI/UX Design | [@username](https://github.com/username) |
| [Teammate 3] | Research | [@username](https://github.com/username) |

---

## 🏆 Hackathon Submission

- **Event:** *[Hackathon Name — e.g., Smart India Hackathon 2025]*
- **Track:** *[e.g., Financial Inclusion / Rural Technology]*
- **Team Name:** *[Your Team Name]*
- **Submission Date:** *[Date]*

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ for rural India | <b>FD सलाहकार</b>
</p>
