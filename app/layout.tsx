import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'PDF Extractor',
  description: 'Extract text, metadata, and table of contents from PDF documents',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'system-ui, -apple-system, sans-serif' }}>
        {children}
      </body>
    </html>
  )
}
