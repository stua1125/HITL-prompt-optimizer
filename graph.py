"""LangGraph 워크플로우 구성 모듈"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState
from nodes import judge_node, refine_node


def create_workflow():
    """프롬프트 최적화 워크플로우를 생성합니다.

    Returns:
        컴파일된 LangGraph 애플리케이션
    """
    # StateGraph 초기화
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("judge", judge_node)
    workflow.add_node("human_input", lambda state: state)  # 인간 개입 대기 노드
    workflow.add_node("refine", refine_node)

    # 시작점 설정
    workflow.set_entry_point("judge")

    # 조건부 라우팅 함수
    def route_after_judge(state: AgentState) -> str:
        """judge 노드 이후 라우팅을 결정합니다.

        - 점수가 80점 이상이거나 반복 3회 도달 시 종료
        - 그 외에는 human_input으로 이동
        """
        if state["is_good"] or state["iteration_count"] >= 3:
            return END
        return "human_input"

    # 엣지 연결
    workflow.add_conditional_edges("judge", route_after_judge)
    workflow.add_edge("human_input", "refine")
    workflow.add_edge("refine", "judge")

    # 체크포인터 설정 (상태 보존)
    memory = MemorySaver()

    # 워크플로우 컴파일 (human_input 전에 interrupt)
    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["human_input"]
    )

    return app


# 기본 앱 인스턴스
app = create_workflow()
