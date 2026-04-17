# FD सलाहकार — Vernacular FD Advisor

> **Hackathon Project** | Making Fixed Deposits simple for first-time users through vernacular AI

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge\&logo=vercel)](https://vernacular-fd-advisor-seven.vercel.app/)
[![Backend](https://img.shields.io/badge/Backend-Render-purple?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

---

## Problem

A user in Gorakhpur sees:

> **“Suryoday Small Finance Bank — 8.50% p.a. — 12M tenor”**

…but doesn’t understand:

* What **p.a.** means
* Whether the bank is **safe**
* How much money they will **actually get**

---

## Solution

**FD सलाहकार** explains everything in **simple Hindi, Tamil, Telugu** — like a trusted friend:

* Explains jargon (p.a., tenure, DICGC)
* Hows exact maturity amount
* Compares banks clearly
* Guides step-by-step FD booking

---

## Features

* **AI Chat (Vernacular)** — Hindi / Tamil / Telugu
* **FD Comparison** — filter, sort, safety tags
* **FD Calculator** — sliders + visual returns
* **Booking Flow** — step-by-step guided form
* **Multilingual UI** — instant language switch

---

## Demo Video

[![Watch Demo]](https://youtu.be/5MkT9rSK2ds)
---

## Screenshots (Flow)

### Compare & Select

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-20-57.png" width="250"/>
  <img src="./Screenshot/Screenshot From 2026-04-18 01-24-52.png" width="250"/>
</p>

### Booking Flow

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-25-12.png" width="250"/>
  <img src="./Screenshot/Screenshot From 2026-04-18 01-25-59.png" width="250"/>
  <img src="./Screenshot/Screenshot From 2026-04-18 01-26-28.png" width="250"/>
</p>

### Confirmation

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-28-40.png" width="250"/>
</p>

### Calculator

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-29-02.png" width="250"/>
</p>

### AI Chat

<p align="center">
  <img src="./Screenshot/Screenshot From 2026-04-18 01-29-27.png" width="250"/>
</p>

---

## Architecture

```
Frontend (React + Vite)
   ↓
Backend (Node + Express)
   ↓
OpenRouter API (AI)
```

---

## Local Setup (Step-by-Step)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/Vernacular-FD-Advisor.git
cd Vernacular-FD-Advisor
```

---

## Backend Setup

```bash
cd Backend
npm install
```

### Create `.env` inside Backend

```env
OPENROUTER_API_KEY=your_secret_key_here
PORT=3001
```

> Never push `.env` to GitHub

---

### Run Backend

```bash
npm start
```

Runs on:

```
http://localhost:3001
```

---

## Frontend Setup

Open new terminal:

```bash
cd Frontend
npm install
```

### Create `.env` inside Frontend

```env
VITE_API_URL=http://localhost:3001
```

---

### Run Frontend

```bash
npm run dev
```

Runs on:

```
http://localhost:5173
```
---

## Test

Open browser:

http://localhost:5173

Try:

* “Safe hai kya?”
* “8.5% ka matlab kya hai?”

---
## Final Output

```
User → Frontend → Backend → AI → Response
```

---
