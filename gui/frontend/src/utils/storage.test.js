import { describe, it, expect, beforeEach } from 'vitest'
import { getLastFile, setLastFile, getQueryHistory, addQueryToHistory } from './storage'

describe('storage utilities', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('getLastFile / setLastFile', () => {
    it('returns null when no file stored', () => {
      expect(getLastFile()).toBeNull()
    })

    it('returns stored file path after setLastFile', () => {
      setLastFile('Examples/Taxi.htn')
      expect(getLastFile()).toBe('Examples/Taxi.htn')
    })

    it('overwrites previous value', () => {
      setLastFile('Examples/Taxi.htn')
      setLastFile('Examples/Game.htn')
      expect(getLastFile()).toBe('Examples/Game.htn')
    })
  })

  describe('getQueryHistory', () => {
    it('returns empty array when no history stored', () => {
      expect(getQueryHistory('htn')).toEqual([])
      expect(getQueryHistory('prolog')).toEqual([])
    })

    it('returns stored array for htn type', () => {
      localStorage.setItem('indhtn_htn_queries', JSON.stringify(['query1.', 'query2.']))
      expect(getQueryHistory('htn')).toEqual(['query1.', 'query2.'])
    })

    it('returns stored array for prolog type', () => {
      localStorage.setItem('indhtn_prolog_queries', JSON.stringify(['at(?x).']))
      expect(getQueryHistory('prolog')).toEqual(['at(?x).'])
    })
  })

  describe('addQueryToHistory', () => {
    it('adds query to empty history', () => {
      const result = addQueryToHistory('htn', 'travel-to(park).')
      expect(result).toEqual(['travel-to(park).'])
      expect(getQueryHistory('htn')).toEqual(['travel-to(park).'])
    })

    it('adds query to front of existing history', () => {
      addQueryToHistory('htn', 'first.')
      const result = addQueryToHistory('htn', 'second.')
      expect(result[0]).toBe('second.')
      expect(result[1]).toBe('first.')
    })

    it('removes duplicate before adding', () => {
      addQueryToHistory('htn', 'query.')
      addQueryToHistory('htn', 'other.')
      const result = addQueryToHistory('htn', 'query.')
      expect(result).toEqual(['query.', 'other.'])
    })

    it('limits to 10 items', () => {
      for (let i = 1; i <= 12; i++) {
        addQueryToHistory('htn', `query${i}.`)
      }
      const result = getQueryHistory('htn')
      expect(result).toHaveLength(10)
      expect(result[0]).toBe('query12.')
      expect(result[9]).toBe('query3.')
    })

    it('returns the updated history array', () => {
      const result = addQueryToHistory('prolog', 'at(?x).')
      expect(Array.isArray(result)).toBe(true)
      expect(result).toContain('at(?x).')
    })
  })
})
