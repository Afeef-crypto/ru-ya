from __future__ import annotations

from ru_ya.models.dream import FollowUpQuestion

FOLLOWUP_CATALOG: dict[str, FollowUpQuestion] = {
    "people_identity": FollowUpQuestion(
        slot="people_identity",
        prompt_en="Who was the person — known or unknown?",
        prompt_ar="من كان الشخص — معروف أم مجهول؟",
    ),
    "setting_indoor_outdoor": FollowUpQuestion(
        slot="setting_indoor_outdoor",
        prompt_en="Was the setting indoors or outdoors?",
        prompt_ar="هل كان المكان داخل بناء أم في الخارج؟",
    ),
    "setting_day_night": FollowUpQuestion(
        slot="setting_day_night",
        prompt_en="Was it day or night in the dream?",
        prompt_ar="هل كان الوقت نهاراً أم ليلاً في المنام؟",
    ),
    "sequence_before": FollowUpQuestion(
        slot="sequence_before",
        prompt_en="What happened immediately before the key action?",
        prompt_ar="ماذا حدث مباشرة قبل الحدث الأساسي؟",
    ),
    "sequence_after": FollowUpQuestion(
        slot="sequence_after",
        prompt_en="What happened immediately after the key action?",
        prompt_ar="ماذا حدث مباشرة بعد الحدث الأساسي؟",
    ),
    "observer_or_actor": FollowUpQuestion(
        slot="observer_or_actor",
        prompt_en="Did you speak or act, or only observe?",
        prompt_ar="هل تكلمت أو فعلت شيئاً، أم كنت تشاهد فقط؟",
    ),
    "symbol_detail": FollowUpQuestion(
        slot="symbol_detail",
        prompt_en="Can you describe the main symbol or object more precisely?",
        prompt_ar="هل يمكنك وصف الرمز أو الشيء الأساسي بدقة أكثر؟",
    ),
    "color_or_state": FollowUpQuestion(
        slot="color_or_state",
        prompt_en="What color or condition was the main object?",
        prompt_ar="ما لون أو حال الشيء الأساسي؟",
    ),
    "spoken_words": FollowUpQuestion(
        slot="spoken_words",
        prompt_en="Do you remember any spoken words?",
        prompt_ar="هل تذكر أي كلام قيل في المنام؟",
    ),
}

CRITICAL_SLOTS = (
    "people_identity",
    "setting_indoor_outdoor",
    "setting_day_night",
    "observer_or_actor",
)
