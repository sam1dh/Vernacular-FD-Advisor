import express from 'express'
import fetch from 'node-fetch'
import cors from 'cors'
import dotenv from 'dotenv'

dotenv.config()

const app  = express()
const PORT = process.env.PORT || 3001

app.use(cors())
app.use(express.json())

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'

// RAG service (Python FastAPI, see /rag). Provides grounded answers with
// citations. Falls back to plain LLM chat when the service is down.
const RAG_SVC_URL = process.env.RAG_SVC_URL || 'http://localhost:8100'

// Free OpenRouter models, tried in order. gpt-3.5-turbo was retired from
// OpenRouter ("no provider serves this model anymore"), so the chat must
// not depend on a single model id. Override via OPENROUTER_MODEL (comma
// separated chain).
const DEFAULT_MODEL_CHAIN = [
  'google/gemma-4-31b-it:free',        // strong Hindi/Tamil/Telugu
  'nvidia/nemotron-3.5-lightning:free',
  'inclusionai/ling-3.2-flash:free',
]
const MODEL_CHAIN = (process.env.OPENROUTER_MODEL || '')
  .split(',')
  .map((m) => m.trim())
  .filter(Boolean)
const CHAT_MODELS = MODEL_CHAIN.length ? MODEL_CHAIN : DEFAULT_MODEL_CHAIN

const LANGUAGE_PROMPTS = {
  hi: `You are a beginner-friendly FD advisor for users in India.

STRICT RULES:
- Always reply in simple Hindi (no English mixing unless user uses English)
- Keep answers VERY SHORT (max 2–3 lines)
- Use simple words like: "paisa", "kamai", "lock", "nikalna"
- Always explain with ₹ example when needed

BEHAVIOR:
- If user is confused → guide step-by-step (ask what they want to do)
- If user asks "kya karu" → suggest next step (amount, time, bank)
- If user asks about safety → explain DICGC ₹5 lakh simply

TONE:
- Be neutral and factual
- DO NOT give advice or recommendations
`,

hi: `You are a beginner-friendly FD advisor for users in India.

STRICT RULES:
- Always reply in simple Hindi (no English mixing unless user uses English)
- Keep answers VERY SHORT (max 2–3 lines)
- Use simple words like: "paisa", "kamai", "lock", "nikalna"
- Always explain with ₹ example when needed

BEHAVIOR:
- If user is confused → guide step-by-step (ask what they want to do)
- If user asks "kya karu" → suggest next step (amount, time, bank)
- If user asks about safety → explain DICGC ₹5 lakh simply

TONE:
- Be neutral and factual
- DO NOT give advice or recommendations
`,
ta: `You are a beginner-friendly FD advisor for users in India.

STRICT RULES:
- Always reply in simple Tamil only (no English mixing unless user uses English)

BEHAVIOR:
- If user is confused → guide step-by-step
- If user asks about safety → explain ₹5 lakh insurance simply

TONE:
- Neutral, no advice

DO NOT:
- give opinions
- mix English unnecessarily
- repeat answers
`,
te: `You are a beginner-friendly FD advisor for users in India.

STRICT RULES:
- Always reply in simple Telugu only (no English mixing unless user uses English)

BEHAVIOR:
- If user is confused → guide step-by-step
- If user asks about safety → explain ₹5 lakh insurance simply

TONE:
- Neutral, no advice

DO NOT:
- give opinions
- mix English unnecessarily
- repeat answers
`,
}

/**
 * POST /api/rag/chat
 * Retrieval-augmented chat: retrieves grounded evidence from the knowledge
 * base (Python RAG service), then answers. Two modes:
 *   - default: extractive answer built from retrieved chunks, with citations
 *   - OPENROUTER_API_KEY set → LLM answers strictly from the retrieved
 *     passages (prompt forbids outside knowledge; reply is discarded and
 *     replaced with the extractive answer if it lacks citation markers)
 */
app.post('/api/rag/chat', async (req, res) => {
  try {
    const { userMessage, language = 'hi' } = req.body
    if (!userMessage?.trim()) {
      return res.status(400).json({ error: 'userMessage is required' })
    }

    const mode = process.env.OPENROUTER_API_KEY ? 'llm' : 'extractive'
    const ragRes = await fetch(`${RAG_SVC_URL}/rag/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: userMessage, language, mode }),
    })

    if (!ragRes.ok) {
      const err = await ragRes.json().catch(() => ({}))
      console.error('RAG service error:', ragRes.status, err)
      return res.status(ragRes.status).json({ error: err.detail || 'RAG service unavailable' })
    }

    const out = await ragRes.json()
    res.json({
      reply: out.answer,
      citations: out.citations,
      abstained: out.abstained,
      confidence: out.confidence,
      mode: out.mode,
      sources: out.retrieved?.slice(0, 3) ?? [],
    })
  } catch (error) {
    console.error('RAG proxy error:', error.message)
    res.status(502).json({ error: 'RAG service unreachable — start it with: python -m rag.server' })
  }
})

/**
 * POST /api/chat
 */
app.post('/api/chat', async (req, res) => {
  try {
    const { userMessage, language = 'hi', fdContext = null } = req.body

    if (!userMessage?.trim()) {
      return res.status(400).json({ error: 'userMessage is required' })
    }

    const apiKey = process.env.OPENROUTER_API_KEY
    if (!apiKey) {
      console.error('OPENROUTER_API_KEY not set in .env')
      return res.status(500).json({ error: 'API key not configured' })
    }

    const systemPrompt = LANGUAGE_PROMPTS[language] || LANGUAGE_PROMPTS.hi

    // Inject FD context into the system prompt so the model knows which FD
    const contextNote = fdContext
      ? `\n\nThe user is currently viewing this Fixed Deposit:\nBank: ${fdContext.bank}\nRate: ${fdContext.rate}% p.a.\nTenor: ${fdContext.tenor} months\nMinimum deposit: ₹${fdContext.minAmount?.toLocaleString('en-IN')}\nType: ${fdContext.type}\nInsured: ${fdContext.fdacInsured ? 'Yes, up to ₹5 lakh (DICGC)' : 'No'}\n\nAnswer questions in the context of this specific FD when relevant.`
      : ''

    const messages = [
      { role: 'system',  content: systemPrompt + contextNote },
      { role: 'user',    content: userMessage },
    ]

    // Try each model in the chain until one responds; free models get
    // rate-limited or retired, so a single model id is a single point of
    // failure.
    let lastErr = null
    for (const model of CHAT_MODELS) {
      const response = await fetch(OPENROUTER_URL, {
        method: 'POST',
        headers: {
          'Content-Type':  'application/json',
          'Authorization': `Bearer ${apiKey}`,
          'HTTP-Referer':  process.env.APP_URL || 'http://localhost:5173',
          'X-Title':       'Vernacular FD Advisor',
        },
        body: JSON.stringify({
          model,
          messages,
          max_tokens:  350,
          temperature: 0.7,
        }),
      })

      if (response.ok) {
        const data  = await response.json()
        const reply = data.choices?.[0]?.message?.content || ''
        return res.json({ reply, model })
      }

      const err = await response.json().catch(() => ({}))
      console.error(`OpenRouter API Error [${model}]:`, err.error?.message || response.status)
      lastErr = err
      // 429/5xx/model-retired → try the next model in the chain
    }

    return res.status(502).json({
      error: lastErr?.error?.message || 'All OpenRouter models failed',
    })

  } catch (error) {
    console.error('Server error:', error.message)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// Health check
app.get('/health', async (_req, res) => {
  let rag = { status: 'unknown' }
  try {
    rag = await (await fetch(`${RAG_SVC_URL}/health`)).json()
  } catch { rag = { status: 'down' } }
  res.json({ status: 'ok', models: CHAT_MODELS, rag })
})

app.listen(PORT, () => {
  console.log(`🚀 Server running  → http://localhost:${PORT}`)
  console.log(`📡 Chat endpoint   → POST http://localhost:${PORT}/api/chat`)
  console.log(`📡 RAG chat        → POST http://localhost:${PORT}/api/rag/chat`)
  console.log(`🔑 Model chain     → ${CHAT_MODELS.join(' | ')}`)
})