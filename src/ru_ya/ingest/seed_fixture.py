"""Minimal in-memory seed corpus for local development and tests."""

from __future__ import annotations

from ru_ya.ingest.curated import CuratedDocumentDraft, prepare_curated_document

SEED_TAXBIR_HADITH = """\
عن أبي قتادة عن النبي صلى الله عليه وسلم قال الرؤيا الصالحة من الله والحلم من الشيطان فإذا حلم أحدكم حلما يكرهه فليبصق عن يساره وليتعوذ بالله منه فلن يضره

If someone sees a dream he dislikes, he should spit to his left and seek refuge with Allah; it will not harm him.
"""

SEED_SYMBOL_SNAKE = """\
الحية في المنام قد تُفسر بعدو، ويُقيد ذلك بصفاتها وحال الرائي، وليست قاعدة قطعية.

A snake in a dream is sometimes interpreted as an enemy, conditioned on its attributes and the dreamer's state — not a certainty.
"""

SEED_FATH_SECTION = """\
كتاب التعبير عند ابن حجر يشرح أحاديث الرؤيا ويفرق بين الرؤيا والحلم وحديث النفس، وينقل كلام أهل العلم مع التخريج.
"""


def build_seed_corpus() -> list[CuratedDocumentDraft]:
    taxonomy = prepare_curated_document(
        title="Seed — Sahih hadith on dreams (fixture)",
        author="al-Bukhari / Muslim (fixture)",
        reliability_tier=1,
        collection="fixture-taxonomy",
        text=SEED_TAXBIR_HADITH,
        topic_tags=["adab", "ta'bir", "taxonomy"],
    )
    dictionary = prepare_curated_document(
        title="Seed — Symbol entry: snake (fixture)",
        author="Tafsir al-Ahlam (disputed attribution, fixture)",
        reliability_tier=3,
        collection="fixture-dictionary",
        text=SEED_SYMBOL_SNAKE,
        topic_tags=["symbol", "snake"],
    )
    commentary = prepare_curated_document(
        title="Seed — Fath al-Bari excerpt (fixture)",
        author="Ibn Hajar",
        reliability_tier=1,
        collection="fixture-fath",
        text=SEED_FATH_SECTION,
        topic_tags=["ta'bir", "commentary"],
        build_pageindex=True,
        section_pairs=[
            ("Kitab al-Ta'bir — overview", SEED_FATH_SECTION),
            ("Ru'ya vs hulm vs hadith al-nafs", SEED_TAXBIR_HADITH),
        ],
    )
    return [taxonomy, dictionary, commentary]
