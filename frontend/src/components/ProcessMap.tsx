import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
  type EdgeMouseHandler,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { formatCount, formatDuration } from "../lib/format.ts"
import type { ProcessEdge, ProcessGraph, ProcessNode } from "../api/types.ts"

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

function StageNode({ data }: { data: Record<string, unknown> }) {
  const activity = String(data.activity ?? "")
  const tone = TONE[activity] ?? "#7c3aed"
  return (
    <div
      data-testid={`node-${activity}`}
      className="w-[196px] rounded-2xl border border-[var(--color-line)] bg-[var(--color-card)] px-3 py-2 shadow-sm"
      style={{ borderTop: `4px solid ${tone}` }}
    >
      <p className="text-sm font-semibold leading-5">{activity}</p>
      <p className="tabular mt-1 text-xs text-[var(--color-muted)]">
        {formatCount(Number(data.case_count ?? 0))} cases · {formatCount(Number(data.event_count ?? 0))} events
      </p>
    </div>
  )
}

const nodeTypes = { stage: StageNode }

function positions(nodes: ProcessNode[]): Map<string, { x: number; y: number }> {
  const columns = new Map<number, ProcessNode[]>()
  for (const node of nodes) {
    const rank = RANK[node.activity] ?? 6
    const bucket = columns.get(rank) ?? []
    bucket.push(node)
    columns.set(rank, bucket)
  }
  const placed = new Map<string, { x: number; y: number }>()
  for (const [rank, bucket] of columns) {
    bucket.sort((left, right) => left.activity.localeCompare(right.activity))
    bucket.forEach((node, index) => {
      placed.set(node.id, { x: rank * 240, y: index * 128 })
    })
  }
  return placed
}

export function ProcessMap({
  graph,
  onNode,
  onEdge,
}: {
  graph: ProcessGraph
  onNode: (node: ProcessNode) => void
  onEdge: (edge: ProcessEdge) => void
}) {
  const maxFrequency = Math.max(1, ...graph.edges.map((edge) => edge.frequency))
  const maxDelay = Math.max(
    1,
    ...graph.edges.map((edge) => edge.median_delay_seconds ?? 0),
  )
  const placed = positions(graph.nodes)
  const nodes: Node[] = graph.nodes.map((node) => ({
    id: node.id,
    type: "stage",
    position: placed.get(node.id) ?? { x: 0, y: 0 },
    data: { ...node },
    draggable: true,
  }))
  const edges: Edge[] = graph.edges.map((edge) => {
    const delay = edge.median_delay_seconds ?? 0
    const hot = delay > maxDelay * 0.72
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: formatCount(edge.case_count),
      style: {
        stroke: hot ? "#d97706" : "#7c3aed",
        strokeWidth: 1.4 + (4.2 * edge.frequency) / maxFrequency,
      },
      labelStyle: { fontSize: 11, fontWeight: 600 },
    }
  })
  const selectNode: NodeMouseHandler = (_event, node) => {
    const match = graph.nodes.find((item) => item.id === node.id)
    if (match) onNode(match)
  }
  const selectEdge: EdgeMouseHandler = (_event, edge) => {
    const match = graph.edges.find((item) => item.id === edge.id)
    if (match) onEdge(match)
  }
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={selectNode}
      onEdgeClick={selectEdge}
      fitView
      fitViewOptions={{ padding: 0.18 }}
      minZoom={0.2}
      nodesConnectable={false}
      proOptions={{ hideAttribution: false }}
      aria-label="Hiring process map"
    >
      <Background gap={18} color="rgba(124, 58, 237, 0.18)" />
      <MiniMap pannable zoomable />
      <Controls showInteractive={false} />
    </ReactFlow>
  )
}

export function delayLabel(seconds: number | null): string {
  return formatDuration(seconds)
}
