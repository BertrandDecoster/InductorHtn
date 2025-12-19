/**
 * Split a solution string into individual operators.
 * Only splits on ", " at parenthesis depth 0 (outside of parentheses).
 * This correctly handles operators like "opMoveTo(player, roomNW, corridorW)"
 * without breaking them apart at internal commas.
 */
export function splitOperators(str) {
  if (!str || str.trim() === '') return []

  const operators = []
  let depth = 0
  let current = ''

  for (let i = 0; i < str.length; i++) {
    const char = str[i]
    if (char === '(') depth++
    else if (char === ')') depth--
    else if (char === ',' && depth === 0 && str[i + 1] === ' ') {
      if (current.trim()) operators.push(current.trim())
      current = ''
      i++ // skip the space
      continue
    }
    current += char
  }

  if (current.trim()) operators.push(current.trim())
  return operators
}
