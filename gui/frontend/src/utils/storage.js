const STORAGE_KEYS = {
  LAST_FILE: 'indhtn_last_file',
  HTN_QUERIES: 'indhtn_htn_queries',
  PROLOG_QUERIES: 'indhtn_prolog_queries'
}

const MAX_HISTORY = 10

export function getLastFile() {
  return localStorage.getItem(STORAGE_KEYS.LAST_FILE)
}

export function setLastFile(filePath) {
  localStorage.setItem(STORAGE_KEYS.LAST_FILE, filePath)
}

export function getQueryHistory(type) {
  const key = type === 'htn' ? STORAGE_KEYS.HTN_QUERIES : STORAGE_KEYS.PROLOG_QUERIES
  const stored = localStorage.getItem(key)
  return stored ? JSON.parse(stored) : []
}

export function addQueryToHistory(type, query) {
  const key = type === 'htn' ? STORAGE_KEYS.HTN_QUERIES : STORAGE_KEYS.PROLOG_QUERIES
  let history = getQueryHistory(type)

  // Remove duplicate if exists, then add to front
  history = history.filter(q => q !== query)
  history.unshift(query)

  // Keep max 10
  history = history.slice(0, MAX_HISTORY)

  localStorage.setItem(key, JSON.stringify(history))
  return history
}
