/**
 * Utility functions for the frontend application
 */

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistance } from 'date-fns'

/**
 * Merge Tailwind CSS classes with proper precedence
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format a date string to a readable format
 */
export function formatDate(date: string | Date, formatStr: string = 'PPP'): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return format(dateObj, formatStr)
}

/**
 * Format a relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return formatDistance(dateObj, new Date(), { addSuffix: true })
}

/**
 * Format a number with commas
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num)
}

/**
 * Format bytes to human-readable size
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * Truncate text to a maximum length
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * Download a file from a blob
 */
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

/**
 * Parse CSV data to JSON
 */
export function parseCsv(csv: string): any[] {
  const lines = csv.split('\n')
  const headers = lines[0].split(',').map(h => h.trim())
  
  return lines.slice(1).map(line => {
    const values = line.split(',').map(v => v.trim())
    return headers.reduce((obj, header, index) => {
      obj[header] = values[index]
      return obj
    }, {} as any)
  })
}

/**
 * Get cognitive label color
 */
export function getCognitiveColor(label: string): string {
  const colors: Record<string, string> = {
    FollowingScent: 'bg-green-100 text-green-700 border-green-300',
    ApproachingSource: 'bg-blue-100 text-blue-700 border-blue-300',
    DietEnrichment: 'bg-purple-100 text-purple-700 border-purple-300',
    PoorScent: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    LeavingPatch: 'bg-red-100 text-red-700 border-red-300',
    ForagingSuccess: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  }
  return colors[label] || 'bg-gray-100 text-gray-700 border-gray-300'
}

/**
 * Validate session data format
 */
export function validateSessionData(data: any): { valid: boolean; errors: string[] } {
  const errors: string[] = []
  
  if (!data.session_id) {
    errors.push('Missing session_id field')
  }
  
  if (!Array.isArray(data.events)) {
    errors.push('Events must be an array')
  } else {
    data.events.forEach((event: any, index: number) => {
      if (!event.event_id) {
        errors.push(`Event ${index} missing event_id`)
      }
      if (!event.timestamp) {
        errors.push(`Event ${index} missing timestamp`)
      }
      if (!event.action_type) {
        errors.push(`Event ${index} missing action_type`)
      }
      if (!event.content) {
        errors.push(`Event ${index} missing content`)
      }
    })
  }
  
  return {
    valid: errors.length === 0,
    errors,
  }
}

/**
 * Sleep for a specified duration
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Debounce a function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  
  return function (...args: Parameters<T>) {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error('Failed to copy:', err)
    return false
  }
}

