import { useState, useCallback } from 'react'
import Head from 'next/head'

const SUPPORTED_EXTENSIONS = ['.pdf', '.md', '.markdown', '.docx']

interface ExtractionResult {
  source_file: string
  file_type: string
  extraction_date: string
  file_hash: string
  metadata: {
    title: string
    author: string | string[] | null
    subject: string | null
    keywords: string[]
    page_count?: number
    word_count?: number
    char_count?: number
  }
  toc: Array<{ level: number; title: string; page?: number; line?: number; paragraph?: number }>
  pages?: Array<{ page: number; text: string }>
  sections?: Array<{ section: number; title: string; text: string }>
  text_output?: string
}

function getFileTypeLabel(fileType: string): string {
  switch (fileType) {
    case 'pdf': return 'PDF'
    case 'markdown': return 'Markdown'
    case 'docx': return 'Word'
    default: return fileType
  }
}

function isValidFile(file: File): boolean {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  return SUPPORTED_EXTENSIONS.includes(ext)
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
      if (isValidFile(droppedFile)) {
        setFile(droppedFile)
        setError(null)
        setResult(null)
      } else {
        setError('Unsupported file type. Please use PDF, Markdown (.md), or Word (.docx)')
      }
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (isValidFile(selectedFile)) {
        setFile(selectedFile)
        setError(null)
        setResult(null)
      } else {
        setError('Unsupported file type. Please use PDF, Markdown (.md), or Word (.docx)')
      }
    }
  }

  const handleExtract = async () => {
    if (!file) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
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

  const getAuthorDisplay = (author: string | string[] | null): string => {
    if (!author) return 'N/A'
    if (Array.isArray(author)) return author.join(', ')
    return author
  }

  return (
    <>
      <Head>
        <title>Document Extractor</title>
        <meta name="description" content="Extract text, metadata, and table of contents from PDF, Markdown, and Word documents" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <div style={styles.container}>
        <header style={styles.header}>
          <h1 style={styles.title}>Document Extractor</h1>
          <p style={styles.subtitle}>
            Extract text, metadata, and table of contents from PDF, Markdown, and Word documents
          </p>
          <div style={styles.badges}>
            <span style={styles.badge}>PDF</span>
            <span style={styles.badge}>Markdown</span>
            <span style={styles.badge}>Word</span>
          </div>
        </header>

        <main style={styles.main}>
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
              accept=".pdf,.md,.markdown,.docx"
              onChange={handleFileChange}
              style={styles.fileInput}
              id="file-input"
            />
            <label htmlFor="file-input" style={styles.fileLabel}>
              {file ? (
                <span>{file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
              ) : (
                <span>Drop file here or click to browse<br/><small style={{opacity: 0.7}}>Supports: PDF, Markdown (.md), Word (.docx)</small></span>
              )}
            </label>
          </div>

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

          <button
            onClick={handleExtract}
            disabled={!file || loading}
            style={{
              ...styles.button,
              ...((!file || loading) ? styles.buttonDisabled : {}),
            }}
          >
            {loading ? 'Extracting...' : 'Extract Document'}
          </button>

          {error && <div style={styles.error}>{error}</div>}

          {result && (
            <div style={styles.results}>
              <div style={styles.resultHeader}>
                <h2 style={styles.resultTitle}>
                  Extraction Complete
                  <span style={styles.fileTypeBadge}>{getFileTypeLabel(result.file_type)}</span>
                </h2>
                <button onClick={handleDownload} style={styles.downloadButton}>
                  Download {outputFormat.toUpperCase()}
                </button>
              </div>

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
                      <td>{getAuthorDisplay(result.metadata.author)}</td>
                    </tr>
                    {result.metadata.page_count && (
                      <tr>
                        <td style={styles.metadataLabel}>Pages:</td>
                        <td>{result.metadata.page_count}</td>
                      </tr>
                    )}
                    {result.metadata.word_count && (
                      <tr>
                        <td style={styles.metadataLabel}>Words:</td>
                        <td>{result.metadata.word_count.toLocaleString()}</td>
                      </tr>
                    )}
                    <tr>
                      <td style={styles.metadataLabel}>Subject:</td>
                      <td>{result.metadata.subject || 'N/A'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {result.toc && result.toc.length > 0 && (
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
                        {item.title}
                        {item.page && <span style={styles.tocPage}>p. {item.page}</span>}
                        {item.line && <span style={styles.tocPage}>line {item.line}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={styles.previewBox}>
                <h3 style={styles.sectionTitle}>Text Preview</h3>
                <pre style={styles.preview}>
                  {result.text_output?.slice(0, 3000) ||
                   (result.pages ? JSON.stringify(result.pages.slice(0, 2), null, 2) :
                    result.sections ? JSON.stringify(result.sections.slice(0, 2), null, 2) : '')}
                  {(result.text_output?.length || 0) > 3000 && '\n\n... [Download for full content]'}
                </pre>
              </div>
            </div>
          )}
        </main>

        <footer style={styles.footer}>
          <p>Document Extractor - Supports PDF, Markdown, and Word documents</p>
        </footer>
      </div>
    </>
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
  badges: {
    marginTop: '1rem',
    display: 'flex',
    justifyContent: 'center',
    gap: '0.5rem',
  },
  badge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    padding: '0.25rem 0.75rem',
    borderRadius: '20px',
    fontSize: '0.85rem',
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
    flexWrap: 'wrap',
    gap: '1rem',
  },
  resultTitle: {
    margin: 0,
    fontSize: '1.5rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  fileTypeBadge: {
    backgroundColor: '#4a90d9',
    color: 'white',
    padding: '0.25rem 0.75rem',
    borderRadius: '20px',
    fontSize: '0.75rem',
    fontWeight: 600,
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
    marginLeft: '0.5rem',
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
