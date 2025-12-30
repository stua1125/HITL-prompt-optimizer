"""CLI 실행 엔트리포인트"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def check_api_key() -> bool:
    """OpenAI API 키가 설정되어 있는지 확인합니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 API 키를 설정해주세요.")
        return False
    return True


def display_header():
    """프로그램 헤더를 출력합니다."""
    print("\n" + "=" * 50)
    print("HITL 프롬프트 옵티마이저 (Prompt Optimizer)")
    print("=" * 50)
    print("프롬프트를 분석하고 최적화하는 도구입니다.")
    print("최대 3회 반복하며, 80점 이상이면 완료됩니다.\n")


def get_confirmation() -> bool:
    """사용자로부터 Y/N 확인을 받습니다.

    Returns:
        True if user confirms (Y/y), False otherwise (N/n)
    """
    while True:
        choice = input("\n🤖 이 프롬프트로 LLM과 채팅하시겠습니까? (Y/N): ").strip().lower()
        if choice in ('y', 'yes'):
            return True
        elif choice in ('n', 'no'):
            return False
        else:
            print("⚠️ Y 또는 N을 입력해주세요.")


def get_user_choice(options: list) -> tuple[str, str]:
    """사용자로부터 선택과 피드백을 받습니다.

    Args:
        options: 보완 선택지 리스트

    Returns:
        (선택한 옵션, 추가 피드백) 튜플
    """
    print("\n📋 보완이 필요합니다. 다음 중 하나를 선택하세요:\n")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")

    while True:
        try:
            choice_input = input("\n👉 번호 선택 (1-4, 또는 'q'로 종료): ").strip()

            if choice_input.lower() == 'q':
                print("\n프로그램을 종료합니다.")
                sys.exit(0)

            choice_idx = int(choice_input) - 1

            if 0 <= choice_idx < len(options):
                break
            print(f"⚠️ 1-{len(options)} 사이의 숫자를 입력해주세요.")
        except ValueError:
            print("⚠️ 올바른 숫자를 입력해주세요.")

    feedback = input("✏️  추가할 구체적인 내용을 입력하세요 (없으면 Enter): ").strip()

    return options[choice_idx], feedback


def run_optimizer():
    """프롬프트 최적화 루프를 실행합니다."""
    from graph import app
    from nodes import chat_with_prompt

    display_header()

    # 초기 프롬프트 입력
    initial_input = input("📝 최적화할 프롬프트를 입력하세요:\n> ").strip()

    if not initial_input:
        print("❌ 프롬프트가 비어있습니다.")
        return

    config = {"configurable": {"thread_id": "prompt-optimizer-1"}}

    # 초기 상태로 시작
    initial_state = {
        "initial_prompt": initial_input,
        "current_prompt": initial_input,
        "score": 0,
        "is_good": False,
        "critique_options": [],
        "user_choice": None,
        "user_feedback": None,
        "iteration_count": 0
    }

    print("\n⏳ 프롬프트 분석 중...")

    # 첫 실행
    for event in app.stream(initial_state, config):
        pass

    # 메인 루프
    while True:
        state = app.get_state(config)

        # 중단 지점 확인 (human_input 노드 대기 중)
        if state.next:
            values = state.values
            score = values.get("score", 0)
            iteration = values.get("iteration_count", 0)

            print(f"\n{'─' * 40}")
            print(f"📊 현재 점수: {score}/100 (반복: {iteration}/3)")
            print(f"📄 현재 프롬프트:\n   {values.get('current_prompt', '')[:100]}...")

            # 사용자 입력 받기
            options = values.get("critique_options", [])
            if options:
                user_choice, user_feedback = get_user_choice(options)

                # 상태 업데이트 및 재개
                app.update_state(
                    config,
                    {
                        "user_choice": user_choice,
                        "user_feedback": user_feedback or "없음"
                    },
                    as_node="human_input"
                )

                print("\n⏳ 프롬프트 개선 중...")

                # 다음 단계 실행
                for event in app.stream(None, config):
                    pass
            else:
                print("⚠️ 선택지가 없습니다. 종료합니다.")
                break
        else:
            # 최적화 완료
            final_state = state.values
            final_prompt = final_state.get('current_prompt', '')

            print(f"\n{'═' * 50}")
            print("✨ 최적화 완료!")
            print(f"{'═' * 50}")
            print(f"📊 최종 점수: {final_state.get('score', 0)}/100")
            print(f"🔄 반복 횟수: {final_state.get('iteration_count', 0)}회")
            print(f"\n📝 원본 프롬프트:\n   {final_state.get('initial_prompt', '')}")
            print(f"\n🎯 최종 프롬프트:")
            print(f"{'─' * 50}")
            print(final_prompt)
            print(f"{'─' * 50}")

            # Y/N 확인 후 LLM 채팅
            if get_confirmation():
                print("\n⏳ LLM에 프롬프트 전송 중...")
                response = chat_with_prompt(final_prompt)
                print(f"\n{'═' * 50}")
                print("💬 LLM 응답:")
                print(f"{'═' * 50}")
                print(response)
                print(f"{'═' * 50}")
            else:
                print("\n👋 채팅을 취소했습니다. 프로그램을 종료합니다.")

            break


def main():
    """메인 함수"""
    if not check_api_key():
        sys.exit(1)

    try:
        run_optimizer()
    except KeyboardInterrupt:
        print("\n\n프로그램이 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
