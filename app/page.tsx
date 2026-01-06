'use client'

import { useState, useCallback } from 'react'

interface ExtractionResult {
  source_file: string
  extraction_date: string
  file_hash: string
  metadata: {
    title: string
    author: string | null
    subject: string | null
    keywords: string[]
    page_count: number
  }
  toc: Array<{ level: number; title: string; page: number }>
  pages: Array<{ page: number; text: string }>
  text_output?: string
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [outputFormat, setOutputFormat] = useState<'txt' | 'json'>('txt')
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile)
        setError(null)
      } else {
        setError('Please drop a PDF file')
      }
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleExtract = async () => {
    if (!file) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      // Convert file to base64
      const buffer = await file.arrayBuffer()
      const base64 = btoa(
        new Uint8Array(buffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      )

      const response = await fetch('/api/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file: base64,
          filename: file.name,
          format: outputFormat,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Extraction failed')
      }

      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!result) return

    let content: string
    let filename: string
    let mimeType: string

    if (outputFormat === 'json') {
      content = JSON.stringify(result, null, 2)
      filename = `${result.metadata.title || 'extracted'}.json`
      mimeType = 'application/json'
    } else {
      content = result.text_output || ''
      filename = `${result.metadata.title || 'extracted'}.txt`
      mimeType = 'text/plain'
    }

    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>PDF Extractor</h1>
        <p style={styles.subtitle}>
          Extract text, metadata, and table of contents from PDF documents
        </p>
      </header>

      <main style={styles.main}>
        {/* Upload Section */}
        <div
          style={{
            ...styles.dropZone,
            ...(dragActive ? styles.dropZoneActive : {}),
          }}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            style={styles.fileInput}
            id="file-input"
          />
          <label htmlFor="file-input" style={styles.fileLabel}>
            {file ? (
              <span>{file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
            ) : (
              <span>Drop PDF here or click to browse</span>
            )}
          </label>
        </div>

        {/* Options */}
        <div style={styles.options}>
          <label style={styles.optionLabel}>
            Output Format:
            <select
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value as 'txt' | 'json')}
              style={styles.select}
            >
              <option value="txt">Text (.txt)</option>
              <option value="json">JSON (.json)</option>
            </select>
          </label>
        </div>

        {/* Extract Button */}
        <button
          onClick={handleExtract}
          disabled={!file || loading}
          style={{
            ...styles.button,
            ...((!file || loading) ? styles.buttonDisabled : {}),
          }}
        >
          {loading ? 'Extracting...' : 'Extract PDF'}
        </button>

        {/* Error */}
        {error && <div style={styles.error}>{error}</div>}

        {/* Results */}
        {result && (
          <div style={styles.results}>
            <div style={styles.resultHeader}>
              <h2 style={styles.resultTitle}>Extraction Complete</h2>
              <button onClick={handleDownload} style={styles.downloadButton}>
                Download {outputFormat.toUpperCase()}
              </button>
            </div>

            {/* Metadata */}
            <div style={styles.metadataBox}>
              <h3 style={styles.sectionTitle}>Metadata</h3>
              <table style={styles.metadataTable}>
                <tbody>
                  <tr>
                    <td style={styles.metadataLabel}>Title:</td>
                    <td>{result.metadata.title}</td>
                  </tr>
                  <tr>
                    <td style={styles.metadataLabel}>Author:</td>
                    <td>{result.metadata.author || 'N/A'}</td>
                  </tr>
                  <tr>
                    <td style={styles.metadataLabel}>Pages:</td>
                    <td>{result.metadata.page_count}</td>
                  </tr>
                  <tr>
                    <td style={styles.metadataLabel}>Subject:</td>
                    <td>{result.metadata.subject || 'N/A'}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* TOC */}
            {result.toc.length > 0 && (
              <div style={styles.tocBox}>
                <h3 style={styles.sectionTitle}>Table of Contents</h3>
                <ul style={styles.tocList}>
                  {result.toc.map((item, i) => (
                    <li
                      key={i}
                      style={{
                        ...styles.tocItem,
                        paddingLeft: `${(item.level - 1) * 20}px`,
                      }}
                    >
                      {item.title} <span style={styles.tocPage}>p. {item.page}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Text Preview */}
            <div style={styles.previewBox}>
              <h3 style={styles.sectionTitle}>Text Preview</h3>
              <pre style={styles.preview}>
                {result.text_output?.slice(0, 3000) || JSON.stringify(result.pages.slice(0, 2), null, 2)}
                {(result.text_output?.length || 0) > 3000 && '\n\n... [Download for full content]'}
              </pre>
            </div>
          </div>
        )}
      </main>

      <footer style={styles.footer}>
        <p>PDF Extractor - Built with Next.js and PyMuPDF</p>
      </footer>
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#1a1a2e',
    color: 'white',
    padding: '2rem',
    textAlign: 'center',
  },
  title: {
    margin: 0,
    fontSize: '2.5rem',
    fontWeight: 700,
  },
  subtitle: {
    margin: '0.5rem 0 0',
    opacity: 0.8,
  },
  main: {
    flex: 1,
    padding: '2rem',
    maxWidth: '900px',
    margin: '0 auto',
    width: '100%',
    boxSizing: 'border-box',
  },
  dropZone: {
    border: '2px dashed #ccc',
    borderRadius: '8px',
    padding: '3rem',
    textAlign: 'center',
    backgroundColor: 'white',
    transition: 'all 0.2s',
    cursor: 'pointer',
  },
  dropZoneActive: {
    borderColor: '#4a90d9',
    backgroundColor: '#e8f4fd',
  },
  fileInput: {
    display: 'none',
  },
  fileLabel: {
    cursor: 'pointer',
    fontSize: '1.1rem',
    color: '#666',
  },
  options: {
    margin: '1.5rem 0',
    display: 'flex',
    gap: '1rem',
  },
  optionLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '0.95rem',
  },
  select: {
    padding: '0.5rem',
    borderRadius: '4px',
    border: '1px solid #ccc',
    fontSize: '0.95rem',
  },
  button: {
    width: '100%',
    padding: '1rem',
    fontSize: '1.1rem',
    fontWeight: 600,
    backgroundColor: '#4a90d9',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  error: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#fee',
    color: '#c00',
    borderRadius: '8px',
    border: '1px solid #fcc',
  },
  results: {
    marginTop: '2rem',
  },
  resultHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  resultTitle: {
    margin: 0,
    fontSize: '1.5rem',
  },
  downloadButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: 600,
  },
  metadataBox: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    marginBottom: '1rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  sectionTitle: {
    margin: '0 0 1rem',
    fontSize: '1.1rem',
    color: '#333',
  },
  metadataTable: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  metadataLabel: {
    fontWeight: 600,
    paddingRight: '1rem',
    paddingBottom: '0.5rem',
    color: '#666',
    width: '100px',
  },
  tocBox: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    marginBottom: '1rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  tocList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  tocItem: {
    padding: '0.5rem 0',
    borderBottom: '1px solid #eee',
  },
  tocPage: {
    color: '#888',
    fontSize: '0.9rem',
  },
  previewBox: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  preview: {
    backgroundColor: '#f8f8f8',
    padding: '1rem',
    borderRadius: '4px',
    overflow: 'auto',
    maxHeight: '400px',
    fontSize: '0.85rem',
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  footer: {
    backgroundColor: '#1a1a2e',
    color: 'white',
    padding: '1rem',
    textAlign: 'center',
    opacity: 0.9,
  },
}
