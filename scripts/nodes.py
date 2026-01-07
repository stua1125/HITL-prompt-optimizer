"""LLM 노드 로직 구현 모듈"""

from typing import List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from state import AgentState

load_dotenv()


class DirectInputEvaluation(BaseModel):
    """60점 미만: 직접 입력 모드 평가 결과"""
    score: int = Field(description="0-100점 사이의 프롬프트 품질 점수")
    guidance: str = Field(description="프롬프트 보충을 위해 사용자가 입력해야 할 내용에 대한 구체적인 안내")


class MultipleChoiceEvaluation(BaseModel):
    """60점 이상: 객관식 모드 평가 결과"""
    score: int = Field(description="0-100점 사이의 프롬프트 품질 점수")
    question: str = Field(description="프롬프트를 개선하기 위한 객관식 질문")
    options: List[str] = Field(description="4가지 선택지 리스트")


# LLM 초기화
llm = ChatOpenAI(model="gpt-4o", temperature=0)
direct_input_llm = llm.with_structured_output(DirectInputEvaluation)
multiple_choice_llm = llm.with_structured_output(MultipleChoiceEvaluation)


def judge_node(state: AgentState) -> dict:
    """프롬프트 품질을 평가하고 점수에 따라 다른 응답을 생성합니다.

    - 60점 미만: 직접 입력 모드 (guidance 제공)
    - 60점 이상: 객관식 모드 (question + options 제공)
    - 90점 이상: 완료

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 상태 딕셔너리
    """
    prompt = state["current_prompt"]
    question_count = state.get("question_count", 0)

    # 먼저 점수만 평가
    score_prompt = f"""다음 프롬프트의 품질을 0-100점으로 평가해주세요.

프롬프트: {prompt}

평가 기준:
1. 명확성: 요청이 구체적이고 명확한가?
2. 맥락: 충분한 배경 정보가 제공되었는가?
3. 목표: 원하는 결과물이 분명한가?
4. 제약조건: 필요한 제한사항이 명시되었는가?

점수만 숫자로 답해주세요."""

    try:
        score_result = llm.invoke(score_prompt)
        score = int(''.join(filter(str.isdigit, score_result.content[:10])))
        score = max(0, min(100, score))
    except Exception:
        score = 50

    # 90점 이상이면 완료
    if score >= 90:
        return {
            "score": score,
            "is_good": True,
            "mode": "multiple_choice",
            "guidance": None,
            "question": None,
            "options": [],
            "question_count": question_count
        }

    # 60점 미만: 직접 입력 모드
    if score < 60:
        direct_prompt = f"""다음 프롬프트를 평가하고, 사용자가 보충해야 할 내용을 안내해주세요.

프롬프트: {prompt}

현재 점수: {score}점

사용자가 프롬프트를 개선하기 위해 직접 입력해야 할 내용을 구체적으로 안내해주세요.
예: "목적, 대상 독자, 원하는 형식, 길이 제한 등을 추가해주세요"

점수는 {score}점으로 고정해주세요."""

        try:
            result = direct_input_llm.invoke(direct_prompt)
            return {
                "score": score,
                "is_good": False,
                "mode": "direct_input",
                "guidance": result.guidance,
                "question": None,
                "options": [],
                "question_count": question_count
            }
        except Exception as e:
            print(f"⚠️ 평가 중 오류 발생: {e}")
            return {
                "score": score,
                "is_good": False,
                "mode": "direct_input",
                "guidance": "프롬프트에 목적, 대상, 형식, 제약조건 등을 추가해주세요.",
                "question": None,
                "options": [],
                "question_count": question_count
            }

    # 60점 이상: 객관식 모드
    mc_prompt = f"""다음 프롬프트를 개선하기 위한 객관식 질문을 만들어주세요.

프롬프트: {prompt}

현재 점수: {score}점

프롬프트를 더 구체적으로 만들기 위해 사용자에게 물어볼 질문 1개와 4가지 선택지를 제시해주세요.
질문은 프롬프트의 부족한 부분을 채우는 데 도움이 되어야 합니다.

점수는 {score}점으로 고정해주세요."""

    try:
        result = multiple_choice_llm.invoke(mc_prompt)
        return {
            "score": score,
            "is_good": False,
            "mode": "multiple_choice",
            "guidance": None,
            "question": result.question,
            "options": result.options,
            "question_count": question_count + 1
        }
    except Exception as e:
        print(f"⚠️ 평가 중 오류 발생: {e}")
        return {
            "score": score,
            "is_good": False,
            "mode": "multiple_choice",
            "guidance": None,
            "question": "프롬프트의 목적은 무엇인가요?",
            "options": ["학습/교육", "업무/비즈니스", "창작/엔터테인먼트", "기타"],
            "question_count": question_count + 1
        }


def refine_node(state: AgentState) -> dict:
    """사용자 입력을 반영하여 프롬프트를 재작성합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        업데이트된 current_prompt를 담은 딕셔너리
    """
    mode = state.get("mode", "direct_input")

    if mode == "direct_input":
        # 직접 입력 모드: 사용자 피드백으로 프롬프트 개선
        refine_prompt = f"""다음 정보를 바탕으로 프롬프트를 더 구체적이고 명확하게 재작성해주세요.

기존 프롬프트: {state['current_prompt']}
사용자가 추가한 내용: {state['user_feedback']}

개선된 프롬프트만 출력해주세요. 다른 설명은 필요 없습니다."""
    else:
        # 객관식 모드: 선택한 답변으로 프롬프트 개선
        refine_prompt = f"""다음 정보를 바탕으로 프롬프트를 더 구체적이고 명확하게 재작성해주세요.

기존 프롬프트: {state['current_prompt']}
질문: {state.get('question', '')}
사용자 선택: {state['user_choice']}

선택한 내용을 자연스럽게 반영하여 프롬프트를 개선해주세요.
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
