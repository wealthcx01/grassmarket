/**
 * Guided-consulting content for the 7 Powers step (GRS-0069). The registry already carries each
 * power's Helmer definition (`RegistryPower.description`) and lifecycle stage; this adds the
 * consulting layer the UX brief asks for — a plain-English "what benefit vs barrier means for THIS
 * power" gloss, and an illustrative brokerage example.
 *
 * These are teaching aids grounded in Helmer's 7 Powers framework (the settled methodology), in the
 * same spirit as the static content on the `/guide` primer — NOT claims about any real firm's actual
 * score. Examples are deliberately generic ("a broker where…"), never an assertion that a named
 * company holds the power.
 *
 * Keyed by the registry `power_key`. `powerGuidanceKeys` is exported so a test can assert every
 * registry power has guidance (a new power must not ship without it).
 */

export interface PowerGuidance {
  /** What a strong *Benefit* (the upside the leader enjoys) looks like for this specific power. */
  benefitHint: string;
  /** What a strong *Barrier* (why a rival can't copy it) looks like for this specific power. */
  barrierHint: string;
  /** How to ASSESS this power objectively (GRS-0105): what evidence establishes the benefit AND the
   *  barrier, and what makes it weak — so a rating is grounded, not a guess picked from a dropdown. */
  assessment: string;
  /** An illustrative brokerage/trading-platform example — a teaching aid, not a scored claim. */
  example: string;
}

export const POWER_GUIDANCE: Record<string, PowerGuidance> = {
  SCALE_ECONOMIES: {
    assessment:
      "Find a real fixed-cost base spread over volume (unit cost visibly falling with size), and evidence a sub-scale rival must price below cost to compete. Weak if costs are mostly variable.",
    benefitHint:
      "Unit costs fall as volume grows — the leader can price where a sub-scale rival loses money.",
    barrierHint:
      "A challenger would have to buy share at a loss to reach the volume that makes the economics work.",
    example:
      "A broker spreading fixed clearing, market-data and compliance cost across millions of accounts. Zero-commission economics only close at scale — a small entrant can't match the price without burning capital.",
  },
  NETWORK_ECONOMIES: {
    assessment:
      "Confirm value to each user rises with the installed base (not just more users), and that a clone starts from zero. Look for engagement/retention that tracks network density, not features.",
    benefitHint:
      "Each new user makes the platform more valuable to every other user; the leader's value compounds.",
    barrierHint:
      "A rival must reproduce the whole installed base at once to match the value proposition — not just the product.",
    example:
      "A social- or copy-trading platform: more traders means richer leaderboards and more strategies to copy, which pulls in more traders. A clone with an empty network offers little.",
  },
  COUNTER_POSITIONING: {
    assessment:
      "Test whether copying the model would cannibalise an incumbent's core revenue — the incumbent's own P&L is the barrier. Weak if incumbents can adopt it without material self-harm.",
    benefitHint:
      "A newer, superior business model the incumbent can't adopt without hurting its existing business.",
    barrierHint:
      "The incumbent's own economics deter imitation — copying you would cannibalise their core revenue.",
    example:
      "A commission-free entrant monetising order flow. A commission-based incumbent can't simply match it without vaporising its per-trade revenue line.",
  },
  SWITCHING_COSTS: {
    assessment:
      "Quantify what a client forgoes by leaving — in-specie transfer friction, tax positions, integrations, habit. Read actual churn and transfer-out times, not stated intent.",
    benefitHint:
      "The value a customer forgoes by leaving — deeper the lock-in, the more pricing power the leader holds.",
    barrierHint:
      "Rivals must compensate the customer for the pain of switching, eroding the rival's own economics.",
    example:
      "Transferring an ISA or portfolio in specie is slow and fiddly; unrealised CGT positions, recurring investments and linked accounts all raise the cost of moving away.",
  },
  BRANDING: {
    assessment:
      "Look for a price/trust premium on an otherwise comparable offering, built over years — unaided awareness, willingness to pay, tenure. Weak if the premium is really product or price, not the name.",
    benefitHint:
      "A durable attribution of higher value (trust, safety, prestige) to an otherwise comparable offering.",
    barrierHint:
      "Brand is slow, costly and uncertain to replicate — built over years, not bought.",
    example:
      "A decades-old, trusted name commands AUM and trust a new app must earn slowly — most acute where investors are choosing who to hand their life savings to.",
  },
  CORNERED_RESOURCE: {
    assessment:
      "Identify the specific coveted asset (licence, IP, talent, routing, deposit base) and confirm rivals cannot obtain it at a reasonable price. Weak if it is merely a head start others can buy.",
    benefitHint:
      "Preferential access to a coveted asset — talent, IP, a deposit base, a scarce licence — on attractive terms.",
    barrierHint:
      "By definition the resource isn't available to rivals; they can't obtain it at any reasonable price.",
    example:
      "An exclusive market-maker relationship, a scarce licence in a hard-to-enter jurisdiction, or proprietary routing that rivals simply cannot obtain.",
  },
  PROCESS_POWER: {
    assessment:
      "Look for superior product/cost from embedded, hard-to-copy process refined over time, with hysteresis (a rival needs an extended, uncertain commitment to match). Weak if it is documented and transferable.",
    benefitHint:
      "Embedded organisation and activity sets that yield superior product or cost, refined over time.",
    barrierHint:
      "Hysteresis and opacity — rivals can only match it through an extended, uncertain commitment.",
    example:
      "A deeply optimised in-house order-management and risk stack built over years. A rival can't buy equivalent execution quality and cost off the shelf.",
  },
};

export const powerGuidanceKeys = Object.keys(POWER_GUIDANCE);
