"""LangGraph 상태 정의 모듈"""

from typing import TypedDict, List, Optional, Literal


class AgentState(TypedDict):
    """프롬프트 최적화 에이전트의 상태를 정의합니다.

    Attributes:
        initial_prompt: 사용자가 처음 입력한 원본 프롬프트
        current_prompt: 현재 최적화 중인 프롬프트
        score: 프롬프트 품질 점수 (0-100)
        is_good: 프롬프트가 충분히 좋은지 여부 (90점 이상)
        mode: 현재 모드 (direct_input: 60점 미만, multiple_choice: 60점 이상)
        guidance: 60점 미만일 때 보충 필요 내용 안내
        question: 60점 이상일 때 객관식 질문
        options: 객관식 선택지 리스트
        user_choice: 사용자가 선택한 보완 항목
        user_feedback: 사용자가 직접 입력한 피드백
        question_count: 객관식 질문 반복 횟수 (최대 5회)
        chat_response: 최종 프롬프트로 LLM 채팅한 응답
    """
    initial_prompt: str
    current_prompt: str
    score: int
    is_good: bool
    mode: Literal["direct_input", "multiple_choice"]
    guidance: Optional[str]
    question: Optional[str]
    options: List[str]
    user_choice: Optional[str]
    user_feedback: Optional[str]
    question_count: int
    chat_response: Optional[str]
