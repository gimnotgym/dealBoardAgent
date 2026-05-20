"""
SKAX Deal Board Agent - Streamlit UI
실행: streamlit run app.py
"""
import os
import sys
import streamlit as st
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from salesforce.sf_client import SFClient
from agent.deal_board_agent import DealBoardAgent
from processors.file_processor import extract_text_from_file
from processors.voice_processor import transcribe_audio, SUPPORTED_AUDIO

# ──────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="SKAX Deal Board Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# CSS 스타일
# ──────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2rem; font-weight: 700; color: #1a237e;
        border-bottom: 3px solid #e53935; padding-bottom: 0.5rem; margin-bottom: 1.5rem;
    }
    .score-card {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        border-radius: 12px; padding: 20px; color: white; text-align: center;
    }
    .score-big { font-size: 3.5rem; font-weight: 800; }
    .score-label { font-size: 0.9rem; opacity: 0.8; }
    .meddic-filled { background: #e8f5e9; border-left: 4px solid #43a047; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
    .meddic-empty  { background: #fff3e0; border-left: 4px solid #fb8c00; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
    .stage-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: 600; background: #e3f2fd; color: #1565c0;
    }
    .action-item {
        background: #f3e5f5; border-radius: 6px; padding: 8px 14px; margin: 4px 0;
        border-left: 3px solid #9c27b0;
    }
    .review-일반     { background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:12px; font-weight:600; }
    .review-관심     { background:#fff9c4; color:#f57f17; padding:3px 10px; border-radius:12px; font-weight:600; }
    .review-집중관리  { background:#fff3e0; color:#e65100; padding:3px 10px; border-radius:12px; font-weight:600; }
    .review-위험     { background:#ffebee; color:#c62828; padding:3px 10px; border-radius:12px; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# 공통 분석 실행 함수
# ──────────────────────────────────────────
def run_analysis(text: str, source_type: str):
    """Claude Agent 호출 및 스트리밍 결과 표시"""
    if not st.session_state.get("agent"):
        st.error("API 키를 먼저 설정해주세요 (사이드바 ⚙️ API 설정)")
        return

    opp = st.session_state.selected_opp
    st.markdown("---")
    st.markdown("### 🤖 AI 분석 결과")

    result_placeholder = st.empty()
    full_text = ""

    try:
        with st.spinner("Claude claude-opus-4-7 분석 중..."):
            gen = st.session_state.agent.analyze_stream(text, opp, source_type)
            update_result = None
            try:
                while True:
                    chunk = next(gen)
                    full_text += chunk
                    if "```json" not in full_text:
                        result_placeholder.markdown(full_text + "▌")
            except StopIteration as e:
                update_result = e.value
                result_placeholder.empty()

        if update_result is None:
            st.error("분석 결과를 받지 못했습니다.")
            return

        st.session_state.last_update = update_result
        st.session_state.analysis_done = True

        st.success(f"✅ 분석 완료 | Deal Score: **{update_result.score.total}점** | 소스: {source_type}")
        st.info("📊 **MEDDIC 현황** 탭에서 상세 결과를 확인하고 Salesforce에 반영할 수 있습니다.")

        if update_result.summary:
            st.markdown("**요약**")
            st.write(update_result.summary)

        if update_result.action_items:
            st.markdown("**추천 액션**")
            for item in update_result.action_items:
                st.markdown(f"• {item}")

        st.balloons()

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")


# ──────────────────────────────────────────
# 세션 상태 초기화
# ──────────────────────────────────────────
if "sf_client" not in st.session_state:
    st.session_state.sf_client = SFClient()
if "selected_opp" not in st.session_state:
    st.session_state.selected_opp = None
if "last_update" not in st.session_state:
    st.session_state.last_update = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "agent" not in st.session_state:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            st.session_state.agent = DealBoardAgent()
        except Exception:
            st.session_state.agent = None
    else:
        st.session_state.agent = None


# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Deal Board Agent")
    st.markdown("---")

    # API 키 설정
    with st.expander("⚙️ API 설정", expanded=not bool(os.getenv("ANTHROPIC_API_KEY"))):
        api_key_input = st.text_input(
            "Anthropic API Key",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            type="password",
            help="sk-ant-... 형식의 API 키를 입력하세요",
        )
        sf_mode_sel = st.selectbox("Salesforce 모드", ["mock (데모)", "live (실 연동)"])
        if st.button("설정 저장"):
            os.environ["ANTHROPIC_API_KEY"] = api_key_input
            os.environ["SF_MODE"] = "mock" if "mock" in sf_mode_sel else "live"
            try:
                st.session_state.agent = DealBoardAgent()
                st.session_state.sf_client = SFClient()
                st.success("✅ 저장 완료!")
            except Exception as e:
                st.error(f"오류: {e}")

    st.markdown("---")

    # 사업기회 선택
    st.markdown("### 📋 사업기회 선택")
    opps = st.session_state.sf_client.get_opportunities()
    opp_options = {f"{o['Name']} ({o['StageName']})": o for o in opps}
    selected_label = st.selectbox("사업기회", list(opp_options.keys()))
    if selected_label:
        # 사업기회가 바뀌면 분석 결과 초기화
        new_opp = opp_options[selected_label]
        if st.session_state.selected_opp and st.session_state.selected_opp.get("Id") != new_opp.get("Id"):
            st.session_state.last_update = None
            st.session_state.analysis_done = False
        st.session_state.selected_opp = new_opp

    # 선택된 딜 요약 카드
    if st.session_state.selected_opp:
        opp = st.session_state.selected_opp
        score = opp.get("DealScore__c", 0)
        score_color = "#4caf50" if score >= 70 else "#ff9800" if score >= 40 else "#f44336"
        st.markdown(f"""
        <div style="background:#f8f9fa; border-radius:10px; padding:14px; margin-top:10px;">
            <div style="font-size:0.85rem; color:#666;">현재 Deal Score</div>
            <div style="font-size:2.5rem; font-weight:800; color:{score_color};">{score}<span style="font-size:1rem;">점</span></div>
            <div style="font-size:0.8rem; color:#999;">{opp.get('SalesReviewStatus__c','')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    sf_mode_display = "🟡 Mock (데모)" if os.getenv("SF_MODE", "mock") == "mock" else "🟢 Live"
    st.markdown(f"**SF 모드**: {sf_mode_display}")
    st.markdown('<div style="font-size:0.75rem; color:#999; margin-top:20px;">SKAX Deal Board Agent v1.0<br>Powered by Claude claude-opus-4-7</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────
# 메인 컨텐츠
# ──────────────────────────────────────────
st.markdown('<div class="main-title">🎯 SKAX Deal Board Agent</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 MEDDIC 현황", "✍️ 텍스트 입력", "📎 파일 첨부", "🎙️ 음성 업로드"])


# ──────────────────────────────────────────
# TAB 1: MEDDIC 현황
# ──────────────────────────────────────────
with tab1:
    if not st.session_state.selected_opp:
        st.info("← 왼쪽에서 사업기회를 선택하세요")
    else:
        opp = st.session_state.selected_opp
        update = st.session_state.last_update

        col_left, col_right = st.columns([2, 1])

        with col_right:
            # 스코어 카드
            if update:
                score = update.score.total
            else:
                score = opp.get("DealScore__c", 0)
            score_color = "#4caf50" if score >= 70 else "#ff9800" if score >= 40 else "#f44336"
            st.markdown(f"""
            <div class="score-card">
                <div class="score-label">DEAL SCORE</div>
                <div class="score-big" style="color:{score_color};">{score}</div>
                <div class="score-label">/ 100점</div>
            </div>
            """, unsafe_allow_html=True)

            if update:
                st.markdown("#### 점수 세부 내역")
                score_items = [
                    ("영업성숙도", update.score.sales_maturity, 30),
                    ("활동성", update.score.activity, 25),
                    ("MEDDIC", update.score.meddic, 25),
                    ("관계성", update.score.relationship, 20),
                ]
                for lbl, val, mx in score_items:
                    pct = (val / mx * 100) if mx > 0 else 0
                    c = "#4caf50" if pct >= 70 else "#ff9800" if pct >= 40 else "#f44336"
                    st.markdown(f"""
                    <div style="margin:6px 0;">
                        <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
                            <span>{lbl}</span><span style="color:{c};">{val}/{mx}</span>
                        </div>
                        <div style="background:#eee; border-radius:4px; height:8px;">
                            <div style="background:{c}; width:{pct:.0f}%; height:8px; border-radius:4px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # 기본 정보
            st.markdown("#### 기본 정보")
            review_status = (update.sales_review_status if update and update.sales_review_status
                             else opp.get("SalesReviewStatus__c", "일반"))
            st.markdown(f'<span class="review-{review_status}">{review_status}</span>', unsafe_allow_html=True)
            if opp.get("Amount"):
                st.metric("예상 금액", f"₩{opp['Amount']:,.0f}")
            if opp.get("CloseDate"):
                st.metric("예상 마감일", opp["CloseDate"])

        with col_left:
            st.markdown(f"### {opp['Name']}")
            stage = (update.stage if update and update.stage else opp.get("StageName", ""))
            st.markdown(f'<span class="stage-badge">📍 {stage}</span>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            if update and update.summary:
                st.markdown("#### 🤖 AI 분석 요약")
                st.info(update.summary)

            # MEDDIC 항목 표시
            st.markdown("#### MEDDIC 항목")

            def get_meddic_val(update_obj, field_attr, sf_opp, sf_key):
                if update_obj:
                    val = getattr(update_obj.meddic, field_attr, None)
                    if val:
                        return val
                return sf_opp.get(sf_key, "") or ""

            meddic_fields = [
                ("📊 Metrics (측정지표)", "metrics", "MEDDIC_Metrics__c"),
                ("💼 Economic Buyer (의사결정자)", "economic_buyer", "MEDDIC_EB__c"),
                ("✅ Decision Criteria (선택기준)", "decision_criteria", "MEDDIC_DC__c"),
                ("🔄 Decision Process (결정절차)", "decision_process", "MEDDIC_DP__c"),
                ("📄 Paper Process (계약절차)", "paper_process", "MEDDIC_Paper__c"),
                ("💡 Identify Pain (핵심고충)", "identify_pain", "MEDDIC_Pain__c"),
                ("🏆 Champion (내부지지자)", "champion", "MEDDIC_Champion__c"),
                ("⚔️ Competition (경쟁현황)", "competition", "MEDDIC_Comp__c"),
            ]

            for label, attr, sf_key in meddic_fields:
                value = get_meddic_val(update, attr, opp, sf_key)
                if value:
                    st.markdown(f'<div class="meddic-filled"><strong>{label}</strong><br><span style="font-size:0.9rem;">{value}</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="meddic-empty"><strong>{label}</strong> &nbsp; <em style="color:#bbb; font-size:0.85rem;">미확인 — 텍스트/파일/음성 탭에서 분석 후 채워집니다</em></div>', unsafe_allow_html=True)

            # 추천 액션
            if update and update.action_items:
                st.markdown("#### 📌 추천 액션")
                for item in update.action_items:
                    st.markdown(f'<div class="action-item">• {item}</div>', unsafe_allow_html=True)

            # SF 반영 버튼
            if update:
                st.markdown("---")
                col_b1, col_b2, col_b3 = st.columns(3)
                with col_b1:
                    if st.button("💾 Salesforce 반영", type="primary", use_container_width=True):
                        with st.spinner("Salesforce 업데이트 중..."):
                            result = st.session_state.sf_client.update_opportunity(opp["Id"], update)
                            chatter_body = (
                                f"[AI 분석 업데이트] {update.analyzed_at}\n\n"
                                f"{update.summary}\n\n"
                                f"Deal Score: {update.score.total}점\n"
                                f"업데이트 항목: {', '.join(result.get('updated_fields', []))}"
                            )
                            st.session_state.sf_client.add_chatter_post(opp["Id"], chatter_body)
                            refreshed = st.session_state.sf_client.get_opportunity(opp["Id"])
                            if refreshed:
                                st.session_state.selected_opp = refreshed
                        mode_tag = "🟡 Mock" if result["mode"] == "mock" else "🟢 Live"
                        updated = ", ".join(result.get("updated_fields", []))
                        st.success(f"{mode_tag} 업데이트 완료!\n업데이트 필드: {updated}")
                with col_b2:
                    if st.button("🔄 분석 초기화", use_container_width=True):
                        st.session_state.last_update = None
                        st.session_state.analysis_done = False
                        st.rerun()
                with col_b3:
                    if update.next_step:
                        st.markdown(f"**다음 단계**: {update.next_step}")


# ──────────────────────────────────────────
# TAB 2: 텍스트 입력
# ──────────────────────────────────────────
with tab2:
    st.markdown("### ✍️ 텍스트로 분석하기")
    st.markdown("회의 내용, 통화 요약, 고객 미팅 기록 등을 자유롭게 입력하세요.")

    if not st.session_state.selected_opp:
        st.warning("← 먼저 사이드바에서 사업기회를 선택하세요")
    else:
        input_type = st.radio(
            "입력 유형",
            ["📞 통화 요약", "🤝 고객 미팅 기록", "📧 이메일/메시지", "📝 기타"],
            horizontal=True,
            key="text_input_type",
        )

        placeholder_texts = {
            "📞 통화 요약": (
                "예) 오늘 삼성전자 김팀장님과 30분 통화. "
                "현재 레거시 ERP 시스템 교체를 검토 중이며 Q4 예산 승인 예정. "
                "ROI 20% 이상이면 진행 의지 있음. MS Azure도 검토 중..."
            ),
            "🤝 고객 미팅 기록": (
                "예) 2024-06-15 현대차 본사 미팅. "
                "참석: 이부회장(CTO), 박본부장(데이터혁신본부). "
                "주요 논의: 실시간 데이터 처리 플랫폼 필요성..."
            ),
            "📧 이메일/메시지": "예) 고객사로부터 받은 이메일 내용을 여기에 붙여넣으세요...",
            "📝 기타": "분석할 내용을 자유롭게 입력하세요...",
        }

        user_text = st.text_area(
            "내용 입력",
            height=280,
            placeholder=placeholder_texts.get(input_type, ""),
            key="text_input_area",
        )

        char_count = len(user_text) if user_text else 0
        st.caption(f"{char_count:,}자 입력됨")

        if st.button(
            "🤖 AI 분석 시작",
            type="primary",
            disabled=not bool(user_text and user_text.strip()),
            key="text_analyze_btn",
        ):
            run_analysis(user_text.strip(), input_type.split()[1] if " " in input_type else input_type)


# ──────────────────────────────────────────
# TAB 3: 파일 첨부
# ──────────────────────────────────────────
with tab3:
    st.markdown("### 📎 파일 첨부로 분석하기")
    st.markdown("회의록, 미팅 자료, 통화 기록 파일을 업로드하세요.")

    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    with col_info1:
        st.markdown("📄 **PDF**\n회의록, 제안서")
    with col_info2:
        st.markdown("📝 **DOCX**\nWord 문서")
    with col_info3:
        st.markdown("📋 **TXT**\n텍스트 파일")
    with col_info4:
        st.markdown("🖼️ **JPG/PNG**\n화이트보드, 메모 사진")

    if not st.session_state.selected_opp:
        st.warning("← 먼저 사이드바에서 사업기회를 선택하세요")
    else:
        uploaded_file = st.file_uploader(
            "파일 선택 (PDF, DOCX, TXT, JPG, PNG)",
            type=["pdf", "docx", "txt", "jpg", "jpeg", "png"],
            key="file_uploader",
        )

        if uploaded_file:
            file_size_kb = len(uploaded_file.getvalue()) / 1024
            st.markdown(f"**파일**: `{uploaded_file.name}` ({file_size_kb:.1f} KB)")

            with st.spinner(f"📄 {uploaded_file.name} 텍스트 추출 중..."):
                extracted_text = extract_text_from_file(uploaded_file)

            if extracted_text.startswith("["):
                st.error(extracted_text)
            else:
                st.success(f"✅ 텍스트 추출 완료 ({len(extracted_text):,}자)")
                with st.expander("📄 추출된 텍스트 미리보기 (앞 2,000자)"):
                    st.text(extracted_text[:2000] + ("..." if len(extracted_text) > 2000 else ""))

                if st.button("🤖 AI 분석 시작", type="primary", key="file_analyze_btn"):
                    run_analysis(extracted_text, f"파일({uploaded_file.name})")


# ──────────────────────────────────────────
# TAB 4: 음성 업로드
# ──────────────────────────────────────────
with tab4:
    st.markdown("### 🎙️ 음성 파일로 분석하기")

    ext_str = ", ".join(sorted(SUPPORTED_AUDIO))
    st.markdown(f"**지원 형식**: {ext_str}")
    st.info(
        "💡 음성 분석은 OpenAI Whisper 모델(로컬 실행)을 사용합니다.\n"
        "첫 실행 시 모델 다운로드(~150MB)가 필요하며 1~3분 소요됩니다."
    )

    if not st.session_state.selected_opp:
        st.warning("← 먼저 사이드바에서 사업기회를 선택하세요")
    else:
        audio_file = st.file_uploader(
            "음성 파일 선택",
            type=["mp3", "mp4", "wav", "m4a", "ogg", "flac"],
            key="audio_uploader",
        )

        if audio_file:
            file_size_mb = len(audio_file.getvalue()) / 1024 / 1024
            st.markdown(f"**파일**: `{audio_file.name}` ({file_size_mb:.1f} MB)")
            st.audio(audio_file)

            if st.button(
                "🎙️ 음성 변환 → AI 분석",
                type="primary",
                key="voice_analyze_btn",
            ):
                with st.spinner("🎙️ 음성 인식 중... (파일 크기에 따라 1~3분 소요)"):
                    transcript = transcribe_audio(audio_file)

                if transcript.startswith("["):
                    st.error(transcript)
                else:
                    st.success(f"✅ 음성 변환 완료 ({len(transcript):,}자)")
                    with st.expander("🗒️ 변환된 텍스트 (앞 2,000자)"):
                        st.text(transcript[:2000] + ("..." if len(transcript) > 2000 else ""))
                    run_analysis(transcript, f"음성({audio_file.name})")
