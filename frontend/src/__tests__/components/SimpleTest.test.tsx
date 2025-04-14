/// <reference types="vitest/globals" />
/// <reference types="@testing-library/jest-dom" />

import { describe, it, expect } from 'vitest';

describe('Simple Tests', () => {
  it('should perform basic math operations', () => {
    expect(1 + 1).toBe(2);
    expect(2 * 3).toBe(6);
    expect(10 - 5).toBe(5);
  });

  it('should manipulate strings correctly', () => {
    expect('hello' + ' world').toBe('hello world');
    expect('EverRaise'.toLowerCase()).toBe('everraise');
    expect('data analysis'.toUpperCase()).toBe('DATA ANALYSIS');
  });

  it('should handle arrays properly', () => {
    const arr = [1, 2, 3];
    expect(arr).toHaveLength(3);
    expect(arr).toContain(2);
    expect(arr.map(x => x * 2)).toEqual([2, 4, 6]);
  });
}); 