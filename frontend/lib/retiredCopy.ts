/**
 * Copy the founder has retired, and which must not come back (GRS-0243 scope 1).
 *
 * Two sentences on the home page were quoted verbatim in feedback on 26/07, survived the GRS-0174
 * copy sweep and were still there on 31/07 when the founder raised them a second time. Rewriting
 * them is easy; the thing that failed twice is *keeping* them rewritten, because a copy change has
 * nothing holding it in place — the next person to touch the hero has no idea a sentence was ever
 * objected to.
 *
 * So the objection is written down where a test can read it. `retiredCopy.test.ts` scans the app
 * source for these strings and fails the build. That is the mechanism GRS-0205 will generalise; this
 * is its first two entries, added by the ticket that needed it.
 *
 * Adding an entry is a decision, not a formality: it says "this exact wording was rejected and the
 * reason survives the rewrite". Include the reason, so a future author knows whether their new
 * sentence has the same problem rather than only that it has the same words.
 */

export type RetiredPhrase = {
  /** The exact wording, as it appeared. Matched as a substring, whitespace-normalised. */
  phrase: string;
  /** Where it was, so a reviewer can see what replaced it. */
  where: string;
  /** Why it was rejected. The reason is the durable part; the wording is just the symptom. */
  why: string;
};

export const RETIRED_COPY: RetiredPhrase[] = [
  // GRS-0243 scope 4. Four empty states that stated their own emptiness. Registered together
  // because they share one fault, not four: each told a first-time user the fact they could
  // already see, and none said what the section was for or what would put something in it.
  {
    phrase: "No engagements yet. Open one from a contracted prospect.",
    where: "Engagements, empty state",
    why:
      "States the emptiness the reader can already see. It also names the fix backwards — you do " +
      "not 'open' an engagement as an action, it opens when a prospect reaches Contracted, and an " +
      "advisor sent looking for a button will not find one.",
  },
  {
    phrase: "No assessments yet. Create one above to begin.",
    where: "Portfolio, empty state",
    why:
      "Says nothing about what a portfolio IS — the page an advisor returns to, holding every " +
      "scored firm with its value and coverage. 'Create one above' also mislabels the page as a " +
      "form rather than a record of work that happens in the wizard.",
  },
  {
    phrase: "No commission lines yet",
    where: "Earnings, empty state",
    why:
      "A first-time user reads this as 'something is missing here' rather than the truth, which " +
      "is that lines are created for you when work is recorded and are never entered by hand. " +
      "The zero is correct and the page has to say why.",
  },

  {
    phrase:
      "Your home for the Bruntsfield Advisory Network — manage your pipeline, run Platform Power " +
      "assessments, generate client deliverables, and grow in the Workbench.",
    where: "Home hero (WelcomeBanner)",
    why:
      "It reads the navigation back to the reader. A first-time user already sees those five " +
      "words in the nav bar; what they cannot see is what the product claims to do, which is what " +
      "a hero is for. Flagged 26/07, survived GRS-0174, still present 31/07.",
  },
  {
    phrase: "New to Platform Power? Start with the primer",
    where: "Home primer banner",
    why:
      "It asks a question whose honest answer is yes for everyone, then offers a link without " +
      "saying what reading it changes. The replacement states the payoff instead of the audience.",
  },
];
