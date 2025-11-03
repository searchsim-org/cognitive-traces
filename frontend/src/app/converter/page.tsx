'use client'

import { useMemo, useState, useRef } from 'react'
import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'
import { Upload as UploadIcon } from 'lucide-react'

type RawRow = Record<string, any>

type Mapping = {
  session_id?: string
  timestamp?: string
  action_type?: string
  content: string[]
  event_id?: string
  joiner: string
}

function parseCSV(text: string): RawRow[] {
  const lines = text.split(/\r?\n/).filter(l => l.trim().length > 0)
  if (lines.length === 0) return []
  const parseLine = (line: string): string[] => {
    const out: string[] = []
    let cur = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i++) {
      const ch = line[i]
      if (ch === '"') {
        if (inQuotes && line[i + 1] === '"') { cur += '"'; i++; }
        else { inQuotes = !inQuotes }
      } else if (ch === ',' && !inQuotes) {
        out.push(cur)
        cur = ''
      } else {
        cur += ch
      }
    }
    out.push(cur)
    return out.map(s => s.trim())
  }
  const header = parseLine(lines[0])
  return lines.slice(1).map(l => {
    const cells = parseLine(l)
    const row: RawRow = {}
    header.forEach((h, i) => { row[h] = cells[i] })
    return row
  })
}

function detectFields(rows: RawRow[]): string[] {
  const set = new Set<string>()
  rows.slice(0, 50).forEach(r => Object.keys(r).forEach(k => set.add(k)))
  return Array.from(set.values()).sort()
}

function parseXML(text: string): RawRow[] {
  const parser = new DOMParser()
  const doc = parser.parseFromString(text, 'application/xml')
  if (doc.getElementsByTagName('parsererror').length) {
    throw new Error('Invalid XML file')
  }
  // Special-case Session Track 2014 structure
  if (doc.documentElement.tagName.toLowerCase() === 'sessiontrack2014') {
    const rows: RawRow[] = []
    const sessionNodes = Array.from(doc.getElementsByTagName('session')) as Element[]
    sessionNodes.forEach((sessionEl) => {
      const userid = sessionEl.getAttribute('userid') || ''
      const sessionNum = sessionEl.getAttribute('num') || ''
      const topicEl = sessionEl.getElementsByTagName('topic')[0]
      const topicNum = topicEl?.getAttribute('num') || ''
      const descEl = topicEl?.getElementsByTagName('desc')[0]
      const topicDesc = (descEl?.textContent || '').trim()
      const interactions = Array.from(sessionEl.getElementsByTagName('interaction')) as Element[]
      interactions.forEach((interEl) => {
        const interactionNum = interEl.getAttribute('num') || ''
        const starttime = interEl.getAttribute('starttime') || ''
        const typ = interEl.getAttribute('type') || ''
        const queryEl = interEl.getElementsByTagName('query')[0]
        const query = (queryEl?.textContent || '').trim()
        const resultsEl = interEl.getElementsByTagName('results')[0]
        const resultNodes = resultsEl ? Array.from(resultsEl.getElementsByTagName('result')) as Element[] : []
        const results = resultNodes.map((r) => ({
          rank: r.getAttribute('rank') || '',
          url: (r.getElementsByTagName('url')[0]?.textContent || '').trim(),
          title: (r.getElementsByTagName('title')[0]?.textContent || '').trim(),
          snippet: (r.getElementsByTagName('snippet')[0]?.textContent || '').trim(),
        }))
        const event_id = `${userid}_${topicNum}_${interactionNum}`
        const content_obj = { topic_desc: topicDesc, query, results }
        rows.push({
          session_id: userid || sessionNum,
          event_id,
          timestamp: starttime,
          action_type: typ,
          content: JSON.stringify(content_obj),
          userid,
          topic_num: topicNum,
          interaction_num: interactionNum,
          topic_desc: topicDesc,
          query,
        })
      })
    })
    return rows
  }
  const all = Array.from(doc.getElementsByTagName('*')) as Element[]
  const counts = new Map<string, number>()
  all.forEach(el => {
    if (el.children && el.children.length > 0) {
      const name = el.tagName
      counts.set(name, (counts.get(name) || 0) + 1)
    }
  })
  let rowsTag = ''
  let max = 0
  counts.forEach((c, name) => {
    if (name !== doc.documentElement.tagName && c > max) { rowsTag = name; max = c }
  })
  const rowNodes = rowsTag ? Array.from(doc.getElementsByTagName(rowsTag)) : Array.from(doc.documentElement.children)
  const rows: RawRow[] = rowNodes.map((node: Element) => {
    const obj: RawRow = {}
    Array.from(node.children).forEach((child: Element) => {
      if (child.children.length === 0) {
        obj[child.tagName] = (child.textContent || '').trim()
      }
    })
    return obj
  }).filter(r => Object.keys(r).length > 0)
  return rows
}

function toStandardRows(rows: RawRow[], mapping: Mapping): RawRow[] {
  let counter = 0
  return rows.map((r) => {
    const content = (mapping.content || []).map(k => (r[k] ?? '')).join(mapping.joiner || ' ')
    const out: RawRow = {
      session_id: mapping.session_id ? r[mapping.session_id] : 's_' + (r['session_id'] ?? ''),
      timestamp: mapping.timestamp ? r[mapping.timestamp] : (r['timestamp'] ?? ''),
      action_type: mapping.action_type ? r[mapping.action_type] : (r['action_type'] ?? ''),
      content,
    }
    const ev = mapping.event_id ? r[mapping.event_id] : undefined
    out.event_id = ev ?? `e_${++counter}`
    return out
  })
}

function download(filename: string, content: string, mime = 'text/plain') {
  const blob = new Blob([content], { type: mime + ';charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function ConverterPage() {
  const [rawRows, setRawRows] = useState<RawRow[]>([])
  const [fields, setFields] = useState<string[]>([])
  const [mapping, setMapping] = useState<Mapping>({ content: [], joiner: ' ' })
  const [error, setError] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [contentAsJson, setContentAsJson] = useState<boolean>(false)
  const [contentJsonKeys, setContentJsonKeys] = useState<string[]>([])

  const standardRows = useMemo((): RawRow[] => {
    if (!rawRows.length) return []
    try {
      if (contentAsJson && contentJsonKeys.length > 0) {
        return rawRows.map((r, idx) => {
          const obj: any = {}
          contentJsonKeys.forEach((k) => { obj[k] = r[k] })
          return {
            session_id: r.session_id ?? (mapping.session_id ? r[mapping.session_id] : r['userid'] ?? r['session'] ?? ''),
            event_id: r.event_id ?? (mapping.event_id ? r[mapping.event_id] : `e_${idx + 1}`),
            timestamp: r.timestamp ?? (mapping.timestamp ? r[mapping.timestamp] : r['starttime'] ?? ''),
            action_type: r.action_type ?? (mapping.action_type ? r[mapping.action_type] : r['type'] ?? ''),
            content: JSON.stringify(obj),
          } as RawRow
        })
      }
      return toStandardRows(rawRows, mapping)
    } catch { return [] }
  }, [rawRows, mapping, contentAsJson, contentJsonKeys])

  const handleFile = async (file: File) => {
    setError(null)
    try {
      const text = await file.text()
      let rows: RawRow[] = []
      if (file.name.toLowerCase().endsWith('.csv') || file.type.includes('csv')) {
        rows = parseCSV(text)
      } else if (file.name.toLowerCase().endsWith('.xml') || file.type.includes('xml')) {
        rows = parseXML(text)
      } else {
        const json = JSON.parse(text)
        rows = Array.isArray(json) ? json : (json.rows || [])
      }
      setRawRows(rows)
      setFields(detectFields(rows))
    } catch (e: any) {
      setError(e?.message || 'Failed to parse file')
    }
  }

  const handleDrop: React.DragEventHandler<HTMLDivElement> = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleFile(e.dataTransfer.files[0])
      // Do not call clearData here; some browsers disallow modification on drop
    }
  }

  const handleDragOver: React.DragEventHandler<HTMLDivElement> = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave: React.DragEventHandler<HTMLDivElement> = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const preview = standardRows.slice(0, 10)

  const downloadJSON = () => download('converted.json', JSON.stringify(standardRows, null, 2), 'application/json')
  const downloadCSV = () => {
    const header = ['session_id','event_id','timestamp','action_type','content']
    // Properly escape CSV fields (quote all fields, escape internal quotes)
    const escapeCsvField = (val: any) => {
      const str = String(val ?? '')
      // Quote all fields and escape internal quotes by doubling them
      return '"' + str.replace(/"/g, '""') + '"'
    }
    const lines = [header.map(escapeCsvField).join(',')].concat(
      standardRows.map(r => header.map(h => escapeCsvField(r[h])).join(','))
    )
    download('converted.csv', lines.join('\n'), 'text/csv')
  }

  const MultiFieldPicker = ({ selected, onChange }: { selected: string[], onChange: (s: string[]) => void }) => (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {fields.map(f => (
          <button
            key={f}
            type="button"
            onClick={() => onChange(selected.includes(f) ? selected.filter(x => x !== f) : [...selected, f])}
            className={`px-3 py-1 rounded-full border text-sm ${selected.includes(f) ? 'bg-gray-900 text-white' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
          >
            {f}
          </button>
        ))}
      </div>
    </div>
  )

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navigation />
      <main className="flex-1">
        <div className="container py-12 md:py-16">
          <div className="text-center mb-12 max-w-3xl mx-auto">
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-gray-900 mb-4">Dataset Converter</h1>
            <p className="text-lg text-gray-600">Map your CSV/JSON fields to the required schema. Combine multiple columns for content.</p>
          </div>

          <div className="grid lg:grid-cols-5 gap-8 max-w-6xl mx-auto">
            {/* Left: Upload & Mapping */}
            <div className="lg:col-span-2 space-y-6">
              <div className="p-6 rounded-2xl border border-gray-200 bg-white">
                <h2 className="text-xl font-bold text-gray-900 mb-4">1) Upload CSV or JSON</h2>
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors ${
                    isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex flex-col items-center gap-2">
                    <UploadIcon className="w-6 h-6 text-gray-500" />
                    <div className="text-sm text-gray-900 font-medium">Drag & drop a CSV/JSON/XML</div>
                    <div className="text-xs text-gray-500">or click to choose a file</div>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xml,application/json,application/xml"
                    className="hidden"
                    onChange={(e) => e.target.files && e.target.files[0] && handleFile(e.target.files[0])}
                  />
                </div>
                {error && <div className="mt-3 text-sm text-red-600">{error}</div>}
                {!!fields.length && (
                  <div className="mt-4 text-xs text-gray-500">Detected fields: {fields.join(', ')}</div>
                )}
              </div>

              <div className="p-6 rounded-2xl border border-gray-200 bg-white">
                <h2 className="text-xl font-bold text-gray-900 mb-4">2) Map Required Fields</h2>
                <div className="space-y-5">
                  <div className="grid grid-cols-1 gap-3">
                    {['session_id','timestamp','action_type','event_id'].map((key) => (
                      <div key={key} className="p-3 rounded-lg border border-gray-200 bg-gray-50">
                        <div className="flex items-center justify-between gap-3">
                          <label className="text-sm text-gray-700 font-medium capitalize">{key.replace('_',' ')}</label>
                          <select
                            value={(mapping as any)[key] || ''}
                            onChange={(e) => setMapping({ ...mapping, [key]: e.target.value || undefined })}
                            className="px-3 py-2 rounded-md border border-gray-300 bg-white text-sm"
                          >
                            <option value="">(not set)</option>
                            {fields.map((f) => (
                              <option key={f} value={f}>{f}</option>
                            ))}
                          </select>
                        </div>
                        {!!fields.length && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {fields.map((f) => (
                              <button
                                key={f}
                                type="button"
                                onClick={() => setMapping({ ...mapping, [key]: f })}
                                className={`px-2 py-1 rounded-full text-xs border ${((mapping as any)[key] === f) ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}`}
                              >
                                {f}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="p-3 rounded-lg border border-gray-200 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <label className="text-sm text-gray-700 font-medium">content</label>
                      <div className="flex items-center gap-2 text-xs text-gray-600">
                        <input id="jsonmode" type="checkbox" className="rounded" checked={contentAsJson} onChange={(e) => setContentAsJson(e.target.checked)} />
                        <label htmlFor="jsonmode">JSON mode</label>
                      </div>
                    </div>

                    {!contentAsJson ? (
                      <>
                        <MultiFieldPicker selected={mapping.content} onChange={(c) => setMapping({ ...mapping, content: c })} />
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-600">Join with</span>
                          <input
                            value={mapping.joiner}
                            onChange={(e) => setMapping({ ...mapping, joiner: e.target.value })}
                            className="px-2 py-1 rounded border border-gray-300 text-sm w-24"
                          />
                        </div>
                      </>
                    ) : (
                      <div className="mt-2">
                        <div className="text-xs text-gray-600 mb-2">Select fields to embed as a JSON object</div>
                        <MultiFieldPicker selected={contentJsonKeys} onChange={setContentJsonKeys} />
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="p-6 rounded-2xl border border-gray-200 bg-white">
                <h2 className="text-xl font-bold text-gray-900 mb-4">3) Export</h2>
                <div className="flex flex-wrap gap-3">
                  <button onClick={downloadCSV} disabled={!standardRows.length} className="px-5 py-3 rounded-full bg-gray-900 text-white hover:bg-gray-800 text-sm disabled:opacity-50">Download CSV</button>
                  <button onClick={downloadJSON} disabled={!standardRows.length} className="px-5 py-3 rounded-full border border-gray-300 hover:bg-gray-50 text-sm">Download JSON</button>
                </div>
              </div>
            </div>

            {/* Right: Preview (restored position) */}
            <div className="lg:col-span-3 p-6 rounded-2xl border-2 border-dashed border-gray-300 bg-gray-50">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Preview</h2>
              {preview.length === 0 ? (
                <div className="text-sm text-gray-500">Upload a file and configure mappings to see a preview.</div>
              ) : (
                <div className="overflow-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-600">
                        <th className="py-2 pr-4">session_id</th>
                        <th className="py-2 pr-4">event_id</th>
                        <th className="py-2 pr-4">timestamp</th>
                        <th className="py-2 pr-4">action_type</th>
                        <th className="py-2 pr-4">content</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.map((r, i) => (
                        <tr key={i} className="border-t border-gray-200">
                          <td className="py-2 pr-4 text-gray-900">{r.session_id}</td>
                          <td className="py-2 pr-4 text-gray-700">{r.event_id}</td>
                          <td className="py-2 pr-4 text-gray-700">{r.timestamp}</td>
                          <td className="py-2 pr-4 text-gray-700">{r.action_type}</td>
                          <td className="py-2 pr-4 text-gray-700 whitespace-pre-wrap break-words">{typeof r.content === 'string' ? r.content : JSON.stringify(r.content)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}


