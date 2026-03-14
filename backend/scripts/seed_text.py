"""Seed text documents: synthetic analyst reports and earnings summaries."""

import argparse
import asyncio

import httpx

DOCUMENTS = [
    {
        "title": "AAPL Q4 2025 Earnings Summary",
        "ticker": "AAPL",
        "source_type": "news",
        "published_at": "2025-10-30",
        "text": (
            "Apple Inc. reported fourth-quarter revenue of $94.9 billion, up 6% year over year, "
            "driven by record Services revenue of $25.0 billion and stronger-than-expected iPhone "
            "sales in Greater China. Gross margin expanded to 46.2%, reflecting favorable product "
            "mix and component cost tailwinds. Management guided Q1 FY2026 revenue between $124B "
            "and $128B, above consensus of $122B. The company announced a $110 billion share "
            "repurchase program and raised its quarterly dividend by 4% to $0.26 per share. "
            "CEO Tim Cook highlighted Apple Intelligence adoption, noting that Siri interactions "
            "increased 35% in markets where the feature launched. Services segment growth was "
            "fueled by advertising, App Store, and iCloud, offsetting moderate declines in "
            "Wearables. iPhone 16 Pro models saw above-plan demand, with titanium supply "
            "constraints easing by late September. Operating cash flow reached $27 billion for "
            "the quarter, bringing the trailing twelve-month figure to $118 billion. Capital "
            "expenditures were $3.2 billion, primarily for data center expansion to support "
            "on-device AI processing. Net income rose 12% to $24.7 billion, or $1.64 per diluted "
            "share, beating the Street estimate of $1.58. Apple's installed base crossed 2.3 "
            "billion active devices globally, a new record."
        ),
    },
    {
        "title": "NVDA FY2026 Q3 Earnings Analysis",
        "ticker": "NVDA",
        "source_type": "news",
        "published_at": "2025-11-20",
        "text": (
            "NVIDIA Corporation delivered another blowout quarter with revenue of $45.1 billion, "
            "up 94% year over year, as hyperscaler demand for Blackwell B200 and GB200 NVL72 "
            "systems continued to outpace supply. Data Center revenue accounted for $39.2 billion, "
            "with cloud service providers representing roughly 50% of data center sales. "
            "Management indicated that Blackwell production is ramping on schedule with TSMC's "
            "CoWoS-L packaging, and that demand visibility extends through FY2027. Gross margin "
            "was 73.5%, down from 75.1% in the prior quarter due to Blackwell ramp costs, but "
            "guided to recover above 75% as yields improve. Gaming revenue grew 15% to $3.8 "
            "billion, aided by the GeForce RTX 5090 launch. Jensen Huang reiterated NVIDIA's "
            "vision of sovereign AI infrastructure, noting new government partnerships in Saudi "
            "Arabia, India, and Japan. Networking revenue (InfiniBand + Spectrum-X) reached "
            "$4.1 billion, with Ethernet-based Spectrum-X growing 300% sequentially as customers "
            "deploy it alongside InfiniBand in large-scale clusters. Free cash flow was $21.8 "
            "billion. The company authorized an additional $50 billion in share buybacks."
        ),
    },
    {
        "title": "MSFT Azure Growth and AI Monetization",
        "ticker": "MSFT",
        "source_type": "news",
        "published_at": "2025-10-24",
        "text": (
            "Microsoft reported fiscal Q1 2026 revenue of $68.7 billion, up 16% year over year, "
            "with Intelligent Cloud segment revenue of $26.4 billion growing 22%. Azure and other "
            "cloud services revenue increased 34%, with AI services contributing 13 percentage "
            "points of that growth — up from 12 points last quarter. CEO Satya Nadella noted that "
            "Azure OpenAI Service now has over 70,000 customers, and GitHub Copilot subscribers "
            "surpassed 4 million. Microsoft 365 Copilot enterprise seats doubled sequentially. "
            "The Activision Blizzard acquisition contributed $2.8 billion in gaming revenue and "
            "is on track to be EPS accretive by Q3. Operating margin expanded 200 basis points "
            "to 45.8%, despite elevated capex of $14.9 billion for AI infrastructure. Management "
            "guided Q2 revenue of $70.5-71.5 billion and maintained full-year capex guidance of "
            "$58-62 billion, signaling sustained investment in AI training and inference capacity. "
            "LinkedIn revenue grew 9% with AI-powered features driving engagement. Dynamics 365 "
            "revenue grew 19%, with Copilot features in CRM and ERP increasing average deal size."
        ),
    },
    {
        "title": "TSLA Robotaxi Unveil and Q3 Delivery Miss",
        "ticker": "TSLA",
        "source_type": "news",
        "published_at": "2025-10-02",
        "text": (
            "Tesla delivered 435,000 vehicles in Q3 2025, missing consensus of 460,000, as the "
            "company prioritized Cybercab production line buildout at Giga Texas over Model Y "
            "output. Revenue was $25.2 billion, up 8% year over year but below the $26.1 billion "
            "estimate. The highlight was the October Robotaxi event at Warner Bros. Studios, where "
            "Elon Musk unveiled the production Cybercab design and demonstrated unsupervised FSD "
            "v13 in a controlled environment. Tesla guided for Cybercab production to begin in "
            "H2 2026 at a target COGS below $25,000. Automotive gross margin was 17.1%, down from "
            "18.9% last year due to price reductions across the lineup and ramp costs. Energy "
            "storage deployed 6.9 GWh, a sequential record. The Megapack factory in Lathrop "
            "reached a 40 GWh annualized run rate. Musk confirmed plans for a dedicated robotaxi "
            "network app and stated that Tesla aims for 1 million unsupervised FSD miles by year "
            "end. Regulatory approval timelines remain uncertain, with California and Texas as "
            "the priority markets."
        ),
    },
    {
        "title": "AMZN AWS Re-Acceleration and Retail Margins",
        "ticker": "AMZN",
        "source_type": "news",
        "published_at": "2025-10-31",
        "text": (
            "Amazon reported Q3 2025 revenue of $162.5 billion, up 11% year over year, with AWS "
            "revenue of $28.8 billion growing 19%, marking three consecutive quarters of "
            "re-acceleration. AWS operating margin hit 33%, up from 30% a year ago, as custom "
            "Trainium2 chips improved inference cost efficiency. CEO Andy Jassy highlighted that "
            "generative AI services on AWS now have a multi-billion dollar annualized revenue "
            "run rate, growing triple digits. North America operating margin reached 5.9%, the "
            "highest since 2018, driven by same-day delivery efficiencies and reduced last-mile "
            "costs. International segment turned profitable for the second consecutive quarter. "
            "Amazon announced Anthropic Claude integration as the default AI assistant across "
            "Alexa Plus, expanding the $10/month subscription launched in Q2. Advertising revenue "
            "grew 24% to $14.3 billion, with Prime Video ad-supported tier contributing. Capital "
            "expenditures were $21.2 billion, primarily for AWS infrastructure, with management "
            "guiding $75 billion full-year capex. Free cash flow was $47 billion on a trailing "
            "twelve-month basis."
        ),
    },
    {
        "title": "Semiconductor Sector Outlook Q4 2025",
        "ticker": None,
        "source_type": "news",
        "published_at": "2025-12-01",
        "text": (
            "The semiconductor industry enters Q4 2025 with bifurcated demand. AI-related chips "
            "(GPUs, HBM, custom ASICs) remain severely supply-constrained, with lead times for "
            "NVIDIA's Blackwell exceeding 40 weeks and SK Hynix HBM3e allocation sold out through "
            "2026. Meanwhile, traditional segments show mixed signals: automotive MCUs are "
            "recovering from a 12-month inventory correction, analog/mixed-signal faces mid-single "
            "digit declines, and industrial IoT remains soft. The SOX index is up 38% YTD, driven "
            "almost entirely by AI beneficiaries (NVDA +180%, AVGO +65%, MRVL +55%). Memory "
            "pricing has stabilized after the DRAM/NAND upcycle peaked in Q2, with Samsung and "
            "Micron guiding for low-single-digit sequential revenue growth. Key risks include "
            "potential US export restrictions on advanced AI chips to the Middle East, TSMC's "
            "Arizona fab yield challenges, and elevated inventory levels in the PC/smartphone "
            "supply chain. The SIA projects 2025 global semiconductor revenue of $685 billion, "
            "up 19% year over year, with AI accounting for roughly $120 billion of the total."
        ),
    },
    {
        "title": "AAPL Services Segment Deep Dive",
        "ticker": "AAPL",
        "source_type": "news",
        "published_at": "2025-11-15",
        "text": (
            "Apple's Services segment continues to be the crown jewel of the company's margin "
            "profile. In FY2025, Services revenue reached $96 billion, up 14% year over year, "
            "with gross margins exceeding 71%. The segment now accounts for 25% of total revenue "
            "but nearly 40% of gross profit. Key growth drivers include: (1) App Store — "
            "benefiting from the shift to in-app subscriptions, with 980 million paid subscribers "
            "across all platforms; (2) Advertising — search ads and News+ placements generating "
            "an estimated $9 billion annually; (3) Apple TV+ — crossing 50 million subscribers "
            "after winning multiple Emmy and Oscar awards; (4) iCloud+ — storage upgrades "
            "accelerating as on-device AI features require cloud sync for training data. "
            "The Google TAC payment ($20B/year for default search) remains a regulatory "
            "overhang following the DOJ antitrust ruling. If forced to compete on merits, Apple "
            "could lose $8-12B in annual high-margin revenue. However, management is building "
            "hedges through Apple Search expansion and the new Apple Intelligence API platform, "
            "which charges developers for on-device ML inference credits."
        ),
    },
    {
        "title": "Bearish Take: Overvaluation in Mega-Cap Tech",
        "ticker": None,
        "source_type": "news",
        "published_at": "2025-12-10",
        "text": (
            "The Magnificent Seven trade at an aggregate forward P/E of 32x, a 55% premium to "
            "the S&P 500 ex-tech at 20.5x. While earnings growth has justified elevated "
            "multiples — the group delivered 33% average EPS growth in 2025 — we see multiple "
            "risks converging in 2026. First, AI capex ROI scrutiny is intensifying: Microsoft, "
            "Google, Amazon, and Meta will collectively spend $240 billion on infrastructure in "
            "2025, but monetization is tracking well below investment pace. Second, regulatory "
            "headwinds are accelerating globally: the EU's Digital Markets Act penalties, "
            "the DOJ's Google search remedy, and potential FTC action against Amazon's "
            "marketplace practices. "
            "Third, the rate environment is less supportive than consensus expects — the Fed is "
            "likely to pause at 4.25% rather than cut further, keeping the equity risk premium "
            "compressed. Our framework suggests 15-20% downside for the group over 12 months if "
            "earnings growth decelerates to 15-18%, which is our base case as AI revenue fails to "
            "scale proportionally to capex. We recommend underweighting mega-cap tech in favor of "
            "mid-cap software names with cleaner AI monetization (DDOG, SNOW, CRWD)."
        ),
    },
]


async def seed_text(api_url: str) -> None:
    """POST each document to the text ingest endpoint."""
    async with httpx.AsyncClient(timeout=120) as client:
        for i, doc in enumerate(DOCUMENTS, 1):
            data = {
                "title": doc["title"],
                "text": doc["text"],
                "source_type": doc["source_type"],
            }
            if doc["ticker"]:
                data["ticker"] = doc["ticker"]
            if doc["published_at"]:
                data["published_at"] = doc["published_at"]

            resp = await client.post(f"{api_url}/api/ingest/text", data=data)
            resp.raise_for_status()
            result = resp.json()
            print(
                f"  [{i}/{len(DOCUMENTS)}] Ingested: {doc['title']} "
                f"({result['chunk_count']} chunks)"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed text documents")
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    print("=== Seeding text documents ===")
    asyncio.run(seed_text(args.api_url))
    print("Done.\n")
