"""
AlgoPharma — Thread scorer.
Combines main post AE result with reply analysis
for a more robust final signal confidence.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path for standalone script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logger = logging.getLogger(__name__)


def score_thread(
    main_ae_result: dict,
    replies: list[str],
    source_health_score: float = 0.85,
) -> dict:
    """
    Score a full post thread.

    Args:
        main_ae_result: Output from detect_ae() on the main post.
        replies: List of reply text strings.
        source_health_score: Health score for the source (0-1).

    Returns:
        {final_confidence, color, corroboration_score, reply_analysis}
    """
    from nlp.ae_detector import detect_ae

    ae_confidence = main_ae_result.get("confidence", 0.0)
    main_drug = main_ae_result.get("drug", "")

    if not replies:
        corroboration_score = 0.5  # neutral default
        reply_analysis = []
    else:
        corroborating = 0
        weakly_corroborating = 0
        contradicting = 0
        neutral_count = 0
        reply_analysis = []

        for reply_text in replies:
            reply_ae = detect_ae(reply_text)
            analysis = {"text_preview": reply_text[:80], "ae_flag": reply_ae["ae_flag"]}

            if reply_ae["ae_flag"]:
                reply_drug = reply_ae.get("drug", "")
                if reply_drug and main_drug and reply_drug.lower() == main_drug.lower():
                    corroborating += 1
                    analysis["verdict"] = "CORROBORATING"
                else:
                    weakly_corroborating += 1
                    analysis["verdict"] = "WEAKLY_CORROBORATING"
            elif reply_ae.get("sentiment", {}).get("label") == "POSITIVE":
                contradicting += 1
                analysis["verdict"] = "CONTRADICTING"
            else:
                neutral_count += 1
                analysis["verdict"] = "NEUTRAL"

            reply_analysis.append(analysis)

        total = len(replies)
        corroboration_score = (corroborating + weakly_corroborating * 0.5) / total if total > 0 else 0.5

    # ── Final confidence formula ─────────────────────────
    final_confidence = (
        ae_confidence * 0.60
        + corroboration_score * 0.25
        + source_health_score * 0.15
    )
    final_confidence = round(min(1.0, final_confidence), 4)

    # ── Signal colour bands ──────────────────────────────
    if final_confidence >= 0.70:
        color = "green"
    elif final_confidence >= 0.50:
        color = "amber"
    else:
        color = "red"

    return {
        "final_confidence": final_confidence,
        "color": color,
        "ae_confidence": ae_confidence,
        "corroboration_score": round(corroboration_score, 4),
        "source_health_score": source_health_score,
        "reply_count": len(replies),
        "reply_analysis": reply_analysis,
    }


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import os
    os.environ["FAST_MODE"] = "false"

    from nlp.ae_detector import detect_ae

    main_text = "Dolo 650 caused severe nausea and stomach pain"
    main_ae = detect_ae(main_text)

    replies = [
        "Same here, Dolo 650 gave me terrible nausea too",
        "I also had nausea from Dolo 650, very bad experience",
        "Dolo 650 made me vomit, horrible side effect",
        "Paracetamol nausea is real, happened to me with Dolo",
        "This medicine worked fine for me, no issues at all",
        "Dolo 650 is great, cured my fever quickly",
    ]

    result = score_thread(main_ae, replies)

    print("=" * 55)
    print("  Thread Scorer — Self-test")
    print("=" * 55)
    print(f"  Main AE: flag={main_ae['ae_flag']}, conf={main_ae['confidence']}")
    print(f"  Replies: {len(replies)}")
    print(f"  Corroboration: {result['corroboration_score']}")
    print(f"  Final confidence: {result['final_confidence']}")
    print(f"  Signal color: {result['color']}")
    print()
    for ra in result["reply_analysis"]:
        print(f"    {ra['verdict']:25s} → \"{ra['text_preview'][:50]}\"")

    print("─" * 55)
    ok = result["color"] in ("green", "amber")
    print(f"{'✅' if ok else '❌'} thread_scorer self-test {'PASS' if ok else 'FAIL'}")
