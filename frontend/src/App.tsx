import { useState } from 'react'

const API = 'http://127.0.0.1:8000'

type Uploaded = { document_id: string; filename: string }

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [docs, setDocs] = useState<Uploaded[]>([])
  const [selected, setSelected] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  async function call(path: string, options: RequestInit = {}) {
    const response = await fetch(`${API}${path}`, options)
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Request failed')
    return data
  }

  async function upload() {
    if (!file) return
    setBusy(true); setStatus('Uploading document...')
    try {
      const body = new FormData(); body.append('file', file)
      const result = await call('/api/documents/upload', { method: 'POST', body })
      setDocs(prev => [...prev, result]); setSelected(result.document_id)
      setStatus(`Uploaded ${result.filename}. Extract it when ready.`)
    } catch (e) { setStatus(String(e)) } finally { setBusy(false) }
  }

  async function extract() {
    if (!selected) return
    setBusy(true); setStatus('Extracting document text...')
    try {
      const result = await call(`/api/documents/${selected}/extract`, { method: 'POST' })
      setStatus(`Extracted ${result.character_count} characters into ${result.chunk_count} chunks.`)
    } catch (e) { setStatus(String(e)) } finally { setBusy(false) }
  }

  async function index() {
    if (!selected) return
    setBusy(true); setStatus('Generating embeddings and indexing...')
    try {
      const result = await call(`/api/documents/${selected}/index`, { method: 'POST' })
      setStatus(`Indexed ${result.indexed_chunks} chunks.`)
    } catch (e) { setStatus(String(e)) } finally { setBusy(false) }
  }

  async function ask() {
    if (!question.trim()) return
    setBusy(true); setAnswer(''); setStatus('Searching documents and asking the local model...')
    try {
      const result = await call('/api/documents/ask', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 5, document_id: selected || null })
      })
      setAnswer(result.answer)
      setStatus(`${result.sources.length} source passage(s) retrieved.`)
    } catch (e) { setStatus(String(e)) } finally { setBusy(false) }
  }

  return <main className="shell">
    <header className="topbar">
      <div className="brand-mark">EI</div>
      <div><div className="eyebrow">LOCAL AI WORKSPACE</div><h1>Enterprise Intelligence</h1></div>
      <span className="local-badge">● Local environment</span>
    </header>
    <section className="intro">
      <div className="eyebrow">DOCUMENT INTELLIGENCE</div>
      <h2>Turn business documents into<br /><em>useful answers and insights.</em></h2>
      <p>Upload a document, process it when you're ready, then search its content with your local AI model.</p>
    </section>
    <section className="grid">
      <article className="card">
        <div className="card-head"><span className="step">01</span><div><h3>Document workspace</h3><p>Add and prepare a document for analysis.</p></div></div>
        <label className="dropzone">
          <input type="file" accept=".pdf,.docx,.xlsx,.csv,.txt" onChange={e => setFile(e.target.files?.[0] || null)} />
          <span className="upload-icon">↑</span>
          <strong>{file ? file.name : 'Choose a document'}</strong>
          <small>PDF, DOCX, XLSX, CSV or TXT</small>
        </label>
        <button disabled={!file || busy} onClick={upload}>Upload document</button>
        <label className="field-label">Uploaded documents</label>
        <select value={selected} onChange={e => setSelected(e.target.value)}>
          <option value="">Select a document</option>
          {docs.map(d => <option key={d.document_id} value={d.document_id}>{d.filename}</option>)}
        </select>
        <div className="button-row">
          <button className="secondary" disabled={!selected || busy} onClick={extract}>Extract text</button>
          <button className="secondary" disabled={!selected || busy} onClick={index}>Create index</button>
        </div>
      </article>
      <article className="card">
        <div className="card-head"><span className="step">02</span><div><h3>Ask your documents</h3><p>Retrieve relevant passages and ask a question.</p></div></div>
        <label className="field-label">Your question</label>
        <textarea value={question} onChange={e => setQuestion(e.target.value)} placeholder="What are the key terms, amounts, or requirements in this document?" />
        <button disabled={!question.trim() || busy} onClick={ask}>Ask local AI</button>
        <div className="answer-box">
          <div className="answer-title">AI RESPONSE</div>
          {answer || <span className="muted">Your answer will appear here after you ask a question.</span>}
        </div>
      </article>
    </section>
    <div className="status"><span className="status-dot" />{busy ? 'Working' : 'Ready'} <span>{status}</span></div>
    <footer>Enterprise Intelligence & Automation Platform <span>Human-reviewed · Local-first</span></footer>
  </main>
}
