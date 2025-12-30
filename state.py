"""LangGraph 상태 정의 모듈"""

from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    """프롬프트 최적화 에이전트의 상태를 정의합니다.

    Attributes:
        initial_prompt: 사용자가 처음 입력한 원본 프롬프트
        current_prompt: 현재 최적화 중인 프롬프트
        score: 프롬프트 품질 점수 (0-100)
        is_good: 프롬프트가 충분히 좋은지 여부 (80점 이상)
        critique_options: LLM이 제안한 4가지 보완 선택지
        user_choice: 사용자가 선택한 보완 항목
        user_feedback: 사용자가 추가로 입력한 피드백
        iteration_count: 최적화 반복 횟수
        chat_response: 최종 프롬프트로 LLM 채팅한 응답
    """
    initial_prompt: str
    current_prompt: str
    score: int
    is_good: bool
    critique_options: List[str]
    user_choice: Optional[str]
    user_feedback: Optional[str]
    iteration_count: int
    chat_response: Optional[str]
