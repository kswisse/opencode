import { AgentRegistry } from './registry';
import { executiveSummaryAgent } from './definitions/executive-summary';
import { problemStatementAgent } from './definitions/problem-statement';
import { solutionAgent } from './definitions/solution';
import { targetCustomersAgent } from './definitions/target-customers';
import { customerPersonasAgent } from './definitions/customer-personas';
import { tamSamSomAgent } from './definitions/tam-sam-som';
import { competitorAnalysisAgent } from './definitions/competitor-analysis';
import { swotAnalysisAgent } from './definitions/swot-analysis';
import { businessModelCanvasAgent } from './definitions/business-model-canvas';
import { revenueModelAgent } from './definitions/revenue-model';
import { pricingStrategyAgent } from './definitions/pricing-strategy';
import { goToMarketStrategyAgent } from './definitions/go-to-market-strategy';
import { mvpDefinitionAgent } from './definitions/mvp-definition';
import { featurePrioritizationAgent } from './definitions/feature-prioritization';
import { technicalArchitectureAgent } from './definitions/technical-architecture';
import { suggestedTechStackAgent } from './definitions/suggested-tech-stack';
import { databaseDesignAgent } from './definitions/database-design';
import { apiOverviewAgent } from './definitions/api-overview';
import { uiSitemapAgent } from './definitions/ui-sitemap';
import { productRoadmapAgent } from './definitions/product-roadmap';
import { riskAnalysisAgent } from './definitions/risk-analysis';
import { financialAssumptionsAgent } from './definitions/financial-assumptions';
import { launchChecklistAgent } from './definitions/launch-checklist';

export function createRegistry(): AgentRegistry {
  const registry = new AgentRegistry();

  const agents = [
    executiveSummaryAgent,
    problemStatementAgent,
    solutionAgent,
    targetCustomersAgent,
    customerPersonasAgent,
    tamSamSomAgent,
    competitorAnalysisAgent,
    swotAnalysisAgent,
    businessModelCanvasAgent,
    revenueModelAgent,
    pricingStrategyAgent,
    goToMarketStrategyAgent,
    mvpDefinitionAgent,
    featurePrioritizationAgent,
    technicalArchitectureAgent,
    suggestedTechStackAgent,
    databaseDesignAgent,
    apiOverviewAgent,
    uiSitemapAgent,
    productRoadmapAgent,
    riskAnalysisAgent,
    financialAssumptionsAgent,
    launchChecklistAgent,
  ];

  // Topological sort: register agents only after their dependencies are registered
  const registered = new Set<string>();
  const maxIterations = agents.length * 2;
  let iteration = 0;

  while (registered.size < agents.length && iteration < maxIterations) {
    iteration++;
    for (const agent of agents) {
      if (registered.has(agent.id)) continue;

      // Check if all dependencies are registered
      const depsMet = agent.dependencies.every(dep => registered.has(dep));
      if (depsMet) {
        registry.register(agent);
        registered.add(agent.id);
      }
    }
  }

  if (registered.size < agents.length) {
    const missing = agents.filter(a => !registered.has(a.id)).map(a => a.id);
    throw new Error(`Could not register all agents. Missing: ${missing.join(', ')}`);
  }

  return registry;
}

export const registry = createRegistry();
