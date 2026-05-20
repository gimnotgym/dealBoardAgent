"""
SKAX Deal Board Agent - Claude claude-opus-4-7 기반 MEDDIC 분석 엔진
"""
import os
import json
import re
from typing import Generator
import anthropic
from models.deal import MEDDICData, DealScoreBreakdown, OpportunityUpdate

SYSTEM_PROMPT = """당신은 SKAX(SK Accenture)의 영업 전문 AI 에이전트입니다.
회의록, 통화 요약, 고객 미팅 내용을 분석하여 MEDDIC 프레임워크 기반으로 영업 기회를 평가합니다.

## 역할
- 입력된 텍스트에서 MEDDIC 각 항목을 추출합니다
- 딜 스코어를 산출합니다 (100점 만점)
- Salesforce 업데이트를 위한 구조화된 데이터를 생성합니다
- 다음 영업 액션을 제안합니다

## MEDDIC 프레임워크
- **Metrics (측정지표)**: 고객이 기대하는 정량적 성과/ROI
- **Economic Buyer (경제적 의사결정자)**: 예산 승인 권한자
- **Decision Criteria (의사결정 기준)**: 솔루션 선택 기준
- **Decision Process (의사결정 프로세스)**: 내부 결재/승인 절차
- **Paper Process (계약 프로세스)**: 계약서/발주서 진행 절차
- **Identify Pain (핵심 고충)**: 고객의 핵심 문제/니즈
- **Champion (내부 지지자)**: 내부에서 우리를 지지하는 담당자
- **Competition (경쟁 현황)**: 경쟁사 및 경쟁 상황

## 딜 스코어 산출 기준 (100점)
### 영업성숙도 (30점)
- Closed Won: 30점
- Negotiation/Review: 25점
- Value Proposition: 20점
- Proposal/Price Quote: 15점
- Needs Analysis: 10점
- Qualification: 5점
- Prospecting: 2점

### 활동성 (25점)
- 최근 7일 이내 접촉: 25점
- 최근 14일 이내: 18점
- 최근 30일 이내: 12점
- 최근 60일 이내: 6점
- 60일 초과: 2점
※ 텍스트에서 최근 활동 여부를 판단

### MEDDIC 충족도 (25점)
- 각 항목 확인 시 약 3점 (8개 항목)
- Pain + Champion 확인 시 보너스 +1

### 관계성 (20점)
- Key Account (S등급): 20점
- A등급: 15점
- B등급: 10점
- C등급: 5점
※ 텍스트에서 고객 중요도/관계 수준 판단

## 출력 형식
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

```json
{
  "meddic": {
    "metrics": "추출된 내용 또는 null",
    "economic_buyer": "추출된 내용 또는 null",
    "decision_criteria": "추출된 내용 또는 null",
    "decision_process": "추출된 내용 또는 null",
    "paper_process": "추출된 내용 또는 null",
    "identify_pain": "추출된 내용 또는 null",
    "champion": "추출된 내용 또는 null",
    "competition": "추출된 내용 또는 null"
  },
  "score": {
    "sales_maturity": 0,
    "activity": 0,
    "meddic": 0,
    "relationship": 0
  },
  "next_step": "추천 다음 단계",
  "stage": "Salesforce StageName 추천 (영어)",
  "ax_yn": true or false,
  "sales_review_status": "일반 or 관심 or 집중관리 or 위험",
  "summary": "3-5문장 요약",
  "action_items": ["액션1", "액션2", "액션3"]
}
```"""


class DealBoardAgent:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        self.client = anthropic.Anthropic(api_key=api_key)

    def analyze_stream(
        self,
        text: str,
        opportunity: dict | None = None,
        source_type: str = "text",
    ) -> Generator[str, None, OpportunityUpdate]:
        """
        텍스트를 분석하고 스트리밍으로 결과를 반환합니다.
        yield: 스트리밍 텍스트 청크
        return: OpportunityUpdate 객체 (StopIteration.value)
        """
        context = ""
        if opportunity:
            context = f"""
## 현재 사업기회 정보
- 사업기회명: {opportunity.get('Name', '')}
- 현재 단계: {opportunity.get('StageName', '')}
- 현재 스코어: {opportunity.get('DealScore__c', 0)}점
- 현재 Pain: {opportunity.get('MEDDIC_Pain__c', '(없음)')}
- 현재 Champion: {opportunity.get('MEDDIC_Champion__c', '(없음)')}
- 현재 경쟁사: {opportunity.get('MEDDIC_Comp__c', '(없음)')}

위 기존 정보를 참고하여 새 입력 내용으로 업데이트하세요.
"""

        user_message = f"""{context}
## 분석할 내용 (출처: {source_type})
{text}

위 내용을 분석하여 MEDDIC 항목을 추출하고 딜 스코어를 산출한 뒤, 지정된 JSON 형식으로만 응답하세요."""

        full_response = ""

        with self.client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text_chunk in stream.text_stream:
                full_response += text_chunk
                yield text_chunk

        return self._parse_response(full_response, source_type, opportunity)

    def _parse_response(
        self,
        raw: str,
        source_type: str,
        opportunity: dict | None,
    ) -> OpportunityUpdate:
        """Claude 응답 JSON을 OpportunityUpdate로 변환"""
        # JSON 블록 추출
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 블록 없이 바로 JSON인 경우
            json_str = raw.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # 파싱 실패 시 최소한의 결과 반환
            return OpportunityUpdate(
                summary=raw[:500],
                source_type=source_type,
                opportunity_id=opportunity.get("Id") if opportunity else None,
            )

        m = data.get("meddic", {})
        meddic = MEDDICData(
            metrics=m.get("metrics"),
            economic_buyer=m.get("economic_buyer"),
            decision_criteria=m.get("decision_criteria"),
            decision_process=m.get("decision_process"),
            paper_process=m.get("paper_process"),
            identify_pain=m.get("identify_pain"),
            champion=m.get("champion"),
            competition=m.get("competition"),
        )

        s = data.get("score", {})
        score = DealScoreBreakdown(
            sales_maturity=int(s.get("sales_maturity", 0)),
            activity=int(s.get("activity", 0)),
            meddic=int(s.get("meddic", 0)),
            relationship=int(s.get("relationship", 0)),
        )

        return OpportunityUpdate(
            opportunity_id=opportunity.get("Id") if opportunity else None,
            opportunity_name=opportunity.get("Name") if opportunity else None,
            meddic=meddic,
            score=score,
            next_step=data.get("next_step"),
            stage=data.get("stage"),
            ax_yn=data.get("ax_yn"),
            sales_review_status=data.get("sales_review_status"),
            summary=data.get("summary", ""),
            action_items=data.get("action_items", []),
            source_type=source_type,
        )
