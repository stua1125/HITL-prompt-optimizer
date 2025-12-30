"""LLM 노드 로직 구현 모듈"""

import os
from typing import List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from state import AgentState

load_dotenv()


class Evaluation(BaseModel):
    """프롬프트 평가 결과 스키마"""
    score: int = Field(description="0-100점 사이의 프롬프트 품질 점수")
    is_good: bool = Field(description="80점 이상이면 True, 미만이면 False")
    options: List[str] = Field(description="프롬프트 보완을 위한 4가지 구체적인 선택지")


# LLM 초기화
llm = ChatOpenAI(model="gpt-4o", temperature=0)
structured_llm = llm.with_structured_output(Evaluation)


def judge_node(state: AgentState) -> dict:
    """프롬프트 품질을 평가하고 보완 선택지를 생성합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 상태 딕셔너리 (score, is_good, critique_options, iteration_count)
    """
    prompt = state["current_prompt"]

    evaluation_prompt = f"""다음 프롬프트의 품질을 평가해주세요.

프롬프트: {prompt}

평가 기준:
1. 명확성: 요청이 구체적이고 명확한가?
2. 맥락: 충분한 배경 정보가 제공되었는가?
3. 목표: 원하는 결과물이 분명한가?
4. 제약조건: 필요한 제한사항이 명시되었는가?

0-100점으로 평가하고, 프롬프트를 개선할 수 있는 4가지 구체적인 방법을 제안해주세요.
각 선택지는 번호 없이 내용만 작성해주세요."""

    try:
        result = structured_llm.invoke(evaluation_prompt)
        return {
            "score": result.score,
            "is_good": result.is_good,
            "critique_options": result.options,
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    except Exception as e:
        print(f"⚠️ 평가 중 오류 발생: {e}")
        return {
            "score": 0,
            "is_good": False,
            "critique_options": ["다시 시도해주세요"],
            "iteration_count": state.get("iteration_count", 0) + 1
        }


def refine_node(state: AgentState) -> dict:
    """사용자 피드백을 반영하여 프롬프트를 재작성합니다.

    Args:
        state: 현재 에이전트 상태 (user_choice, user_feedback 포함)

    Returns:
        업데이트된 current_prompt를 담은 딕셔너리
    """
    refine_prompt = f"""다음 정보를 바탕으로 프롬프트를 더 구체적이고 명확하게 재작성해주세요.

기존 프롬프트: {state['current_prompt']}
선택한 보완 항목: {state['user_choice']}
추가 피드백: {state['user_feedback']}

개선된 프롬프트만 출력해주세요. 다른 설명은 필요 없습니다."""

    try:
        result = llm.invoke(refine_prompt)
        return {"current_prompt": result.content}
    except Exception as e:
        print(f"⚠️ 재작성 중 오류 발생: {e}")
        return {"current_prompt": state['current_prompt']}


def chat_with_prompt(prompt: str) -> str:
    """최종 프롬프트로 LLM과 채팅합니다.

    Args:
        prompt: 최적화된 최종 프롬프트

    Returns:
        LLM의 응답 문자열
    """
    try:
        result = llm.invoke(prompt)
        return result.content
    except Exception as e:
        return f"⚠️ 채팅 중 오류 발생: {e}"
