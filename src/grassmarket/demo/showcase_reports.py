"""Worked example client reports for the showcase brokerages (GRS-0236).

The founder's report was blunt: *"I can't seem to download example client reports."* They could not,
and the reason was not a bug in the download. `brokerage_showcase.py` seeds three brokerages with
five deliverables each and wrote no prose at all, so every demo report sat in the "unwritten" state
and both release paths refused with the 409 naming six empty sections. The showcase predates the
prose requirement (GRS-0211, wired 2026-07-30) and was never revisited.

**This is authored content, reviewed as content.** It is the product's best output on display: a
first-time user opens a showcase deliverable, downloads a PDF, and either holds something a real
client could have received or learns that we do not have one. Lorem would be worse than the refusal,
because a refusal is at least honest about the state of things.

Three deliberate constraints on how it is written:

1. **No numerals in the body.** The content model refuses any figure the section has not declared
   (rule 3), and rightly — but the deeper reason to keep numbers out of these paragraphs is that
   this prose is seeded against a scoring run whose numbers can change when coefficients are
   re-elicited. Prose that quotes a score would quietly go stale and start contradicting the
   appendix beside it. The appendix carries the numbers; the body carries the argument.
2. **Distinct per firm, and specific.** Three variations on "a strong platform with room to improve"
   would show a reader that the assessment says nothing. Revolut, Hargreaves Lansdown and WeBull
   have genuinely different shapes — a distribution-led neobank, an incumbent platform with a
   defended franchise, and a technology-led challenger — and the reports say so.
3. **Honest about what a demo is.** Each report's appendix states that it is an illustrative record
   built from published information, not a client engagement. These render watermarked (ADR-0029,
   GRS-0229), and the prose does not pretend otherwise.
"""

from __future__ import annotations

# Keyed by `BrokerageSpec.subject`. Each value is the six sections in `SECTION_ORDER`, as the
# `PUT /deliverables/<id>/report-prose` payload expects them: `{kind: {heading, body[]}}`.
#
# The headings are the reader-facing ones from the PDF and the web page, so the seeded example looks
# exactly like an advisor's own report rather than like seed data.
SHOWCASE_PROSE: dict[str, dict[str, dict[str, object]]] = {
    "Revolut": {
        "business": {
            "heading": "The business",
            "body": [
                "Revolut sells banking, foreign exchange and investing to retail customers through "
                "a single mobile application. Trading is one surface among several rather than the "
                "whole proposition, and that shapes everything else in this report: the firm "
                "acquires a customer for one job and monetises them across many.",
                "The economics follow from distribution rather than from execution. Revolut's "
                "advantage over a specialist broker is that it already holds the customer "
                "relationship and the balance; its disadvantage is that trading is competing "
                "internally for engineering attention with cards, credit, savings and business "
                "banking.",
            ],
        },
        "advantage": {
            "heading": "Where the advantage sits",
            "body": [
                "The durable advantage is brand and distribution. Revolut is a recognised consumer "
                "name in markets where most brokers are not, and it acquires investing customers "
                "at a cost a standalone platform cannot match because the acquisition has already "
                "happened for another product.",
                "Counter-positioning is real but partial. An incumbent broker cannot easily copy "
                "the multi-product app without disrupting the revenue it already has, which is the "
                "shape of a genuine strategic barrier. What is not yet durable is switching cost: "
                "a customer's holdings are portable and the relationship, while broad, is not deep "
                "in the way a full wealth relationship becomes.",
                "Network effects are present at the payments layer and largely absent at the "
                "investing layer. The report does not credit the second to the first.",
            ],
        },
        "constraint": {
            "heading": "What is holding it back",
            "body": [
                "The binding constraint is the depth of the trading platform relative to the "
                "breadth of the franchise. The front end and the application layer are strong; the "
                "order and execution management underneath them is thinner than the customer "
                "numbers would lead an observer to expect.",
                "That gap does not hurt while the average customer trades occasionally in liquid "
                "instruments. It begins to hurt the moment the firm wants the customers it already "
                "has to trade more, or to trade products where execution quality is visible. The "
                "constraint is therefore not a problem the firm has today; it is the ceiling on "
                "the strategy the firm has announced.",
            ],
        },
        "actions": {
            "heading": "What to do about it",
            "body": [
                "Deepen the execution layer before marketing the trading proposition harder. The "
                "order in which those two happen decides whether increased engagement is met with "
                "capability or with incidents.",
                "Second, make the switching cost real by moving from custody of assets to "
                "ownership of the customer's financial picture — tax reporting, cost basis and "
                "planning are the surfaces that make leaving expensive, and they are cheaper to "
                "build than execution infrastructure.",
                "Third, treat the multi-product advantage as a strategic asset to be defended "
                "rather than a fact to be assumed. It is the thing an incumbent cannot copy "
                "quickly, and it is the thing a better-funded neobank could.",
            ],
        },
        "value": {
            "heading": "What that is worth",
            "body": [
                "The value of closing the execution gap is not primarily new revenue from trading. "
                "It is the removal of a ceiling on a strategy the firm is already spending to "
                "pursue, which makes it a cost of preserving the value already built rather than "
                "an investment in new value.",
                "Read the appendix figures in that light. The headline index measures the platform "
                "as it stands; the range around it reflects how much of this assessment rests on "
                "published information rather than on inspection.",
            ],
        },
        "appendix": {
            "heading": "Technical appendix",
            "body": [
                "This is an illustrative example record, built from published information, and it "
                "is not a client engagement. It is seeded so that a new advisor can see a complete "
                "report end to end; every rendition of it is watermarked accordingly.",
                "The figures below come from the scoring run this report is bound to. The "
                "methodology and coefficient versions that produced them are stated in the footer "
                "of every rendition, and the run is immutable, so this appendix and the document "
                "you are holding cannot drift apart.",
            ],
        },
    },
    "Hargreaves Lansdown": {
        "business": {
            "heading": "The business",
            "body": [
                "Hargreaves Lansdown runs the largest direct-to-consumer investment platform in "
                "the United Kingdom. It holds client assets, charges for administering them, and "
                "sells research, funds and a dealing service on top. The platform fee on assets "
                "under administration is the spine of the business.",
                "That structure means the firm's revenue moves with markets and with flows rather "
                "than with trading volume, which makes it steadier than a broker's and more "
                "exposed to fee compression than a broker's is.",
            ],
        },
        "advantage": {
            "heading": "Where the advantage sits",
            "body": [
                "The advantage is a defended franchise: brand, scale and switching cost operating "
                "together. Clients hold long-lived tax-advantaged accounts, and moving them is "
                "administratively unpleasant in a way that has nothing to do with how good a "
                "competitor's product is. That is switching cost in its strongest form, because it "
                "is created by the product's own structure rather than by inertia.",
                "Scale economies are genuine on the administration side. The cost of running a "
                "platform does not rise proportionally with assets on it, and the firm has more "
                "assets on it than anyone else in its market.",
                "What the firm does not have is a cornered resource or a process advantage its "
                "competitors could not replicate given time and capital. The moat is structural "
                "and "
                "commercial rather than technical.",
            ],
        },
        "constraint": {
            "heading": "What is holding it back",
            "body": [
                "The constraint is that the defended franchise is defended against the wrong "
                "attack. Switching cost protects the firm from a client leaving; it does not "
                "protect the fee from being competed down by a platform that accepts a lower one, "
                "and it does not protect the next generation of clients who have not yet chosen a "
                "platform to be locked into.",
                "The platform's own infrastructure reflects a business built for administration "
                "rather than for engagement. It is capable and it is not fast to change, and the "
                "pressure it will come under is a pressure to change quickly.",
            ],
        },
        "actions": {
            "heading": "What to do about it",
            "body": [
                "Compete for the client who has not yet chosen, on the terms that client actually "
                "uses to choose. That is a distribution and product problem before it is a pricing "
                "one, and pricing alone will not answer it.",
                "Modernise the platform incrementally behind a stable interface rather than "
                "attempting a replacement. The firm's advantage is continuity; a migration that "
                "puts continuity at risk spends the moat to buy the modernisation.",
                "Make the research and planning surfaces the reason to stay, so that switching "
                "cost is increasingly something the client would regret rather than something the "
                "paperwork imposes on them.",
            ],
        },
        "value": {
            "heading": "What that is worth",
            "body": [
                "The value here is defensive and it is large. A fee-led platform business loses "
                "value slowly and then suddenly, and the work described above is what converts a "
                "slow decline into a defensible position.",
                "The appendix figures show a platform that scores well on the dimensions its "
                "current business needs and less well on the dimensions its next one will. That "
                "gap, rather than the headline number, is the finding.",
            ],
        },
        "appendix": {
            "heading": "Technical appendix",
            "body": [
                "This is an illustrative example record, built from published information, and it "
                "is not a client engagement. It is seeded so that a new advisor can see a complete "
                "report end to end; every rendition of it is watermarked accordingly.",
                "The figures below come from the scoring run this report is bound to. The "
                "methodology and coefficient versions that produced them are stated in the footer "
                "of every rendition, and the run is immutable, so this appendix and the document "
                "you are holding cannot drift apart.",
            ],
        },
    },
    "WeBull": {
        "business": {
            "heading": "The business",
            "body": [
                "WeBull is a technology-led retail brokerage. It competes on the quality of the "
                "trading experience — data, charting, execution and low headline cost — rather "
                "than on holding a broad financial relationship with its customers.",
                "The customer it wins is the customer who cares what the platform does, which is a "
                "smaller population than a bank's and a considerably more demanding one. Revenue "
                "follows activity rather than balances, so the business is more sensitive to how "
                "much its customers trade than to how much they hold.",
            ],
        },
        "advantage": {
            "heading": "Where the advantage sits",
            "body": [
                "The advantage is the platform itself. The infrastructure underneath the product "
                "is genuinely strong, and in a market where most competitors treat the trading "
                "stack as a cost centre, treating it as the product is a real position.",
                "That advantage is closest in kind to process power: it comes from accumulated "
                "engineering rather than from a contract, a brand or a network, which makes it "
                "durable while it is maintained and perishable if it is not.",
                "Brand strength is materially behind the incumbents in every market the firm "
                "operates in, and this report does not treat product quality as though it were "
                "brand. They behave differently under pressure.",
            ],
        },
        "constraint": {
            "heading": "What is holding it back",
            "body": [
                "The constraint is customer acquisition, not capability. The firm has built a "
                "platform better than its share of the market, which is the signature of a "
                "distribution problem rather than a product one.",
                "Because revenue follows activity, the firm is also exposed to the trading cycle "
                "in "
                "a way a fee-led platform is not. A quiet market reduces revenue without reducing "
                "the cost of running the infrastructure that produced the advantage in the first "
                "place.",
            ],
        },
        "actions": {
            "heading": "What to do about it",
            "body": [
                "Convert platform quality into something a customer can perceive before they "
                "become a customer. Advantages that only reveal themselves after acquisition are "
                "advantages that cannot help acquisition.",
                "Second, build a reason for a customer to hold assets rather than only to trade "
                "them. That is the change that decouples revenue from the cycle, and it is a "
                "product decision rather than a marketing one.",
                "Third, defend the engineering advantage deliberately. Process power decays "
                "quietly, and a firm whose whole position rests on it should be measuring that "
                "decay rather than assuming the lead holds.",
            ],
        },
        "value": {
            "heading": "What that is worth",
            "body": [
                "The value of acting here is asymmetric. The platform investment is already made, "
                "so the return on solving distribution is unusually high — and the cost of not "
                "solving it is that the investment quietly stops earning.",
                "The appendix figures show exactly this shape: infrastructure scoring well above "
                "the commercial position built on it. Where those two diverge, the smaller one is "
                "the constraint.",
            ],
        },
        "appendix": {
            "heading": "Technical appendix",
            "body": [
                "This is an illustrative example record, built from published information, and it "
                "is not a client engagement. It is seeded so that a new advisor can see a complete "
                "report end to end; every rendition of it is watermarked accordingly.",
                "The figures below come from the scoring run this report is bound to. The "
                "methodology and coefficient versions that produced them are stated in the footer "
                "of every rendition, and the run is immutable, so this appendix and the document "
                "you are holding cannot drift apart.",
            ],
        },
    },
}
