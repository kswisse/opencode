import { SectionId } from '../types/project';
import { TOKEN_BUDGETS } from '../config';

export class TokenManager {
  private used = 0;
  private budget: number;
  private warningThreshold: number;
  onWarning?: (current: number, limit: number) => void;

  constructor(budget: number, warningPercent = 0.8) {
    this.budget = budget;
    this.warningThreshold = budget * warningPercent;
  }

  estimateForSections(sectionIds: SectionId[]): number {
    let total = 0;
    for (const id of sectionIds) {
      const est = TOKEN_BUDGETS[id];
      total += est.input + est.output;
    }
    return Math.ceil(total * 1.15); // 15% overhead
  }

  track(sectionId: SectionId, usage: { input: number; output: number }): void {
    this.used += usage.input + usage.output;

    if (this.used >= this.warningThreshold && this.onWarning) {
      this.onWarning(this.used, this.budget);
    }
  }

  canAfford(sectionId: SectionId): boolean {
    const est = TOKEN_BUDGETS[sectionId];
    return this.used + est.input + est.output <= this.budget;
  }

  getRemaining(): number {
    return Math.max(0, this.budget - this.used);
  }

  getUsageReport() {
    return {
      used: this.used,
      budget: this.budget,
      remaining: this.getRemaining(),
      percentUsed: Math.round((this.used / this.budget) * 100),
    };
  }
}
