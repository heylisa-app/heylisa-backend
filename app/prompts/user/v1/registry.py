#/app/prompts/user/v1/registry.py

from __future__ import annotations

from typing import Dict

from app.prompts.user.v1.blocks import (
    UserPromptBlock,
    SMALLTALK_INTRO,
    DISCOVERY,
    DISCOVERY_PENDING,
    ONBOARDING,
    SMALL_TALK,
    ACTION_REQUEST,
    FUNCTIONAL_QUESTION,
    GENERAL_QUESTION,
    PAYWALL_SOFT_WARNING,
    AMABILITIES,
    DECISION_SUPPORT,
    MOTIVATIONAL_GUIDANCE,
    DEEP_WORK,
    PROFESSIONAL_REQUEST,
    SENSITIVE_QUESTION,
    URGENT_REQUEST,
    ONGOING_PERSONAL,
    ONGOING_PRO,
)

USER_BLOCKS_BY_STATE: Dict[str, UserPromptBlock] = {
    "smalltalk_intro": SMALLTALK_INTRO,
    "discovery": DISCOVERY,
    "discovery_pending": DISCOVERY_PENDING,
    "onboarding": ONBOARDING,
    "ongoing_pro": ONGOING_PRO,
    "ongoing_personal": ONGOING_PERSONAL,
}

USER_BLOCKS_BY_INTENT: Dict[str, UserPromptBlock] = {
    "action_request": ACTION_REQUEST,
    "functional_question": FUNCTIONAL_QUESTION,
    "general_question": GENERAL_QUESTION,
    "small_talk": SMALL_TALK,
    "amabilities": AMABILITIES,
    "decision_support": DECISION_SUPPORT,
    "motivational_guidance": MOTIVATIONAL_GUIDANCE,
    "deep_work": DEEP_WORK,
    "professional_request": PROFESSIONAL_REQUEST,
    "sensitive_question": SENSITIVE_QUESTION,
    "urgent_request": URGENT_REQUEST,
}

USER_BLOCKS_MISC: Dict[str, UserPromptBlock] = {
    "paywall_soft_warning": PAYWALL_SOFT_WARNING,
}
