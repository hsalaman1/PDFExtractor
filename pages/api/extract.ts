import type { NextApiRequest, NextApiResponse } from 'next'
import pdf from 'pdf-parse'
import mammoth from 'mammoth'
import matter from 'gray-matter'
import crypto from 'crypto'

interface ExtractionResult {
  source_file: string
  file_type: string
  extraction_date: string
  file_hash: string
  metadata: {
    title: string
    author: string | null
    subject: string | null
    keywords: string[]
    page_count?: number
    word_count?: number
  }
  toc: Array<{ level: number; title: string; page?: number; line?: number }>
  text_output: string
  pages?: Array<{ page: number; text: string }>
  sections?: Array<{ section: number; title: string; text: string }>
}

function computeHash(data: Buffer): string {
  return `sha256:${crypto.createHash('sha256').update(data).digest('hex')}`
}

function getFileType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  if (ext === 'pdf') return 'pdf'
  if (ext === 'md' || ext === 'markdown') return 'markdown'
  if (ext === 'docx') return 'docx'
  throw new Error(`Unsupported file type: ${ext}`)
}

function extractHeadings(text: string): Array<{ level: number; title: string; line: number }> {
  const headings: Array<{ level: number; title: string; line: number }> = []
  const lines = text.split('\n')

  lines.forEach((line, index) => {
    const match = line.match(/^(#{1,6})\s+(.+)$/)
    if (match) {
      headings.push({
        level: match[1].length,
        title: match[2].trim(),
        line: index + 1
      })
    }
  })

  return headings
}

async function extractPdf(buffer: Buffer, filename: string): Promise<ExtractionResult> {
  const data = await pdf(buffer)

  const metadata = {
    title: data.info?.Title || filename.replace('.pdf', ''),
    author: data.info?.Author || null,
    subject: data.info?.Subject || null,
    keywords: data.info?.Keywords ? data.info.Keywords.split(',').map((k: string) => k.trim()) : [],
    page_count: data.numpages,
    word_count: data.text.split(/\s+/).length
  }

  const textOutput = [
    `# ${metadata.title}`,
    metadata.author ? `# Author: ${metadata.author}` : '',
    `# Source: ${filename}`,
    `# Pages: ${metadata.page_count}`,
    '='.repeat(60),
    '',
    data.text
  ].filter(Boolean).join('\n')

  return {
    source_file: filename,
    file_type: 'pdf',
    extraction_date: new Date().toISOString(),
    file_hash: computeHash(buffer),
    metadata,
    toc: [],
    text_output: textOutput
  }
}

async function extractMarkdown(buffer: Buffer, filename: string): Promise<ExtractionResult> {
  const content = buffer.toString('utf-8')
  const { data: frontmatter, content: body } = matter(content)

  const headings = extractHeadings(body)
  const wordCount = body.split(/\s+/).length

  const metadata = {
    title: frontmatter.title || filename.replace(/\.(md|markdown)$/, ''),
    author: frontmatter.author || null,
    subject: frontmatter.description || frontmatter.subject || null,
    keywords: frontmatter.tags || frontmatter.keywords || [],
    word_count: wordCount
  }

  const textOutput = [
    `# ${metadata.title}`,
    metadata.author ? `# Author: ${metadata.author}` : '',
    `# Source: ${filename}`,
    `# Words: ${wordCount}`,
    '='.repeat(60),
    '',
    body
  ].filter(Boolean).join('\n')

  return {
    source_file: filename,
    file_type: 'markdown',
    extraction_date: new Date().toISOString(),
    file_hash: computeHash(buffer),
    metadata,
    toc: headings,
    text_output: textOutput
  }
}

async function extractDocx(buffer: Buffer, filename: string): Promise<ExtractionResult> {
  const result = await mammoth.extractRawText({ buffer })
  const text = result.value
  const wordCount = text.split(/\s+/).length

  const metadata = {
    title: filename.replace('.docx', ''),
    author: null,
    subject: null,
    keywords: [],
    word_count: wordCount
  }

  const textOutput = [
    `# ${metadata.title}`,
    `# Source: ${filename}`,
    `# Words: ${wordCount}`,
    '='.repeat(60),
    '',
    text
  ].join('\n')

  return {
    source_file: filename,
    file_type: 'docx',
    extraction_date: new Date().toISOString(),
    file_hash: computeHash(buffer),
    metadata,
    toc: [],
    text_output: textOutput
  }
}

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '50mb'
    }
  }
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const { file, filename } = req.body

    if (!file || !filename) {
      return res.status(400).json({ error: 'Missing file or filename' })
    }

    const buffer = Buffer.from(file, 'base64')
    const fileType = getFileType(filename)

    let result: ExtractionResult

    switch (fileType) {
      case 'pdf':
        result = await extractPdf(buffer, filename)
        break
      case 'markdown':
        result = await extractMarkdown(buffer, filename)
        break
      case 'docx':
        result = await extractDocx(buffer, filename)
        break
      default:
        return res.status(400).json({ error: `Unsupported file type: ${fileType}` })
    }

    return res.status(200).json(result)
  } catch (error) {
    console.error('Extraction error:', error)
    return res.status(500).json({
      error: error instanceof Error ? error.message : 'Extraction failed'
    })
  }
}
