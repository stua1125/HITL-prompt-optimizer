"""
HITL Prompt Optimizer - Tkinter GUI
모던하고 사용성 좋은 프롬프트 최적화 GUI 애플리케이션
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from typing import Optional, Callable
import os
from dotenv import load_dotenv

load_dotenv()


class ModernStyle:
    """모던 UI 스타일 정의"""

    # 색상 팔레트
    BG_PRIMARY = "#1a1a2e"      # 다크 네이비
    BG_SECONDARY = "#16213e"    # 딥 블루
    BG_CARD = "#0f3460"         # 카드 배경

    ACCENT = "#e94560"          # 핑크/레드 액센트
    ACCENT_HOVER = "#ff6b6b"    # 호버 색상

    TEXT_PRIMARY = "#ffffff"    # 흰색 텍스트
    TEXT_SECONDARY = "#a0a0a0"  # 회색 텍스트
    TEXT_MUTED = "#6c757d"      # 뮤트 텍스트

    SUCCESS = "#4ecca3"         # 성공/완료 색상
    WARNING = "#ffc107"         # 경고 색상
    INFO = "#17a2b8"            # 정보 색상

    # 폰트
    FONT_FAMILY = "SF Pro Display" if os.name == "darwin" else "Segoe UI"
    FONT_TITLE = (FONT_FAMILY, 24, "bold")
    FONT_SUBTITLE = (FONT_FAMILY, 14, "bold")
    FONT_BODY = (FONT_FAMILY, 12)
    FONT_SMALL = (FONT_FAMILY, 10)
    FONT_BUTTON = (FONT_FAMILY, 11, "bold")

    # 크기
    PADDING = 20
    RADIUS = 10


class PromptOptimizerGUI:
    """프롬프트 최적화 GUI 메인 클래스"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HITL Prompt Optimizer")
        self.root.geometry("900x700")
        self.root.configure(bg=ModernStyle.BG_PRIMARY)
        self.root.resizable(True, True)

        # 상태 변수
        self.current_prompt = ""
        self.score = 0
        self.question_count = 0
        self.mode = "direct_input"
        self.is_processing = False

        # LLM 클라이언트 초기화
        self.llm = None
        self._init_llm()

        # UI 구성
        self._setup_styles()
        self._create_widgets()

    def _init_llm(self):
        """LLM 클라이언트 초기화"""
        try:
            from langchain_openai import ChatOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "your_openai_api_key_here":
                self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        except Exception as e:
            print(f"LLM 초기화 실패: {e}")

    def _setup_styles(self):
        """ttk 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')

        # 프로그레스바 스타일
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=ModernStyle.BG_SECONDARY,
            background=ModernStyle.ACCENT,
            darkcolor=ModernStyle.ACCENT,
            lightcolor=ModernStyle.ACCENT,
            bordercolor=ModernStyle.BG_SECONDARY,
            thickness=8
        )

    def _create_widgets(self):
        """UI 위젯 생성"""
        # 메인 컨테이너
        main_container = tk.Frame(self.root, bg=ModernStyle.BG_PRIMARY)
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # 헤더
        self._create_header(main_container)

        # 점수 및 상태 카드
        self._create_status_card(main_container)

        # 프롬프트 입력 영역
        self._create_prompt_section(main_container)

        # 선택지 영역
        self._create_options_section(main_container)

        # 결과 영역
        self._create_result_section(main_container)

        # 하단 버튼
        self._create_bottom_buttons(main_container)

    def _create_header(self, parent):
        """헤더 생성"""
        header_frame = tk.Frame(parent, bg=ModernStyle.BG_PRIMARY)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # 타이틀
        title_label = tk.Label(
            header_frame,
            text="✨ HITL Prompt Optimizer",
            font=ModernStyle.FONT_TITLE,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_PRIMARY
        )
        title_label.pack(side=tk.LEFT)

        # 서브타이틀
        subtitle_label = tk.Label(
            header_frame,
            text="Human-in-the-Loop 프롬프트 최적화",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_PRIMARY
        )
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0), pady=(10, 0))

    def _create_status_card(self, parent):
        """상태 카드 생성"""
        card_frame = tk.Frame(parent, bg=ModernStyle.BG_CARD, padx=20, pady=15)
        card_frame.pack(fill=tk.X, pady=(0, 15))

        # 상단: 점수와 모드
        top_row = tk.Frame(card_frame, bg=ModernStyle.BG_CARD)
        top_row.pack(fill=tk.X)

        # 점수 표시
        score_frame = tk.Frame(top_row, bg=ModernStyle.BG_CARD)
        score_frame.pack(side=tk.LEFT)

        tk.Label(
            score_frame,
            text="점수",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_CARD
        ).pack(anchor=tk.W)

        self.score_label = tk.Label(
            score_frame,
            text="0/100",
            font=(ModernStyle.FONT_FAMILY, 28, "bold"),
            fg=ModernStyle.ACCENT,
            bg=ModernStyle.BG_CARD
        )
        self.score_label.pack(anchor=tk.W)

        # 모드 표시
        mode_frame = tk.Frame(top_row, bg=ModernStyle.BG_CARD)
        mode_frame.pack(side=tk.LEFT, padx=(40, 0))

        tk.Label(
            mode_frame,
            text="모드",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_CARD
        ).pack(anchor=tk.W)

        self.mode_label = tk.Label(
            mode_frame,
            text="대기 중",
            font=ModernStyle.FONT_SUBTITLE,
            fg=ModernStyle.INFO,
            bg=ModernStyle.BG_CARD
        )
        self.mode_label.pack(anchor=tk.W)

        # 질문 횟수
        count_frame = tk.Frame(top_row, bg=ModernStyle.BG_CARD)
        count_frame.pack(side=tk.LEFT, padx=(40, 0))

        tk.Label(
            count_frame,
            text="질문 횟수",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_CARD
        ).pack(anchor=tk.W)

        self.count_label = tk.Label(
            count_frame,
            text="0/5",
            font=ModernStyle.FONT_SUBTITLE,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_CARD
        )
        self.count_label.pack(anchor=tk.W)

        # 프로그레스바
        progress_frame = tk.Frame(card_frame, bg=ModernStyle.BG_CARD)
        progress_frame.pack(fill=tk.X, pady=(15, 0))

        self.progress = ttk.Progressbar(
            progress_frame,
            style="Custom.Horizontal.TProgressbar",
            length=100,
            mode='determinate',
            maximum=100
        )
        self.progress.pack(fill=tk.X)

    def _create_prompt_section(self, parent):
        """프롬프트 입력 영역"""
        prompt_frame = tk.Frame(parent, bg=ModernStyle.BG_PRIMARY)
        prompt_frame.pack(fill=tk.X, pady=(0, 15))

        # 레이블
        tk.Label(
            prompt_frame,
            text="📝 프롬프트 입력",
            font=ModernStyle.FONT_SUBTITLE,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_PRIMARY
        ).pack(anchor=tk.W, pady=(0, 8))

        # 텍스트 입력
        self.prompt_input = scrolledtext.ScrolledText(
            prompt_frame,
            height=4,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_SECONDARY,
            fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=10,
            wrap=tk.WORD
        )
        self.prompt_input.pack(fill=tk.X)
        self.prompt_input.insert(tk.END, "최적화할 프롬프트를 입력하세요...")
        self.prompt_input.bind("<FocusIn>", self._on_prompt_focus_in)
        self.prompt_input.bind("<FocusOut>", self._on_prompt_focus_out)

        # 시작 버튼
        self.start_btn = tk.Button(
            prompt_frame,
            text="🚀 분석 시작",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.ACCENT,
            fg=ModernStyle.TEXT_PRIMARY,
            activebackground=ModernStyle.ACCENT_HOVER,
            activeforeground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2",
            command=self._start_analysis
        )
        self.start_btn.pack(anchor=tk.E, pady=(10, 0))

    def _create_options_section(self, parent):
        """선택지 영역"""
        self.options_frame = tk.Frame(parent, bg=ModernStyle.BG_PRIMARY)
        self.options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 질문 레이블
        self.question_label = tk.Label(
            self.options_frame,
            text="",
            font=ModernStyle.FONT_SUBTITLE,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_PRIMARY,
            wraplength=800,
            justify=tk.LEFT
        )
        self.question_label.pack(anchor=tk.W, pady=(0, 15))

        # 선택지 버튼 컨테이너
        self.buttons_container = tk.Frame(self.options_frame, bg=ModernStyle.BG_PRIMARY)
        self.buttons_container.pack(fill=tk.X)

        # 직접 입력 필드 (숨김)
        self.direct_input_frame = tk.Frame(self.options_frame, bg=ModernStyle.BG_PRIMARY)

        tk.Label(
            self.direct_input_frame,
            text="✏️ 추가할 내용을 입력하세요:",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_PRIMARY
        ).pack(anchor=tk.W, pady=(10, 5))

        self.direct_input_entry = tk.Entry(
            self.direct_input_frame,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_SECONDARY,
            fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT
        )
        self.direct_input_entry.pack(fill=tk.X, ipady=10, pady=(0, 10))

        self.submit_direct_btn = tk.Button(
            self.direct_input_frame,
            text="제출",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.SUCCESS,
            fg=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._submit_direct_input
        )
        self.submit_direct_btn.pack(anchor=tk.E)

        # 초기에는 숨김
        self.options_frame.pack_forget()

    def _create_result_section(self, parent):
        """결과 영역"""
        self.result_frame = tk.Frame(parent, bg=ModernStyle.BG_CARD, padx=20, pady=15)

        # 결과 헤더
        tk.Label(
            self.result_frame,
            text="🎯 최적화된 프롬프트",
            font=ModernStyle.FONT_SUBTITLE,
            fg=ModernStyle.SUCCESS,
            bg=ModernStyle.BG_CARD
        ).pack(anchor=tk.W, pady=(0, 10))

        # 결과 텍스트
        self.result_text = scrolledtext.ScrolledText(
            self.result_frame,
            height=5,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_SECONDARY,
            fg=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=10,
            wrap=tk.WORD
        )
        self.result_text.pack(fill=tk.X)

        # 실행 버튼
        self.execute_btn = tk.Button(
            self.result_frame,
            text="💬 이 프롬프트로 채팅하기",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.SUCCESS,
            fg=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2",
            command=self._execute_chat
        )
        self.execute_btn.pack(anchor=tk.E, pady=(15, 0))

        # 초기에는 숨김
        self.result_frame.pack_forget()

    def _create_bottom_buttons(self, parent):
        """하단 버튼"""
        bottom_frame = tk.Frame(parent, bg=ModernStyle.BG_PRIMARY)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        # 리셋 버튼
        self.reset_btn = tk.Button(
            bottom_frame,
            text="🔄 초기화",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_SECONDARY,
            fg=ModernStyle.TEXT_SECONDARY,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self._reset
        )
        self.reset_btn.pack(side=tk.LEFT)

        # 상태 레이블
        self.status_label = tk.Label(
            bottom_frame,
            text="준비됨",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_MUTED,
            bg=ModernStyle.BG_PRIMARY
        )
        self.status_label.pack(side=tk.RIGHT)

    def _on_prompt_focus_in(self, event):
        """프롬프트 입력 포커스 인"""
        if self.prompt_input.get("1.0", tk.END).strip() == "최적화할 프롬프트를 입력하세요...":
            self.prompt_input.delete("1.0", tk.END)

    def _on_prompt_focus_out(self, event):
        """프롬프트 입력 포커스 아웃"""
        if not self.prompt_input.get("1.0", tk.END).strip():
            self.prompt_input.insert(tk.END, "최적화할 프롬프트를 입력하세요...")

    def _start_analysis(self):
        """분석 시작"""
        prompt = self.prompt_input.get("1.0", tk.END).strip()

        if not prompt or prompt == "최적화할 프롬프트를 입력하세요...":
            messagebox.showwarning("입력 필요", "프롬프트를 입력해주세요.")
            return

        if not self.llm:
            messagebox.showerror("API 키 오류", "OPENAI_API_KEY가 설정되지 않았습니다.")
            return

        self.current_prompt = prompt
        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED, text="분석 중...")
        self.status_label.config(text="분석 중...", fg=ModernStyle.WARNING)

        # 별도 스레드에서 분석 실행
        threading.Thread(target=self._analyze_prompt, daemon=True).start()

    def _analyze_prompt(self):
        """프롬프트 분석 (별도 스레드)"""
        try:
            # 점수 평가
            score_prompt = f"""다음 프롬프트의 품질을 0-100점으로 평가해주세요.

프롬프트: {self.current_prompt}

평가 기준:
1. 명확성: 요청이 구체적이고 명확한가?
2. 맥락: 충분한 배경 정보가 제공되었는가?
3. 목표: 원하는 결과물이 분명한가?
4. 제약조건: 필요한 제한사항이 명시되었는가?

점수만 숫자로 답해주세요."""

            result = self.llm.invoke(score_prompt)
            score = int(''.join(filter(str.isdigit, result.content[:10])))
            score = max(0, min(100, score))

            self.score = score

            # UI 업데이트 (메인 스레드에서)
            self.root.after(0, lambda: self._update_after_analysis(score))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

    def _update_after_analysis(self, score):
        """분석 후 UI 업데이트"""
        self.score_label.config(text=f"{score}/100")
        self.progress['value'] = score

        # 점수에 따른 색상
        if score >= 90:
            self.score_label.config(fg=ModernStyle.SUCCESS)
            self._show_completion()
        elif score >= 60:
            self.score_label.config(fg=ModernStyle.WARNING)
            self.mode = "multiple_choice"
            self.mode_label.config(text="객관식 모드", fg=ModernStyle.WARNING)
            self._show_multiple_choice()
        else:
            self.score_label.config(fg=ModernStyle.ACCENT)
            self.mode = "direct_input"
            self.mode_label.config(text="직접 입력 모드", fg=ModernStyle.ACCENT)
            self._show_direct_input()

        self.start_btn.config(state=tk.NORMAL, text="🚀 분석 시작")
        self.status_label.config(text="분석 완료", fg=ModernStyle.SUCCESS)
        self.is_processing = False

    def _show_direct_input(self):
        """직접 입력 모드 표시"""
        self.options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.question_label.config(
            text="❓ 프롬프트 보충이 필요합니다. 아래에서 추가할 정보 유형을 선택하거나 직접 입력하세요."
        )

        # 기존 버튼 제거
        for widget in self.buttons_container.winfo_children():
            widget.destroy()

        # 선택 버튼 생성
        options = [
            ("🎯 목적/용도 추가", "이 프롬프트의 목적이나 사용 용도를 명시"),
            ("👥 대상/독자 지정", "결과물의 대상 독자나 사용자를 지정"),
            ("📋 형식/포맷 명시", "원하는 출력 형식이나 포맷을 지정"),
            ("⚙️ 제약조건 추가", "길이, 스타일, 기술 수준 등 제한사항 명시")
        ]

        for i, (label, desc) in enumerate(options):
            btn_frame = tk.Frame(self.buttons_container, bg=ModernStyle.BG_SECONDARY, padx=15, pady=12)
            btn_frame.pack(fill=tk.X, pady=5)
            btn_frame.bind("<Button-1>", lambda e, l=label: self._select_option(l))
            btn_frame.bind("<Enter>", lambda e, f=btn_frame: f.config(bg=ModernStyle.BG_CARD))
            btn_frame.bind("<Leave>", lambda e, f=btn_frame: f.config(bg=ModernStyle.BG_SECONDARY))

            tk.Label(
                btn_frame,
                text=label,
                font=ModernStyle.FONT_BODY,
                fg=ModernStyle.TEXT_PRIMARY,
                bg=ModernStyle.BG_SECONDARY,
                cursor="hand2"
            ).pack(anchor=tk.W)

            tk.Label(
                btn_frame,
                text=desc,
                font=ModernStyle.FONT_SMALL,
                fg=ModernStyle.TEXT_SECONDARY,
                bg=ModernStyle.BG_SECONDARY,
                cursor="hand2"
            ).pack(anchor=tk.W)

            # 이벤트 전파
            for child in btn_frame.winfo_children():
                child.bind("<Button-1>", lambda e, l=label: self._select_option(l))
                child.bind("<Enter>", lambda e, f=btn_frame: f.config(bg=ModernStyle.BG_CARD))
                child.bind("<Leave>", lambda e, f=btn_frame: f.config(bg=ModernStyle.BG_SECONDARY))

        # 직접 입력 필드 표시
        self.direct_input_frame.pack(fill=tk.X, pady=(15, 0))

    def _show_multiple_choice(self):
        """객관식 모드 표시"""
        self.question_count += 1
        self.count_label.config(text=f"{self.question_count}/5")

        if self.question_count > 5:
            self._show_completion()
            return

        self.options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.direct_input_frame.pack_forget()

        # 질문 생성
        threading.Thread(target=self._generate_question, daemon=True).start()

    def _generate_question(self):
        """객관식 질문 생성"""
        try:
            question_prompt = f"""다음 프롬프트를 개선하기 위한 객관식 질문을 만들어주세요.

프롬프트: {self.current_prompt}

다음 형식으로 답해주세요:
질문: (프롬프트 개선을 위한 질문)
1. (선택지1)
2. (선택지2)
3. (선택지3)
4. (선택지4)"""

            result = self.llm.invoke(question_prompt)
            lines = result.content.strip().split('\n')

            question = lines[0].replace("질문:", "").strip() if lines else "어떤 옵션을 선택하시겠습니까?"
            options = []
            for line in lines[1:]:
                if line.strip() and line[0].isdigit():
                    opt = line.split('.', 1)[-1].strip() if '.' in line else line.strip()
                    options.append(opt)

            if len(options) < 4:
                options = ["옵션 1", "옵션 2", "옵션 3", "옵션 4"]

            self.root.after(0, lambda: self._display_question(question, options[:4]))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

    def _display_question(self, question, options):
        """질문 및 선택지 표시"""
        self.question_label.config(text=f"❓ {question}")

        # 기존 버튼 제거
        for widget in self.buttons_container.winfo_children():
            widget.destroy()

        # 선택지 버튼 (2x2 그리드)
        for i, opt in enumerate(options):
            row = i // 2
            col = i % 2

            btn = tk.Button(
                self.buttons_container,
                text=f"{i+1}. {opt}",
                font=ModernStyle.FONT_BODY,
                bg=ModernStyle.BG_SECONDARY,
                fg=ModernStyle.TEXT_PRIMARY,
                activebackground=ModernStyle.BG_CARD,
                activeforeground=ModernStyle.TEXT_PRIMARY,
                relief=tk.FLAT,
                padx=20,
                pady=15,
                cursor="hand2",
                anchor=tk.W,
                command=lambda o=opt: self._select_option(o)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # 그리드 설정
        self.buttons_container.grid_columnconfigure(0, weight=1)
        self.buttons_container.grid_columnconfigure(1, weight=1)

    def _select_option(self, option):
        """선택지 선택"""
        self.status_label.config(text="프롬프트 개선 중...", fg=ModernStyle.WARNING)
        threading.Thread(target=lambda: self._refine_prompt(option), daemon=True).start()

    def _submit_direct_input(self):
        """직접 입력 제출"""
        text = self.direct_input_entry.get().strip()
        if text:
            self._select_option(text)
            self.direct_input_entry.delete(0, tk.END)

    def _refine_prompt(self, user_input):
        """프롬프트 개선"""
        try:
            refine_prompt = f"""다음 정보를 바탕으로 프롬프트를 더 구체적이고 명확하게 재작성해주세요.

기존 프롬프트: {self.current_prompt}
사용자 입력: {user_input}

개선된 프롬프트만 출력해주세요."""

            result = self.llm.invoke(refine_prompt)
            self.current_prompt = result.content.strip()

            # 재분석
            self.root.after(0, self._reanalyze)

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

    def _reanalyze(self):
        """재분석"""
        self.prompt_input.delete("1.0", tk.END)
        self.prompt_input.insert(tk.END, self.current_prompt)
        self._analyze_prompt()

    def _show_completion(self):
        """완료 표시"""
        self.options_frame.pack_forget()
        self.result_frame.pack(fill=tk.X, pady=(0, 15))

        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, self.current_prompt)
        self.result_text.config(state=tk.DISABLED)

        self.mode_label.config(text="완료!", fg=ModernStyle.SUCCESS)
        self.status_label.config(text="✨ 최적화 완료!", fg=ModernStyle.SUCCESS)

    def _execute_chat(self):
        """최종 프롬프트로 채팅"""
        self.status_label.config(text="LLM 응답 생성 중...", fg=ModernStyle.WARNING)
        self.execute_btn.config(state=tk.DISABLED)

        threading.Thread(target=self._get_chat_response, daemon=True).start()

    def _get_chat_response(self):
        """채팅 응답 생성"""
        try:
            result = self.llm.invoke(self.current_prompt)
            response = result.content

            self.root.after(0, lambda: self._show_chat_response(response))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

    def _show_chat_response(self, response):
        """채팅 응답 표시"""
        # 새 창에서 응답 표시
        response_window = tk.Toplevel(self.root)
        response_window.title("💬 LLM 응답")
        response_window.geometry("700x500")
        response_window.configure(bg=ModernStyle.BG_PRIMARY)

        tk.Label(
            response_window,
            text="💬 LLM 응답",
            font=ModernStyle.FONT_TITLE,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_PRIMARY
        ).pack(pady=20)

        response_text = scrolledtext.ScrolledText(
            response_window,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_SECONDARY,
            fg=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=10,
            wrap=tk.WORD
        )
        response_text.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        response_text.insert(tk.END, response)
        response_text.config(state=tk.DISABLED)

        self.execute_btn.config(state=tk.NORMAL)
        self.status_label.config(text="응답 생성 완료", fg=ModernStyle.SUCCESS)

    def _show_error(self, message):
        """에러 표시"""
        messagebox.showerror("오류", message)
        self.status_label.config(text="오류 발생", fg=ModernStyle.ACCENT)
        self.start_btn.config(state=tk.NORMAL, text="🚀 분석 시작")
        self.is_processing = False

    def _reset(self):
        """초기화"""
        self.current_prompt = ""
        self.score = 0
        self.question_count = 0
        self.mode = "direct_input"
        self.is_processing = False

        self.score_label.config(text="0/100", fg=ModernStyle.ACCENT)
        self.mode_label.config(text="대기 중", fg=ModernStyle.INFO)
        self.count_label.config(text="0/5")
        self.progress['value'] = 0

        self.prompt_input.config(state=tk.NORMAL)
        self.prompt_input.delete("1.0", tk.END)
        self.prompt_input.insert(tk.END, "최적화할 프롬프트를 입력하세요...")

        self.options_frame.pack_forget()
        self.result_frame.pack_forget()

        self.status_label.config(text="준비됨", fg=ModernStyle.TEXT_MUTED)

    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    app = PromptOptimizerGUI()
    app.run()


if __name__ == "__main__":
    main()
