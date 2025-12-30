랭그래프(LangGraph)와 OpenAI API를 활용하여 **'Human-in-the-Loop 프롬프트 최적화 도구'**를 개발하기 위한 상세 기획서 및 프로젝트 구조를 마크다운 형식으로 작성해 드립니다.

이 문서를 Claude Code나 IDE의 개발 어시스턴트에게 입력하면 프로젝트를 자동으로 구성하고 실행할 수 있도록 설계했습니다.

프로젝트 기획서: HITL 프롬프트 가디언 (Prompt Guardian)
본 프로젝트는 사용자의 모호한 프롬프트를 분석하여 점수를 매기고, 부족한 경우 4가지 선택지를 통해 인간의 개입(HITL)을 유도하여 최적의 프롬프트를 완성하는 LangGraph 기반 에이전트입니다.

1. 프로젝트 구조 (File Structure)
Plaintext

prompt-optimizer/
├── .env                # API Key 설정
├── requirements.txt    # 의존성 라이브러리
├── state.py           # LangGraph 상태 정의
├── nodes.py           # LLM 로직 및 노드 함수
├── graph.py           # 랭그래프 워크플로우 구성
└── main.py            # 실행 엔트리포인트 (CLI 인터페이스)
2. 개발 요구사항 및 단계별 실행 가이드
단계 1: 환경 설정 (requirements.txt)
Plaintext

langgraph
langchain-openai
python-dotenv
pydantic
단계 2: 상태 정의 (state.py)
에이전트가 흐름 내내 유지할 데이터를 정의합니다.

Python

from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    initial_prompt: str
    current_prompt: str
    score: int
    is_good: bool
    critique_options: List[str]
    user_choice: Optional[str]
    user_feedback: Optional[str]
    iteration_count: int
단계 3: 노드 로직 구현 (nodes.py)
OpenAI API를 사용하여 분석 및 수정을 담당합니다. Pydantic을 사용하여 출력을 구조화합니다.

Python

import os
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from state import AgentState

class Evaluation(BaseModel):
    score: int = Field(description="0-100점 사이의 점수")
    is_good: bool = Field(description="80점 이상이면 True")
    options: List[str] = Field(description="보완을 위한 4가지 선택지 리스트")

llm = ChatOpenAI(model="gpt-4o", temperature=0)
structured_llm = llm.with_structured_output(Evaluation)

def judge_node(state: AgentState):
    """프롬프트 품질 평가 및 선택지 생성"""
    prompt = state["current_prompt"]
    res = structured_llm.invoke(f"다음 프롬프트의 품질을 평가하고 보완점 4개를 제안해줘: {prompt}")
    return {
        "score": res.score,
        "is_good": res.is_good,
        "critique_options": res.options,
        "iteration_count": state.get("iteration_count", 0) + 1
    }

def refine_node(state: AgentState):
    """사용자 피드백을 반영하여 프롬프트 재작성"""
    combined_info = f"""
    기존 프롬프트: {state['current_prompt']}
    선택한 보완항목: {state['user_choice']}
    추가 피드백: {state['user_feedback']}
    """
    res = llm.invoke(f"위 정보를 바탕으로 더 구체적이고 명확한 프롬프트로 재작성해줘. 결과만 출력해.\n{combined_info}")
    return {"current_prompt": res.content}
단계 4: 그래프 구성 (graph.py)
interrupt_before를 사용하여 인간의 입력을 기다리는 지점을 설정합니다.

Python

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from nodes import judge_node, refine_node
from state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("judge", judge_node)
workflow.add_node("human_input", lambda state: state) # 대기 노드
workflow.add_node("refine", refine_node)

workflow.set_entry_point("judge")

def route_after_judge(state: AgentState):
    if state["is_good"] or state["iteration_count"] >= 3:
        return END
    return "human_input"

workflow.add_conditional_edges("judge", route_after_judge)
workflow.add_edge("human_input", "refine")
workflow.add_edge("refine", "judge")

# 체크포인터 설정 (상태 보존)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["human_input"])
단계 5: 메인 실행부 (main.py)
CLI 환경에서 사용자와 상호작용하며 interrupt 상황을 처리합니다.

Python

import os
from dotenv import load_dotenv
from graph import app

load_dotenv()

def run_optimizer():
    config = {"configurable": {"thread_id": "1"}}
    initial_input = input("최적화할 프롬프트를 입력하세요: ")
    
    # 1. 시작
    for event in app.stream({"initial_prompt": initial_input, "current_prompt": initial_input}, config):
        pass

    while True:
        state = app.get_state(config)
        
        # 중단 지점 확인 (인간의 개입이 필요한 경우)
        if state.next:
            print(f"\n현재 점수: {state.values['score']}")
            print("보완이 필요합니다. 다음 중 하나를 선택하세요:")
            for i, opt in enumerate(state.values['critique_options']):
                print(f"{i+1}. {opt}")
            
            choice_idx = int(input("\n번호 선택 (1-4): ")) - 1
            feedback = input("추가할 구체적인 내용을 입력하세요: ")
            
            # 상태 업데이트 및 재개
            app.update_state(config, {
                "user_choice": state.values['critique_options'][choice_idx],
                "user_feedback": feedback
            }, as_node="human_input")
            
            for event in app.stream(None, config):
                pass
        else:
            print("\n✨ 최적화 완료!")
            print(f"최종 프롬프트: {state.values['current_prompt']}")
            break

if __name__ == "__main__":
    run_optimizer()
3. 실행 방법 (Sequential Steps)
환경 파일 생성: .env 파일을 만들고 OPENAI_API_KEY=your_key_here를 입력합니다.

라이브러리 설치: pip install -r requirements.txt 실행.

파일 작성: 위 제공된 코드를 각각의 파일명으로 저장합니다.

실행: python main.py를 실행하여 프롬프트 최적화 루프를 시작합니다.

4. Claude Code 에이전트를 위한 지시문
"위 마크다운에 기재된 파일 구조와 코드를 바탕으로 프로젝트 폴더를 생성해줘. 각 노드의 프롬프트는 한국어로 자연스럽게 동작하도록 조정해주고, main.py 실행 시 터미널에서 사용자가 1~4번 중 선택하여 프롬프트가 점진적으로 발전하는 것을 확인할 수 있게 작성해줘."
