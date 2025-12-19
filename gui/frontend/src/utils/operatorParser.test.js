import { describe, it, expect } from 'vitest'
import { splitOperators } from './operatorParser'

describe('splitOperators', () => {
  it('returns single operator unchanged', () => {
    expect(splitOperators('opWalk(a, b)')).toEqual(['opWalk(a, b)'])
  })

  it('splits multiple simple operators', () => {
    expect(splitOperators('op1(), op2()')).toEqual(['op1()', 'op2()'])
  })

  it('keeps operator arguments together', () => {
    // KEY TEST: This is the bug - naive split breaks this
    const input = 'opMoveTo(player, roomNW, corridorW)'
    expect(splitOperators(input)).toEqual(['opMoveTo(player, roomNW, corridorW)'])
  })

  it('handles multiple operators with arguments', () => {
    const input = 'opMoveTo(player, roomNW), opAttack(enemy, sword)'
    expect(splitOperators(input)).toEqual([
      'opMoveTo(player, roomNW)',
      'opAttack(enemy, sword)'
    ])
  })

  it('handles nested parentheses', () => {
    const input = 'op1(a, foo(x, y)), op2(b)'
    expect(splitOperators(input)).toEqual(['op1(a, foo(x, y))', 'op2(b)'])
  })

  it('handles empty string', () => {
    expect(splitOperators('')).toEqual([])
  })

  it('handles single operator no args', () => {
    expect(splitOperators('opDone()')).toEqual(['opDone()'])
  })
})
