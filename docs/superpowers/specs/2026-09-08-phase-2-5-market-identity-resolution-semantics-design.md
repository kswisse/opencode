# Phase 2.5 — Market Identity & Resolution Semantics: Domain Analysis

**Analyst**: Quinn (Investment Researcher)  
**Date**: 2026-09-08  
**Purpose**: Establish domain foundation for distinguishing "similar contracts" from "economically equivalent contracts" in a quantitative prediction market research engine.

---

## Table of Contents

1. [Prediction Market Contract Semantics](#1-prediction-market-contract-semantics)
2. [Resolution Rule Analysis](#2-resolution-rule-analysis)
3. [Expiry and Settlement Semantics](#3-expiry-and-settlement-semantics)
4. [Cross-Venue Economic Equivalence](#4-cross-venue-economic-equivalence)
5. [Edge Cases and Adversarial Examples](#5-edge-cases-and-adversarial-examples)
6. [Explicit Mapping Requirements](#6-explicit-mapping-requirements)
7. [Domain Model Requirements](#7-domain-model-requirements)

---

## 1. Prediction Market Contract Semantics

### 1.1 What Makes Two Contracts "The Same Event"

Two contracts reference **the same event** if and only if they satisfy all of the following:

| Criterion | Definition | Example Violation |
|-----------|------------|-------------------|
| **Event Identity** | The underlying real-world phenomenon being predicted is identical | "Will Candidate X win?" vs "Will Candidate X receive >50%?" — the event is "winning" vs "receiving >50%"; these are different events even when outcome is usually identical |
| **Temporal Scope** | The time window over which the event is observed is identical | "Will BTC hit $100k today?" vs "Will BTC hit $100k this week?" — different temporal scopes |
| **Event Boundary** | The start and end conditions for the event are identical | "Will Company Y be acquired before 2027?" vs "Will Company Y be acquired before Q1 2027 ends?" — subtly different boundaries |

**Formal Definition**: Contract A and Contract B reference the same event iff:

```
Event(A) = Event(B) ⟺
  Subject(A) = Subject(B) ∧
  TemporalScope(A) = TemporalScope(B) ∧
  EventBoundary(A) = EventBoundary(B)
```

Where:
- `Subject` = the real-world phenomenon being predicted
- `TemporalScope` = the time window for observation
- `EventBoundary` = the precise start/end conditions

### 1.2 What Makes Two Contracts "The Same Outcome"

Two contracts share **the same outcome** if and only if they resolve identically whenever the underlying event resolves. This requires:

| Criterion | Definition |
|-----------|------------|
| **Outcome Equivalence** | For all possible resolutions of Event(A) and Event(B), both contracts pay out to the same party |
| **Resolution Compatibility** | The resolution conditions are logically equivalent — not just coincidentally aligned |

**Key Distinction**: "Same outcome" is a subset of "same event." Two contracts can reference the same event but have different outcomes (e.g., a binary market vs a multi-outcome market on the same election).

### 1.3 What Makes Two Contracts "Opposite Outcomes"

Two contracts are **opposite outcomes** if and only if:

```
Opposite(A, B) ⟺
  ForAll(event_resolutions):
    Payoff(A, resolution) = 1 - Payoff(B, resolution)
    AND Payoff(A, resolution) + Payoff(B, resolution) = 1
```

**Properties**:
- Opposite contracts are necessarily on the same event (same subject, temporal scope, boundary)
- If Outcome(A) = YES and Outcome(B) = NO for binary markets, they are opposites
- If Outcome(A) = "X > 50%" and Outcome(B) = "X ≤ 50%", they are opposites
- The sum of prices for opposite contracts should equal 1.00 (minus fees/spread) in an efficient market

**Edge Case**: Opposite contracts are NOT the same as "complementary" contracts. In multi-outcome markets, contracts on outcomes A and B are complementary if A ∪ B covers all possibilities, but they are not opposites unless A and B are the only two outcomes.

### 1.4 Resolution Source Importance

The resolution source is the **authoritative mechanism** that determines the outcome. Two contracts on the same event can resolve differently if they use different resolution sources.

| Source Type | Description | Risk Profile |
|-------------|-------------|--------------|
| **Official Government Source** | Regulatory filings, election results from official bodies | Low ambiguity, high credibility, may have reporting delays |
| **Designated Data Provider** | Bloomberg, Reuters, specific API endpoints | Medium ambiguity (API changes, outages), high credibility |
| **Market Consensus** | Aggregate of multiple sources, often with fallback rules | Higher ambiguity, may have edge cases around conflicting sources |
| **Manual Resolution** | Platform operator decides | Highest ambiguity, governance risk |

**Critical Rule**: Two contracts are economically equivalent only if they use the **same resolution source** OR if their resolution sources are provably equivalent for the event in question.

### 1.5 Settlement Timing Importance

Settlement timing determines **when** the contract pays out, which creates:

- **Time Value of Money**: Earlier settlement is more valuable
- **Reinvestment Opportunity**: Earlier settlement allows capital redeployment
- **Risk Window**: Longer settlement windows expose to counterparty risk
- **Arbitrage Timing Risk**: Cross-venue arbitrage profits depend on settlement timing alignment

**Rule**: Two contracts with different settlement timing are NOT economically equivalent, even if they resolve to the same outcome. The price difference should reflect the time value differential.

---

## 2. Resolution Rule Analysis

### 2.1 How Resolution Rules Determine Economic Equivalence

Resolution rules define the **mapping from real-world events to contract outcomes**. Two contracts are economically equivalent only if their resolution rules produce identical outcomes for all possible event states.

**Formal Test**: Let `R(A, s)` be the resolution function for contract A given world state `s`. Contracts A and B are economically equivalent only if:

```
ForAll(s ∈ PossibleWorlds): R(A, s) = R(B, s)
```

### 2.2 Resolution Source Analysis

#### 2.2.1 Source Hierarchy

```
Tier 1: Official Primary Source (e.g., Associated Press for elections, FDA for approvals)
Tier 2: Designated Secondary Source (e.g., Bloomberg Terminal for price data)
Tier 3: Market Consensus with Defined Rules
Tier 4: Platform Operator Discretion
```

**Key Consideration**: When contract A uses Tier 1 source and contract B uses Tier 2 source, they may resolve differently if:
- Tier 2 source has errors or delays
- Tier 2 source uses different methodology
- There is ambiguity in the event definition that the sources interpret differently

#### 2.2.2 Source Disambiguation Rules

For price-based contracts, resolution sources must specify:

1. **Price Feed**: Which specific API/data provider (e.g., `BTC-USD-PRICE` on Coinbase vs `BTC-USD` on Binance)
2. **Price Type**: Last trade, volume-weighted average, bid-ask midpoint, closing price
3. **Price Timestamp**: Exact moment of price observation (e.g., "12:00:00 UTC exactly" vs "at any point during 12:00-12:01 UTC")
4. **Fallback Rules**: What happens if the primary source is unavailable

### 2.3 Resolution Condition Analysis

#### 2.3.1 Threshold Types

| Type | Example | Economic Properties |
|------|---------|-------------------|
| **Exact Threshold** | "BTC > $100,000" | Binary outcome, sensitive to exact price |
| **Range** | "BTC between $95,000 and $105,000" | Binary outcome, less sensitive to price volatility |
| **Relative Change** | "BTC up >10% from current price" | Depends on reference price, may create circularity |
| **Multi-Threshold** | "Candidate X wins by >5% margin" | Binary outcome, dependent on margin calculation |

#### 2.3.2 Threshold Precision

Contracts must specify:
- **Decimal Precision**: "BTC > $100,000.00" vs "BTC > $100,000" (the latter typically means > $100,000.00)
- **Rounding Rules**: How prices with more decimals are handled
- **Boundary Conditions**: Whether the threshold itself is included (e.g., "≥" vs ">")

### 2.4 Valid Resolution Outcomes

Each contract must define the complete set of valid resolution outcomes:

| Outcome Set | Example | Properties |
|-------------|---------|------------|
| **Binary** | YES/NO | Simplest case, always exactly one outcome |
| **Multi-Outcome Mutually Exclusive** | "Candidate A wins", "Candidate B wins", "Other wins" | Exactly one outcome, outcomes partition the space |
| **Multi-Outcome Non-Exclusive** | "Candidate A wins", "Candidate B wins" (independent markets) | Multiple outcomes can be true simultaneously |
| **Range-Based** | "BTC closes between $90k-$95k", "$95k-$100k", "$100k-$105k", etc. | Must cover all possible outcomes, no gaps |

**Critical Rule**: Multi-outcome markets where outcomes are NOT mutually exclusive and NOT collectively exhaustive create arbitrage opportunities that are actually FALSE positives — the sum of contract prices may exceed 1.00 legitimately.

### 2.5 Unresolved/Void/Cancelled Possibilities

Contracts must handle:

| Condition | Definition | Economic Impact |
|-----------|------------|-----------------|
| **Void Event** | Event does not occur (e.g., election is cancelled) | All contracts on the event may resolve to 0 or be refunded |
| **Suspended Market** | Trading suspended but event still occurs | Arbitrage timing risk increases |
| **Disputed Resolution** | Challenge to resolution source or outcome | Uncertainty window, potential for re-resolution |
| **Platform Default** | Platform cannot pay out | Counterparty risk, potential total loss |

**Key Rule**: Two contracts are economically equivalent only if they handle void/cancelled scenarios identically. If contract A refunds in void scenarios and contract B resolves to NO, they are NOT equivalent even though they look equivalent in normal scenarios.

---

## 3. Expiry and Settlement Semantics

### 3.1 Expiration Timestamp vs Resolution Timestamp

| Timestamp | Definition | Economic Significance |
|-----------|------------|---------------------|
| **Expiration Timestamp** | When the contract stops accepting new positions | Determines the last moment to enter/exit |
| **Resolution Timestamp** | When the outcome is determined | Determines when settlement begins |
| **Settlement Timestamp** | When funds are distributed | Determines when capital is available |

**Critical Distinction**: Two contracts can have the same expiration timestamp but different resolution timestamps if:
- One contract resolves at expiration and the other has a grace period
- Resolution depends on a source that reports with delay
- There is a dispute resolution window

### 3.2 Settlement Compatibility Requirements

For two contracts to be treated as economically equivalent for cross-venue arbitrage:

```
SettlementCompatible(A, B) ⟺
  ResolutionTime(A) = ResolutionTime(B) ∨ |ResolutionTime(A) - ResolutionTime(B)| < Threshold
  AND SettlementMechanism(A) = SettlementMechanism(B)
  AND SettlementCurrency(A) = SettlementCurrency(B)
  AND SettlementDelay(A) ≈ SettlementDelay(B)
```

**Threshold**: The maximum acceptable time difference between resolution timestamps depends on:
- Interest rate environment (higher rates → lower threshold)
- Capital opportunity cost (higher opportunity cost → lower threshold)
- Platform counterparty risk (higher risk → lower threshold)

### 3.3 When Two Contracts Can Be Treated as Economically Equivalent

Two contracts are economically equivalent (and thus eligible for true arbitrage) if and only if:

```
EconomicallyEquivalent(A, B) ⟺
  SameEvent(A, B) ∧
  SameOutcome(A, B) ∨ OppositeOutcome(A, B) ∨
  SameResolutionSource(A, B) ∨ EquivalentResolutionSource(A, B) ∨
  SettlementCompatible(A, B) ∧
  NoVoidScenarioMismatch(A, B)
```

**Definition**: Two contracts are economically equivalent if and only if, for every possible world state, they yield identical economic outcomes (payoffs, timing, and settlement).

---

## 4. Cross-Venue Economic Equivalence

### 4.1 True Arbitrage vs Relative Value Trade

| Classification | Conditions | Risk Profile |
|----------------|------------|--------------|
| **True Arbitrage** | Same event, same outcome (or opposite), same resolution source, settlement compatible, no transfer risk | Near-riskless profit, limited by execution speed and fees |
| **Relative Value Trade** | Similar event, similar outcome, different resolution source, or settlement incompatible | Profit depends on correlation between contracts, exposed to basis risk |

**Decision Rule**: A cross-venue opportunity is true arbitrage IFF all of the following hold:
1. The events are identical (same subject, temporal scope, boundary)
2. The outcomes are identical or opposite
3. The resolution sources are equivalent or identical
4. Settlement timing is compatible (within threshold)
5. There is no void scenario mismatch
6. Transfer between venues is possible within the settlement window
7. Fees + slippage < price differential

### 4.2 Transfer Risk

Transfer risk is the risk that capital cannot be moved between venues in time to exploit the arbitrage:

| Risk Factor | Description | Mitigation |
|-------------|-------------|------------|
| **Transfer Delay** | Time to move funds between venues | Pre-position capital on both venues |
| **Transfer Limits** | Venue-imposed withdrawal/deposit limits | Maintain sufficient balances |
| **Transfer Fees** | Network/gas fees for transfers | Include in arbitrage calculation |
| **Transfer Failure** | Technical failures preventing transfer | Have backup transfer methods |

**Key Rule**: If transfer time > (resolution time difference between venues), the opportunity is NOT true arbitrage regardless of price differential.

### 4.3 Settlement Risk Across Venues

Settlement risk arises when:
- One venue settles before the other (asymmetric settlement)
- One venue delays or fails to settle
- Settlement amounts differ due to fees or adjustments

**Mitigation**: True arbitrage requires symmetric settlement — both venues settle at approximately the same time with the same amount.

---

## 5. Edge Cases and Adversarial Examples

### 5.1 Contracts That LOOK Equivalent But Aren't

#### Example 1: Election Win vs Majority Vote

| Contract A | Contract B |
|------------|------------|
| "Will Candidate X win the 2028 Presidential Election?" | "Will Candidate X receive >50% of the popular vote?" |

**Why they're NOT equivalent**:
- Candidate can win the Electoral College without a popular vote majority (e.g., 2000, 2016)
- Resolution source: A resolves based on Electoral College results; B resolves based on popular vote count
- In a multi-candidate race, a candidate could win with <50% popular vote

#### Example 2: Point-in-Time vs Path-Dependent

| Contract A | Contract B |
|------------|------------|
| "Will BTC be above $100,000 at 12:00 UTC on 2026-12-31?" | "Will BTC ever reach $100,000 before the end of 2026?" |

**Why they're NOT equivalent**:
- A is path-independent: only the price at 12:00 UTC matters
- B is path-dependent: any touch of $100k triggers YES resolution
- If BTC reaches $100k at 11:00 UTC then drops to $90k by 12:00 UTC, A resolves NO and B resolves YES

#### Example 3: Different Resolution Windows

| Contract A | Contract B |
|------------|------------|
| "Will it rain in NYC on July 4, 2026?" | "Will it rain in NYC at any point on July 4, 2026?" |

**Why they're NOT equivalent**:
- "On July 4" typically means daily average or specific measurement time
- "At any point" means any minute during the day
- A thunderstorm at 3:00 AM that clears by noon may resolve differently

#### Example 4: Different Resolution Sources

| Contract A (Polymarket) | Contract B (Kalshi) |
|-------------------------|---------------------|
| "Will the Fed cut rates in September 2026?" (resolves based on FOMC announcement) | "Will the Fed cut rates in September 2026?" (resolves based on CME FedWatch consensus) |

**Why they're NOT equivalent**:
- If FOMC announces a cut but it's disputed or delayed, resolution sources may disagree
- CME FedWatch is market-implied, not official announcement
- Timing of resolution: A resolves at FOMC announcement, B may resolve based on market close

#### Example 5: Multi-Outcome vs Binary

| Contract A | Contract B |
|------------|------------|
| "Which party will win the 2028 election?" (multi-outcome: Democrat, Republican, Other) | "Will the Republican candidate win the 2028 election?" (binary: YES/NO) |

**Why they LOOK different but may be equivalent for specific positions**:
- A Republican YES in B is economically equivalent to the Republican outcome in A
- But the market structures are fundamentally different (mutually exclusive outcomes vs independent binary)

### 5.2 Contracts That ARE Equivalent But Look Different

#### Example 1: Rephrased Questions

| Contract A | Contract B |
|------------|------------|
| "Will the S&P 500 close above 5,000 on 2026-12-31?" | "Will the S&P 500 index value be greater than 5,000 at market close on December 31, 2026?" |

**Why they ARE equivalent**:
- Same event (S&P 500 closing price)
- Same temporal scope (December 31, 2026)
- Same outcome (>5,000)
- Same resolution source (official S&P 500 closing price)

#### Example 2: Complementary Binary Markets

| Contract A | Contract B |
|------------|------------|
| "Will Candidate X win?" (YES/NO) | "Will Candidate Y win?" (YES/NO) in a two-candidate race |

**Why they ARE equivalent (as opposites)**:
- If only two candidates, A and B are exact opposites
- A YES = B NO, A NO = B YES
- Sum of prices should equal 1.00

#### Example 3: Different Platform Formatting

| Contract A (Polymarket) | Contract B (Kalshi) |
|-------------------------|---------------------|
| "ETH above $5,000 on 2026-12-31?" (YES = above) | "ETH at or above $5,000 on 2026-12-31?" (YES = at or above) |

**Why they ARE equivalent** (assuming $5,000 is exactly the threshold):
- The difference between ">" and "≥" only matters if ETH is exactly $5,000.00
- In practice, ETH prices are quoted to 2 decimals, so the probability of being exactly $5,000.00 is negligible
- For practical purposes, these resolve identically

### 5.3 False Positive Arbitrage Scenarios

A false positive occurs when the system detects an arbitrage opportunity that doesn't actually exist:

#### Scenario 1: Apparent Price Divergence Due to Different Resolution Sources

- Contract A (Polymarket): "Will it rain in NYC?" at $0.60 (resolves based on NYC weather station)
- Contract B (Kalshi): "Will it rain in NYC?" at $0.40 (resolves based on Central Park weather station)
- **False Arbitrage**: Buy B, sell A. But the resolution sources are different — Central Park vs a different NYC station may report differently.

#### Scenario 2: Apparent Price Divergence Due to Different Temporal Definitions

- Contract A: "Will BTC be above $100k on 2026-12-31?" at $0.55
- Contract B: "Will BTC be above $100k at 12:00 UTC on 2026-12-31?" at $0.45
- **False Arbitrage**: Buy B, sell A. But A may resolve based on closing price (5pm EST), not 12:00 UTC.

#### Scenario 3: Apparent Price Divergence Due to Void Scenarios

- Contract A: "Will the election happen?" at $0.95
- Contract B: "Will Candidate X win?" at $0.45
- **False Arbitrage**: These are not on the same event. B assumes the election happens; A is about whether it happens at all.

### 5.4 False Negative Arbitrage Scenarios

A false negative occurs when the system misses a legitimate arbitrage opportunity:

#### Scenario 1: Different Phrasing, Same Event

- Contract A: "Will the Fed cut rates in September?" at $0.70
- Contract B: "Will there be a 25bp+ rate reduction in September 2026?" at $0.35
- **Missed Arbitrage**: The system may fail to recognize these as the same event due to different wording.

#### Scenario 2: Different Platform, Same Contract

- Contract A: "BTC above $100k on Dec 31?" at $0.55 on Polymarket
- Contract B: "Bitcoin price > $100,000 (Dec 31, 2026)" at $0.40 on Kalshi
- **Missed Arbitrage**: Different naming conventions may prevent matching.

---

## 6. Explicit Mapping Requirements

### 6.1 What Information a Trusted Caller Must Provide

For cross-venue arbitrage to be reliable, the caller must provide:

```typescript
interface ContractMapping {
  // Core Identity
  contractA: ContractIdentifier;
  contractB: ContractIdentifier;
  
  // Event Equivalence Declaration
  eventEquivalence: EventEquivalenceDeclaration;
  
  // Outcome Relationship
  outcomeRelationship: OutcomeRelationship;
  
  // Resolution Compatibility
  resolutionCompatibility: ResolutionCompatibility;
  
  // Settlement Compatibility
  settlementCompatibility: SettlementCompatibility;
  
  // Confidence and Source
  confidence: 'high' | 'medium' | 'low';
  mappingSource: 'manual' | 'algorithmic' | 'hybrid';
  notes?: string;
}

interface EventEquivalenceDeclaration {
  sameEvent: boolean;
  subjectMatch: boolean;
  temporalScopeMatch: boolean;
  eventBoundaryMatch: boolean;
  equivalenceReason: string;
  potentialDiscrepancies?: string[];
}

interface OutcomeRelationship {
  type: 'identical' | 'opposite' | 'complementary' | 'unrelated';
  mappingRules: OutcomeMappingRule[];
}

interface OutcomeMappingRule {
  outcomeA: string;  // e.g., "YES", "Republican", ">50%"
  outcomeB: string;  // e.g., "NO", "Democrat", "≤50%"
  relationship: 'same' | 'opposite' | 'no-correspondence';
}

interface ResolutionCompatibility {
  sameSource: boolean;
  sourceEquivalenceReason?: string;
  timingCompatible: boolean;
  maxTimingDifferenceMs: number;
  thresholdMatch: boolean;
  voidScenarioMatch: boolean;
}

interface SettlementCompatibility {
  timingCompatible: boolean;
  maxSettlementDifferenceMs: number;
  mechanismMatch: boolean;
  currencyMatch: boolean;
  feeStructureSimilar: boolean;
}
```

### 6.2 Validation Rules for Mappings

#### Rule 1: Event Equivalence Must Be Explicit

```
IF eventEquivalence.sameEvent = false
THEN reject mapping (not suitable for arbitrage)
```

#### Rule 2: Outcome Relationship Must Be Consistent

```
IF outcomeRelationship.type = 'opposite'
THEN for all mapping rules:
  relationship must be 'opposite'
  AND sum of probabilities ≈ 1.0 (within tolerance)
```

#### Rule 3: Resolution Sources Must Be Compatible

```
IF resolutionCompatibility.sameSource = false
AND resolutionCompatibility.sourceEquivalenceReason = undefined
THEN reject mapping (resolution source mismatch)
```

#### Rule 4: Settlement Timing Must Be Compatible

```
IF settlementCompatibility.timingCompatible = false
THEN reject mapping (settlement timing mismatch)
```

#### Rule 5: Void Scenario Handling Must Match

```
IF resolutionCompatibility.voidScenarioMatch = false
THEN reject mapping (void scenario handling mismatch)
```

#### Rule 6: Cross-Mapping Consistency

```
IF mapping(contractA, contractB) exists
AND mapping(contractB, contractC) exists
THEN mapping(contractA, contractC) must be derivable and consistent
```

### 6.3 How to Reject Inconsistent Mappings

#### Inconsistency Detection Algorithm

```
function validateMappingConsistency(mappings: ContractMapping[]): ValidationResult {
  issues = [];
  
  // Check for contradictory event equivalence
  for each mapping in mappings:
    if !mapping.eventEquivalence.sameEvent:
      issues.add("Event equivalence explicitly false")
    
    if mapping.outcomeRelationship.type == 'opposite':
      if sum(mapping.outcomeRelationship.mappingRules.probabilities) != 1.0:
        issues.add("Opposite outcome probabilities don't sum to 1.0")
  
  // Check for transitivity violations
  for each triple (A, B, C) where mappings exist:
    if mapping(A, B).eventEquivalence.sameEvent
    AND mapping(B, C).eventEquivalence.sameEvent
    AND !mapping(A, C).eventEquivalence.sameEvent:
      issues.add("Transitivity violation: A~B and B~C but not A~C")
  
  // Check for resolution source conflicts
  for each pair (A, B) where mappings exist:
    if mapping(A, B).resolutionCompatibility.sameSource = false
    AND mapping(A, B).resolutionCompatibility.sourceEquivalenceReason contains "identical":
      issues.add("Resolution sources claimed identical but marked as different")
  
  return issues.length == 0 ? VALID : INVALID(issues);
}
```

---

## 7. Domain Model Requirements

### 7.1 Entities

#### Entity 1: Contract

```typescript
interface Contract {
  id: string;                          // Unique identifier
  venue: Venue;                        // Polymarket, Kalshi, etc.
  externalId: string;                  // Venue-specific identifier
  title: string;                       // Human-readable title
  description: string;                 // Full resolution rules text
  
  // Event Reference
  event: EventReference;
  
  // Outcome Definition
  outcomes: Outcome[];
  
  // Resolution Specification
  resolution: ResolutionSpecification;
  
  // Settlement Specification
  settlement: SettlementSpecification;
  
  // Market Data
  currentPrice: number;
  volume24h: number;
  lastUpdated: timestamp;
}
```

#### Entity 2: EventReference

```typescript
interface EventReference {
  id: string;                          // Canonical event identifier
  subject: string;                     // What the event is about
  temporalScope: TemporalScope;        // Time window
  eventBoundary: EventBoundary;        // Start/end conditions
  
  // Derived Fields
  canonicalName: string;               // Normalized event name
  category: string;                    // Election, Crypto, Weather, etc.
  tags: string[];                      // Searchable tags
}
```

#### Entity 3: TemporalScope

```typescript
interface TemporalScope {
  type: 'point-in-time' | 'range' | 'path-dependent';
  
  // For point-in-time
  observationTime?: timestamp;
  observationTimezone?: string;
  
  // For range
  startTime?: timestamp;
  endTime?: timestamp;
  
  // For path-dependent
  pathCondition?: string;              // e.g., "ever reaches $100k"
}
```

#### Entity 4: EventBoundary

```typescript
interface EventBoundary {
  // When the event "starts" being observable
  startCondition: string;
  
  // When the event "ends" and outcome is determined
  endCondition: string;
  
  // How ambiguity at boundaries is resolved
  boundaryResolutionRule: string;
}
```

#### Entity 5: Outcome

```typescript
interface Outcome {
  id: string;
  label: string;                      // "YES", "Republican", ">50%"
  value: number;                      // 1 if this outcome is true, 0 otherwise
  
  // For multi-outcome markets
  isMutuallyExclusive: boolean;
  isCollectivelyExhaustive: boolean;
  
  // Mapping to other outcomes
  equivalentOutcomes: OutcomeReference[];
  oppositeOutcomes: OutcomeReference[];
}
```

#### Entity 6: ResolutionSpecification

```typescript
interface ResolutionSpecification {
  source: ResolutionSource;
  
  // Timing
  resolutionTime: timestamp;
  resolutionTimezone: string;
  
  // Conditions
  resolutionCondition: string;        // The rule that determines outcome
  
  // Handling of edge cases
  voidScenarioHandling: 'refund' | 'resolve-no' | 'resolve-yes' | 'platform-discretion';
  disputeHandling: string;            // How disputes are resolved
  
  // Source details
  sourceUrl?: string;                 // URL to resolution source
  sourceApiKey?: string;              // API endpoint for data
  fallbackSources?: ResolutionSource[];
}
```

#### Entity 7: ResolutionSource

```typescript
interface ResolutionSource {
  tier: 1 | 2 | 3 | 4;              // Source hierarchy tier
  name: string;                       // "Associated Press", "Bloomberg", etc.
  type: 'official' | 'designated' | 'consensus' | 'manual';
  
  // For price-based sources
  priceFeed?: string;                 // API endpoint
  priceType?: 'last-trade' | 'vwap' | 'bid-ask-midpoint' | 'closing';
  priceTimestamp?: string;            // Exact moment of observation
  
  // Reliability metrics
  historicalAccuracy: number;         // 0-1 score
  averageDelay: number;               // Seconds from event to resolution
}
```

#### Entity 8: SettlementSpecification

```typescript
interface SettlementSpecification {
  settlementTime: timestamp;
  settlementTimezone: string;
  
  mechanism: 'instant' | 'batch' | 'manual';
  currency: string;                   // "USD", "USDC", etc.
  
  // Fee structure
  fees: FeeStructure;
  
  // Settlement confirmation
  confirmationRequired: boolean;
  confirmationTimeout: number;        // Seconds
}
```

#### Entity 9: FeeStructure

```typescript
interface FeeStructure {
  tradingFee: number;                 // Percentage of trade value
  settlementFee: number;              // Flat fee per settlement
  withdrawalFee: number;              // Fee to move funds off-platform
  
  // Volume-based discounts
  volumeTiers?: VolumeTier[];
}
```

#### Entity 10: ContractMapping

```typescript
interface ContractMapping {
  id: string;
  contractA: ContractReference;
  contractB: ContractReference;
  
  eventEquivalence: EventEquivalenceDeclaration;
  outcomeRelationship: OutcomeRelationship;
  resolutionCompatibility: ResolutionCompatibility;
  settlementCompatibility: SettlementCompatibility;
  
  confidence: 'high' | 'medium' | 'low';
  mappingSource: 'manual' | 'algorithmic' | 'hybrid';
  
  // Validation status
  isValidated: boolean;
  validationErrors?: string[];
  validatedAt?: timestamp;
  validatedBy?: string;
  
  // Audit trail
  createdAt: timestamp;
  updatedAt: timestamp;
  createdBy: string;
  notes?: string;
}
```

### 7.2 Required Fields per Entity

| Entity | Required Fields | Optional Fields |
|--------|----------------|-----------------|
| Contract | id, venue, externalId, title, description, event, outcomes, resolution, settlement | currentPrice, volume24h, lastUpdated |
| EventReference | id, subject, temporalScope, eventBoundary, canonicalName, category | tags |
| TemporalScope | type | observationTime, startTime, endTime, pathCondition |
| EventBoundary | startCondition, endCondition, boundaryResolutionRule | |
| Outcome | id, label, value, isMutuallyExclusive, isCollectivelyExhaustive | equivalentOutcomes, oppositeOutcomes |
| ResolutionSpecification | source, resolutionTime, resolutionCondition, voidScenarioHandling | sourceUrl, fallbackSources |
| ResolutionSource | tier, name, type | priceFeed, priceType, priceTimestamp |
| SettlementSpecification | settlementTime, mechanism, currency, fees | confirmationRequired |
| FeeStructure | tradingFee, settlementFee, withdrawalFee | volumeTiers |
| ContractMapping | id, contractA, contractB, eventEquivalence, outcomeRelationship, resolutionCompatibility, settlementCompatibility, confidence, mappingSource | isValidated, validationErrors, notes |

### 7.3 Invariants That Must Hold

#### Invariant 1: Event Reference Integrity

```
∀ contract ∈ Contracts:
  contract.event != null
  AND contract.event.subject != ""
  AND contract.event.temporalScope != null
  AND contract.event.eventBoundary != null
```

#### Invariant 2: Outcome Completeness

```
∀ contract ∈ Contracts:
  |contract.outcomes| >= 2
  AND (∃ outcome ∈ contract.outcomes: outcome.isCollectivelyExhaustive = true)
    OR (sum(outcome.value for outcome in contract.outcomes) = 1)
```

#### Invariant 3: Resolution Source Validity

```
∀ contract ∈ Contracts:
  contract.resolution.source != null
  AND contract.resolution.source.tier ∈ {1, 2, 3, 4}
  AND contract.resolution.voidScenarioHandling ∈ {'refund', 'resolve-no', 'resolve-yes', 'platform-discretion'}
```

#### Invariant 4: Mapping Consistency

```
∀ mapping ∈ ContractMappings:
  mapping.contractA != mapping.contractB
  AND mapping.eventEquivalence.sameEvent = true
  → mapping.outcomeRelationship.type ∈ {'identical', 'opposite', 'complementary'}
  AND mapping.resolutionCompatibility.timingCompatible = true
  AND mapping.settlementCompatibility.timingCompatible = true
```

#### Invariant 5: Transitivity of Equivalence

```
∀ (a, b, c) ∈ Contracts³:
  if EconomicallyEquivalent(a, b) AND EconomicallyEquivalent(b, c)
  then EconomicallyEquivalent(a, c)
```

#### Invariant 6: Opposite Outcome Complementarity

```
∀ mapping ∈ ContractMappings where mapping.outcomeRelationship.type = 'opposite':
  ∀ rule ∈ mapping.outcomeRelationship.mappingRules:
    rule.relationship = 'opposite'
  AND sum(contractA.outcomes where relationship='opposite' with contractB.outcomes) = 1.0
```

#### Invariant 7: Settlement Timing Bounds

```
∀ mapping ∈ ContractMappings:
  mapping.settlementCompatibility.maxSettlementDifferenceMs < MAX_SETTLEMENT_THRESHOLD
  where MAX_SETTLEMENT_THRESHOLD is configurable (default: 1 hour = 3,600,000 ms)
```

---

## Appendix A: Reference Implementation — Equivalence Check Algorithm

```typescript
function areEconomicallyEquivalent(
  contractA: Contract,
  contractB: Contract,
  mapping?: ContractMapping
): EquivalenceResult {
  
  // If explicit mapping provided, use it
  if (mapping) {
    return validateMapping(mapping);
  }
  
  // Otherwise, attempt algorithmic detection
  const result: EquivalenceResult = {
    isEquivalent: false,
    confidence: 'low',
    reasons: [],
    blockers: []
  };
  
  // Step 1: Check event identity
  const eventMatch = checkEventIdentity(contractA.event, contractB.event);
  if (!eventMatch.isMatch) {
    result.blockers.push(`Event mismatch: ${eventMatch.reason}`);
    return result;
  }
  result.reasons.push('Event identity confirmed');
  
  // Step 2: Check outcome relationship
  const outcomeRelationship = determineOutcomeRelationship(contractA.outcomes, contractB.outcomes);
  if (outcomeRelationship.type === 'unrelated') {
    result.blockers.push('Outcomes are unrelated');
    return result;
  }
  result.reasons.push(`Outcome relationship: ${outcomeRelationship.type}`);
  
  // Step 3: Check resolution compatibility
  const resolutionCompat = checkResolutionCompatibility(contractA.resolution, contractB.resolution);
  if (!resolutionCompat.isCompatible) {
    result.blockers.push(`Resolution incompatibility: ${resolutionCompat.reason}`);
    return result;
  }
  result.reasons.push('Resolution sources compatible');
  
  // Step 4: Check settlement compatibility
  const settlementCompat = checkSettlementCompatibility(contractA.settlement, contractB.settlement);
  if (!settlementCompat.isCompatible) {
    result.blockers.push(`Settlement incompatibility: ${settlementCompat.reason}`);
    return result;
  }
  result.reasons.push('Settlement timing compatible');
  
  // Step 5: Check void scenario handling
  const voidMatch = checkVoidScenarioHandling(contractA.resolution, contractB.resolution);
  if (!voidMatch.isMatch) {
    result.blockers.push(`Void scenario handling mismatch: ${voidMatch.reason}`);
    return result;
  }
  result.reasons.push('Void scenario handling matches');
  
  // All checks passed
  result.isEquivalent = true;
  result.confidence = calculateConfidence(eventMatch, outcomeRelationship, resolutionCompat, settlementCompat);
  
  return result;
}

function checkEventIdentity(eventA: EventReference, eventB: EventReference): MatchResult {
  // Check subject
  const subjectSimilarity = calculateStringSimilarity(eventA.subject, eventB.subject);
  if (subjectSimilarity < 0.8) {
    return { isMatch: false, reason: `Subject mismatch: "${eventA.subject}" vs "${eventB.subject}"` };
  }
  
  // Check temporal scope
  const temporalMatch = compareTemporalScopes(eventA.temporalScope, eventB.temporalScope);
  if (!temporalMatch.isMatch) {
    return { isMatch: false, reason: `Temporal scope mismatch: ${temporalMatch.reason}` };
  }
  
  // Check event boundary
  const boundaryMatch = compareEventBoundaries(eventA.eventBoundary, eventB.eventBoundary);
  if (!boundaryMatch.isMatch) {
    return { isMatch: false, reason: `Event boundary mismatch: ${boundaryMatch.reason}` };
  }
  
  return { isMatch: true, similarity: subjectSimilarity };
}

function determineOutcomeRelationship(
  outcomesA: Outcome[],
  outcomesB: Outcome[]
): OutcomeRelationship {
  // Binary case
  if (outcomesA.length === 2 && outcomesB.length === 2) {
    const yesA = outcomesA.find(o => o.label === 'YES');
    const yesB = outcomesB.find(o => o.label === 'YES');
    
    if (yesA && yesB) {
      // Check if outcomes are identical or opposite
      if (outcomesA[0].label === outcomesB[0].label && outcomesA[1].label === outcomesB[1].label) {
        return { type: 'identical', mappingRules: [{ outcomeA: 'YES', outcomeB: 'YES', relationship: 'same' }] };
      }
      if (outcomesA[0].label === outcomesB[1].label && outcomesA[1].label === outcomesB[0].label) {
        return { type: 'opposite', mappingRules: [{ outcomeA: 'YES', outcomeB: 'NO', relationship: 'opposite' }] };
      }
    }
  }
  
  // Multi-outcome case
  // Check for complementary relationships
  const allOutcomesA = new Set(outcomesA.map(o => o.label));
  const allOutcomesB = new Set(outcomesB.map(o => o.label));
  
  if (allOutcomesA.size === allOutcomesB.size && 
      allOutcomesA.size === allOutcomesA.union(allOutcomesB).size) {
    return { type: 'identical', mappingRules: outcomesA.map(o => ({ outcomeA: o.label, outcomeB: o.label, relationship: 'same' })) };
  }
  
  return { type: 'unrelated', mappingRules: [] };
}
```

---

## Appendix B: Summary of Key Rules

1. **Two contracts are the same event** iff they have the same subject, temporal scope, and event boundary.

2. **Two contracts are the same outcome** iff they reference the same event AND resolve identically for all possible world states.

3. **Two contracts are opposite outcomes** iff they reference the same event AND for all world states, one pays out exactly when the other does not.

4. **Two contracts are economically equivalent** iff they are the same event AND (same outcome OR opposite outcome) AND same resolution source AND settlement compatible AND void scenario handling matches.

5. **Cross-venue arbitrage is true arbitrage** only when all of the above conditions hold AND transfer is possible within the settlement window AND total fees are less than the price differential.

6. **Explicit mappings must declare** event equivalence, outcome relationship, resolution compatibility, and settlement compatibility. Mappings must be validated for consistency before use.

7. **The domain model must enforce** invariants for event reference integrity, outcome completeness, resolution source validity, mapping consistency, transitivity of equivalence, opposite outcome complementarity, and settlement timing bounds.

---

*End of Analysis — Quinn, Investment Researcher, 2026-09-08*
