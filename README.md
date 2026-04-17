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
![Alt Text](./Screenshot/Screenshot%20From%202026-04-18%2001-20-57.png)
![Alt Text](./Screenshot/Screenshot%20From%202026-04-18%2001-24-52.png)
![Alt Text](./Screenshot/Screenshot%20From%202026-04-18%2001-25-12.png)
![Alt Text](./Screenshot/Screenshot%20From%202026-04-18%2001-25-59.png)
![Alt Text](./Screenshot/Screenshot%20From%202026-04-18%2001-26-28.png)
![Alt Text](./Screenshot/Screenshot%20From%202026-04-18%2001-28-40.png)
![Alt Text](./Screenshot/Screenshot%20From%202026-04-18%2001-29-02.png)
![Alt Text](./Screenshot/Screenshot%20From%202026-04-18%2001-29-27.png)

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

