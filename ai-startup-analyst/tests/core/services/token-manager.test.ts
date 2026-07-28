import { describe, it, expect } from 'vitest';
import { TokenManager } from '@/core/services/token-manager';

describe('TokenManager', () => {
  it('should track token usage', () => {
    const manager = new TokenManager(50000);

    manager.track('executive-summary', { input: 1000, output: 500 });
    manager.track('problem-statement', { input: 800, output: 400 });

    const report = manager.getUsageReport();
    expect(report.used).toBe(2700);
    expect(report.budget).toBe(50000);
    expect(report.remaining).toBe(47300);
  });

  it('should estimate tokens for sections', () => {
    const manager = new TokenManager(50000);

    const estimate = manager.estimateForSections(['executive-summary', 'problem-statement']);
    expect(estimate).toBeGreaterThan(0);
  });

  it('should warn at threshold', () => {
    const manager = new TokenManager(1000, 0.5);
    const warnings: Array<{ current: number; limit: number }> = [];

    manager.onWarning = (current, limit) => warnings.push({ current, limit });

    manager.track('executive-summary', { input: 400, output: 200 });
    expect(warnings).toHaveLength(1);
  });

  it('should report budget exceeded', () => {
    const manager = new TokenManager(100);

    manager.track('executive-summary', { input: 60, output: 50 });

    expect(manager.canAfford('problem-statement')).toBe(false);
  });
});
