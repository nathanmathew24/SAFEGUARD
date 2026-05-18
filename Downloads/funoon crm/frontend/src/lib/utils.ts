export function formatAED(amount: number): string {
  return `AED ${amount.toLocaleString('en-AE')}`
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function formatRelative(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'yesterday'
  if (diffDays < 7) return `${diffDays}d ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
  return formatDate(dateStr)
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(' ')
}

export function stageLabelMap(stage: string): string {
  const map: Record<string, string> = {
    inbound: 'Inbound',
    qualifying: 'Qualifying',
    proposal_sent: 'Proposal sent',
    negotiating: 'Negotiating',
    closed_won: 'Closed',
    live: 'Live',
    churned: 'Churned',
  }
  return map[stage] ?? stage
}
