import { describe, it, expect } from 'vitest';
import { SectionRouter } from '@/core/services/section-router';
import { createRegistry } from '@/core/agents';
import { InputAnalysisResult } from '@/core/types/project';

describe('SectionRouter', () => {
  const registry = createRegistry();
  const router = new SectionRouter(registry);

  const baseAnalysis: InputAnalysisResult = {
    originalIdea: 'Test idea',
    type: 'saas',
    model: 'b2b',
    complexity: 'moderate',
    industry: 'test',
    hasHardware: false,
    hasRegulatoryRequirements: false,
    isTwoSidedMarketplace: false,
    requiresIntegrations: false,
  };

  it('should include always-relevant sections', () => {
    const sections = router.resolve(baseAnalysis);
    expect(sections).toContain('executive-summary');
    expect(sections).toContain('problem-statement');
    expect(sections).toContain('solution');
    expect(sections).toContain('launch-checklist');
  });

  it('should include TAM/SAM/SOM for non-agency types', () => {
    const sections = router.resolve(baseAnalysis);
    expect(sections).toContain('tam-sam-som');
    expect(sections).toContain('revenue-model');
  });

  it('should exclude TAM/SAM/SOM for agency type', () => {
    const agencyAnalysis = { ...baseAnalysis, type: 'agency' as const };
    const sections = router.resolve(agencyAnalysis);
    expect(sections).not.toContain('tam-sam-som');
    expect(sections).not.toContain('revenue-model');
  });

  it('should include technical architecture for complex projects', () => {
    const complexAnalysis = { ...baseAnalysis, complexity: 'complex' as const };
    const sections = router.resolve(complexAnalysis);
    expect(sections).toContain('technical-architecture');
  });

  it('should exclude technical architecture for simple projects', () => {
    const simpleAnalysis = { ...baseAnalysis, complexity: 'simple' as const };
    const sections = router.resolve(simpleAnalysis);
    expect(sections).not.toContain('technical-architecture');
  });

  it('should include API overview for SaaS type', () => {
    const sections = router.resolve(baseAnalysis);
    expect(sections).toContain('api-overview');
  });

  it('should exclude API overview for agency type', () => {
    const agencyAnalysis = { ...baseAnalysis, type: 'agency' as const };
    const sections = router.resolve(agencyAnalysis);
    expect(sections).not.toContain('api-overview');
  });
});
