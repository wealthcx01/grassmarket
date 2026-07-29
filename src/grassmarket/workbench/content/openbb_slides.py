"""The OpenBB course, rebuilt to the GRS-0215 depth standard (GRS-0216).

The founder's standard, in their words:

    "by the end of the OpenBB course an advisor should have been able to download, sign up to
    OpenBB, create their own workspaces (multiple) and know exactly how and when to sell it."

and, on what a lesson is:

    "A lesson is 20-40 slides of interactive detail with a test before the next section."

Eight sections. Each is one lesson of 20 to 40 slides and a test the advisor passes before the next
opens. Every factual claim carries a `SourceRef` to OpenBB's own documentation, checked at
July 2026. Where a slide states a version, a price or a limit, it cites the page it came from,
because the failure this rebuild corrects was content summarised from memory.

**This course is incomplete and the depth check says so.** `SECTIONS_AUTHORED` lists what exists;
`SECTIONS_PLANNED` lists what does not. The course does not pass `assert_meets_standard` until all
eight are written, which is deliberate: the previous attempt shipped a renderer with no content and
still read as progress.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.learning import (
    CourseModule,
    Lesson,
    SectionTest,
    Slide,
    SlideKind,
    SourceRef,
    SourceRefKind,
    TestQuestion,
)

_NS = "grassmarket:academy:product-openbb"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


# --- Sources, declared once so a link is fixed in one place -------------------------------

DOCS_WORKSPACE = SourceRef(
    title="OpenBB Workspace overview",
    url="https://docs.openbb.co/workspace",
    kind=SourceRefKind.DOCS,
)
DOCS_INSTALL = SourceRef(
    title="OpenBB Python package: installation",
    url="https://docs.openbb.co/odp/python/installation",
    kind=SourceRefKind.DOCS,
)
DOCS_QUICKSTART = SourceRef(
    title="OpenBB Python package: quickstart",
    url="https://docs.openbb.co/odp/python/quickstart",
    kind=SourceRefKind.DOCS,
)
DOCS_DASHBOARDS = SourceRef(
    title="OpenBB Workspace: dashboards",
    url="https://docs.openbb.co/workspace/analysts/dashboards",
    kind=SourceRefKind.DOCS,
)
DOCS_WIDGETS = SourceRef(
    title="OpenBB Workspace: widgets overview",
    url="https://docs.openbb.co/workspace/analysts/widgets/overview",
    kind=SourceRefKind.DOCS,
)
DOCS_APPS = SourceRef(
    title="OpenBB Workspace: apps",
    url="https://docs.openbb.co/workspace/analysts/apps",
    kind=SourceRefKind.DOCS,
)
DOCS_PLATFORM_INSTALLER = SourceRef(
    title="OpenBB Workspace: platform installer",
    url="https://docs.openbb.co/workspace/getting-started/platform-installer",
    kind=SourceRefKind.DOCS,
)
SITE_WORKSPACE = SourceRef(
    title="OpenBB Workspace product page",
    url="https://openbb.co/products/workspace/",
    kind=SourceRefKind.DOCS,
)
BLOG_MARKETPLACE = SourceRef(
    title="Introducing the OpenBB App Marketplace",
    url="https://openbb.co/blog/introducing-the-openbb-app-marketplace/",
    kind=SourceRefKind.BLOG,
)
REPO = SourceRef(
    title="OpenBB on GitHub",
    url="https://github.com/OpenBB-finance/OpenBB",
    kind=SourceRefKind.REPO,
)


def _s(
    order: int,
    kind: SlideKind,
    title: str,
    body: str,
    *,
    refs: tuple[SourceRef, ...] = (),
    checkpoint: str | None = None,
) -> Slide:
    return Slide(
        order=order,
        kind=kind,
        title=title,
        body=body,
        references=refs,
        checkpoint_prompt=checkpoint,
    )


# --- Section 1 — What OpenBB is, and why that matters in a client meeting ------------------

_S1_BODY = (
    "By the end of this lesson you can explain, without notes, what OpenBB is, which of its "
    "products a client would actually buy, and what problem it solves for them. You will also be "
    "able to say what it is not, which matters more than it sounds: the fastest way to lose a "
    "sophisticated buyer is to describe OpenBB as a cheap Bloomberg, because they have heard that "
    "claim before and it is not the claim OpenBB makes about itself."
)

_SECTION_1_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The one-sentence version",
        "OpenBB Workspace is, in OpenBB's own words, \"a secure application for enterprise AI "
        'workflows" that brings together data management, a customisable interface, and AI. Hold '
        "on to the phrase *enterprise AI workflows*. It tells you who the buyer is and what they "
        "are trying to do, and it is a very different pitch from a terminal replacement.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Two products, and you must not confuse them",
        "OpenBB sells two things. The **open-source Python package** (`pip install openbb`) is a "
        "data layer that a developer or quant uses in code. **OpenBB Workspace** is the "
        "commercial, browser-based product an investment team uses. Almost every commission "
        "conversation you have will be about Workspace. Almost every technical objection you hear "
        "will be about the package.",
        refs=(DOCS_WORKSPACE, DOCS_INSTALL),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why an open core matters commercially",
        "The open-source package is not a giveaway, it is the distribution channel. A quant tries "
        "it on their own laptop, likes the data coverage, and the firm's conversation about "
        "Workspace starts from someone inside who already trusts the tooling. When you qualify an "
        "account, finding that engineer is often faster than finding the budget holder.",
        refs=(REPO,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The widget is the atomic unit",
        "A **widget** is what OpenBB calls a self-contained data component: a data source, its "
        "metadata, a visual layer, and configurable parameters, rendered as a table, a chart, a "
        "PDF or something else. Everything else in Workspace is made of widgets. If you understand "
        "widgets you can follow any demo you are shown.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Dashboards: where an analyst actually works",
        "A **dashboard** is a personal analytical space. The analyst combines widgets, links their "
        "parameters so they update together, and adds static files, AI artifacts and notes. "
        "Dashboards are shareable across the organisation, which is the feature that turns one "
        "analyst's work into something the desk uses.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Apps: a dashboard someone already built for you",
        "An **app** is a pre-built dashboard template for a specific workflow: curated widgets, "
        "linked parameters, an AI agent already attached, and prompts written for that job. "
        "Portfolio management, market surveillance and research apps are the examples OpenBB "
        "gives. In a demo, an app is what makes the product look finished rather than empty.",
        refs=(DOCS_APPS,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The App Marketplace",
        "OpenBB runs an App Marketplace where data providers publish apps. Every app in it works "
        "with OpenBB's native AI Copilot and supports custom agent workflows, so an analyst can "
        "open an app, ask a question in plain language, and get an answer grounded in that "
        "provider's data. For a client already paying a provider, this is a reason to look.",
        refs=(BLOG_MARKETPLACE,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "AI agents, and the word that sells them",
        'OpenBB\'s agents "leverage the metadata from your widgets to query the right datasets" '
        "and can watch dashboards for anomalies while holding context across several sources. The "
        "word that matters to a compliance-minded buyer is **grounded**: the answer comes from "
        "their data, not from a model's memory of the internet.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Structured and unstructured, in one place",
        "OpenBB describes a unified system handling structured and unstructured data from "
        "proprietary, licensed and public sources through a single interface. Most firms you will "
        "meet have all three and no single interface. That gap is the opening, and it is worth "
        "asking about directly in a first meeting.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "What OpenBB is not",
        "It is not a market data licence. It does not give a client the right to data they do not "
        "already pay for. It is not a replacement for an order management system, a risk engine or "
        "a book of record. Saying this early makes you more credible, not less, and it stops a "
        "deal dying in month three on an expectation you set in month one.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "The Bloomberg question, and how to handle it",
        "Someone will ask whether this replaces Bloomberg. The honest answer is that it does not "
        "try to. OpenBB's own positioning is enterprise AI workflows over data the firm already "
        "has and already pays for. Reach for seat reduction only where the client tells you a seat "
        "is used for something OpenBB genuinely does, and do not claim parity.",
        refs=(SITE_WORKSPACE,),
    ),
    _s(
        11,
        SlideKind.EXAMPLE,
        "Where this lands: a retail brokerage",
        "A retail broker's research desk publishes daily commentary from four vendors, a "
        "spreadsheet of internal positioning and a PDF from compliance. The analyst spends the "
        "first ninety minutes of each day assembling, not thinking. That is a dashboard with "
        "linked parameters and one agent, and it is the clearest first use case in this segment.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        12,
        SlideKind.EXAMPLE,
        "Where this lands: a wealth manager",
        "A wealth manager wants a consistent house view in front of every adviser, refreshed "
        "daily, with the firm's own model portfolios alongside market data. The shareable "
        "dashboard is the product here, and the buying trigger is usually a consistency or "
        "supervision problem rather than a data problem.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        13,
        SlideKind.EXAMPLE,
        "Where this lands: an exchange or data business",
        "An exchange's data team has product managers who need to see how their own feeds are "
        "used against competitors. Widgets over their own data plus public reference data is a "
        "narrow, fast build. It also opens the second conversation, which is whether they should "
        "publish an app to the Marketplace themselves.",
        refs=(BLOG_MARKETPLACE,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "Mapping this to the segments we assess",
        "Our registry segments the market into retail brokerage, wealth manager, exchange, bank "
        "and information vendor. OpenBB has a plausible story in all five, but the *trigger* "
        "differs: research cost in brokerage, consistency in wealth, product insight at an "
        "exchange. Sell to the trigger, not to the product.",
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "Where OpenBB shows up in a Platform Power assessment",
        "An OpenBB conversation usually starts from an infrastructure finding rather than a "
        "product pitch: a weak research or data module, or a customer-proposition gap where the "
        "client cannot get a consistent view in front of their own users. When the assessment "
        "surfaces that, you have a reason to talk that the client already agreed with.",
    ),
    _s(
        16,
        SlideKind.WALKTHROUGH,
        "Read the overview page yourself",
        "Open the Workspace overview in OpenBB's documentation and read it end to end. It is "
        "short. Pay attention to the order in which they introduce concepts, because that order is "
        "the one their own sales conversations follow and a client who has read anything will have "
        "read this page.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        17,
        SlideKind.WALKTHROUGH,
        "Write the four terms down in your own words",
        "Widget, dashboard, app, agent. Write one sentence for each, without copying the docs. If "
        "you cannot do it for one of them, go back to that slide now rather than later, because "
        "every remaining section assumes these four words.",
    ),
    _s(
        18,
        SlideKind.WALKTHROUGH,
        "Look at the App Marketplace",
        "Open the App Marketplace announcement and look at which providers have published apps. "
        "You are looking for a name your client already pays for. That is the single most useful "
        "fact you can walk into a first meeting holding.",
        refs=(BLOG_MARKETPLACE,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "A first meeting, in four sentences",
        '"You have data from three vendors and your own book, and no one place to look at both. " '
        '"Your analysts rebuild the same view every morning." "OpenBB is a workspace where you '
        'assemble that once and put an AI agent on top of it, grounded in your data." "Shall I '
        'show you what one of your mornings looks like in it?" Notice there is no feature list.',
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "The two objections you will hear first",
        '"We already have Bloomberg" and "our data is not allowed to leave our environment". '
        "The first is answered by not competing with it. The second is a real question about "
        "deployment, which the next sections cover, and it is the one that decides whether a deal "
        "is possible at all.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say it out loud",
        "Explain OpenBB to an imaginary client in under sixty seconds, out loud, without notes. "
        "Include what it is, who it is for, and one thing it does not do. If you reach for a "
        "feature list, start again. The test at the end of this section assumes you can do this.",
        checkpoint="Record or write your sixty-second explanation and keep it. You will reuse it "
        "in section 8, and comparing the two versions is the point.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Name your first three targets",
        "From your own pipeline or from the registry, pick three firms where the research or "
        "data-consolidation problem on the last few slides is plausibly real. Write one sentence "
        "each on why. These are the accounts you will practise against for the rest of the course.",
        checkpoint="Write down three named firms and one sentence each on the problem you think "
        "OpenBB solves for them.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "What the next section does",
        "You now know what it is. Next you install it, because an advisor who has never run the "
        "product cannot answer the second question in any real meeting. The install is genuinely "
        "quick and the failure modes are worth meeting on your own machine rather than on a call.",
        refs=(DOCS_INSTALL,),
    ),
)

SECTION_1_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="Which OpenBB product will most of your commission conversations be about?",
            options=(
                "The open-source Python package",
                "OpenBB Workspace",
                "The App Marketplace",
                "The legacy Terminal",
            ),
            answer_index=1,
            explanation=(
                "Workspace is the commercial product an investment team buys. The Python package "
                "is the open-source data layer, and it matters mostly as a way in and as the "
                "source of technical objections."
            ),
        ),
        TestQuestion(
            prompt="What is a widget in OpenBB Workspace?",
            options=(
                "A saved search",
                "A self-contained data component with its source, metadata, visual layer\n"
                " and parameters",
                "A licence to a market data feed",
                "An AI agent attached to a dashboard",
            ),
            answer_index=1,
            explanation=(
                "OpenBB describes widgets as the fundamental data units. Everything else in "
                "Workspace is assembled from them, so this is the term to be sure of."
            ),
        ),
        TestQuestion(
            prompt="A prospect says: does this replace Bloomberg? What is the best answer?",
            options=(
                "Yes, at a fraction of the cost",
                "No, and it does not try to. It is a workspace for AI workflows over data\n"
                " you already have",
                "Only for research teams",
                "Yes, once you add the App Marketplace",
            ),
            answer_index=1,
            explanation=(
                "OpenBB does not claim parity, and a sophisticated buyer has heard the cheap-"
                "Bloomberg pitch before. Declining the comparison makes you more credible and "
                "avoids setting an expectation that kills the deal later."
            ),
        ),
        TestQuestion(
            prompt="What makes an OpenBB app different from a dashboard?",
            options=(
                "An app is read-only",
                "An app is a pre-built template with curated widgets, linked parameters,\n"
                " an agent and prompts for a specific workflow",
                "An app runs on the client's own servers",
                "There is no difference",
            ),
            answer_index=1,
            explanation=(
                "Apps are pre-configured dashboards for a named workflow. In a demo they are what "
                "makes the product look finished instead of empty."
            ),
        ),
        TestQuestion(
            prompt="Which of these does OpenBB NOT give a client?",
            options=(
                "A single interface over structured and unstructured data",
                "AI agents grounded in their own data",
                "The right to market data they do not already licence",
                "Shareable dashboards",
            ),
            answer_index=2,
            explanation=(
                "OpenBB is not a data licence. Saying so early makes you more credible and stops "
                "a deal dying later on an expectation you set in the first meeting."
            ),
        ),
        TestQuestion(
            prompt="Why does the open-source package matter to you commercially?",
            options=(
                "It is what the client pays for",
                "It is the distribution channel: someone technical inside the firm often\n"
                " already trusts it",
                "It is required to run Workspace",
                "It carries the commission",
            ),
            answer_index=1,
            explanation=(
                "The package gets OpenBB in front of a quant or engineer before you arrive. "
                "Finding that person is often faster than finding the budget holder."
            ),
        ),
    ),
)


def section_1() -> CourseModule:
    """Section 1: what OpenBB is, and why that matters in a client meeting."""
    return CourseModule(
        id=_id("module", "what-it-is"),
        title="What OpenBB is, and why that matters in a meeting",
        order=0,
        lessons=(
            Lesson(
                id=_id("lesson", "what-it-is"),
                title="What OpenBB is",
                body=_S1_BODY,
                order=0,
                slides=_SECTION_1_SLIDES,
                drill_topics=("product:openbb:what-it-is",),
                measurement=(
                    "You can explain OpenBB to a client in under sixty seconds, without notes, "
                    "including one thing it does not do."
                ),
            ),
        ),
        section_test=SECTION_1_TEST,
    )


# --- Section 2 — Install it, and make it work on your own machine -------------------------

_S2_BODY = (
    "By the end of this lesson OpenBB is installed on your machine, you have pulled real market "
    "data with it, and you have met the two or three ways the install goes wrong. That last part "
    "is the reason this section exists. An advisor who has only read about a product cannot answer "
    "the second question in a real meeting, and the second question is always more specific than "
    "the first."
)

_SECTION_2_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "What you are installing, and what you are not",
        "This section installs the open-source Python package. It is not Workspace, which runs in "
        "a browser and is what a client buys. You are installing the package because it is the "
        "fastest honest way to see OpenBB's data coverage with your own eyes, and because a "
        "technical buyer will ask whether you have used it.",
        refs=(DOCS_INSTALL, DOCS_WORKSPACE),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "What your machine needs",
        "OpenBB states that most systems capable of running Python 3.10 to 3.14 will work, and "
        "recommends a processor five years old or newer, an up-to-date operating system and at "
        "least 8GB of RAM. The stated minimums are Windows 11 or macOS Big Sur. If your machine is "
        "below that, say so now rather than debugging for an hour.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Check your Python version first",
        "Run `python --version`. If it reports anything below 3.10 or above 3.14, install a "
        "supported version before going further. Most install failures reported by new users are "
        "a Python version problem wearing a different error message, and five seconds here saves "
        "twenty minutes later.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Why a virtual environment is not optional",
        "OpenBB says plainly that installing directly to the system Python or the base environment "
        "is not recommended, and to create a new environment first. OpenBB pulls in a large "
        "dependency tree. Installing it into your system Python is how you break an unrelated tool "
        "next week and never connect the two events.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        4,
        SlideKind.WALKTHROUGH,
        "Create the environment",
        "In a terminal, in a directory you can find again:\n\n"
        "```bash\npython -m venv .openbb\n```\n\n"
        "This creates an isolated environment in a folder called `.openbb`. OpenBB also documents "
        "Conda, VS Code, PyCharm and Jupyter routes; venv is the one with the fewest moving parts.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        5,
        SlideKind.WALKTHROUGH,
        "Activate it",
        "On macOS or Linux:\n\n```bash\nsource .openbb/bin/activate\n```\n\n"
        "On Windows:\n\n```powershell\n.openbb\\Scripts\\activate\n```\n\n"
        "Your prompt should now show `(.openbb)`. If it does not, the activate command did not "
        "run, and everything after this will install to the wrong place.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        6,
        SlideKind.WALKTHROUGH,
        "Install the package",
        "```bash\npip install openbb\n```\n\n"
        "That is the whole install. It will take a few minutes and print a great deal. A wall of "
        "dependency output is normal and is not an error; look at the last line rather than the "
        "middle of the log.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        7,
        SlideKind.WALKTHROUGH,
        "Build the static assets",
        "```bash\nopenbb-build\n```\n\n"
        "OpenBB generates required static assets on first import. In containers and CI it should "
        "be invoked immediately after installation. Running it by hand now means your first import "
        "is fast instead of mysteriously slow.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        8,
        SlideKind.WALKTHROUGH,
        "Import it",
        "Start Python and run:\n\n```python\nfrom openbb import obb\n```\n\n"
        "The first import does real work and may take a moment. If it returns without an error, "
        "the install is sound. `obb` is the single entry point to everything.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        9,
        SlideKind.WALKTHROUGH,
        "Your first real data call",
        "```python\nquote_data = obb.equity.price.quote("
        'symbol="AAPL", provider="yfinance")\n```\n\n'
        "This is OpenBB's own quickstart example. `yfinance` needs no API key, which is why it is "
        "the right first call. You have just pulled live market data through OpenBB.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Look at it as a table",
        "```python\nquote_data.to_df()\n```\n\n"
        "Every OpenBB result converts to a pandas DataFrame with `.to_df()`. This one method is "
        "why a quant takes the package seriously: whatever they pull lands in the shape they "
        "already work in.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The shape of every call",
        "`obb.<asset class>.<category>.<endpoint>(...)`. Equity, price, quote. Once you see that "
        "pattern you can guess your way around the library without the documentation, which is a "
        "useful thing to be able to demonstrate on a call.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Ask for a time series",
        "```python\nobb.equity.price.historical(\n"
        '    symbol="AAPL", start_date="2026-01-01", provider="yfinance"\n'
        ").to_df()\n```\n\n"
        "Time-series endpoints take `start_date` and `end_date`. This is the call to have ready "
        "when someone asks what the package actually gives them.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Providers, and the behaviour that surprises people",
        "Most endpoints accept several providers. If you do not name one, OpenBB picks "
        "alphabetically. And if a provider needs an API key that has not been added to settings, "
        "OpenBB skips it and tries the next. That fallback is convenient and it means two runs can "
        "quietly use different sources.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "Why that fallback matters to a client",
        "A research team that cannot say which vendor a number came from has a provenance problem, "
        "and in a regulated firm that is a real one. Name the provider explicitly in anything that "
        "matters. This is also a good, honest thing to raise unprompted in a technical meeting.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "API keys",
        "Keys live in OpenBB settings rather than in your code. You do not need any for this "
        "lesson, because `yfinance` needs none. You will need them the moment a client asks about "
        "a vendor they already pay for, which is usually the second conversation.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "The local API, and the port to remember",
        "The platform API runs on `http://localhost:6900` by default. That port is worth "
        "remembering: it is how Workspace talks to a locally-running platform, and it is the first "
        "thing to check when a client's engineer says the connection is not working.",
        refs=(DOCS_PLATFORM_INSTALLER,),
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "The browser gotcha",
        "OpenBB notes that Brave and Safari need an HTTPS connection, with SSL certificate setup "
        "documented separately. If a demo fails on someone's laptop and they are using Safari, "
        "this is the first thing to check rather than the last.",
        refs=(DOCS_PLATFORM_INSTALLER,),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "How much data you are looking at",
        "OpenBB describes access to more than 350 datasets across roughly a dozen data vendors and "
        "hundreds of widgets. Quote the number as approximate and cite it. A precise-sounding "
        "figure you cannot source is worse in a meeting than an honest range.",
        refs=(DOCS_PLATFORM_INSTALLER,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "When the install fails: wrong Python",
        "Symptom: `pip install openbb` resolves for a long time and then fails on a dependency you "
        "have never heard of. Cause, nearly always: a Python version outside 3.10 to 3.14. Fix: "
        "check `python --version` inside the activated environment, not outside it.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        20,
        SlideKind.EXAMPLE,
        "When the install fails: the wrong environment",
        "Symptom: the install succeeds and `from openbb import obb` fails with a module-not-found "
        "error. Cause: you installed into one environment and are importing from another. Fix: "
        "confirm your prompt shows `(.openbb)`, then re-run the install.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        21,
        SlideKind.EXAMPLE,
        "When the first import is very slow",
        "Symptom: `from openbb import obb` hangs for a long time the first time. Cause: the static "
        "asset build is happening at import. Fix: it is expected once; if you want to avoid it, "
        "run `openbb-build` after installing, which is what OpenBB recommends for containers.",
        refs=(DOCS_INSTALL,),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "Docker and source installs exist",
        "OpenBB documents a Docker build from `platformAPI.Dockerfile` and a source install via "
        "the develop branch, Poetry and `python dev_install.py`. You will not need either, but "
        "knowing they exist lets you answer a client engineer without guessing.",
        refs=(DOCS_INSTALL, REPO),
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Prove the install",
        "Run the quote call and the historical call, and keep the output. This is the evidence "
        "that you have actually used the product rather than read about it, and it is the thing "
        "that changes how a technical buyer treats you.",
        checkpoint="Save a screenshot or paste of your own `obb.equity.price.quote` output, with "
        "the provider named explicitly.",
    ),
    _s(
        24,
        SlideKind.CHECKPOINT,
        "Pull data for one of your three targets",
        "Take one of the three firms you named in section 1. If it is listed, pull its price "
        "history. If it is not, pull a listed competitor. Walking into a meeting having already "
        "looked at their numbers through the product you are selling is a small thing that lands.",
        checkpoint="Run a historical price call for one of your three named targets, or its "
        "closest listed competitor, and keep the output.",
    ),
    _s(
        25,
        SlideKind.CONCEPT,
        "What the next section does",
        "You have the open-source package running. Next you sign up to Workspace, which is the "
        "product a client actually buys, and get oriented in it. Everything you have just learned "
        "about providers and provenance carries directly into that conversation.",
        refs=(DOCS_WORKSPACE,),
    ),
)

SECTION_2_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="Which Python versions does OpenBB state it supports?",
            options=("3.6 to 3.9", "3.10 to 3.14", "Any version", "3.12 only"),
            answer_index=1,
            explanation=(
                "OpenBB states most systems capable of running Python 3.10 to 3.14 will be "
                "compatible. Most reported install failures are a version problem in disguise."
            ),
        ),
        TestQuestion(
            prompt="Why does OpenBB tell you to create a virtual environment first?",
            options=(
                "It is faster",
                "Installing to the system or base environment is not recommended, and\n"
                " OpenBB has a large dependency tree",
                "It is required for API keys",
                "Workspace will not connect otherwise",
            ),
            answer_index=1,
            explanation=(
                "OpenBB says directly that installing to the system Python or base environment is "
                "not recommended. Breaking an unrelated tool next week is the real cost."
            ),
        ),
        TestQuestion(
            prompt="You do not name a provider on a call. What does OpenBB do?",
            options=(
                "Refuses the call",
                "Picks alphabetically, and skips any provider whose API key is missing",
                "Uses the fastest provider",
                "Always uses yfinance",
            ),
            answer_index=1,
            explanation=(
                "Default selection is alphabetical, and a provider without a configured key is "
                "skipped for the next one. Convenient, and a provenance risk worth naming to a "
                "regulated client."
            ),
        ),
        TestQuestion(
            prompt="What port does the platform API use by default?",
            options=("8080", "3000", "6900", "5432"),
            answer_index=2,
            explanation=(
                "`http://localhost:6900`. It is the first thing to check when a client engineer "
                "says Workspace cannot see their local platform."
            ),
        ),
        TestQuestion(
            prompt="A client demos on Safari and the connection fails. What is your first thought?",
            options=(
                "Their firewall",
                "Brave and Safari need an HTTPS connection, per OpenBB's own note",
                "Their Python version",
                "The API key",
            ),
            answer_index=1,
            explanation=(
                "OpenBB documents this specifically. Knowing it turns an embarrassing demo failure "
                "into a thirty-second fix."
            ),
        ),
        TestQuestion(
            prompt="What does `.to_df()` do, and why does it matter commercially?",
            options=(
                "Downloads a file; it matters for compliance",
                "Converts a result to a pandas DataFrame; it means a quant gets data in\n"
                " the shape they already work in",
                "Formats output for Workspace",
                "Nothing, it is deprecated",
            ),
            answer_index=1,
            explanation=(
                "Every result converts with `.to_df()`. That one method is a large part of why a "
                "technical user takes the package seriously."
            ),
        ),
    ),
)


def section_2() -> CourseModule:
    """Section 2: install it, and make it work on your own machine."""
    return CourseModule(
        id=_id("module", "install"),
        title="Install it, and make it work on your own machine",
        order=1,
        lessons=(
            Lesson(
                id=_id("lesson", "install"),
                title="Installing OpenBB and pulling your first data",
                body=_S2_BODY,
                order=0,
                slides=_SECTION_2_SLIDES,
                drill_topics=("product:openbb:install",),
                measurement=(
                    "OpenBB is installed in its own environment on your machine and you have "
                    "pulled real price data with an explicitly named provider."
                ),
            ),
        ),
        section_test=SECTION_2_TEST,
    )


# --- Section 3 — Sign up to Workspace and find your way around ----------------------------

_S3_BODY = (
    "By the end of this lesson you have an OpenBB Workspace account, you have opened it, and you "
    "can find the four things that matter without hunting: the widget library, a dashboard, an "
    "app, and the agent. This is the product a client buys, so being fluent in the first ninety "
    "seconds of it is worth more to you than any amount of feature knowledge."
)

_SECTION_3_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Where Workspace lives",
        "Workspace runs in the browser at pro.openbb.co. OpenBB's own documentation points you "
        "there to explore its capabilities and the app gallery. This is the thing you demo. The "
        "package you installed in the last section is not.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        1,
        SlideKind.WALKTHROUGH,
        "Create your account",
        "Go to pro.openbb.co and sign up. Use your @bruntsfield.capital address rather than a "
        "personal one: you will be showing this screen to clients, and an account in your own name "
        "at the firm is part of looking like a professional rather than a hobbyist.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The tiers, and which one you are in",
        "OpenBB documents several ways in: the PWA, Enterprise, Lite, and the Platform Installer. "
        "You will almost certainly start on the free tier. Know which one you are demonstrating "
        'from, because a client asking "can I do that?" is really asking "is that in the tier '
        'you are quoting me?"',
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        3,
        SlideKind.WALKTHROUGH,
        "Open the widget library",
        "Click the search field top left, or press `Cmd+K` on a Mac or `Ctrl+K` on Windows. That "
        "keyboard shortcut is the single most useful thing to know in a demo: it makes you look "
        "like someone who uses the product rather than someone reading a script.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "What a widget actually contains",
        "OpenBB describes a widget as more than a chart or a table: it is a data container built "
        "to "
        "answer a specific analytical question. Four parts. A data source, a metadata layer, a "
        "visual presentation, and parameters. Learn those four and every widget in the library "
        "stops being a mystery.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The data source",
        "Where the information comes from: a feed, a database, the organisation's own custom data, "
        "or a static file. That last one matters more than it looks. A client with a spreadsheet "
        "nobody can get out of email has a widget-shaped problem.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The metadata layer",
        "Title, description, category, sub-category and source attribution. Source attribution is "
        "the one to point at in a regulated firm: the widget carries where its number came from, "
        "which is the provenance question you met in the last section, answered in the product.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The visual layer",
        "Tables, charts, PDFs or custom views. PDFs being first-class is worth noticing: a "
        "research "
        "note and a price series can sit on the same dashboard, which is exactly the "
        "structured-and-unstructured story from section 1 made concrete.",
        refs=(DOCS_WIDGETS, DOCS_WORKSPACE),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Parameters, and why they are the demo moment",
        "Parameters are the interactive part: date ranges, ticker selection and so on. When "
        "widgets "
        "share a parameter name, changing a ticker or a date range in one automatically updates "
        "every linked widget. Watching a whole dashboard move from one field is the moment a "
        "prospect leans in.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Widget controls you get for free",
        "Universal controls include refresh settings, export to CSV, JSON and Excel, and view "
        "toggles. Export matters commercially: an analyst who can get the data out is far less "
        "afraid of being locked in, and lock-in fear is a common quiet objection.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Table widgets",
        "Tables offer column sorting, filtering and grouping, and generate Excel Add-in formulas "
        "automatically. If your client lives in Excel, and many wealth managers do, that automatic "
        "formula generation is a more persuasive detail than anything about AI.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "Chart widgets",
        "Charts are TradingView-based, with technical indicator overlays and adjustable "
        "timeframes. "
        "Naming TradingView is useful in a room: it is a product almost every prospect has already "
        "used, so it answers the unspoken question about whether the charting is any good.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Create your first dashboard",
        "Click the `+` button in the sidebar to create a new dashboard, and give it a descriptive "
        'name. Name it after a real use case rather than "test" — you will keep this one, and '
        "you will show it to someone.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Put something on it",
        "Click Add Widget, or right-click to reach the context menu. Then drag and drop widgets "
        "where you want them, resizing and arranging so the important data is emphasised. Spend a "
        "minute on the arrangement; a cramped dashboard demos badly.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "Organising a dashboard that grew",
        "A navigation bar widget lets you separate widgets into categories, which is the answer "
        "when a dashboard has outgrown one screen. You can also disable grouping from the "
        "right-click menu when the automatic behaviour is not what you want.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "Managing dashboards",
        "The ellipsis menu next to each dashboard in the sidebar gives you Rename, Move to "
        "folders, "
        "Duplicate and Open in new window. Duplicate is the one you will use most: build a good "
        "dashboard once, then clone it per client.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "Sharing, and why it is the commercial hinge",
        "Share sits in the same ellipsis menu and is how you collaborate with team members. This "
        "is "
        "where a single analyst's work becomes the desk's. Almost every business case you write "
        "will lean on this rather than on any individual widget.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "Exporting a dashboard as configuration",
        "Right-click and choose Export apps.json to export the dashboard configuration. This is "
        "how "
        'a dashboard becomes an app, and it is the answer to "can we standardise this across the '
        'team?" — which is a buying question, not a technical one.',
        refs=(DOCS_DASHBOARDS, DOCS_APPS),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "Refreshing data",
        "Refresh data updates every widget with the latest information. Know where it is before a "
        "demo. Stale numbers on screen while you talk about real-time workflows is an avoidable "
        "way to lose the room.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The agent, and the word to use",
        "The AI agent reads the metadata from your widgets to query the right datasets, and can "
        "watch dashboards for anomalies. The word to use with a compliance-minded buyer is "
        "grounded: it answers from what is on the dashboard, not from what a model remembers.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        20,
        SlideKind.EXAMPLE,
        "Ninety seconds that works",
        "Open a dashboard. Press `Cmd+K`, add a widget, change one parameter and let the linked "
        "widgets move. Ask the agent a question about what is on screen. Stop. That sequence "
        "demonstrates the whole product and leaves them asking the next question.",
        refs=(DOCS_WIDGETS, DOCS_DASHBOARDS),
    ),
    _s(
        21,
        SlideKind.EXAMPLE,
        "What not to do in a first demo",
        "Do not tour the widget library. Do not open settings. Do not explain the difference "
        "between the package and Workspace unless asked. A prospect remembers one thing from a "
        "first demo, so choose which one it is going to be before you start.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Account created",
        "You need a real account for the next two sections, both of which are you building things. "
        "Do this now rather than reading ahead.",
        checkpoint="Create your OpenBB Workspace account at pro.openbb.co using your "
        "@bruntsfield.capital address, and confirm you can sign in.",
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Find four things without help",
        "Open the widget library with the keyboard shortcut, create an empty dashboard, open the "
        "ellipsis menu, and locate the agent. No documentation. If any of the four takes more than "
        "a few seconds, do it twice more now.",
        checkpoint="Time yourself finding the widget library, a new dashboard, the ellipsis menu "
        "and the agent. Note anything that took you longer than ten seconds.",
    ),
    _s(
        24,
        SlideKind.CONCEPT,
        "What the next section does",
        "You have an account and you know where things are. Next you build a real workspace for "
        "one "
        "of the three targets you named in section 1, which is the first time in this course you "
        "make something you could actually show a client.",
        refs=(DOCS_DASHBOARDS,),
    ),
)

SECTION_3_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What opens the widget library?",
            options=(
                "The settings menu",
                "The search field top left, or Cmd+K / Ctrl+K",
                "Right-click on the sidebar",
                "The agent",
            ),
            answer_index=1,
            explanation=(
                "The keyboard shortcut is the single most useful thing to know in a demo. It makes "
                "you look like someone who uses the product rather than reads about it."
            ),
        ),
        TestQuestion(
            prompt="What are the four parts of a widget?",
            options=(
                "Chart, table, PDF, export",
                "Data source, metadata layer, visual presentation, parameters",
                "Title, data, agent, share link",
                "Source, licence, refresh, owner",
            ),
            answer_index=1,
            explanation=(
                "OpenBB describes a widget as a data container built to answer a specific "
                "analytical question, made of those four parts. Learn them and the library stops "
                "being a mystery."
            ),
        ),
        TestQuestion(
            prompt="Two widgets share a parameter name. What happens when you change it in one?",
            options=(
                "Nothing, each widget is independent",
                "Every linked widget updates automatically",
                "The dashboard reloads",
                "You are asked to confirm",
            ),
            answer_index=1,
            explanation=(
                "Shared parameter names link widgets. Watching a whole dashboard move from one "
                "field is the moment a prospect leans in, so it is the thing to demo."
            ),
        ),
        TestQuestion(
            prompt="Where do you find Share, Rename and Duplicate for a dashboard?",
            options=(
                "The agent panel",
                "The ellipsis menu next to the dashboard in the sidebar",
                "The widget library",
                "Export apps.json",
            ),
            answer_index=1,
            explanation=(
                "Sharing is the commercial hinge: it is how one analyst's work becomes the desk's, "
                "and most business cases lean on it rather than on any individual widget."
            ),
        ),
        TestQuestion(
            prompt="Why does automatic Excel formula generation on table widgets matter?",
            options=(
                "It is required for export",
                "Many buyers, wealth managers especially, live in Excel, so it can persuade"
                " more than the AI story",
                "It replaces the agent",
                "It is only available in Enterprise",
            ),
            answer_index=1,
            explanation=(
                "Meeting a client where they already work is usually more persuasive than asking "
                "them to move. Know your buyer's actual daily tool."
            ),
        ),
        TestQuestion(
            prompt=(
                "A prospect asks whether the team can standardise a dashboard you just built. "
                "What is the mechanism?"
            ),
            options=(
                "Share it read-only",
                "Right-click and Export apps.json, which is how a dashboard becomes an app",
                "Duplicate it for each person",
                "It is not possible",
            ),
            answer_index=1,
            explanation=(
                "Exporting the configuration turns a dashboard into an app. The question is a "
                "buying question dressed as a technical one, so answer it as one."
            ),
        ),
    ),
)


def section_3() -> CourseModule:
    """Section 3: sign up to Workspace and find your way around."""
    return CourseModule(
        id=_id("module", "sign-up-and-orientation"),
        title="Sign up to Workspace and find your way around",
        order=2,
        lessons=(
            Lesson(
                id=_id("lesson", "sign-up-and-orientation"),
                title="Your Workspace account, and the four things that matter",
                body=_S3_BODY,
                order=0,
                slides=_SECTION_3_SLIDES,
                drill_topics=("product:openbb:workspace",),
                measurement=(
                    "You have a Workspace account and can reach the widget library, a new "
                    "dashboard, the ellipsis menu and the agent without looking anything up."
                ),
            ),
        ),
        section_test=SECTION_3_TEST,
    )


def rebuilt_sections() -> tuple[CourseModule, ...]:
    """The sections rebuilt to the GRS-0215 standard, in order. Grows as GRS-0216 progresses."""
    return (section_1(), section_2(), section_3())


# Sections written so far, and sections still to write. The depth check fails while anything is in
# SECTIONS_PLANNED, so this course cannot read as finished until it is.
SECTIONS_AUTHORED: tuple[str, ...] = ("what-it-is", "install", "sign-up-and-orientation")
SECTIONS_PLANNED: tuple[str, ...] = (
    "first-workspace",
    "second-workspace",
    "the-data",
    "who-buys-and-why",
    "how-and-when-to-sell",
)
