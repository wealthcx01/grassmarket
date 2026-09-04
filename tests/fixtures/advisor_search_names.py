"""Firm names an advisor would plausibly type into New Assessment search (GRS-0210 scope 1).

Committed so the coverage bar is **visible and raisable**, not a number somebody remembers. Each
name is one an advisor at this firm would actually type — not a string chosen because it happens to
match. Grouped by segment, because a search that finds every bank and no wealth manager is not 80%
good; it is unusable for half the pipeline, and an aggregate figure would hide that.

Sources: `data/gtm/sources/list-of-banks.xlsx`, `exchange-supplier-list.xlsx`, the LSEG contributor
institution map, and the retail brokers and wealth managers named in the PRD.
"""

from __future__ import annotations

#: Global and UK banks. Drawn from the imported bank list plus the obvious majors.
BANKS: tuple[str, ...] = (
    "HSBC",
    "Barclays",
    "Lloyds",
    "NatWest",
    "Santander",
    "JPMorgan",
    "Goldman Sachs",
    "Morgan Stanley",
    "Citibank",
    "UBS",
    "BNP Paribas",
    "Deutsche Bank",
    "Standard Chartered",
    "Credit Agricole",
    "Societe Generale",
    "Nomura",
    "Mizuho",
    "RBC",
    "Scotiabank",
    "ING",
    "Rabobank",
    "Commerzbank",
    "Danske Bank",
    "Nordea",
    "Bank of America",
    "Wells Fargo",
    "BBVA",
    "UniCredit",
    "Intesa Sanpaolo",
    "Julius Baer",
    "Bank of China",
    "Mitsubishi UFJ",
    "Handelsbanken",
    "KBC",
    "Erste Group",
)

#: Exchanges and market infrastructure.
EXCHANGES: tuple[str, ...] = (
    "London Stock Exchange",
    "LSEG",
    "Deutsche Boerse",
    "Euronext",
    "NASDAQ",
    "NYSE",
    "CME Group",
    "ICE",
    "Cboe",
    "SIX Swiss Exchange",
    "Japan Exchange Group",
    "Hong Kong Exchanges",
    "Singapore Exchange",
    "B3",
    "TMX Group",
    "Borsa Italiana",
    "Bolsa de Madrid",
    "Warsaw Stock Exchange",
    "Nasdaq Nordic",
    "MIAX",
)

#: Retail brokers and trading platforms — where a UK advisor's pipeline actually lives.
BROKERS: tuple[str, ...] = (
    "Hargreaves Lansdown",
    "AJ Bell",
    "interactive investor",
    "IG Group",
    "CMC Markets",
    "Plus500",
    "Saxo Bank",
    "Interactive Brokers",
    "Charles Schwab",
    "Robinhood",
    "eToro",
    "Freetrade",
    "Trading 212",
    "DEGIRO",
    "Fidelity",
    "Vanguard",
    "Webull",
    "Tastytrade",
    "Swissquote",
    "Flatex",
    "Lightyear",
    "Wealthify",
    "Nutmeg",
)

#: Traditional wealth and asset managers.
WEALTH_MANAGERS: tuple[str, ...] = (
    "St. James's Place",
    "Schroders",
    "Rathbones",
    "Quilter",
    "abrdn",
    "Brewin Dolphin",
    "Evelyn Partners",
    "Brooks Macdonald",
    "Investec Wealth",
    "Canaccord Genuity",
    "Tilney",
    "Close Brothers",
    "M&G",
    "Jupiter Asset Management",
    "Liontrust",
    "Man Group",
    "Ninety One",
    "Baillie Gifford",
    "Legal & General",
    "Aviva Investors",
    "BlackRock",
    "Amundi",
    "Allianz Global Investors",
    "Pictet",
    "Lombard Odier",
)

#: Information vendors and data suppliers — the exchange-supplier corpus.
VENDORS: tuple[str, ...] = (
    "Bloomberg",
    "Refinitiv",
    "FactSet",
    "Morningstar",
    "S&P Global",
    "Moody's",
    "MSCI",
    "Six Financial Information",
    "Quandl",
    "Benzinga",
    "Edgar Online",
    "Interactive Data",
    "Markit",
    "Tradeweb",
    "MarketAxess",
    "OpenBB",
    "Brandfetch",
)

#: How people actually type: short forms and legal-suffix noise (GRS-0210 scope 3).
SHORT_FORMS: dict[str, str] = {
    "HL": "Hargreaves Lansdown",
    "SJP": "St. James's Place",
    "LSEG": "London Stock Exchange",
    "IBKR": "Interactive Brokers",
    "GS": "Goldman Sachs",
    "JPM": "JPMorgan",
    "Barclays plc": "Barclays",
    "HSBC Holdings": "HSBC",
    "Schroders plc": "Schroders",
    "Man Group plc": "Man Group",
}

BY_SEGMENT: dict[str, tuple[str, ...]] = {
    "banks": BANKS,
    "exchanges": EXCHANGES,
    "brokers": BROKERS,
    "wealth managers": WEALTH_MANAGERS,
    "vendors": VENDORS,
}

#: Every plain name, deduplicated, order preserved.
ALL_NAMES: tuple[str, ...] = tuple(
    dict.fromkeys(name for names in BY_SEGMENT.values() for name in names)
)


#: **Held out on purpose.** None of these is in `data/gtm/sources/advisor-market.csv`.
#:
#: The curated list was written to cover `ALL_NAMES`, so a 100% score against `ALL_NAMES` partly
#: marks its own homework: it proves the names somebody thought of are covered, not that the 121st
#: name an advisor types will be. These are plausible firms deliberately left out, so the gap
#: between the two numbers is visible instead of assumed.
HELD_OUT: tuple[str, ...] = (
    "Cazenove",
    "Killik & Co",
    "Charles Stanley",
    "Redmayne Bentley",
    "Walker Crips",
    "7IM",
    "Ruffer",
    "Sarasin & Partners",
    "Waverton",
    "Tribe Impact Capital",
    "Shore Capital",
    "Peel Hunt",
    "Numis",
    "Panmure Gordon",
    "Winterflood",
)
