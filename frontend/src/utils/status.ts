export interface StatusInfo {
  label: string;
  badgeColor: string;
  bgColor: string;
  borderColor: string;
  icon: string;
  category: 'satisfied' | 'attention' | 'insufficient';
  desc: string;
}

export function mapStatus(rawStatus?: string): StatusInfo {
  const raw = (rawStatus || '').toUpperCase();
  if (raw === 'COMPLIANT' || raw === 'SATISFIED') {
    return {
      label: 'Compliant',
      badgeColor: '#15803d',
      bgColor: '#dcfce7',
      borderColor: '#86efac',
      icon: '✅',
      category: 'satisfied',
      desc: 'The available evidence supports the applicable requirement.',
    };
  } else if (
    raw === 'PARTIALLY_COMPLIANT' ||
    raw === 'POTENTIALLY_NON_COMPLIANT' ||
    raw === 'NEEDS_ATTENTION' ||
    raw === 'NON_COMPLIANT'
  ) {
    return {
      label: 'Needs Attention',
      badgeColor: '#b45309',
      bgColor: '#fef3c7',
      borderColor: '#fcd34d',
      icon: '⚠️',
      category: 'attention',
      desc: 'A potential regulatory gap or issue was identified.',
    };
  } else {
    // MISSING_EVIDENCE, NEEDS_REVIEW, INSUFFICIENT_INFORMATION
    return {
      label: 'Insufficient Information',
      badgeColor: '#1d4ed8',
      bgColor: '#dbeafe',
      borderColor: '#93c5fd',
      icon: 'ℹ️',
      category: 'insufficient',
      desc: 'There is not enough evidence in the uploaded document to reach a conclusion.',
    };
  }
}

export function formatDate(dtStr?: string): string {
  if (!dtStr) return 'N/A';
  try {
    const cleaned = dtStr.replace('Z', '+00:00');
    const dt = new Date(cleaned);
    if (isNaN(dt.getTime())) {
      return String(dtStr).slice(0, 19);
    }
    return dt.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return String(dtStr).slice(0, 19);
  }
}
