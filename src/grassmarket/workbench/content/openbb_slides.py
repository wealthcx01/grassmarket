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

All eight sections are written (2026-07-29). `SECTIONS_AUTHORED` lists them and `SECTIONS_PLANNED`
is empty. While it was not empty a test asserted the course was unfinished, so it could never read
as done; that test has been deleted now that it is, which is what its own failure message asked
for. The point of the mechanism was that the previous attempt shipped a renderer with no content
and still read as progress.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.learning import (
    CourseModule,
    Lesson,
    LessonAsset,
    SectionTest,
    Slide,
    SlideKind,
    SourceRef,
    SourceRefKind,
    TestQuestion,
)

from grassmarket.workbench.content.openbb_diagrams import SVG

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
LICENCE = SourceRef(
    title="OpenBB ODP licence (AGPLv3), on GitHub",
    url="https://github.com/OpenBB-finance/OpenBB/blob/develop/LICENSE",
    kind=SourceRefKind.REPO,
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
    asset: LessonAsset | None = None,
) -> Slide:
    return Slide(
        order=order,
        kind=kind,
        title=title,
        body=body,
        references=refs,
        checkpoint_prompt=checkpoint,
        asset=asset,
    )


def _diagram(key: str, caption: str, alt: str) -> LessonAsset:
    """A course diagram (GRS-0225). The drawing is generated from the SceneSpec under
    `design/motion/courses/openbb/`; the caption and the alt text are written here, beside the slide
    they belong to, because they are prose and a generator has no business writing them.

    `SVG[key]` raises on an unknown key rather than returning a placeholder — a slide that silently
    lost its diagram would still render, and look finished.
    """
    return LessonAsset(caption=caption, alt=alt, svg=SVG[key])


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
        asset=_diagram(
            "two_products",
            "Two products, one company — and only one of them is a commission conversation.",
            "Two panels side by side. On the left, the Open Data Platform: open source, AGPLv3, "
            "bought by nobody and installed by a quant with pip install openbb. On the right, "
            "OpenBB Workspace: commercial, in the browser, used by an investment team, at "
            "pro.openbb.co. A line beneath reads: almost every commission conversation is about "
            "the right-hand box.",
        ),
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
        "their data, not from a model's memory of the internet.\n\n"
        "Workspace also exposes an **MCP** endpoint, so agents the firm already uses — Claude "
        "Code, Cursor, Codex — can work over that same governed data with permissions and lineage "
        "enforced. That is the sharpest enterprise hook in the product: agents are already loose "
        "inside the firm, and this is the argument for them running somewhere governed rather than "
        "somewhere nobody can audit.",
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
        asset=_diagram(
            "what_runs_where",
            "What you install, and what a client buys. Different machines, different products.",
            "Two boxes. On the left, your machine: the open-source package installed with pip "
            "install openbb, and the platform API on localhost:6900. On the right, their browser: "
            "OpenBB Workspace at pro.openbb.co, marked as the commercial product. An arrow runs "
            "from left to right labelled 'talks to'. Beneath: you install the left-hand box, the "
            "client pays for the right-hand one.",
        ),
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
        asset=_diagram(
            "widget_anatomy",
            "The four parts of a widget. The metadata layer is the one compliance cares about.",
            "One widget broken into four stacked parts: data source (a feed, a database, their "
            "own data, a static file); metadata layer (title, category, and the source "
            "attribution); visual layer (table, chart, PDF, or a custom view); and parameters (the "
            "interactive part: ticker, date range). An arrow runs from the metadata layer to a "
            "highlighted panel reading: this is your answer when compliance asks where a number "
            "came from.",
        ),
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
        asset=_diagram(
            "linked_parameters",
            "One field moves everything. This is the demo, so practise it until it is boring.",
            "A single ticker field at the top of a dashboard, holding a symbol. Three arrows fan "
            "out from it down to three widgets: a price chart, fundamentals, and news and "
            "filings. Changing the one field updates all three. A line beneath reads: a prospect "
            "does not care that you have three widgets, they care about this.",
        ),
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


# --- Section 4 — Build your first workspace, for a real target ----------------------------

_S4_BODY = (
    "By the end of this lesson you have built a working research dashboard for one of the three "
    "firms you named in section 1, and you can rebuild it in front of someone in about five "
    "minutes. This is the first thing in this course you could actually put on a screen in a "
    "client meeting, and building it for a real target rather than a sample ticker is the whole "
    "point: a demo about their business is a different conversation from a demo about Apple."
)

_SECTION_4_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "What you are building, and why this one",
        "A morning research dashboard: the view an analyst would open at 7am. It is the most "
        "common real use case, it is quick to build, and it maps directly onto the pain you "
        "identified in section 1. Do not start with something clever.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        1,
        SlideKind.WALKTHROUGH,
        "Pick the target",
        "Take the first of the three firms you wrote down. If they are listed, you will use their "
        "own ticker. If they are not, pick the closest listed competitor and be ready to say why "
        "you chose it, because in a real meeting someone will ask.",
    ),
    _s(
        2,
        SlideKind.WALKTHROUGH,
        "Create and name the dashboard",
        "Click the `+` in the sidebar, and give it a descriptive name. Name it after the firm and "
        'the job, not after yourself: "Meridian — morning research" rather than "my '
        'dashboard". You will be sharing this.',
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        3,
        SlideKind.WALKTHROUGH,
        "Add a price chart",
        "Press `Cmd+K` or `Ctrl+K`, search for a price chart widget, and add it. Set the ticker to "
        "your target. The charts are TradingView-based, so the interaction will already feel "
        "familiar to anyone who has traded.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        4,
        SlideKind.WALKTHROUGH,
        "Add a fundamentals table",
        "Add a table widget carrying the firm's fundamentals. Tables give you column sorting, "
        "filtering and grouping. Sort it into the order an analyst would actually read, because a "
        "default sort is a small signal that nobody has thought about the view.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        5,
        SlideKind.WALKTHROUGH,
        "Add news or filings",
        "Add a widget carrying news or regulatory filings for the same firm. This is the slide "
        "where the dashboard stops being a chart and becomes a workspace: two different shapes of "
        "information, one subject.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        6,
        SlideKind.WALKTHROUGH,
        "Link the parameters",
        "Make sure all three widgets use the same parameter name for the ticker. Now change it in "
        "one and watch the others follow. This is the moment you will replay in every demo you "
        "ever give of this product, so get it working before you go further.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Why the linked parameter is the whole demo",
        "A prospect does not care that you have three widgets. They care that one field drives the "
        "whole view, because that is the thing their current spreadsheet cannot do. Everything "
        "else on the dashboard is supporting evidence for that one interaction.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        8,
        SlideKind.WALKTHROUGH,
        "Arrange it for a screen share",
        "Drag and resize so the chart is dominant, the table is readable without scrolling, and "
        "the news sits to one side. Test it at the window size you actually present at, which is "
        "usually smaller than the one you build at.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Readability beats completeness",
        "A dashboard with four legible widgets demos better than one with nine cramped ones. You "
        "are not proving coverage, you are proving that a morning takes five minutes instead of "
        "ninety. Cut anything that does not serve that sentence.",
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Add a navigation bar if it has grown",
        "If you have gone past one screen, add a navigation bar widget and separate the widgets "
        "into categories. Do this rather than shrinking everything, because shrinking is how a "
        "dashboard becomes unreadable on a shared screen.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Ask the agent something",
        "Open the agent and ask a question about what is on the dashboard. It reads the metadata "
        "from your widgets to query the right datasets, so ask something that needs two of your "
        "widgets at once. That is what shows it is grounded rather than generic.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        12,
        SlideKind.EXAMPLE,
        "A question that lands, and one that does not",
        '"What changed in the filings this week that the price has not reacted to?" needs two '
        'sources and is the kind of thing an analyst actually asks. "What is the share price?" '
        "is on the screen already, and asking it makes the agent look like a toy.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Refresh it",
        "Use Refresh data and confirm every widget updates. Do this before any demo. Stale numbers "
        "on screen while you talk about a real-time workflow is a small failure that costs more "
        "credibility than it should.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Export something",
        "Export one widget to CSV or Excel. You are checking it works, and you are learning where "
        'the control is, because "can we get the data out?" is one of the most common quiet '
        "objections and you want to answer it by doing it rather than saying yes.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Duplicate it",
        "Use the ellipsis menu next to the dashboard and choose Duplicate. You now have a "
        "template. "
        "This is how you will build the second workspace in the next section, and how you will "
        "spin one up per client without starting again.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "Dashboard, app, and which word to use",
        "What you built is a dashboard: a blank canvas you configured. An app is a pre-configured "
        "template with curated widgets, a chosen agent and its own prompt library. Use the right "
        "word in front of a client, because they will hear both from OpenBB.",
        refs=(DOCS_APPS,),
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "What an app adds on top",
        "Apps carry three things a dashboard does not: curated widgets with parameters already "
        "synchronised, a library of pre-written prompts for that domain, and an AI agent tuned to "
        "it that activates when you select the app. That prompt library is the part clients "
        "underestimate.",
        refs=(DOCS_APPS,),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "Turning your dashboard into something the team uses",
        "Right-click and Export apps.json to export the configuration. That file is how a good "
        "dashboard stops being one person's and becomes the desk's standard. It is also the "
        'honest answer to "how do we roll this out?"',
        refs=(DOCS_DASHBOARDS, DOCS_APPS),
        asset=_diagram(
            "dashboard_to_app",
            "How one person's dashboard becomes the desk's standard.",
            "A configured dashboard on the left — widgets a single analyst arranged — passing "
            "through an Export apps.json step in the middle, and arriving on the right as an app "
            "the whole desk opens. The point of the drawing is that the middle step is one "
            "right-click, not a project.",
        ),
    ),
    _s(
        19,
        SlideKind.WALKTHROUGH,
        "Share it with someone",
        "Use Share from the ellipsis menu and send it to a colleague. Watch what they do with it "
        "cold, without you narrating. Anything they hesitate over is something a client will "
        "hesitate over, and it is much cheaper to find out now.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        20,
        SlideKind.EXAMPLE,
        "What good looks like",
        "Four to six widgets. One linked parameter that moves everything. One agent question that "
        "needs two sources. Readable on a shared screen at meeting size. Buildable by you, from "
        "nothing, in about five minutes while talking.",
    ),
    _s(
        21,
        SlideKind.EXAMPLE,
        "The most common mistake",
        "Building the dashboard you find interesting rather than the one your client's analyst "
        "would open. You are not demonstrating the product's range, you are demonstrating that "
        "you understood their morning. Those are different dashboards.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Build it",
        "This is the section's deliverable. Not a screenshot from the documentation: your own "
        "dashboard, for your own target, that you built.",
        checkpoint="Build a working dashboard for one of your three named targets with at least "
        "three widgets and one working linked parameter. Keep a screenshot.",
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Rebuild it from scratch, timed",
        "Delete it and build it again while timing yourself. The second build is the one that "
        "matters, because in a real meeting you will be building while talking and answering "
        "questions. Aim to be under ten minutes.",
        checkpoint="Rebuild the dashboard from an empty canvas and record how long it took.",
    ),
    _s(
        24,
        SlideKind.CONCEPT,
        "What the next section does",
        "One dashboard proves you can use the product. The founder asked for workspaces, plural, "
        "and the reason is that the second one is where you learn what generalises. Next you build "
        "a deliberately different one for a different job.",
        refs=(DOCS_DASHBOARDS,),
    ),
)

SECTION_4_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What is the single most important interaction to get working before a demo?",
            options=(
                "Exporting to Excel",
                "One linked parameter that moves every widget at once",
                "The agent",
                "Refreshing data",
            ),
            answer_index=1,
            explanation=(
                "A prospect does not care that you have three widgets. They care that one field "
                "drives the whole view, because that is what their spreadsheet cannot do."
            ),
        ),
        TestQuestion(
            prompt="You built a configured canvas. Is that a dashboard or an app?",
            options=(
                "An app",
                "A dashboard: an app is a pre-configured template with curated widgets, a chosen "
                "agent and its own prompts",
                "Either word is fine",
                "A workspace",
            ),
            answer_index=1,
            explanation=(
                "The client will hear both words from OpenBB. Using the right one is a small "
                "signal that you know the product."
            ),
        ),
        TestQuestion(
            prompt="How does a good dashboard become the desk's standard?",
            options=(
                "Share it with everyone individually",
                "Right-click and Export apps.json, which is the configuration other people can use",
                "Duplicate it per person",
                "Rebuild it in each account",
            ),
            answer_index=1,
            explanation=(
                'Exporting the configuration is the honest answer to "how do we roll this out?", '
                "which is a buying question rather than a technical one."
            ),
        ),
        TestQuestion(
            prompt="Which agent question demonstrates grounding best?",
            options=(
                "What is the share price?",
                "What changed in the filings this week that the price has not reacted to?",
                "Summarise this company",
                "What do you think of this stock?",
            ),
            answer_index=1,
            explanation=(
                "It needs two of your widgets at once. A question whose answer is already on "
                "screen makes the agent look like a toy."
            ),
        ),
        TestQuestion(
            prompt="Why build the dashboard for a real target rather than a sample ticker?",
            options=(
                "Sample tickers are not supported",
                "A demo about their business is a different conversation from a demo about Apple",
                "It loads faster",
                "It is required for export",
            ),
            answer_index=1,
            explanation=(
                "You are not demonstrating the product's range. You are demonstrating that you "
                "understood their morning, and those are different dashboards."
            ),
        ),
        TestQuestion(
            prompt="Your dashboard has grown past one screen. What do you do?",
            options=(
                "Shrink every widget",
                "Add a navigation bar widget and separate widgets into categories",
                "Delete widgets until it fits",
                "Open it in a new window",
            ),
            answer_index=1,
            explanation=(
                "Shrinking is how a dashboard becomes unreadable on a shared screen, which is the "
                "only size that matters for a demo."
            ),
        ),
    ),
)


def section_4() -> CourseModule:
    """Section 4: build your first workspace, for a real target."""
    return CourseModule(
        id=_id("module", "first-workspace"),
        title="Build your first workspace, for a real target",
        order=3,
        lessons=(
            Lesson(
                id=_id("lesson", "first-workspace"),
                title="Your first dashboard, built for a firm you are actually chasing",
                body=_S4_BODY,
                order=0,
                slides=_SECTION_4_SLIDES,
                drill_topics=("product:openbb:workspace",),
                measurement=(
                    "You can build a three-widget dashboard with a working linked parameter for a "
                    "named target, from an empty canvas, in under ten minutes while talking."
                ),
            ),
        ),
        section_test=SECTION_4_TEST,
    )


# --- Section 5 — A second workspace, for a different job ----------------------------------

_S5_BODY = (
    "By the end of this lesson you have a second workspace that is deliberately not a copy of the "
    "first, and you can say what generalises between them. The founder asked for workspaces, "
    "plural, and this is why: one dashboard proves you can follow instructions, while the second "
    "one is where you find out which parts of the first were the product and which parts were "
    "the ticker you happened to pick."
)

_SECTION_5_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Why a second one, and why different",
        "If your second dashboard is the first with a new ticker, you have learned nothing. Pick a "
        "different JOB: not another firm, another question. That is what exposes the parts of "
        "Workspace you have not touched yet.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Three jobs worth building for",
        "A monitoring view that watches for something changing. A comparison view that puts "
        "several "
        "firms side by side. A client-reporting view that someone outside the desk will read. Each "
        "stresses a different part of the product.",
        refs=(DOCS_DASHBOARDS, DOCS_WORKSPACE),
        asset=_diagram(
            "three_jobs",
            "The job decides the shape. Build the one your target's segment already needs.",
            "Three miniature workspace layouts side by side, deliberately different shapes. "
            "Comparison: four small panels in a grid, several firms side by side, suiting an "
            "exchange or a bank. Monitoring: one large panel with a single highlighted element "
            "that changes, suiting a retail brokerage. Client reporting: two panels, each with a "
            "label line beneath it, read outside the room, suiting a wealth manager.",
        ),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Pick by segment, not by preference",
        "Choose the job that matches the segment you sell into most. Monitoring suits an exchange "
        "or a data team. Comparison suits a broker's research desk. Client reporting suits a "
        "wealth manager. Build the one you will actually demo.",
    ),
    _s(
        3,
        SlideKind.WALKTHROUGH,
        "Start from a duplicate, then gut it",
        "Duplicate your first dashboard from the ellipsis menu, then delete most of it. Starting "
        "from a duplicate keeps your parameter naming; gutting it stops you accidentally "
        "rebuilding the same view with a different title.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        4,
        SlideKind.WALKTHROUGH,
        "Name it for the job",
        '"Retail brokers — weekly comparison" rather than "dashboard 2". You are building a '
        "library, and in three months the name is the only thing that tells you which of these was "
        "worth keeping.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        5,
        SlideKind.WALKTHROUGH,
        "Build the comparison view",
        "If you chose comparison: add the same widget several times, one per firm, and do NOT link "
        "their tickers. Then add one table that holds all of them. Side by side is a different "
        "layout discipline from a single subject.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        6,
        SlideKind.WALKTHROUGH,
        "Or build the monitoring view",
        "If you chose monitoring: build around something that changes, and lean on the agent's "
        "ability to watch dashboards for anomalies. The value here is not the widgets, it is not "
        "having to look at them every hour.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        7,
        SlideKind.WALKTHROUGH,
        "Or build the client-reporting view",
        "If you chose reporting: build for someone who will not be in the room when they read it. "
        "Fewer widgets, more labelling, and the source attribution visible. This one is a wealth "
        "manager's buying trigger far more often than a data one.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "When to link parameters and when not to",
        "Linking is right when every widget is about one subject and wrong when the whole point is "
        "several subjects at once. Knowing which is which is the difference between using the "
        "product and repeating a trick you were shown.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        9,
        SlideKind.WALKTHROUGH,
        "Use a static file",
        "Add something that is not a market feed: a PDF, a spreadsheet, a note. Dashboards take "
        "static files, AI artifacts and notes alongside widgets, and almost every client you meet "
        "has an important file that currently lives in email.",
        refs=(DOCS_DASHBOARDS, DOCS_WORKSPACE),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Why the static file matters commercially",
        "Structured plus unstructured in one interface is OpenBB's own claim, and it is abstract "
        "until a client sees their own committee pack sitting next to a price series. Have this "
        "ready, because it converts a nod into a question.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Give this one its own agent question",
        "Write a question specific to this job rather than reusing the first one. A comparison "
        "view "
        'wants "which of these diverged most this week and why". A monitoring view wants "what '
        'changed since yesterday that I should care about".',
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "Prompts are a product feature, not an afterthought",
        "An app carries a library of pre-written prompts tailored to its analytical focus. Your "
        "second dashboard is where you start building your own, and a good prompt you can reuse is "
        "worth more in a demo than another widget.",
        refs=(DOCS_APPS,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Organise both dashboards",
        "Use Move to folders from the ellipsis menu and put both into a folder named for you or "
        "for "
        "the segment. Two is when a library starts, and a library nobody organised is how an "
        "advisor ends up rebuilding the same view for the fourth time.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "What the second build teaches you",
        "Usually one of three things. That your parameter naming from the first build was sloppy. "
        "That you do not know the widget library as well as you thought. Or that the layout you "
        "liked does not survive a different job. All three are worth finding now.",
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Export both configurations",
        "Right-click and Export apps.json on each. You now have two portable configurations. This "
        "is the beginning of something you can hand to a client rather than something you have to "
        "be present for.",
        refs=(DOCS_DASHBOARDS, DOCS_APPS),
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "The library you are actually building",
        "By the end of your first quarter you should have one dashboard per job per segment, not "
        "one per client. A client-specific dashboard is a duplicate with the ticker changed, and "
        "that takes two minutes if the job-level one is right.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "How this changes a meeting",
        "Instead of showing a product, you open the dashboard that matches the job they just "
        "described and change the ticker to their firm. The demo becomes about them within about "
        "fifteen seconds, and that is the entire advantage of having built these in advance.",
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "A trap worth naming",
        "Do not build a dashboard live in a first meeting to prove you can. You will be talking, "
        "answering questions, and something will not load. Build in advance, change the ticker "
        "live. Rebuild live only when someone asks how hard it is.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "What to do when a widget you want does not exist",
        "Workspace supports the organisation's own custom data as a widget data source, so the "
        'answer to "can it show our internal book?" is usually yes with work rather than no. '
        "Do not promise a timeline; promise to find out and come back.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "The honest limit of what you have built",
        "Two dashboards on public data prove you can use the product. They do not prove it works "
        "on "
        "the client's own data behind their own controls, which is the question that decides "
        "enterprise deals. Say so before they do.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Build the second one",
        "A different job, not a different ticker. This is the clause of the founder's standard "
        "that says workspaces, plural, and it is the one that separates an advisor who has used "
        "the product from one who has followed a tutorial once. Take the time to pick a job you "
        "will genuinely demo rather than the quickest one to build.",
        checkpoint="Build a second dashboard for a genuinely different job, including at least one "
        "static file, and keep a screenshot of both.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Write down what generalised",
        "In three sentences: what you reused, what you had to rethink, and which of the two you "
        "would open in front of a client tomorrow. This is the reflection that turns two builds "
        "into a method.",
        checkpoint="Write three sentences on what carried over from the first dashboard, what did "
        "not, and which one you would demo.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "What the next section does",
        "You can build. Next is the data itself: what OpenBB gives a client, what it does not, and "
        "the licensing questions that decide whether a deal is possible at all. It is the least "
        "glamorous section and the one that saves you the most wasted time.",
        refs=(DOCS_WORKSPACE,),
    ),
)

SECTION_5_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What makes a second dashboard worth building?",
            options=(
                "A different ticker",
                "A different job, which is what exposes the parts of the product you have not "
                "touched",
                "More widgets",
                "A different client",
            ),
            answer_index=1,
            explanation=(
                "If the second is the first with a new ticker you have learned nothing. The second "
                "build is where you find out what was the product and what was the ticker."
            ),
        ),
        TestQuestion(
            prompt="When should you NOT link parameters across widgets?",
            options=(
                "Never, always link them",
                "When the whole point of the view is several subjects side by side",
                "When using a table widget",
                "When the agent is enabled",
            ),
            answer_index=1,
            explanation=(
                "Knowing when linking is wrong is the difference between using the product and "
                "repeating a trick you were shown."
            ),
        ),
        TestQuestion(
            prompt="Why add a static file such as a PDF to a dashboard?",
            options=(
                "It loads faster than a feed",
                "It makes OpenBB's structured-plus-unstructured claim concrete, and every client "
                "has an important file living in email",
                "It is required for sharing",
                "It enables the agent",
            ),
            answer_index=1,
            explanation=(
                "The claim is abstract until a client sees their own committee pack next to a "
                "price series. That is what turns a nod into a question."
            ),
        ),
        TestQuestion(
            prompt="Should you build a dashboard live in a first meeting?",
            options=(
                "Yes, it proves you can",
                "No. Build in advance and change the ticker live; rebuild live only if asked how "
                "hard it is",
                "Only for wealth managers",
                "Only if the client asks",
            ),
            answer_index=1,
            explanation=(
                "You will be talking, answering questions, and something will not load. The demo "
                "should become about them in fifteen seconds, not in ten minutes."
            ),
        ),
        TestQuestion(
            prompt="How many dashboards should you have by the end of a quarter?",
            options=(
                "One per client",
                "One per job per segment; a client-specific one is a two-minute duplicate",
                "As many as possible",
                "Exactly two",
            ),
            answer_index=1,
            explanation=(
                "A client-specific dashboard is a duplicate with the ticker changed. That is cheap "
                "only if the job-level one is right."
            ),
        ),
        TestQuestion(
            prompt="What do two dashboards on public data NOT prove?",
            options=(
                "That you can use the product",
                "That it works on the client's own data behind their own controls",
                "That parameters link",
                "That the agent is grounded",
            ),
            answer_index=1,
            explanation=(
                "That question decides enterprise deals, and saying it before the client does "
                "makes you more credible rather than less."
            ),
        ),
    ),
)


def section_5() -> CourseModule:
    """Section 5: a second workspace, for a different job."""
    return CourseModule(
        id=_id("module", "second-workspace"),
        title="A second workspace, for a different job",
        order=4,
        lessons=(
            Lesson(
                id=_id("lesson", "second-workspace"),
                title="Your second dashboard, and what generalises",
                body=_S5_BODY,
                order=0,
                slides=_SECTION_5_SLIDES,
                drill_topics=("product:openbb:workspace",),
                measurement=(
                    "You have two dashboards for genuinely different jobs, one of them carrying a "
                    "static file, and you can say in three sentences what carried over."
                ),
            ),
        ),
        section_test=SECTION_5_TEST,
    )


# --- Section 6 — The data, and the licensing that decides whether a deal is possible ------

_S6_BODY = (
    "By the end of this lesson you can answer the two questions that kill OpenBB deals late: what "
    "data does a client actually get, and what are we allowed to build on the open-source code. "
    "This is the least glamorous section in the course and it saves you the most wasted time, "
    "because both questions are cheap to answer in month one and expensive to discover in month "
    "four."
)

_SECTION_6_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The sentence to memorise",
        "OpenBB is a way to work with data. It is not a way to get data you are not licensed for. "
        "Every difficult conversation in this section is a variation on somebody hoping the second "
        "half of that sentence is not true.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "What comes in the box",
        "OpenBB documents access to more than 350 datasets across roughly a dozen data vendors, "
        "surfaced through hundreds of widgets. Quote that as approximate and cite it. A precise "
        "number you cannot source is worse in a meeting than an honest range.",
        refs=(DOCS_PLATFORM_INSTALLER,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Free providers versus keyed providers",
        "Some providers need no API key, which is why `yfinance` was the right first call in "
        "section 2. Most useful ones need a key, and that key represents a contract the client "
        "already has or will need. OpenBB does not supply it.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The client's existing vendors are the opportunity",
        "A firm paying for a market data vendor already holds the entitlement. Bringing it into "
        "OpenBB is a consolidation conversation, not a procurement one, and consolidation "
        "conversations move far faster because no new contract is required.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        4,
        SlideKind.WALKTHROUGH,
        "Find out what they already pay for",
        "Before any technical conversation, ask which data vendors they hold. Write the list down. "
        "That list determines whether the first build is a two-week job or a two-quarter one, and "
        "asking early makes you look like someone who has done this before.",
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Their own data is a first-class source",
        "A widget's data source can be a feed, a database, the organisation's own custom data, "
        "or "
        "a static file. Their internal book, their positions, their research notes: all valid "
        "sources. This is usually where the real value sits, and it is not a data purchase at all.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The provenance problem, restated for a client",
        "OpenBB picks a provider alphabetically when you do not name one, and skips any whose key "
        "is missing. In a regulated firm that means a number can come from a different source "
        "between two runs. Raise it unprompted; it is the kind of honesty that wins technical "
        "buyers.",
        refs=(DOCS_QUICKSTART,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The metadata layer is your answer",
        "Every widget carries source attribution in its metadata. When a compliance officer asks "
        "where a number came from, the answer is in the product rather than in a spreadsheet "
        "somebody maintains. Point at this rather than describing it.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Two products, two licensing worlds",
        "This is the distinction that matters most in this section. The open-source Open Data "
        "Platform is licensed one way. OpenBB Workspace is a commercial product licensed another. "
        "Conflating them is how an advisor promises something the client cannot legally do.",
        refs=(LICENCE, DOCS_WORKSPACE),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "The Open Data Platform is AGPLv3",
        "The GitHub repository states the licence as AGPLv3. That is a strong copyleft licence, "
        "and "
        "its network clause is the part that surprises people: offering modified software over a "
        "network can trigger source disclosure obligations.",
        refs=(LICENCE, REPO),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Why AGPL matters to a bank or a broker",
        "A firm that forks the open-source platform, modifies it, and serves it to its own clients "
        "over a network may be obliged to publish those modifications. Most financial firms will "
        "not accept that. This is a real objection and it deserves a real answer.",
        refs=(LICENCE,),
        asset=_diagram(
            "agpl_decision",
            "Two questions decide the answer. Learn the shape of this, not a form of words.",
            "A decision tree headed: can the client build on the open-source platform? The first "
            "question is whether they are MODIFYING the platform. No leads to 'using it as "
            "published' — no AGPL obligation to publish anything. Yes leads to a second question: "
            "are they SERVING it to others over a network? No leads to 'internal use only' — "
            "modify freely, the network clause is not triggered. Yes leads to 'source disclosure "
            "bites' — this is what a commercial arrangement is for. Beneath, in warning colour: "
            "name the licence, say the commercial route exists, never advise on it yourself.",
        ),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The answer: commercial licensing exists",
        "OpenBB separates the open-source ODP from the commercial Workspace product precisely so "
        "an enterprise has a route that is not AGPL. When a client raises copyleft, the response "
        "is that this is what the commercial arrangement is for.",
        refs=(REPO, DOCS_WORKSPACE),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "Where white-labelling actually happens",
        "In Workspace, not by forking the open-source platform. Branding, custom apps, custom "
        "widgets and the firm's own data behind them are Workspace capabilities. An advisor who "
        "suggests forking the AGPL code to white-label has created a legal problem.",
        refs=(DOCS_APPS, DOCS_WIDGETS, LICENCE),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Read the licence line for yourself",
        "Open the repository and find the licence. Thirty seconds. You will be asked about it by "
        'someone technical, and "I have read it" is a materially different answer from "I '
        'believe it is open source".',
        refs=(LICENCE, REPO),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "Deployment is the other half of the question",
        '"Can our data leave our environment?" is a different question from licensing and is '
        "usually the one that decides an enterprise deal. OpenBB documents several routes in, "
        "including Enterprise and a platform installer, which is where that conversation goes.",
        refs=(
            DOCS_WORKSPACE,
            DOCS_PLATFORM_INSTALLER,
        ),
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "The local platform, and the port again",
        "A locally-running platform API on `http://localhost:6900` is how a firm keeps a data "
        "layer "
        "inside its own environment while using Workspace on top. Knowing that this shape exists "
        "is often enough to keep a conversation alive past the first objection.",
        refs=(DOCS_PLATFORM_INSTALLER,),
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The conversation that goes wrong",
        "An advisor says the platform is open source, the client's architect hears \"we can fork "
        'it and build our client portal on it", and four months later legal finds AGPL. The deal '
        "does not just stall, it costs you the relationship.",
        refs=(LICENCE,),
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "The same conversation, done properly",
        '"The data platform is AGPLv3, so if you are planning to modify it and serve it to your '
        "own clients, that needs a commercial arrangement rather than the open-source licence. "
        'Workspace is the supported route for that. Shall I get you the specifics?"',
        refs=(LICENCE, DOCS_WORKSPACE),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What you must never do",
        "Never advise on licensing. State the licence, state that a commercial route exists, and "
        "route the specifics to OpenBB and to the client's own counsel. You are a distributor, "
        "not their lawyer, and the difference protects both of you.",
        refs=(LICENCE,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "Export as a lock-in answer",
        "Widgets export to CSV, JSON and Excel. Lock-in is a quiet objection almost nobody voices "
        "directly, and demonstrating an export answers it in five seconds without anyone having to "
        "admit they were worried.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        20,
        SlideKind.EXAMPLE,
        "A qualification question that saves a quarter",
        '"If this works, would you be putting it in front of your own clients, or is it internal '
        'to the desk?" The answer tells you immediately whether you are in a Workspace '
        "conversation or a licensing one, and it costs you nothing to ask in the first meeting.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Write the licensing answer in your own words",
        "Two or three sentences you could say out loud to a client's architect without notes. Get "
        "it right now, calmly, rather than improvising it under pressure in a room where somebody "
        "technical is listening carefully.",
        checkpoint='Write your two-to-three sentence answer to "is this open source, and can we '
        'build on it?" and keep it with your sixty-second explanation from section 1.',
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "List one target's data vendors",
        "Take one of your three named targets and find out, or make your best documented guess at, "
        "which market data vendors they hold. Note how you found out. This is the research that "
        "makes a first meeting land.",
        checkpoint="Write down the data vendors you believe one named target holds, and how you "
        "established it.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "What the next section does",
        "You now know what the product does and what it is allowed to do. Next is who actually "
        "buys "
        "it: which segment, which person in the room, and what has to have happened for them to be "
        "looking at all.",
    ),
)

SECTION_6_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What licence is the open-source Open Data Platform under?",
            options=("MIT", "Apache 2.0", "AGPLv3", "Proprietary"),
            answer_index=2,
            explanation=(
                "The GitHub repository states AGPLv3. Its network clause is the part that "
                "surprises people, and it is a real objection for any firm serving clients."
            ),
        ),
        TestQuestion(
            prompt=(
                "A client wants to fork the open-source platform and serve it to their own "
                "clients. What do you say?"
            ),
            options=(
                "Go ahead, it is open source",
                "That may trigger AGPL source-disclosure obligations; a commercial arrangement "
                "is the supported route, and I will get you the specifics",
                "It is not technically possible",
                "You need to ask your own lawyer, I cannot comment",
            ),
            answer_index=1,
            explanation=(
                "State the licence, state that a commercial route exists, and route the specifics "
                "to OpenBB and their counsel. Never advise on licensing yourself."
            ),
        ),
        TestQuestion(
            prompt="Where does white-labelling actually happen?",
            options=(
                "By forking the open-source platform",
                "In Workspace, through branding, custom apps and custom widgets",
                "It is not supported",
                "Through the App Marketplace only",
            ),
            answer_index=1,
            explanation=(
                "An advisor who suggests forking the AGPL code to white-label has created a legal "
                "problem rather than closed a deal."
            ),
        ),
        TestQuestion(
            prompt="Does OpenBB give a client data they are not licensed for?",
            options=(
                "Yes, that is the point",
                "No. It is a way to work with data, not a way to get data you are not licensed for",
                "Only public data",
                "Only in Enterprise",
            ),
            answer_index=1,
            explanation=(
                "Every difficult conversation in this area is somebody hoping that is not true. "
                "Saying it early stops a deal dying on an expectation you set."
            ),
        ),
        TestQuestion(
            prompt="Why is a client's existing vendor list the first thing to ask about?",
            options=(
                "To estimate their budget",
                "It turns the deal into a consolidation conversation rather than a procurement "
                "one, which moves far faster",
                "To check they can afford it",
                "It is required for the install",
            ),
            answer_index=1,
            explanation=(
                "Existing entitlements need no new contract. That list decides whether the first "
                "build is a two-week job or a two-quarter one."
            ),
        ),
        TestQuestion(
            prompt="How do you answer an unspoken lock-in worry?",
            options=(
                "Explain the contract terms",
                "Demonstrate an export to CSV or Excel, which answers it without anyone "
                "admitting they were worried",
                "Offer a discount",
                "Point at the open-source licence",
            ),
            answer_index=1,
            explanation=(
                "Lock-in is a quiet objection almost nobody voices. Showing the export takes five "
                "seconds and removes it."
            ),
        ),
    ),
)


def section_6() -> CourseModule:
    """Section 6: the data, and the licensing that decides whether a deal is possible."""
    return CourseModule(
        id=_id("module", "the-data"),
        title="The data, and the licensing that decides whether a deal is possible",
        order=5,
        lessons=(
            Lesson(
                id=_id("lesson", "the-data"),
                title="What the client gets, and what we are allowed to build",
                body=_S6_BODY,
                order=0,
                slides=_SECTION_6_SLIDES,
                drill_topics=("product:openbb:licensing",),
                measurement=(
                    'You can answer "is this open source, and can we build on it?" in two or '
                    "three sentences without notes, and you know one target's data vendors."
                ),
            ),
        ),
        section_test=SECTION_6_TEST,
    )


# --- Section 7 — Who buys it, in which segment, and what triggers the purchase ------------

_S7_BODY = (
    "By the end of this lesson you can look at a firm in our registry and say, with reasons, "
    "whether OpenBB is a real conversation there, who in the building would care, and what has to "
    "have happened for them to be looking at all. Qualification is the highest-leverage skill in "
    "this course, because the cost of a bad opportunity is not the meeting, it is the quarter."
)

_SECTION_7_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Sell to the trigger, not to the product",
        "Nobody buys a workspace. They buy the end of a specific irritation. Your job in "
        "qualification is to find the irritation and check it is expensive enough that somebody is "
        "already complaining about it upward.",
        asset=_diagram(
            "segment_triggers",
            "Five segments, five different irritations, five different people who feel it.",
            "A table of the five segments we assess, what opens each, and who feels it. Retail "
            "brokerage: research cost, felt by the head of research. Wealth manager: consistency "
            "and supervision, felt by someone compliance-adjacent. Exchange: product insight on "
            "their own feeds, felt by the data product manager. Bank: consolidation and AI "
            "governance, felt by the architect. Information vendor: distribution rather than "
            "consumption, felt by the commercial lead.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The five segments we assess",
        "Retail brokerage, wealth manager, exchange, bank, information vendor. OpenBB has a "
        "plausible story in all five, which is exactly why you must not treat them as one market. "
        "The trigger is different in each, and so is the person who feels it.",
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Retail brokerage: the trigger is research cost",
        "A research desk assembling the same view every morning from four vendors is paying "
        "analyst salary for clerical work. The person who feels it is the head of research. The "
        "person who funds it is whoever owns the research budget, and they are often not the same.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Wealth manager: the trigger is consistency",
        "Fifty advisers giving fifty slightly different house views is a supervision problem "
        "before "
        "it is a data problem. The buyer is often compliance-adjacent, and the winning "
        "demonstration is a shared dashboard rather than a clever widget.",
        refs=(DOCS_DASHBOARDS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Exchange: the trigger is product insight",
        "An exchange's data product managers need to see how their own feeds are used and how "
        "they "
        "compare. Their own data plus public reference data is a narrow, fast build, and it opens "
        "a second conversation about publishing an app themselves.",
        refs=(BLOG_MARKETPLACE,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Bank: the trigger is consolidation and governance",
        "Banks have every vendor and no single view, plus an AI governance problem they are "
        "already "
        "being asked about internally. Grounded answers over their own data is the phrase that "
        "gets you a second meeting here.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Information vendor: the trigger is distribution",
        "A data business does not need another way to look at data. It needs its data in front of "
        "more people, which makes the App Marketplace the conversation rather than Workspace "
        "seats. This is a genuinely different sale and worth recognising early.",
        refs=(BLOG_MARKETPLACE,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The four people you will meet",
        "The analyst who feels the pain. The engineer who will judge whether it is real. The "
        "budget "
        "holder who does not care about either. And the compliance or risk voice who can stop it. "
        "You need all four, and you will usually be introduced to one.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The analyst",
        "They want their morning back. Show them the linked parameter and the agent question. They "
        "will not sign anything, but without them nothing happens, and they are the cheapest "
        "person in the building to get excited.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "The engineer",
        "They will ask about deployment, data residency, the licence and whether it can reach "
        "internal systems. Sections 2 and 6 exist for this person. Being straight with them about "
        "AGPL is worth more than any feature you could name.",
        refs=(LICENCE, DOCS_PLATFORM_INSTALLER),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "The budget holder",
        "They want a number and a comparison to what they already spend. Seat reduction only where "
        "the client has told you a seat does something OpenBB genuinely does. Never invent the "
        "saving; an unfounded number is remembered longer than a good demo.",
        refs=(SITE_WORKSPACE,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The compliance voice",
        "They want to know where a number came from and what an AI agent is allowed to see. Source "
        "attribution in the widget metadata and grounding in the firm's own data are your two "
        "answers, and both are demonstrable rather than assertable.",
        refs=(DOCS_WIDGETS, DOCS_WORKSPACE),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Score your three targets",
        "For each of the three firms you named in section 1, write the trigger you believe is "
        "real, "
        "the person who feels it, and one piece of evidence. If you cannot name evidence, you have "
        "a guess rather than an opportunity, and it is better to know that now.",
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Where the assessment does this work for you",
        "A Platform Power assessment surfaces a weak research or data module, or a customer "
        "proposition gap, and the client has already agreed with the finding. Starting from that "
        "is a completely different conversation from arriving with a product.",
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "Opening from an assessment finding",
        '"Your infrastructure review flagged research tooling as the weakest module, and you '
        "agreed. The specific thing behind that score was your analysts rebuilding the same view "
        'each morning. I want to show you what that looks like solved."',
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "Opening cold, without an assessment",
        '"You have data from three vendors and your own book. Who assembles the morning view, and '
        'how long does it take them?" A question, not a pitch. The answer tells you whether to '
        "continue and gives you the number you will quote back later.",
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "Disqualify early and say so",
        "A firm with one vendor, no internal data and no AI pressure is not an OpenBB opportunity. "
        "Saying so costs you a meeting and buys you a reputation. Advisors who never disqualify "
        "end the quarter busy and empty.",
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "Three signals it is real",
        "Somebody has already complained upward about the problem. There is a named person whose "
        "job would change. And there is a date something has to be ready by. Two of three is "
        "workable; one of three is a conversation, not a deal.",
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "Three signals it is not",
        "Everyone is enthusiastic and nobody owns it. The problem is described in the abstract "
        'rather than with a number. And the only pressure is that a competitor has "something '
        'with AI". That last one is the most seductive and the least real.',
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "Using the registry properly",
        "Our GTM registry holds targets and named contacts by segment. Use it to find the analyst "
        "or the data lead rather than starting at the top, because the person who feels the pain "
        "will introduce you far more effectively than a cold approach to the budget holder.",
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Qualify your three, honestly",
        "Score each of your three targets against the three signals. You are looking for one to be "
        "genuinely strong rather than three to be plausible, and being honest with yourself here "
        "is worth more than any technique later in this course.",
        checkpoint="Score your three targets against the three signals, and write which one you "
        "would actually spend a quarter on and why.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Name the four people at your best target",
        "Analyst, engineer, budget holder, compliance voice. Names where you can get them, roles "
        "where you cannot. The gaps in that list are your next fortnight of work.",
        checkpoint="Write the four roles at your strongest target, with names where you have them "
        "and a plan for the ones you do not.",
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "What the next section does",
        "You know who buys and why. The last section is the sell itself: the first meeting, the "
        "objections you will actually hear, the pricing conversation, and what a good outcome "
        "looks "
        "like at each stage.",
    ),
)

SECTION_7_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What is the trigger in a wealth manager?",
            options=(
                "Research cost",
                "Consistency and supervision: fifty advisers giving fifty slightly different "
                "house views",
                "Product insight",
                "Distribution",
            ),
            answer_index=1,
            explanation=(
                "It is a supervision problem before it is a data problem, and the winning demo "
                "is a "
                "shared dashboard rather than a clever widget."
            ),
        ),
        TestQuestion(
            prompt="An information vendor is interested. What are you probably selling?",
            options=(
                "Workspace seats",
                "Distribution, through the App Marketplace — a genuinely different sale",
                "The open-source platform",
                "A consolidation project",
            ),
            answer_index=1,
            explanation=(
                "A data business does not need another way to look at data. It needs its data in "
                "front of more people. Recognising this early saves a wasted quarter."
            ),
        ),
        TestQuestion(
            prompt="Which four people do you need?",
            options=(
                "CEO, CTO, CFO, COO",
                "The analyst who feels the pain, the engineer who judges it, the budget holder, "
                "and the compliance voice",
                "Whoever answers the phone",
                "The head of research only",
            ),
            answer_index=1,
            explanation=(
                "You need all four and will usually be introduced to one. The compliance voice can "
                "stop it, and the analyst is the cheapest person to get excited."
            ),
        ),
        TestQuestion(
            prompt="Which is the LEAST real buying signal?",
            options=(
                "Somebody has complained upward about the problem",
                "A competitor has 'something with AI'",
                "There is a named person whose job would change",
                "There is a date something must be ready by",
            ),
            answer_index=1,
            explanation=(
                "It is the most seductive signal and the least real. Enthusiasm without ownership "
                "ends a quarter busy and empty."
            ),
        ),
        TestQuestion(
            prompt="Where should seat-reduction savings come from?",
            options=(
                "A standard percentage",
                "Only where the client has told you a seat does something OpenBB genuinely does",
                "The published price list",
                "Whatever makes the business case work",
            ),
            answer_index=1,
            explanation=(
                "An invented number is remembered far longer than a good demo. Never invent the "
                "saving."
            ),
        ),
        TestQuestion(
            prompt="Why is opening from an assessment finding stronger than opening cold?",
            options=(
                "It is faster",
                "The client has already agreed with the finding, so you are not arguing about "
                "whether the problem exists",
                "It avoids the engineer",
                "It sets the price",
            ),
            answer_index=1,
            explanation=(
                "Starting from something they agreed with is a completely different conversation "
                "from arriving with a product."
            ),
        ),
    ),
)


def section_7() -> CourseModule:
    """Section 7: who buys it, in which segment, and what triggers the purchase."""
    return CourseModule(
        id=_id("module", "who-buys-and-why"),
        title="Who buys it, and what has to have happened first",
        order=6,
        lessons=(
            Lesson(
                id=_id("lesson", "who-buys-and-why"),
                title="Qualification: the segment, the person, and the trigger",
                body=_S7_BODY,
                order=0,
                slides=_SECTION_7_SLIDES,
                drill_topics=("product:openbb:qualification",),
                measurement=(
                    "You can score a target against the three buying signals and name the four "
                    "people you need, with evidence rather than a guess."
                ),
            ),
        ),
        section_test=SECTION_7_TEST,
    )


# --- Section 8 — How and when to sell it --------------------------------------------------

_S8_BODY = (
    "By the end of this lesson you can run the whole sale: the first meeting, the demo, the "
    "objections you will actually hear, the pricing conversation, and what a good outcome looks "
    "like at each stage. This is the clause of the founder's standard that says an advisor should "
    "know exactly how and when to sell it, and it is the section the rest of the course exists to "
    "make possible."
)

_SECTION_8_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "When to sell it, in one line",
        "When a firm has data in more than one place, somebody expensive assembling it by hand, "
        "and "
        "a reason this year to care about AI governance. Two of those three is a conversation. All "
        "three is a deal.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "When not to sell it",
        "One vendor, no internal data, no AI pressure. Or a firm whose actual problem is an order "
        "management system, a risk engine or a book of record. Recommending OpenBB into either is "
        "how an advisor loses the right to recommend anything.",
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The shape of the sale",
        "First meeting to find the irritation. Demo on something recognisably theirs. Technical "
        "conversation about deployment and licence. Scoped pilot on their own data. Then pricing. "
        "Skipping straight to pricing is the most common way this stalls.",
        asset=_diagram(
            "the_sale",
            "Five stages, and the one thing that tells you a stage actually closed.",
            "Five stages left to right, with the good outcome under each. First meeting: a number "
            "and a name. Demo: a question you could not answer. Technical: an introduction to the "
            "engineer. Pilot, highlighted as the real close: a date. Price: a scoped quote from "
            "OpenBB. Beneath: anything vaguer at any stage means you are one stage behind where "
            "you think.",
        ),
    ),
    _s(
        3,
        SlideKind.WALKTHROUGH,
        "The first meeting: ask, do not present",
        "Open with the question from section 7: who assembles the morning view, and how long does "
        "it take. Then be quiet. The number they give you is the number you will quote back for "
        "the rest of the deal, and you only get it by not talking.",
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "What to listen for",
        "A named person. A time cost. A recent incident. Any of the three gives you something "
        "concrete to build the demo around. Vague enthusiasm gives you nothing, however pleasant "
        "the meeting felt afterwards.",
    ),
    _s(
        5,
        SlideKind.WALKTHROUGH,
        "The demo: change one field",
        "Open the dashboard you built for their job. Change the ticker to their firm. Let the "
        "linked "
        "widgets move. That is the demo. Everything after it is answering questions rather than "
        "presenting.",
        refs=(DOCS_WIDGETS, DOCS_DASHBOARDS),
    ),
    _s(
        6,
        SlideKind.WALKTHROUGH,
        "Then ask the agent one question",
        "One question that needs two of the widgets at once. Not a summary, not a price. Something "
        "an analyst in that room would actually want to know, ideally something they mentioned in "
        "the first meeting.",
        refs=(DOCS_WORKSPACE,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Then stop",
        "Do not tour the widget library. Do not open settings. A prospect remembers one thing from "
        "a demo, and you want it to be that one field moving the whole view. Silence after it is a "
        "technique, not an accident.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Objection: we already have Bloomberg",
        'Do not compete. "It does not replace it. It is a place to work with data you already pay '
        "for, including your own, with an AI layer that answers from that rather than from the "
        'internet." Declining the comparison makes you more credible.',
        refs=(SITE_WORKSPACE, DOCS_WORKSPACE),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Objection: our data cannot leave our environment",
        "This is a real question and often the one that decides the deal. OpenBB documents several "
        "deployment routes including Enterprise and a local platform installer, so the honest "
        "answer is that this is a solved shape and you will get them the specifics.",
        refs=(DOCS_PLATFORM_INSTALLER, DOCS_WORKSPACE),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Objection: is this open source, can we just build it ourselves",
        "The Open Data Platform is AGPLv3. If they intend to modify it and serve it to their own "
        "clients, that needs a commercial arrangement. Say the licence name, say the route exists, "
        "and route the specifics onward. Never advise.",
        refs=(LICENCE,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "Objection: what happens to our data with the AI",
        "The agent reads widget metadata to query the right datasets, so it answers from what is "
        "on "
        "the dashboard. Say grounded, demonstrate source attribution in the metadata, and offer "
        "the "
        "compliance voice a session of their own.",
        refs=(DOCS_WORKSPACE, DOCS_WIDGETS),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "Objection: we would be locked in",
        "Rarely said out loud. Export a widget to Excel in front of them without making a speech "
        "about it. Five seconds, objection gone, and nobody had to admit they were worried.",
        refs=(DOCS_WIDGETS,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Objection: nobody here will use it",
        "The most honest objection on the list and the one most worth taking seriously. Answer it "
        "with the shared dashboard and Export apps.json: adoption is a standardisation question, "
        "not an enthusiasm question.",
        refs=(DOCS_DASHBOARDS, DOCS_APPS),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "The pilot is the real close",
        "A scoped pilot on their own data, with one named analyst and a date, is worth more than "
        "any proposal. It converts an argument about whether it would work into an observation of "
        "whether it did.",
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Scope the pilot narrowly",
        "One workflow, one team, one dataset of theirs, one date. Resist every attempt to widen "
        "it. "
        "A pilot that tries to prove everything proves nothing and takes a quarter to fail.",
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "Pricing: what you can and cannot say",
        "Pricing is a scoped quote from OpenBB, not a number you carry. What you can do is frame "
        "the comparison: what they spend now on the assembling, the seats and the duplication. "
        "Never quote a figure you have not been given.",
        refs=(SITE_WORKSPACE,),
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "Where your commission comes from",
        "The Academy commission lesson resolves the live rate from the current schedule rather "
        "than "
        "being written here, so it is right rather than remembered. Read it before a pricing "
        "conversation, not after.",
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "A good outcome at each stage",
        "First meeting: a number and a name. Demo: a question you could not answer. Technical: an "
        "introduction to the engineer. Pilot: a date. Anything vaguer than that at any stage means "
        "you are one stage behind where you think you are.",
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "The deal that dies quietly",
        "Everyone enjoyed the demo, nobody owns the problem, and the follow-up email goes "
        "unanswered for three weeks. It died at the first meeting, when you presented instead of "
        "asking. Recognising that early is worth more than a rescue attempt.",
    ),
    _s(
        20,
        SlideKind.EXAMPLE,
        "Where the assessment does the selling",
        "A Platform Power engagement that flagged research tooling has already established the "
        "problem and got the client to agree with it. Your job is then to show the solved version, "
        "which is a far shorter distance to travel.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say the sixty seconds again",
        "Record your sixty-second explanation of OpenBB, as you did in section 1, and compare the "
        "two. The difference between them is what this course was for, and it is worth seeing "
        "rather than assuming.",
        checkpoint="Record your sixty-second explanation again and compare it with the version you "
        "kept from section 1. Note what changed.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Write the first meeting for your best target",
        "Your opening question, the demo you will show, the two objections you expect from that "
        "specific firm, and the outcome you want. One page. This is the artefact you take into the "
        "room next week.",
        checkpoint="Write a one-page first-meeting plan for your strongest target: opening "
        "question, demo, expected objections, and the outcome you want.",
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Book it",
        "The course ends here and the work does not. You have the product installed, two "
        "dashboards, a qualified target and a meeting plan. The only remaining step is the one "
        "nobody can do for you.",
        checkpoint="Book, or write the outreach for, a first meeting with your strongest target.",
    ),
    _s(
        24,
        SlideKind.CONCEPT,
        "What you should be able to do now",
        "Explain OpenBB in sixty seconds. Install it and pull data. Build two dashboards for "
        "different jobs. Answer the licensing question without notes. Qualify a target against "
        "three signals. Run a first meeting and a demo. That was the whole standard.",
    ),
)

SECTION_8_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="When is OpenBB a real opportunity?",
            options=(
                "Whenever a firm has data",
                "Data in more than one place, somebody expensive assembling it by hand, and a "
                "reason this year to care about AI governance",
                "When they are unhappy with Bloomberg",
                "When they have budget",
            ),
            answer_index=1,
            explanation=(
                "Two of those three is a conversation. All three is a deal. Anything less is a "
                "meeting you will enjoy and a quarter you will lose."
            ),
        ),
        TestQuestion(
            prompt="What is the demo?",
            options=(
                "A tour of the widget library",
                "Open the dashboard for their job, change the ticker to their firm, and let the "
                "linked widgets move",
                "The App Marketplace",
                "Building a dashboard live",
            ),
            answer_index=1,
            explanation=(
                "A prospect remembers one thing. Make it the field that moves the whole view, then "
                "stop talking."
            ),
        ),
        TestQuestion(
            prompt=(
                "A prospect asks whether they could just build it themselves on the "
                "open-source code."
            ),
            options=(
                "Yes, it is open source",
                "The platform is AGPLv3; modifying it and serving it to their own clients needs "
                "a commercial arrangement, and I will get the specifics",
                "No, that is not allowed",
                "Only with Enterprise",
            ),
            answer_index=1,
            explanation=(
                "Name the licence, say the route exists, route the specifics onward. You are a "
                "distributor, not their lawyer."
            ),
        ),
        TestQuestion(
            prompt="What actually closes the deal?",
            options=(
                "A proposal",
                "A scoped pilot on their own data, with one named analyst and a date",
                "The pricing conversation",
                "A second demo",
            ),
            answer_index=1,
            explanation=(
                "It converts an argument about whether it would work into an observation of "
                "whether it did. Scope it narrowly or it proves nothing."
            ),
        ),
        TestQuestion(
            prompt="What is a good outcome from a first meeting?",
            options=(
                "They liked it",
                "A number and a name",
                "A follow-up scheduled",
                "A request for pricing",
            ),
            answer_index=1,
            explanation=(
                "Anything vaguer means you are a stage behind where you think you are. The number "
                "is what you quote back for the rest of the deal."
            ),
        ),
        TestQuestion(
            prompt="Can you quote a price?",
            options=(
                "Yes, from the price list",
                "No. Pricing is a scoped quote from OpenBB; you frame the comparison against "
                "what they spend now",
                "Only for Enterprise",
                "Only after the pilot",
            ),
            answer_index=1,
            explanation=(
                "Never quote a figure you have not been given. An invented number outlives a good "
                "demo in a client's memory."
            ),
        ),
    ),
)


def section_8() -> CourseModule:
    """Section 8: how and when to sell it."""
    return CourseModule(
        id=_id("module", "how-and-when-to-sell"),
        title="How and when to sell it",
        order=7,
        lessons=(
            Lesson(
                id=_id("lesson", "how-and-when-to-sell"),
                title="The first meeting, the demo, the objections, and the close",
                body=_S8_BODY,
                order=0,
                slides=_SECTION_8_SLIDES,
                drill_topics=("product:openbb:sell-motion",),
                measurement=(
                    "You have a one-page first-meeting plan for a qualified target, and you have "
                    "booked or written the outreach for that meeting."
                ),
            ),
        ),
        section_test=SECTION_8_TEST,
    )


def rebuilt_sections() -> tuple[CourseModule, ...]:
    """The sections rebuilt to the GRS-0215 standard, in order. Grows as GRS-0216 progresses."""
    return (
        section_1(),
        section_2(),
        section_3(),
        section_4(),
        section_5(),
        section_6(),
        section_7(),
        section_8(),
    )


# Sections written so far, and sections still to write. The depth check fails while anything is in
# SECTIONS_PLANNED, so this course cannot read as finished until it is.
SECTIONS_AUTHORED: tuple[str, ...] = (
    "what-it-is",
    "install",
    "sign-up-and-orientation",
    "first-workspace",
    "second-workspace",
    "the-data",
    "who-buys-and-why",
    "how-and-when-to-sell",
)
# All eight are written. The tuple stays, empty, because the test that guards it reads it
# and because the next course to be rebuilt will start from this file as its pattern.
SECTIONS_PLANNED: tuple[str, ...] = ()
