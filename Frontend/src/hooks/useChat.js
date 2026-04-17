import { useState, useCallback, useEffect } from 'react'
import { askAdvisor } from '../api/gemini'

function timestamp() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const WELCOME = {
  hi: 'नमस्ते! मैं आपका FD सलाहकार हूँ। आप मुझसे Fixed Deposit के बारे में कोई भी सवाल पूछ सकते हैं। 😊',
  ta: 'வணக்கம்! நான் உங்கள் FD ஆலோசகர். Fixed Deposit பற்றி எந்த கேள்வியும் கேளுங்கள். 😊',
  te: 'నమస్కారం! నేను మీ FD సలహాదారుడిని. Fixed Deposit గురించి ఏదైనా అడగండి. 😊',
}

const FEEDBACK = {
  hi: 'क्या confusing लगा? मैं मदद करता हूँ 🙂',
  ta: 'குழப்பமாக இருந்தால் சொல்லுங்கள். நான் உதவுகிறேன் 🙂',
  te: 'గందరగోళం ఉంటే చెప్పండి. నేను సహాయం చేస్తాను 🙂',
}

export function useChat(language = 'hi', fdContext = null) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: WELCOME[language] || WELCOME.hi,
      time: timestamp(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  /* Update welcome message when language changes */
  useEffect(() => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        text: WELCOME[language] || WELCOME.hi,
        time: timestamp(),
      },
    ])
  }, [language])

function detectIntent(msg) {
  const m = msg.toLowerCase()

  if (m.includes('easy') || m.includes('confusing') || m.includes('problem')) {
    return 'feedback'
  }

  if (m.includes('kya') || m.includes('matlab') || m.includes('what')) {
    return 'explain'
  }

  if (m.includes('kya karu') || m.includes('help')) {
    return 'guide'
  }

  return 'general'
}
  const send = useCallback(
    async (text) => {
      const trimmed = (text || input).trim()
      if (!trimmed || loading) return

      const userMsg = {
        id: Date.now().toString(),
        role: 'user',
        text: trimmed,
        time: timestamp(),
      }

      setMessages((prev) => [...prev, userMsg])
      setInput('')
      setLoading(true)
      const intent = detectIntent(trimmed)

      if (intent === 'feedback') {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString() + 'f',
            role: 'assistant',
            text: FEEDBACK[language] || FEEDBACK.hi,
            time: timestamp(),
          },
        ])
        setLoading(false)
        return
      }

      try {
        const contextText = fdContext
            ? `User selected ${fdContext.bank} with ${fdContext.rate}% interest`
            : ""

          const reply = await askAdvisor({
            userMessage: contextText + "\nUser: " + trimmed,
            language,
            fdContext
          })
        setMessages((prev) => [
          ...prev,
          { id: Date.now().toString() + 'r', role: 'assistant', text: reply, time: timestamp() },
        ])
      } catch (err) {
        const errorText = {
          hi: 'माफ़ कीजिए, अभी जवाब नहीं मिला। फिर से कोशिश करें।',
          ta: 'மன்னிக்கவும், இப்போது பதில் கிடைக்கவில்லை. மீண்டும் முயற்சிக்கவும்.',
          te: 'క్షమించండి, ఇప్పుడు జవాబు రాలేదు. మళ్ళీ ప్రయత్నించండి.',
        }
        setMessages((prev) => [
          ...prev,
          { id: Date.now().toString() + 'e', role: 'assistant', text: errorText[language] || errorText.hi, time: timestamp() },
        ])
      } finally {
        setLoading(false)
      }
    },
    [input, loading, language, fdContext]
  )

  return { messages, input, setInput, loading, send }
}