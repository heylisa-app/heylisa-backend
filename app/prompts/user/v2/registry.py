from __future__ import annotations

from typing import Dict

from app.prompts.user.v2.blocks import (
    UserPromptBlock,
    SMALLTALK_ONBOARDING,
    DISCOVERY_CAPABILITIES,
    NORMAL_RUN,
    AMABILITIES,
    EMOTIONAL_SUPPORT,
    MEDICAL_ASSISTANCE,
    PATIENT_CASE_ASSISTANCE,
    CABINET_ASSISTANCE,
    PRODUCT_SUPPORT,
    TASK_EXECUTION,
    OUT_OF_SCOPE,
)

USER_BLOCKS_BY_STATE: Dict[str, UserPromptBlock] = {
    "smalltalk_onboarding": SMALLTALK_ONBOARDING,
    "discovery_capabilities": DISCOVERY_CAPABILITIES,
    "normal_run": NORMAL_RUN,
}

USER_BLOCKS_BY_INTENT: Dict[str, UserPromptBlock] = {
    "amabilities": AMABILITIES,
    "emotional_support": EMOTIONAL_SUPPORT,
    "medical_assistance": MEDICAL_ASSISTANCE,
    "patient_case_assistance": PATIENT_CASE_ASSISTANCE,
    "cabinet_assistance": CABINET_ASSISTANCE,
    "product_support": PRODUCT_SUPPORT,
    "task_execution": TASK_EXECUTION,
    "out_of_scope": OUT_OF_SCOPE,
}

USER_BLOCKS_MISC: Dict[str, UserPromptBlock] = {}