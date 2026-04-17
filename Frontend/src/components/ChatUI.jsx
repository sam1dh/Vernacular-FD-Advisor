import { useRef, useEffect } from 'react'
import { useChat } from '../hooks/useChat'
import { QUICK_QUESTIONS, JARGON } from '../api/gemini'

export default function ChatUI({ language, fdContext, pendingMsg, onPendingMsgConsumed }) {
  const { messages, input, setInput, loading, send } = useChat(language, fdContext)
  const bottomRef  = useRef(null)
  const consumedRef = useRef(false)
  const pendingMsgRef = useRef(null)

  /* Auto-scroll on new messages */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  /* Fire pendingMsg once when arriving from Calculator jargon pill */
  useEffect(() => {
    if (pendingMsg && pendingMsg !== pendingMsgRef.current) {
      pendingMsgRef.current = pendingMsg
      onPendingMsgConsumed?.()
      send(pendingMsg)
    }
  }, [pendingMsg, onPendingMsgConsumed])

  /* Reset consumed flag when language changes so pills still work */
  useEffect(() => { consumedRef.current = false }, [language])

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send(input)
    }
  }

  const quickQs = QUICK_QUESTIONS[language] || QUICK_QUESTIONS.hi

  const placeholder = {
    hi: 'अपना सवाल यहाँ लिखें...',
    ta: 'உங்கள் கேள்வியை இங்கே எழுதுங்கள்...',
    te: 'మీ ప్రశ్న ఇక్కడ రాయండి...',
  }[language] || 'Ask your question...'

  return (
    <div className="chat-container">

      {/* Messages */}
      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-bubble ${msg.role}`}>
            <div className="bubble-content">{msg.text}</div>
            <div className="bubble-time">{msg.time}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble assistant loading">
            <div className="typing-dots"><span /><span /><span /></div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick question chips */}
      <div className="quick-questions">
        {quickQs.map((q, i) => (
          <button
            key={i}
            className="quick-btn"
            onClick={() => send(q)}
            disabled={loading}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Jargon pills */}
      <div className="jargon-pills-row">
        {(JARGON[language] || JARGON.hi).map(({ term, q }) => (
          <button
            key={term}
            className="jargon-pill"
            onClick={() => send(q)}
            disabled={loading}
            title={q}
          >
            {term}
          </button>
        ))}
      </div>

      {/* Input row */}
      <div className="chat-input-row">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder={placeholder}
          rows={2}
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={() => send(input)}
          disabled={loading || !input.trim()}
          aria-label="Send"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M22 2L11 13"       stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>

    </div>
  )
}