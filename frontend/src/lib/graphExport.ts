import type { ProcessGraph } from "../api/types.ts"

const RANK: Record<string, number> = {
  Applied: 0,
  Screened: 1,
  "Interview Scheduled": 2,
  "Interview Completed": 3,
  Offer: 4,
  Hired: 5,
  Rejected: 5,
  Withdrawn: 5,
}

const TONE: Record<string, string> = {
  Applied: "#7c3aed",
  Screened: "#4f46e5",
  "Interview Scheduled": "#d97706",
  "Interview Completed": "#0284c7",
  Offer: "#c026d3",
  Hired: "#059669",
  Rejected: "#e11d48",
  Withdrawn: "#64748b",
}

function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
}

function layout(graph: ProcessGraph): Map<string, { x: number; y: number }> {
  const columns = new Map<number, typeof graph.nodes>()
  for (const node of graph.nodes) {
    const rank = RANK[node.activity] ?? 6
    const bucket = columns.get(rank) ?? []
    bucket.push(node)
    columns.set(rank, bucket)
  }
  const placed = new Map<string, { x: number; y: number }>()
  for (const [rank, bucket] of columns) {
    bucket.sort((left, right) => left.activity.localeCompare(right.activity))
    bucket.forEach((node, index) => {
      placed.set(node.id, { x: 40 + rank * 220, y: 40 + index * 110 })
    })
  }
  return placed
}

/** Deterministic SVG of the DFG for download (independent of the live React Flow DOM). */
export function graphToSvg(graph: ProcessGraph): string {
  const placed = layout(graph)
  const width = Math.max(640, ...[...placed.values()].map((point) => point.x + 200))
  const height = Math.max(360, ...[...placed.values()].map((point) => point.y + 90))
  const maxFrequency = Math.max(1, ...graph.edges.map((edge) => edge.frequency))
  const edges = graph.edges
    .map((edge) => {
      const from = placed.get(edge.source)
      const to = placed.get(edge.target)
      if (!from || !to) return ""
      const x1 = from.x + 180
      const y1 = from.y + 36
      const x2 = to.x
      const y2 = to.y + 36
      const stroke = 1.2 + (3.5 * edge.frequency) / maxFrequency
      return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#7c3aed" stroke-width="${stroke}" marker-end="url(#arrow)" />`
    })
    .join("\n")
  const nodes = graph.nodes
    .map((node) => {
      const point = placed.get(node.id)
      if (!point) return ""
      const tone = TONE[node.activity] ?? "#7c3aed"
      return `
      <g>
        <rect x="${point.x}" y="${point.y}" width="180" height="72" rx="14" fill="#ffffff" stroke="#e2e8f0" />
        <rect x="${point.x}" y="${point.y}" width="180" height="6" rx="3" fill="${tone}" />
        <text x="${point.x + 12}" y="${point.y + 30}" font-family="Segoe UI, sans-serif" font-size="13" font-weight="600" fill="#0f172a">${escapeXml(node.activity)}</text>
        <text x="${point.x + 12}" y="${point.y + 52}" font-family="Segoe UI, sans-serif" font-size="11" fill="#64748b">${node.case_count} cases</text>
      </g>`
    })
    .join("\n")
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#7c3aed" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#f8fafc" />
  ${edges}
  ${nodes}
</svg>`
}

export function downloadBlob(filename: string, blob: Blob): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export function downloadText(filename: string, text: string, mime: string): void {
  downloadBlob(filename, new Blob([text], { type: mime }))
}

export async function downloadGraphSvg(graph: ProcessGraph, filename = "hiring-process-map.svg"): Promise<void> {
  downloadText(filename, graphToSvg(graph), "image/svg+xml;charset=utf-8")
}

export async function downloadGraphPng(graph: ProcessGraph, filename = "hiring-process-map.png"): Promise<void> {
  const svg = graphToSvg(graph)
  const image = new Image()
  const svgUrl = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml;charset=utf-8" }))
  try {
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve()
      image.onerror = () => reject(new Error("Could not render the process map for PNG export."))
      image.src = svgUrl
    })
    const canvas = document.createElement("canvas")
    canvas.width = image.width || 1280
    canvas.height = image.height || 720
    const context = canvas.getContext("2d")
    if (!context) throw new Error("Canvas is unavailable in this browser.")
    context.fillStyle = "#f8fafc"
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0)
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((value) => {
        if (value) resolve(value)
        else reject(new Error("PNG encoding failed."))
      }, "image/png")
    })
    downloadBlob(filename, blob)
  } finally {
    URL.revokeObjectURL(svgUrl)
  }
}
