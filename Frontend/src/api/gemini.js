
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

export async function askAdvisor({ userMessage, language = 'hi', fdContext = null }) {
  if (!userMessage?.trim()) {
    throw new Error('Message cannot be empty')
  }

  try {
    const res = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userMessage,
        language,
        fdContext,
      }),
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.error || 'Backend API request failed')
    }

    const data = await res.json()
    return data.reply || ''
  } catch (error) {
    console.error('API Error:', error.message)
    throw error
  }
}

export const QUICK_QUESTIONS = {
  hi: [
    '8.50% का मतलब क्या है?',
    'Small Finance Bank सुरक्षित है?',
    '₹10,000 जमा करूँ तो कितना मिलेगा?',
    'Tenor का मतलब बताएं',
  ],
  ta: [
    '8.50% என்றால் என்ன?',
    'Small Finance Bank பாதுகாப்பானதா?',
    '₹10,000 வைத்தால் எவ்வளவு கிடைக்கும்?',
    'Tenor என்றால் என்ன?',
  ],
  te: [
    '8.50% అంటే ఏమిటి?',
    'Small Finance Bank సురక్షితమా?',
    '₹10,000 వేస్తే ఎంత వస్తుంది?',
    'Tenor అంటే ఏమిటి?',
  ],
}
export const JARGON = {
  hi: [
    { term: 'Interest Rate',   q: 'Interest Rate क्या होता है?' },
    { term: 'P.a.',            q: 'p.a. का मतलब क्या है?' },
    { term: 'Tenor',           q: 'Tenor का मतलब क्या है?' },
    { term: 'Principal',       q: 'Principal क्या होता है?' },
    { term: 'Maturity',        q: 'Maturity Amount क्या होता है?' },
    { term: 'Compounding',     q: 'Compounding यानी चक्रवृद्धि ब्याज क्या होता है?' },
    { term: 'Cumulative',      q: 'Cumulative FD क्या होता है?' },
    { term: 'Non-Cumulative',  q: 'Non-Cumulative FD क्या होता है?' },
    { term: 'TDS',             q: 'FD पर TDS क्या होता है और कब कटता है?' },
    { term: 'Premature',       q: 'Premature withdrawal का मतलब क्या है?' },
    { term: 'Auto Renewal',    q: 'Auto Renewal क्या होता है?' },
    { term: 'DICGC',           q: 'DICGC बीमा क्या है?' },
    { term: 'Senior Citizen',  q: 'Senior Citizen को FD में क्या अतिरिक्त फायदा मिलता है?' },
  ],

  ta: [
    { term: 'Interest Rate',   q: 'Interest Rate என்றால் என்ன?' },
    { term: 'P.a.',            q: 'p.a. என்றால் என்ன?' },
    { term: 'Tenor',           q: 'Tenor என்றால் என்ன?' },
    { term: 'Principal',       q: 'Principal என்றால் என்ன?' },
    { term: 'Maturity',        q: 'Maturity Amount என்றால் என்ன?' },
    { term: 'Compounding',     q: 'Compounding வட்டி என்றால் என்ன?' },
    { term: 'Cumulative',      q: 'Cumulative FD என்றால் என்ன?' },
    { term: 'Non-Cumulative',  q: 'Non-Cumulative FD என்றால் என்ன?' },
    { term: 'TDS',             q: 'FD-ல் TDS என்றால் என்ன?' },
    { term: 'Premature',       q: 'Premature withdrawal என்றால் என்ன?' },
    { term: 'Auto Renewal',    q: 'Auto Renewal என்றால் என்ன?' },
    { term: 'DICGC',           q: 'DICGC காப்பீடு என்றால் என்ன?' },
    { term: 'Senior Citizen',  q: 'மூத்தோருக்கு FD-ல் என்ன சலுகை?' },
  ],

  te: [
    { term: 'Interest Rate',   q: 'Interest Rate అంటే ఏమిటి?' },
    { term: 'P.a.',            q: 'p.a. అంటే ఏమిటి?' },
    { term: 'Tenor',           q: 'Tenor అంటే ఏమిటి?' },
    { term: 'Principal',       q: 'Principal అంటే ఏమిటి?' },
    { term: 'Maturity',        q: 'Maturity Amount అంటే ఏమిటి?' },
    { term: 'Compounding',     q: 'Compounding వడ్డీ అంటే ఏమిటి?' },
    { term: 'Cumulative',      q: 'Cumulative FD అంటే ఏమిటి?' },
    { term: 'Non-Cumulative',  q: 'Non-Cumulative FD అంటే ఏమిటి?' },
    { term: 'TDS',             q: 'FD పై TDS అంటే ఏమిటి?' },
    { term: 'Premature',       q: 'Premature withdrawal అంటే ఏమిటి?' },
    { term: 'Auto Renewal',    q: 'Auto Renewal అంటే ఏమిటి?' },
    { term: 'DICGC',           q: 'DICGC బీమా అంటే ఏమిటి?' },
    { term: 'Senior Citizen',  q: 'Senior Citizen కు FD లో అదనపు లాభం ఏమిటి?' },
  ],
}