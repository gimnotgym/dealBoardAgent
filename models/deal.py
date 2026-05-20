from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class MEDDICData:
    """MEDDIC 프레임워크 데이터 모델"""
    metrics: Optional[str] = None           # 측정 지표 / ROI 근거
    economic_buyer: Optional[str] = None    # 경제적 의사결정자
    decision_criteria: Optional[str] = None # 의사결정 기준
    decision_process: Optional[str] = None  # 의사결정 프로세스
    paper_process: Optional[str] = None     # 계약/서류 절차
    identify_pain: Optional[str] = None     # 핵심 Pain Point
    champion: Optional[str] = None          # 내부 지지자
    competition: Optional[str] = None       # 경쟁사 현황


@dataclass
class DealScoreBreakdown:
    """딜 스코어 세부 내역 (100점 만점)"""
    sales_maturity: int = 0    # 영업성숙도 (30점)
    activity: int = 0          # 활동성 (25점)
    meddic: int = 0            # MEDDIC 충족도 (25점)
    relationship: int = 0      # 관계성 (20점)

    @property
    def total(self) -> int:
        return self.sales_maturity + self.activity + self.meddic + self.relationship


@dataclass
class OpportunityUpdate:
    """Salesforce 사업기회 업데이트 데이터"""
    opportunity_id: Optional[str] = None
    opportunity_name: Optional[str] = None

    # MEDDIC 필드
    meddic: MEDDICData = field(default_factory=MEDDICData)

    # 스코어
    score: DealScoreBreakdown = field(default_factory=DealScoreBreakdown)

    # 기타 필드
    next_step: Optional[str] = None
    close_date: Optional[str] = None
    amount: Optional[float] = None
    stage: Optional[str] = None
    ax_yn: Optional[bool] = None            # AX 사업 여부
    sales_review_status: Optional[str] = None

    # 메타
    summary: str = ""                        # AI 분석 요약
    action_items: list = field(default_factory=list)  # 후속 액션
    source_type: str = ""                    # text / file / voice
    analyzed_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
