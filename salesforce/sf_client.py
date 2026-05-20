"""
Salesforce 연동 클라이언트
SF_MODE=mock  → 실제 API 호출 없이 로컬 딕셔너리로 시뮬레이션
SF_MODE=live  → simple-salesforce 사용
"""
import os
from typing import Optional
from models.deal import OpportunityUpdate

# ──────────────────────────────────────────
# Mock 데이터 (데모용 사업기회 목록)
# ──────────────────────────────────────────
MOCK_OPPORTUNITIES = {
    "OPP-001": {
        "Id": "OPP-001",
        "Name": "삼성전자 AI 플랫폼 구축",
        "StageName": "Proposal/Price Quote",
        "Amount": 1500000000,
        "CloseDate": "2024-09-30",
        "DealScore__c": 42,
        "MEDDIC_Metrics__c": "",
        "MEDDIC_EB__c": "",
        "MEDDIC_DC__c": "",
        "MEDDIC_DP__c": "",
        "MEDDIC_Paper__c": "",
        "MEDDIC_Pain__c": "레거시 시스템 비효율, AI 전환 필요",
        "MEDDIC_Champion__c": "IT혁신팀 김팀장",
        "MEDDIC_Comp__c": "Microsoft, AWS",
        "AX_YN__c": True,
        "SalesReviewStatus__c": "일반",
        "NextStep": "",
        "AccountId": "ACC-001",
        "AccountName": "삼성전자",
    },
    "OPP-002": {
        "Id": "OPP-002",
        "Name": "LG화학 ERP 고도화",
        "StageName": "Needs Analysis",
        "Amount": 800000000,
        "CloseDate": "2024-12-31",
        "DealScore__c": 28,
        "MEDDIC_Metrics__c": "",
        "MEDDIC_EB__c": "",
        "MEDDIC_DC__c": "",
        "MEDDIC_DP__c": "",
        "MEDDIC_Paper__c": "",
        "MEDDIC_Pain__c": "",
        "MEDDIC_Champion__c": "",
        "MEDDIC_Comp__c": "SAP, Oracle",
        "AX_YN__c": False,
        "SalesReviewStatus__c": "관심",
        "NextStep": "",
        "AccountId": "ACC-002",
        "AccountName": "LG화학",
    },
    "OPP-003": {
        "Id": "OPP-003",
        "Name": "현대자동차 데이터 분석 플랫폼",
        "StageName": "Value Proposition",
        "Amount": 2000000000,
        "CloseDate": "2024-08-15",
        "DealScore__c": 61,
        "MEDDIC_Metrics__c": "생산효율 15% 향상, 불량률 30% 감소 목표",
        "MEDDIC_EB__c": "CTO 이부회장",
        "MEDDIC_DC__c": "클라우드 네이티브, 실시간 처리 필수",
        "MEDDIC_DP__c": "기술검토(완료) → 경영진 승인 → 계약",
        "MEDDIC_Paper__c": "",
        "MEDDIC_Pain__c": "실시간 생산 데이터 분석 불가, 의사결정 지연",
        "MEDDIC_Champion__c": "데이터혁신본부 박본부장",
        "MEDDIC_Comp__c": "Databricks",
        "AX_YN__c": True,
        "SalesReviewStatus__c": "집중관리",
        "NextStep": "경영진 PT 일정 확정",
        "AccountId": "ACC-003",
        "AccountName": "현대자동차",
    },
}


class SFClient:
    def __init__(self):
        self.mode = os.getenv("SF_MODE", "mock").lower()
        self._sf = None
        if self.mode == "live":
            self._connect()

    def _connect(self):
        try:
            from simple_salesforce import Salesforce
            self._sf = Salesforce(
                username=os.getenv("SF_USERNAME"),
                password=os.getenv("SF_PASSWORD"),
                security_token=os.getenv("SF_SECURITY_TOKEN"),
                domain=os.getenv("SF_DOMAIN", "login"),
            )
        except Exception as e:
            print(f"[SF 연결 실패] {e} → mock 모드로 전환")
            self.mode = "mock"

    def get_opportunities(self) -> list[dict]:
        """사업기회 목록 조회"""
        if self.mode == "mock":
            return list(MOCK_OPPORTUNITIES.values())

        result = self._sf.query(
            "SELECT Id, Name, StageName, Amount, CloseDate, DealScore__c, "
            "MEDDIC_Metrics__c, MEDDIC_EB__c, MEDDIC_DC__c, MEDDIC_DP__c, "
            "MEDDIC_Paper__c, MEDDIC_Pain__c, MEDDIC_Champion__c, MEDDIC_Comp__c, "
            "AX_YN__c, SalesReviewStatus__c, NextStep "
            "FROM Opportunity WHERE IsClosed = false ORDER BY CloseDate ASC LIMIT 50"
        )
        return result.get("records", [])

    def get_opportunity(self, opp_id: str) -> Optional[dict]:
        """특정 사업기회 조회"""
        if self.mode == "mock":
            return MOCK_OPPORTUNITIES.get(opp_id)

        return self._sf.Opportunity.get(opp_id)

    def update_opportunity(self, opp_id: str, update: OpportunityUpdate) -> dict:
        """사업기회 MEDDIC 및 스코어 업데이트"""
        payload = {}

        m = update.meddic
        if m.metrics:
            payload["MEDDIC_Metrics__c"] = m.metrics
        if m.economic_buyer:
            payload["MEDDIC_EB__c"] = m.economic_buyer
        if m.decision_criteria:
            payload["MEDDIC_DC__c"] = m.decision_criteria
        if m.decision_process:
            payload["MEDDIC_DP__c"] = m.decision_process
        if m.paper_process:
            payload["MEDDIC_Paper__c"] = m.paper_process
        if m.identify_pain:
            payload["MEDDIC_Pain__c"] = m.identify_pain
        if m.champion:
            payload["MEDDIC_Champion__c"] = m.champion
        if m.competition:
            payload["MEDDIC_Comp__c"] = m.competition

        if update.score.total > 0:
            payload["DealScore__c"] = update.score.total

        if update.next_step:
            payload["NextStep"] = update.next_step
        if update.stage:
            payload["StageName"] = update.stage
        if update.sales_review_status:
            payload["SalesReviewStatus__c"] = update.sales_review_status
        if update.ax_yn is not None:
            payload["AX_YN__c"] = update.ax_yn

        if self.mode == "mock":
            if opp_id in MOCK_OPPORTUNITIES:
                MOCK_OPPORTUNITIES[opp_id].update(payload)
            return {"success": True, "mode": "mock", "updated_fields": list(payload.keys())}

        self._sf.Opportunity.update(opp_id, payload)
        return {"success": True, "mode": "live", "updated_fields": list(payload.keys())}

    def add_chatter_post(self, opp_id: str, body: str) -> dict:
        """Chatter 피드 포스트 추가"""
        if self.mode == "mock":
            return {"success": True, "mode": "mock", "body": body[:50] + "..."}

        self._sf.FeedItem.create({
            "ParentId": opp_id,
            "Body": body,
            "Type": "TextPost",
        })
        return {"success": True, "mode": "live"}
