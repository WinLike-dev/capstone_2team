import json
from pathlib import Path


def make_chunk(
    *,
    source: str,
    category: str,
    subtopic: str,
    chunk_title: str,
    text: str,
    year: int | str,
    evidence_type: str,
    population: str,
    use_case: str,
    tags: list[str],
) -> dict:
    merged_tags = list(
        dict.fromkeys(
            [
                category,
                f"subtopic:{subtopic}",
                f"evidence:{evidence_type}",
                f"population:{population}",
                f"use_case:{use_case}",
                *tags,
            ]
        )
    )
    return {
        "source": source,
        "category": category,
        "subtopic": subtopic,
        "chunk_title": chunk_title,
        "text": text,
        "year": year,
        "evidence_type": evidence_type,
        "population": population,
        "use_case": use_case,
        "tags": merged_tags,
    }


def build_dataset() -> list[dict]:
    items: list[dict] = []

    def add(**kwargs):
        items.append(make_chunk(**kwargs))

    source = "ACSM Resistance Training Position Stand (2026)"
    category = "workout_resistance_guidelines"
    common = dict(source=source, category=category, year=2026, evidence_type="guideline", population="general_adult")
    add(subtopic="overview", chunk_title="저항운동 처방 개요", use_case="program_design",
        tags=["저항운동", "운동계획", "초보자", "중급자"],
        text="ACSM 저항운동 가이드는 운동 목적과 숙련도에 따라 강도, 볼륨, 빈도, 휴식을 조절하라고 본다. 근력, 근비대, 파워는 같은 저항운동이라도 처방 목표가 다르므로 한 가지 규칙으로 모두 해결하지 않는다. 프로그램을 설계할 때는 안전성, 기술 숙련, 회복 능력을 먼저 확인한 뒤 세부 수치를 정한다.", **common)
    add(subtopic="beginner", chunk_title="초보자 시작 원칙", use_case="novice_programming",
        tags=["초보자", "전신운동", "빈도", "기술숙련"],
        text="초보자는 전신 위주의 기본 동작을 주 2~3회 반복하면서 기술 습득과 회복 적응을 우선한다. 각 세션에서 주요 근육군을 다루되, 실패 지점까지 몰아붙이기보다 동작 품질이 유지되는 범위에서 세트 수를 조절하는 편이 안전하다. 처음에는 과도한 분할보다 일관된 반복 노출이 더 중요하다.", **common)
    add(subtopic="intermediate_advanced", chunk_title="중급자와 고급자 처방", use_case="intermediate_programming",
        tags=["중급자", "고급자", "분할루틴", "점진과부하"],
        text="중급자와 고급자는 부위별 분할, 피로 분산, 운동 변형을 더 적극적으로 활용할 수 있다. 다만 숙련도가 높을수록 무조건 볼륨을 늘리는 것이 아니라, 수행 질을 유지하면서 주당 자극량을 관리해야 한다. 고강도 세션과 회복 세션을 섞어 누적 피로를 통제하는 것이 장기 성과에 유리하다.", **common)
    add(subtopic="hypertrophy", chunk_title="근비대 목표의 기본 원리", use_case="hypertrophy_programming",
        tags=["근비대", "볼륨", "빈도", "세트수"],
        text="근비대 목표에서는 중간 이상 강도의 부하를 사용하면서 주당 충분한 세트 수를 확보하는 것이 핵심이다. 한 번에 지나치게 많은 세트를 넣기보다 주간 단위로 자극량을 분배하면 수행 질과 회복을 함께 관리하기 쉽다. 운동 선택은 큰 근육군 복합운동을 축으로 하고, 부족한 부위를 보완 운동으로 메우는 방식이 효율적이다.", **common)
    add(subtopic="strength", chunk_title="근력 향상 처방 원칙", use_case="strength_programming",
        tags=["근력", "고중량", "휴식", "반복수"],
        text="근력 향상 목적에서는 상대적으로 높은 부하와 낮은 반복, 충분한 세트 간 휴식이 중요하다. 동일한 운동 기술을 반복적으로 연습해야 신경계 효율과 기술 정확도가 함께 올라간다. 보조운동은 약점 보완용으로 쓰되 메인 리프트의 질을 해치지 않는 범위에서 배치하는 것이 바람직하다.", **common)
    add(subtopic="power", chunk_title="파워 훈련 적용", use_case="power_programming",
        tags=["파워", "폭발적수행", "피로관리", "속도"],
        text="파워 훈련은 무게 자체보다 폭발적인 의도와 빠른 수축 속도가 중요하다. 피로가 누적된 상태에서는 출력이 떨어지므로, 파워 세션은 대개 신선한 상태에서 먼저 수행하는 편이 좋다. 반복수가 늘어날수록 속도 저하가 생기면 세트를 끊어 품질을 보존해야 한다.", **common)
    add(subtopic="older_adults", chunk_title="고령자 적용", use_case="older_adults",
        tags=["고령자", "기능유지", "균형", "안전"],
        text="고령자는 근력뿐 아니라 기능 유지와 낙상 예방이 중요한 목표가 된다. 저항운동은 큰 근육군, 자세 안정성, 일상 동작과 연결되는 패턴을 우선하고, 점진적으로 강도를 높여도 된다. 다만 통증, 균형 문제, 기저질환을 고려해 운동 범위와 속도를 조절해야 한다.", **common)
    add(subtopic="progression", chunk_title="점진과부하와 안전", use_case="program_adjustment",
        tags=["점진과부하", "안전", "부상예방", "회복"],
        text="프로그램 진행은 무게만 늘리는 방식이 아니라 세트 수, 빈도, 운동 범위, 기술 안정성을 함께 본다. 통증이 누적되거나 수행 질이 떨어지면 강도를 억지로 올리기보다 볼륨과 빈도를 먼저 조정하는 것이 안전하다. 회복이 부족한 상태에서 장기간 밀어붙이면 오히려 성과가 정체되기 쉽다.", **common)

    source = "NSCA Exercise Technique Manual for Resistance Training, 4th ed"
    category = "workout_technique"
    common = dict(source=source, category=category, year=2024, evidence_type="manual", population="general_adult")
    add(subtopic="squat_pattern", chunk_title="스쿼트 패턴", use_case="technique_cueing",
        tags=["스쿼트", "무릎", "고관절", "자세교정"],
        text="스쿼트 계열에서는 발의 지지, 무릎과 발끝의 정렬, 몸통의 안정성이 기본이다. 내려갈수록 허리가 말리거나 무릎이 안쪽으로 붕괴하면 부하 분산이 무너질 수 있다. 발 압력을 고르게 유지하고, 고관절과 무릎이 함께 굽혀지는 패턴을 만드는 것이 핵심이다.", **common)
    add(subtopic="hinge_pattern", chunk_title="힙힌지와 데드리프트", use_case="technique_cueing",
        tags=["데드리프트", "힙힌지", "척추중립", "햄스트링"],
        text="데드리프트와 힙힌지는 무릎보다 고관절의 접힘과 펴짐이 중심이 된다. 척추 중립을 유지하고 바벨이나 덤벨이 몸에서 과하게 멀어지지 않게 해야 허리 부담을 줄일 수 있다. 당기는 동작보다 세팅과 복압 형성이 먼저라는 점을 반복적으로 지도하는 것이 좋다.", **common)
    add(subtopic="horizontal_press", chunk_title="벤치프레스와 수평 미는 동작", use_case="technique_cueing",
        tags=["벤치프레스", "어깨", "견갑", "푸시"],
        text="벤치프레스에서는 견갑 안정과 발 지지가 출발점이다. 바 경로가 흔들리거나 팔꿈치가 과도하게 벌어지면 어깨 전면 부담이 커질 수 있다. 어깨를 고정한 상태에서 가슴, 삼두, 전면 어깨가 자연스럽게 협응하도록 큐를 단순화하는 것이 효과적이다.", **common)
    add(subtopic="horizontal_pull", chunk_title="로우와 수평 당기기", use_case="technique_cueing",
        tags=["로우", "등운동", "견갑후인", "풀"],
        text="로우 계열은 팔로만 당기지 않고 견갑 움직임과 등 상부의 수축을 함께 만들어야 한다. 허리를 흔들어 반동을 크게 쓰기 시작하면 목표 근육의 긴장 유지가 어려워질 수 있다. 시작 자세에서 몸통 각도와 손잡이 경로를 먼저 고정한 뒤 반복을 쌓는 편이 좋다.", **common)
    add(subtopic="overhead_press", chunk_title="오버헤드 프레스", use_case="technique_cueing",
        tags=["오버헤드프레스", "어깨안정성", "복압", "상지"],
        text="머리 위로 미는 동작은 어깨 가동성과 흉추 자세, 몸통 안정성이 함께 필요하다. 허리를 과하게 꺾어 보상하면 어깨와 요추에 부담이 커질 수 있다. 갈비뼈 과신전을 줄이고, 바가 정면에서 수직에 가깝게 움직이도록 지도하는 것이 좋다.", **common)
    add(subtopic="machine_setup", chunk_title="머신 사용과 세팅", use_case="machine_training",
        tags=["머신", "세팅", "관절정렬", "초보자"],
        text="머신은 자유중량보다 경로가 정해져 있지만, 시트 높이와 손잡이 위치가 맞지 않으면 관절 스트레스가 커질 수 있다. 초보자에게 머신을 쓸 때도 축 정렬과 가동범위 조절을 함께 교육해야 한다. 편한 무게보다 올바른 세팅을 먼저 확인하는 것이 중요하다.", **common)
    add(subtopic="spotting", chunk_title="보조자와 안전 확보", use_case="gym_safety",
        tags=["보조자", "스포팅", "안전", "실패반복"],
        text="보조자는 사용자를 대신 들어주는 사람이 아니라 실패 위험을 통제하는 사람이다. 특히 벤치프레스와 같은 고위험 리프트에서는 시작 전 도움 방식과 실패 신호를 미리 합의해야 한다. 예측하지 못한 잡아당김이나 과도한 개입은 오히려 자세를 무너뜨릴 수 있다.", **common)
    add(subtopic="common_errors", chunk_title="흔한 오류와 부상 기전", use_case="injury_prevention",
        tags=["오류교정", "부상예방", "무게욕심", "반동"],
        text="흔한 오류는 대개 과한 중량, 반동 사용, 불완전한 세팅에서 나온다. 통증이 생긴 뒤에야 자세를 고치기보다, 반복 중 흔들림과 정렬 붕괴를 초기 경고 신호로 보는 편이 좋다. 무게 증가와 기술 향상을 분리해서 생각하도록 코칭하는 것이 장기적으로 안전하다.", **common)

    source = "NSCA Essentials of Strength Training and Conditioning, 5th ed"
    category = "workout_program_design"
    common = dict(source=source, category=category, year=2024, evidence_type="textbook", population="general_adult")
    add(subtopic="periodization_overview", chunk_title="주기화 개요", use_case="program_design",
        tags=["주기화", "프로그램설계", "장기계획", "피크"],
        text="주기화는 한 주의 운동표가 아니라, 수주에서 수개월 동안 목표에 맞춰 자극을 배치하는 방식이다. 강도와 볼륨을 항상 동시에 올리기보다, 어떤 시기에는 기술과 볼륨을, 어떤 시기에는 강도와 성과를 우선한다. 장기 계획이 있으면 피로 누적을 예측하고 조절하기 쉬워진다.", **common)
    add(subtopic="linear", chunk_title="선형 주기화", use_case="program_design",
        tags=["선형주기화", "기초체력", "초보자", "중급자"],
        text="선형 주기화는 시간이 갈수록 강도를 높이고 볼륨을 줄이는 형태로 이해하면 쉽다. 목표가 명확하고 경험 수준이 낮은 사람에게는 구조가 단순해 적용하기 좋다. 다만 생활 피로가 큰 시기에는 너무 기계적으로 강도를 올리지 않도록 조절 여지를 남겨야 한다.", **common)
    add(subtopic="nonlinear", chunk_title="비선형 주기화", use_case="program_design",
        tags=["비선형주기화", "일일변동", "주간변동", "숙련자"],
        text="비선형 주기화는 같은 주 안에서도 고반복, 중간반복, 저반복 자극을 섞을 수 있다. 숙련자나 여러 목표를 동시에 관리해야 하는 상황에서 유연성이 크다. 다만 세션마다 의도가 분명해야 하고, 피로가 누적되는 패턴은 기록으로 점검해야 한다.", **common)
    add(subtopic="deload", chunk_title="디로딩 원칙", use_case="fatigue_management",
        tags=["디로딩", "피로관리", "회복", "감량주기"],
        text="디로딩은 무조건 쉬는 주가 아니라, 피로를 낮추면서 기술과 리듬을 유지하는 조절 주간이다. 보통 볼륨을 먼저 줄이고 필요하면 강도도 함께 낮춘다. 정체, 통증, 수면 저하, 수행 질 악화가 반복되면 디로딩을 계획적으로 넣는 편이 좋다.", **common)
    add(subtopic="fatigue", chunk_title="피로 누적 관리", use_case="fatigue_management",
        tags=["피로누적", "수면", "회복", "퍼포먼스"],
        text="수행 저하가 항상 의지 부족을 뜻하지는 않는다. 주기적인 피로 관리에는 수면, 근육통, 운동 속도, 세트 후 체감 난도 같은 지표를 함께 보는 편이 좋다. 피로가 큰데도 같은 자극을 강행하면 다음 세션의 기술 질과 적응 효율이 떨어질 수 있다.", **common)
    add(subtopic="training_log", chunk_title="훈련 일지 설계", use_case="tracking",
        tags=["운동일지", "기록", "RPE", "세트관리"],
        text="훈련 일지는 단순히 무게를 적는 표가 아니라 조정의 근거다. 세트 수, 반복수, 사용 중량, 체감 난도, 통증 여부를 같이 남기면 다음 주 계획 수정을 더 정확하게 할 수 있다. 기록이 쌓이면 어떤 부하에서 잘 반응하는지 패턴을 발견하기 쉬워진다.", **common)
    add(subtopic="progression_adjustment", chunk_title="진도 조정 규칙", use_case="program_adjustment",
        tags=["진도조정", "중량증가", "반복증가", "오토레귤레이션"],
        text="진도는 매번 중량을 올리는 방식으로만 만들지 않는다. 반복수 상한 도달, 세트 추가, 휴식 조절, 기술 안정성 향상도 모두 진행으로 볼 수 있다. 계획보다 몸 상태가 나쁜 날에는 자극 목표는 유지하되 무게를 조정하는 오토레귤레이션이 유용하다.", **common)
    add(subtopic="novice_vs_advanced", chunk_title="초보자와 고급자의 차이", use_case="program_design",
        tags=["초보자", "고급자", "회복능력", "분화"],
        text="초보자는 적은 자극에도 잘 적응하므로 프로그램을 단순하게 유지하는 편이 좋다. 고급자는 같은 자극에 익숙해져 변형과 세밀한 분배가 더 필요하지만, 동시에 회복 비용도 커진다. 경험 수준이 올라갈수록 복잡성보다 정밀성이 중요해진다.", **common)

    source = "Schoenfeld et al. (2017) Volume Meta-analysis"
    category = "hypertrophy_volume"
    common = dict(source=source, category=category, year=2017, evidence_type="meta_analysis", population="resistance_trained")
    add(subtopic="dose_response", chunk_title="볼륨과 근비대의 용량-반응", use_case="hypertrophy_programming",
        tags=["근비대", "볼륨", "메타분석", "주당세트"],
        text="이 메타분석은 주당 저항운동 볼륨이 근비대와 관련된 중요한 변수라는 점을 지지한다. 대체로 더 많은 유효 세트는 더 큰 근비대와 연결되지만, 개인의 회복 한계와 수행 질을 무시한 무조건적 증가를 뜻하지는 않는다. 볼륨은 늘릴수록 좋은 것이 아니라 감당 가능한 범위에서 높을수록 유리하다고 해석하는 편이 안전하다.", **common)
    add(subtopic="low_vs_high", chunk_title="낮은 볼륨과 높은 볼륨 비교", use_case="hypertrophy_programming",
        tags=["세트수", "저볼륨", "고볼륨", "근비대"],
        text="낮은 볼륨 루틴은 시간이 적게 들고 회복이 쉽지만, 일정 수준 이상에서는 근비대 자극이 부족해질 수 있다. 반대로 높은 볼륨 루틴은 성장 자극을 늘릴 수 있지만 수행 질 저하와 통증, 회복 문제를 함께 가져올 수 있다. 따라서 세트 수는 생활 피로와 운동 숙련도를 고려해 단계적으로 올리는 편이 좋다.", **common)
    add(subtopic="per_muscle_group", chunk_title="부위별 주당 볼륨 해석", use_case="hypertrophy_programming",
        tags=["부위별볼륨", "대근육", "소근육", "분할루틴"],
        text="부위별 주당 볼륨은 한 세션의 펌핑감보다 주간 총량으로 보는 편이 더 유용하다. 대근육군은 여러 복합운동에서 중복 자극을 받으므로 단순 세트 수 계산만으로 부족할 수 있고, 소근육은 중복 피로까지 고려해야 한다. 분할루틴 설계 시에는 직접 세트와 간접 세트를 함께 해석해야 한다.", **common)
    add(subtopic="practical_use", chunk_title="실무 적용 규칙", use_case="coaching",
        tags=["실무적용", "주간계획", "회복", "운동빈도"],
        text="실무적으로는 낮은 주당 세트로 시작해, 정체가 오면 세트 수를 소폭 늘리는 접근이 관리하기 쉽다. 세트 수를 늘렸는데 수행 질이 무너지면 빈도 조정이나 운동 선택 변경이 먼저일 수 있다. 볼륨 증가는 성과 신호와 회복 신호를 같이 확인하면서 진행해야 한다.", **common)

    source = "Schoenfeld et al. (2016) Frequency Meta-analysis"
    category = "hypertrophy_frequency"
    common = dict(source=source, category=category, year=2016, evidence_type="meta_analysis", population="resistance_trained")
    add(subtopic="frequency_vs_volume", chunk_title="빈도와 총볼륨의 관계", use_case="hypertrophy_programming",
        tags=["빈도", "주당횟수", "총볼륨", "메타분석"],
        text="빈도는 단독 변수라기보다 총볼륨을 어떻게 나눠 담는지와 함께 봐야 한다. 주당 총 세트가 같다면 빈도 차이의 효과는 생각보다 작을 수 있지만, 실제 현장에서는 빈도를 올리면 세션당 피로가 줄어 수행 질이 좋아지는 장점이 있다. 따라서 빈도는 회복과 세션 길이 관리 도구로 해석하는 것이 유용하다.", **common)
    add(subtopic="beginner", chunk_title="초보자의 빈도 설정", use_case="novice_programming",
        tags=["초보자", "전신루틴", "주당2회", "기술습득"],
        text="초보자는 같은 동작을 자주 연습하는 편이 기술 습득과 적응에 유리할 수 있다. 부위당 주 2회 이상 자극은 전신 루틴이나 상하체 분할로 구현하기 쉽다. 다만 빈도를 올렸다고 해서 매 세션을 고강도로 몰아야 하는 것은 아니다.", **common)
    add(subtopic="split_design", chunk_title="분할 설계와 빈도", use_case="split_programming",
        tags=["분할루틴", "주당빈도", "회복분산", "고급자"],
        text="고급자에게 빈도는 단순히 자주 한다는 뜻보다 자극을 세션 간에 분배한다는 의미가 크다. 한 번에 많은 세트를 몰아넣기보다 주당 여러 번 나눠 수행하면 메인 세트의 질을 유지하기 쉽다. 바쁜 일정에서는 빈도와 세션 길이의 균형을 맞추는 것이 핵심이다.", **common)
    add(subtopic="limitations", chunk_title="제한점과 해석 주의", use_case="evidence_interpretation",
        tags=["제한점", "개인차", "근비대", "회복능력"],
        text="빈도 연구는 대상자 수준, 총볼륨 통제, 운동 선택 차이에 따라 결과가 흔들릴 수 있다. 그래서 특정 빈도를 절대 정답처럼 적용하기보다, 같은 주당 자극을 더 잘 소화하게 만드는 빈도를 찾는 접근이 현실적이다. 개인차가 크므로 기록 기반 조정이 필요하다.", **common)

    source = "ACSM Guidelines for Exercise Testing and Prescription, 12th ed"
    category = "cardio_guidelines"
    common = dict(source=source, category=category, year=2024, evidence_type="guideline", population="general_adult")
    add(subtopic="fitt", chunk_title="FITT 기본 원칙", use_case="cardio_programming",
        tags=["유산소", "FITT", "빈도", "시간"],
        text="유산소 처방은 빈도, 강도, 시간, 유형을 함께 정하는 FITT 원칙으로 설계한다. 목적이 체력 향상인지 감량인지, 위험도가 높은지에 따라 같은 걷기나 자전거도 처방 방식이 달라진다. 프로그램은 항상 현재 체력과 회복 수준에서 시작해야 한다.", **common)
    add(subtopic="target_hr", chunk_title="목표 심박수 설정", use_case="cardio_programming",
        tags=["심박수", "목표심박수", "강도설정", "카보넨"],
        text="목표 심박수는 최대심박수 추정식이나 심박수 예비량 개념을 활용해 설정할 수 있다. 실제 현장에서는 심박수와 함께 자각적 운동강도, 말하기 가능 여부를 함께 확인해야 오차를 줄일 수 있다. 심박수 수치만 맹신하기보다 상황에 맞는 복수 지표를 사용하는 편이 좋다.", **common)
    add(subtopic="risk_screening", chunk_title="운동 전 위험도 확인", use_case="risk_screening",
        tags=["위험도평가", "PAR-Q", "심혈관", "운동전점검"],
        text="유산소 운동 전에는 증상, 병력, 약물 복용, 최근 활동 수준을 먼저 확인해야 한다. 특히 흉통, 어지럼, 호흡곤란, 조절되지 않는 고혈압이 있으면 강도 높은 유산소를 바로 시작하지 않는 편이 안전하다. 위험도 평가는 프로그램 시작 전뿐 아니라 중간 점검에도 필요하다.", **common)
    add(subtopic="novice_cardio", chunk_title="초보자 유산소 시작", use_case="novice_programming",
        tags=["초보자", "걷기", "저중강도", "운동습관"],
        text="초보자는 낮은 강도와 짧은 시간으로 시작해 주당 빈도를 서서히 높이는 방식이 유지에 유리하다. 처음부터 고강도 인터벌을 강요하면 회복과 심리적 부담이 커질 수 있다. 걷기, 고정식 자전거, 실내 계단처럼 접근성이 높은 유형이 시작점으로 적합하다.", **common)
    add(subtopic="fat_loss", chunk_title="감량 목적 유산소", use_case="fat_loss",
        tags=["체지방감량", "칼로리소모", "유산소빈도", "지속가능성"],
        text="감량 목적 유산소는 칼로리 소모뿐 아니라 지속 가능성이 중요하다. 너무 강한 유산소는 식욕, 피로, 하체 회복에 영향을 줄 수 있으므로 식단과 저항운동과 함께 균형 있게 배치해야 한다. 주간 총 활동량을 높이되 근력운동을 방해하지 않는 수준이 좋다.", **common)
    add(subtopic="crf", chunk_title="심폐체력 향상", use_case="cardio_programming",
        tags=["심폐지구력", "중강도", "고강도", "심폐향상"],
        text="심폐체력 향상은 중강도 지속운동과 인터벌 모두로 가능하지만, 현재 체력과 위험도에 맞는 접근이 필요하다. 기초 체력이 낮은 사람은 지속운동으로 기반을 만든 뒤 인터벌을 추가하는 방식이 부담이 적다. 성과를 높이고 싶어도 너무 빠른 강도 상승은 오히려 역효과가 될 수 있다.", **common)
    add(subtopic="progression", chunk_title="유산소 진행 규칙", use_case="program_adjustment",
        tags=["점진증가", "시간증가", "강도증가", "회복"],
        text="유산소는 보통 시간과 빈도를 먼저 늘리고, 그다음 강도를 높이는 편이 안전하다. 강도와 시간을 동시에 크게 올리면 피로와 부상 위험이 커질 수 있다. 진행은 주 단위로 작게 조정하고, 회복이 흔들리면 다시 낮추는 유연성이 필요하다.", **common)
    add(subtopic="stop_signs", chunk_title="중단 또는 수정이 필요한 신호", use_case="risk_screening",
        tags=["중단기준", "흉통", "어지럼", "통증"],
        text="운동 중 흉통, 실신감, 비정상적인 호흡곤란, 날카로운 통증이 나타나면 즉시 강도를 낮추거나 중단해야 한다. 근육 피로와 위험 신호를 구분하는 교육이 중요하다. 특히 고위험군은 '참고 버티기'보다 조기 중단 기준을 명확히 알아두는 편이 안전하다.", **common)

    source = "Buchheit & Laursen (2013) HIIT Programming Puzzle Part I/II"
    category = "hiit_programming"
    common = dict(source=source, category=category, year=2013, evidence_type="review", population="general_adult")
    add(subtopic="definition", chunk_title="HIIT 정의와 목적", use_case="cardio_programming",
        tags=["HIIT", "인터벌", "프로토콜", "심폐향상"],
        text="HIIT는 높은 강도의 운동 구간과 회복 구간을 교대로 배치하는 방식이다. 핵심은 강도를 단순히 높이는 것이 아니라 work와 rest를 어떻게 조합하느냐에 있다. 같은 HIIT라도 목표가 VO2max 향상인지 시간 효율인지에 따라 설계가 달라진다.", **common)
    add(subtopic="work_rest", chunk_title="운동-휴식 비율", use_case="cardio_programming",
        tags=["운동휴식비율", "회복", "인터벌설계", "강도"],
        text="인터벌 설계에서 운동 시간과 휴식 시간의 비율은 수행 질과 대사 스트레스를 크게 바꾼다. 너무 짧은 휴식은 다음 반복의 강도를 떨어뜨리고, 너무 긴 휴식은 자극 특성을 바꿀 수 있다. 목표 적응을 생각하며 비율을 정해야 한다.", **common)
    add(subtopic="long_interval", chunk_title="긴 인터벌 활용", use_case="cardio_programming",
        tags=["긴인터벌", "4x4", "심폐적응", "VO2max"],
        text="비교적 긴 인터벌은 심폐 부하를 크게 걸어 VO2max와 심혈관 적응을 노릴 때 자주 사용된다. 다만 체력이 낮은 사람에게는 주관적 고통과 회복 부담이 커질 수 있다. 긴 인터벌은 빈도보다 품질을 먼저 지키는 것이 중요하다.", **common)
    add(subtopic="short_interval", chunk_title="짧은 인터벌 활용", use_case="cardio_programming",
        tags=["짧은인터벌", "반복질", "시간효율", "속도유지"],
        text="짧은 인터벌은 비교적 높은 출력과 기술 품질을 유지하면서 반복 수를 확보하기 좋다. 러닝, 자전거, 로잉처럼 리듬이 중요한 종목에서 활용도가 높다. 단, 짧다고 해서 쉽다는 뜻은 아니며 총 반복량 관리가 필요하다.", **common)
    add(subtopic="physiology", chunk_title="생리학적 적응", use_case="evidence_interpretation",
        tags=["생리학", "미토콘드리아", "심혈관적응", "대사"],
        text="HIIT는 심혈관 기능, 근육의 산화 능력, 대사 효율 등 다양한 적응을 유도할 수 있다. 하지만 모든 적응이 동시에 최대화되는 것은 아니며, 프로토콜의 성격에 따라 편향이 생긴다. 따라서 원하는 적응을 먼저 정하고 프로토콜을 고르는 것이 합리적이다.", **common)
    add(subtopic="recovery", chunk_title="스케줄링과 회복", use_case="fatigue_management",
        tags=["회복", "주당빈도", "근력운동병행", "피로관리"],
        text="HIIT는 체감 강도가 높아 저항운동이나 경기 일정과 충돌하기 쉽다. 하체 근력 세션과 가까이 붙이면 회복이 흔들릴 수 있으므로 주간 배치를 신중히 해야 한다. 초보자는 적은 빈도로 시작해 적응을 확인하는 편이 낫다.", **common)

    source = "Sultana et al. (2019) Low-volume HIIT Review"
    category = "hiit_efficiency"
    common = dict(source=source, category=category, year=2019, evidence_type="review", population="general_adult")
    add(subtopic="definition", chunk_title="저용량 HIIT 정의", use_case="cardio_programming",
        tags=["저용량HIIT", "시간효율", "짧은세션", "유산소"],
        text="저용량 HIIT는 전체 운동 시간이 짧아도 의미 있는 대사 자극을 만들도록 설계된 인터벌 접근이다. 시간이 부족한 사람에게는 접근성이 높지만, 짧은 시간 안에 높은 강도를 요구하므로 기초 체력이 아주 낮다면 바로 적용하기 어렵다. 짧다고 해서 가볍다는 뜻은 아니라는 점을 설명해야 한다.", **common)
    add(subtopic="body_composition", chunk_title="체성분 변화", use_case="fat_loss",
        tags=["체성분", "체지방감량", "시간효율", "HIIT"],
        text="짧은 인터벌 기반 유산소도 체성분과 심폐지표에 긍정적 변화를 만들 수 있다는 점이 강조된다. 다만 체지방 변화는 식사, 총 활동량, 순응도 영향을 크게 받는다. 따라서 저용량 HIIT는 만능 감량법이 아니라 일정이 빡빡한 사람을 위한 선택지로 보는 편이 좋다.", **common)
    add(subtopic="adherence", chunk_title="시간 효율과 순응도", use_case="habit_building",
        tags=["순응도", "바쁜직장인", "짧은운동", "운동습관"],
        text="운동 시간이 짧으면 시작 장벽이 낮아져 순응도에 도움이 될 수 있다. 그러나 세션 자체가 매우 힘들다면 장기 유지에는 오히려 불리할 수도 있다. 실제 적용에서는 시간 효율과 심리적 부담을 함께 고려해 프로토콜을 고르는 것이 중요하다.", **common)
    add(subtopic="application", chunk_title="초보자 적용", use_case="novice_programming",
        tags=["초보자", "실내자전거", "걷기인터벌", "점진적용"],
        text="초보자에게는 러닝 전력질주보다 실내 자전거나 경사 걷기처럼 충격이 낮은 방식이 더 안전할 수 있다. 처음부터 길고 강한 세션을 하기보다 짧은 반복 수로 적응을 확인해야 한다. 컨디션이 불안정한 날에는 지속운동으로 대체하는 유연성도 필요하다.", **common)

    source = "Hindle et al. (2012) PNF Stretching Review"
    category = "mobility_pnf"
    common = dict(source=source, category=category, year=2012, evidence_type="review", population="general_adult")
    add(subtopic="mechanism", chunk_title="PNF의 기본 원리", use_case="mobility",
        tags=["PNF", "가동범위", "신경생리", "유연성"],
        text="PNF 스트레칭은 수축과 이완을 조합해 가동범위 향상을 노리는 기법이다. 단순히 늘리는 것보다 신경계 반응을 함께 활용한다는 점이 특징이다. 숙련된 지도 아래 적용하면 특정 관절의 가동범위를 빠르게 개선하는 데 도움이 될 수 있다.", **common)
    add(subtopic="hold_relax", chunk_title="홀드-릴랙스", use_case="mobility",
        tags=["hold-relax", "햄스트링", "가동성", "스트레칭"],
        text="홀드-릴랙스는 목표 근육을 짧게 등척성 수축한 뒤 이완하면서 신장하는 방식이다. 수축 강도를 과도하게 높이면 경직이 커질 수 있으므로 중간 강도의 수축이 실용적이다. 호흡과 긴장 완화를 함께 지도하면 반응이 더 안정적이다.", **common)
    add(subtopic="contract_relax", chunk_title="컨트랙트-릴랙스", use_case="mobility",
        tags=["contract-relax", "고관절", "PNF", "유연성"],
        text="컨트랙트-릴랙스는 목표 관절을 움직이는 방향으로 능동 수축을 활용해 이후 신장을 돕는다. 코치가 관절 범위를 강제로 밀기보다 사용자와 협력해 부드럽게 범위를 확장하는 것이 좋다. 통증을 동반한 과한 압박은 피해야 한다.", **common)
    add(subtopic="contraindications", chunk_title="금기와 주의", use_case="injury_prevention",
        tags=["금기", "급성통증", "관절불안정", "주의사항"],
        text="급성 통증, 염증, 최근 손상, 관절 불안정성이 있는 경우에는 PNF를 무리하게 적용하지 않는 편이 안전하다. 가동범위 향상이 목표여도 통증이 기준점이 되면 안 된다. 운동 전 PNF를 쓸 때는 이후 수행 종목과의 충돌도 고려해야 한다.", **common)

    source = "Behm et al. (2016) Stretching and Performance Review"
    category = "stretching_performance"
    common = dict(source=source, category=category, year=2016, evidence_type="review", population="healthy_active")
    add(subtopic="static_before_performance", chunk_title="정적 스트레칭과 수행", use_case="warmup",
        tags=["정적스트레칭", "퍼포먼스", "워밍업", "근력"],
        text="운동 직전에 긴 시간의 정적 스트레칭을 하면 순간적인 힘과 속도 발휘가 떨어질 수 있다는 점이 반복적으로 보고된다. 특히 중량 훈련이나 스프린트 전에는 과도한 정적 스트레칭을 주축으로 삼지 않는 편이 낫다. 필요하다면 짧고 제한적으로 사용하는 편이 안전하다.", **common)
    add(subtopic="dynamic_warmup", chunk_title="동적 스트레칭의 장점", use_case="warmup",
        tags=["동적스트레칭", "워밍업", "체온상승", "운동전준비"],
        text="동적 스트레칭은 체온을 올리고 관절을 준비시키며 운동 특이적 움직임을 리허설하는 데 유리하다. 경기나 훈련 전에는 대개 동적 준비가 실무적으로 더 적합하다. 다만 동작의 범위와 속도는 준비 단계에 맞게 조절해야 한다.", **common)
    add(subtopic="rom_benefit", chunk_title="가동범위 향상", use_case="mobility",
        tags=["가동범위", "유연성", "장기적용", "회복"],
        text="스트레칭은 장기적으로 가동범위를 늘리는 데 도움을 줄 수 있다. 다만 즉시 성과 향상보다 가동범위 확보, 불편감 감소, 특정 자세 준비에 더 적합한 경우가 많다. 목표가 무엇인지에 따라 스트레칭의 위치를 훈련 전이나 후로 다르게 배치하는 것이 좋다.", **common)
    add(subtopic="practice_rule", chunk_title="실무 적용 규칙", use_case="coaching",
        tags=["실무적용", "운동전", "운동후", "루틴설계"],
        text="운동 전에는 짧은 동적 준비를 기본으로 하고, 정적 스트레칭은 운동 후나 별도 세션으로 분리하는 접근이 무난하다. 유연성 제한이 특정 동작의 기술을 방해할 때만 목적성 있게 스트레칭을 앞쪽에 배치한다. 스트레칭은 만능 해결책이 아니라 준비 전략의 일부로 보는 것이 좋다.", **common)

    source = "2025 한국인 영양소 섭취기준"
    category = "nutrition_kdri"
    common = dict(source=source, category=category, year=2025, evidence_type="national_guideline", population="korean_population")
    add(subtopic="energy", chunk_title="에너지 필요량 개요", use_case="meal_planning",
        tags=["에너지필요량", "활동량", "기초대사", "한국인"],
        text="KDRI는 연령, 성별, 생애주기, 활동 수준에 따라 에너지 필요량을 다르게 본다. 같은 체중이라도 활동량과 생활 패턴이 다르면 유지 칼로리 추정이 크게 달라질 수 있다. 코칭에서는 먼저 유지 수준을 추정한 뒤 목표에 맞춰 증감하는 방식이 실용적이다.", **common)
    add(subtopic="protein", chunk_title="일반 단백질 기준", use_case="meal_planning",
        tags=["단백질", "권장량", "일반성인", "영양기준"],
        text="KDRI의 일반 단백질 기준은 결핍 예방과 기본 건강 유지에 초점을 둔다. 따라서 운동선수나 근비대 목표 사용자에게는 그대로 적용하기보다 운동 상황에 맞는 상향 조정이 필요할 수 있다. 일반 기준과 운동 처방 기준을 구분해서 설명해야 혼동이 적다.", **common)
    add(subtopic="carbohydrate_fat", chunk_title="탄수화물과 지방의 기본 틀", use_case="meal_planning",
        tags=["탄수화물", "지방", "비율", "기본식단"],
        text="탄수화물과 지방은 총 에너지 균형 안에서 배분해야 한다. 활동량이 높은 사람은 탄수화물이 수행과 회복에 더 중요할 수 있고, 포만감 관리가 중요할 때는 지방과 단백질의 비중 조절이 의미를 가진다. 기본 틀은 균형식이지만 실제 배분은 목적에 따라 달라질 수 있다.", **common)
    add(subtopic="adult_men_women", chunk_title="성인 남녀 적용", use_case="meal_planning",
        tags=["성인남성", "성인여성", "활동량", "식사설계"],
        text="성인 남녀는 평균 체격과 에너지 필요량이 달라 같은 식단이 항상 같은 결과를 주지 않는다. 한국인 기준을 사용할 때는 성별 차이를 기본값으로 참고하되, 실제 코칭에서는 체중 변화와 포만감 반응을 함께 본다. 표준 수치는 출발점일 뿐 최종 답은 아니다.", **common)
    add(subtopic="older_adults", chunk_title="고령층 고려", use_case="older_adults",
        tags=["고령층", "근감소예방", "식사빈도", "단백질품질"],
        text="고령층은 총 섭취량이 줄어들기 쉬워 단백질과 미량영양소 밀도를 더 신경 써야 한다. 식사량이 적다면 한 끼의 단백질 품질과 소화 가능성을 함께 보아야 한다. 씹기, 소화, 약물 복용 같은 현실 제약도 식단 설계에 포함해야 한다.", **common)
    add(subtopic="weight_management", chunk_title="체중 관리 해석", use_case="fat_loss",
        tags=["체중관리", "감량", "증량", "에너지조절"],
        text="KDRI는 체중 감량이나 벌크업 전용 가이드라기보다 기본 영양 기준의 출발점이다. 감량 시에는 결핍을 피하면서 에너지를 줄여야 하고, 증량 시에는 과잉 섭취로 체지방이 지나치게 늘지 않게 조절해야 한다. 따라서 체중 목표는 KDRI 위에 별도 전략을 얹는 방식으로 다루는 편이 맞다.", **common)
    add(subtopic="coaching", chunk_title="코칭 적용 규칙", use_case="coaching",
        tags=["코칭", "한국서비스", "기준치", "개인화"],
        text="한국 사용자에게는 해외 기준보다 KDRI를 기본 프레임으로 삼는 편이 설명과 수용성이 좋다. 다만 운동량이 큰 사용자는 스포츠영양 기준을 함께 참고해야 한다. KDRI는 기본선, 스포츠영양은 목표 보정치라는 구조로 설명하면 실무 적용이 편하다.", **common)
    add(subtopic="cautions", chunk_title="기준치 해석 주의", use_case="evidence_interpretation",
        tags=["해석주의", "기준치", "개인차", "운동자"],
        text="기준치는 평균적인 건강 유지 목적의 수치이므로 개인의 질병, 운동량, 감량 상태, 소화 문제를 모두 반영하지는 않는다. 표준 권장량보다 더 많이 먹는 것이 항상 좋은 것도 아니다. 실제 코칭에서는 기준치와 실제 반응 데이터를 같이 봐야 한다.", **common)

    source = "ISSN Position Stand: Protein and Exercise (2017)"
    category = "nutrition_protein"
    common = dict(source=source, category=category, year=2017, evidence_type="position_stand", population="exercising_adult")
    add(subtopic="daily_total", chunk_title="하루 총 단백질", use_case="muscle_gain",
        tags=["단백질", "총섭취량", "근비대", "운동자"],
        text="ISSN 단백질 포지션 스탠드는 규칙적 운동을 하는 사람에게 일반인보다 높은 단백질 섭취가 도움이 될 수 있다고 본다. 하루 총 단백질은 훈련 목적과 에너지 상태에 따라 달라지며, 근비대나 체중 감량 시에는 더 높은 범위가 자주 사용된다. 총량이 가장 큰 축이라는 점이 중요하다.", **common)
    add(subtopic="distribution", chunk_title="식사 간 분배", use_case="meal_planning",
        tags=["식사분배", "단백질분배", "한끼단백질", "MPS"],
        text="단백질은 하루에 몰아먹기보다 여러 끼에 나눠 섭취하는 편이 실무적으로 유리하다. 식사 간 분배는 포만감, 소화, 훈련 시간과 함께 조정해야 한다. 한 끼의 질과 총량을 동시에 보는 접근이 더 안정적이다.", **common)
    add(subtopic="quality", chunk_title="단백질 질과 식품 선택", use_case="meal_planning",
        tags=["단백질질", "필수아미노산", "동물성", "식물성"],
        text="단백질 총량이 같아도 식품의 질과 필수아미노산 구성은 다를 수 있다. 식물성 위주 식단은 총량을 조금 더 여유 있게 잡거나 조합을 신경 쓰는 편이 안전하다. 소화 불편과 알레르기 여부도 실제 식품 선택에서 중요하다.", **common)
    add(subtopic="hypertrophy", chunk_title="근비대 적용", use_case="muscle_gain",
        tags=["근비대", "저항운동", "회복", "단백질"],
        text="근비대를 목표로 할 때는 저항운동 자극과 단백질 섭취가 함께 가야 한다. 단백질만 높인다고 근육이 늘지는 않으며, 훈련 볼륨과 회복이 뒷받침되어야 한다. 실무적으로는 훈련 주간 볼륨이 늘어날수록 식사 계획도 같이 정교해져야 한다.", **common)
    add(subtopic="dieting", chunk_title="감량기 적용", use_case="fat_loss",
        tags=["감량기", "근손실방지", "포만감", "단백질상향"],
        text="에너지 적자가 있는 감량기에는 근손실 방지를 위해 단백질 비중을 더 신경 쓰는 경우가 많다. 체중 변화 속도가 빠를수록 근육 유지 측면에서 보수적인 접근이 필요하다. 단백질을 올리더라도 전체 식단 순응도와 소화 가능성을 같이 확인해야 한다.", **common)

    source = "ISSN Position Stand: Nutrient Timing (2017)"
    category = "nutrition_timing"
    common = dict(source=source, category=category, year=2017, evidence_type="position_stand", population="exercising_adult")
    add(subtopic="pre_exercise", chunk_title="운동 전 영양", use_case="training_day_nutrition",
        tags=["운동전식사", "탄수화물", "단백질", "소화"],
        text="운동 전 식사는 소화가 잘되는 탄수화물과 적절한 단백질을 중심으로 구성하는 경우가 많다. 운동 직전 과도한 지방과 식이섬유는 일부 사용자에게 불편감을 줄 수 있다. 실제 적용에서는 훈련 시간과 위장 반응을 함께 고려해야 한다.", **common)
    add(subtopic="during_exercise", chunk_title="운동 중 영양", use_case="training_day_nutrition",
        tags=["운동중영양", "수분", "장시간운동", "탄수화물보충"],
        text="운동 중 영양은 장시간 세션이나 지구성 운동에서 중요성이 더 커진다. 짧은 일반 웨이트 세션에서는 무조건 보충이 필요한 것은 아니다. 다만 땀 손실이 크거나 세션이 길면 수분과 탄수화물 보충 전략을 따로 가져가는 편이 좋다.", **common)
    add(subtopic="post_exercise", chunk_title="운동 후 영양", use_case="training_day_nutrition",
        tags=["운동후영양", "회복", "단백질", "탄수화물"],
        text="운동 후 영양은 회복을 돕지만, 소위 아나볼릭 윈도우를 지나치게 좁게 볼 필요는 없다. 직전과 직후 식사가 하루 전체 섭취 안에 자연스럽게 배치되면 충분한 경우가 많다. 핵심은 즉시성보다 하루 총량과 반복 가능성이다.", **common)
    add(subtopic="daily_context", chunk_title="하루 전체 맥락", use_case="meal_planning",
        tags=["하루총량", "영양타이밍", "순응도", "현실적용"],
        text="영양 타이밍은 하루 전체 식단이 정리된 상태에서 미세 조정하는 도구다. 총 섭취량이 부족한데 타이밍만 맞춘다고 성과가 크게 좋아지지는 않는다. 따라서 타이밍 전략은 기본 식사 패턴이 안정된 뒤 적용하는 편이 효율적이다.", **common)

    source = "EAACI Food Allergy Management (2024/2023)"
    category = "nutrition_allergy"
    common = dict(source=source, category=category, year="2024/2023", evidence_type="guideline", population="food_allergy")
    add(subtopic="avoidance", chunk_title="회피 원칙", use_case="allergy_safe_planning",
        tags=["알레르기", "회피원칙", "식단안전", "교체식품"],
        text="식품 알레르기 관리의 기본은 원인 식품의 명확한 회피와 오염 가능성 확인이다. 추정만으로 과도하게 많은 식품군을 제한하면 영양 불균형과 순응도 문제를 만들 수 있다. 진단 정보가 명확할수록 대체식 설계도 더 정교해진다.", **common)
    add(subtopic="labels", chunk_title="라벨 읽기", use_case="allergy_safe_planning",
        tags=["식품라벨", "알레르기표시", "가공식품", "주의문구"],
        text="가공식품에서는 원재료명과 알레르기 표시 문구를 함께 읽어야 한다. 동일 식품군이라도 제조 라인과 첨가물에 따라 위험도가 달라질 수 있다. 코칭에서는 '먹어도 되는 식품' 목록보다 '확인해야 하는 기준'을 먼저 교육하는 편이 재현성이 높다.", **common)
    add(subtopic="protein_substitution", chunk_title="단백질 대체", use_case="allergy_safe_planning",
        tags=["단백질대체", "유청대체", "식물성단백질", "알레르기"],
        text="유청이나 우유 단백질을 쓰기 어려운 경우에는 콩, 완두, 계란, 육류, 생선 등 허용 가능한 대체원을 조합해야 한다. 단백질 총량뿐 아니라 소화 반응과 식감 수용성도 실제 지속성에 영향을 준다. 보충제보다 일상식 기반 대체가 우선일 수 있다.", **common)
    add(subtopic="milk_egg_substitution", chunk_title="우유와 달걀 대체", use_case="allergy_safe_planning",
        tags=["우유알레르기", "달걀알레르기", "대체식품", "영양보완"],
        text="우유와 달걀 제한은 단백질 외에도 칼슘, 비타민, 조리 편의성 문제를 함께 만든다. 대체 음료나 대체 식품을 쓸 때는 강화 여부와 단백질 함량을 따로 확인하는 편이 좋다. '비슷해 보이는 제품'이 영양적으로 같은 것은 아니라는 점을 설명해야 한다.", **common)
    add(subtopic="cross_reactivity", chunk_title="교차 반응 주의", use_case="allergy_safe_planning",
        tags=["교차반응", "견과류", "갑각류", "과일알레르기"],
        text="일부 사용자는 원인 식품과 유사한 식품군에도 반응할 수 있어 교차 반응 가능성을 고려해야 한다. 다만 모든 유사 식품을 무조건 금지하면 과도한 제한이 될 수 있다. 실제 적용은 진단 정보와 개인 반응 기록을 함께 보며 보수적으로 진행하는 편이 안전하다.", **common)
    add(subtopic="restaurant_emergency", chunk_title="외식과 응급 대응", use_case="allergy_safe_planning",
        tags=["외식", "응급대응", "교차오염", "안전"],
        text="외식에서는 재료보다 조리 도구와 교차 오염 위험이 더 큰 문제가 될 수 있다. 알레르기 이력이 심한 사용자는 메뉴 자체보다 조리 환경을 먼저 확인해야 한다. 응급 계획이 필요한 사람에게는 식단 제안보다 안전 행동 수칙을 우선 설명해야 한다.", **common)

    source = "ISSN Position Stand: Creatine Supplementation and Exercise (2017)"
    category = "supplement_creatine"
    common = dict(source=source, category=category, year=2017, evidence_type="position_stand", population="exercising_adult")
    add(subtopic="loading", chunk_title="로딩과 유지", use_case="supplement_use",
        tags=["크레아틴", "로딩", "유지복용", "보충제"],
        text="크레아틴은 로딩 후 유지 복용을 하거나, 로딩 없이 꾸준히 복용하는 방식이 모두 가능하다. 실무적으로는 복잡한 로딩보다 지속 가능한 유지 복용을 택하는 사용자도 많다. 중요한 것은 하루하루의 일관성이다.", **common)
    add(subtopic="benefit", chunk_title="기대 효과", use_case="supplement_use",
        tags=["근력", "무산소성능", "반복질", "크레아틴"],
        text="크레아틴은 고강도 반복 수행과 무산소성 운동에서 도움을 줄 가능성이 크다. 특히 저항운동의 총 반복 질을 높이는 방향으로 체감되는 경우가 많다. 다만 훈련이 부실한 상태에서 보충제만으로 큰 변화를 기대하는 것은 무리다.", **common)
    add(subtopic="safety", chunk_title="안전과 주의점", use_case="supplement_use",
        tags=["안전성", "체중증가", "수분", "주의사항"],
        text="크레아틴은 비교적 연구가 많이 축적된 보충제지만, 모든 사용자에게 무조건 필요하지는 않다. 초기 체중 변화나 위장 불편이 있을 수 있어 반응을 확인하며 시작하는 편이 좋다. 기저질환이나 복용 약물이 있다면 전문 상담이 우선이다.", **common)

    source = "Omega-3 and Exercise Recovery Review (2025)"
    category = "supplement_omega3"
    common = dict(source=source, category=category, year=2025, evidence_type="review", population="general_adult")
    add(subtopic="recovery", chunk_title="회복과 염증 조절", use_case="supplement_use",
        tags=["오메가3", "회복", "염증", "근육통"],
        text="오메가-3는 회복과 염증 반응 조절 측면에서 관심을 받지만, 모든 사용자가 체감할 만큼 큰 효과를 얻는 것은 아니다. 식사에서 지방질이 부족하거나 생선 섭취가 적은 경우에 보충 고려 가치가 더 커질 수 있다. 보충제보다 기본 식사 패턴 점검이 먼저일 수 있다.", **common)
    add(subtopic="dose", chunk_title="용량 해석", use_case="supplement_use",
        tags=["용량", "EPA", "DHA", "보충전략"],
        text="오메가-3는 제품마다 EPA와 DHA 함량이 크게 달라 단순 캡슐 개수만으로 비교하기 어렵다. 실제 적용에서는 라벨의 유효 함량을 확인해야 한다. 과도한 기대보다 식습관 보완 수단으로 해석하는 편이 현실적이다.", **common)
    add(subtopic="caution", chunk_title="주의점", use_case="supplement_use",
        tags=["주의점", "항응고제", "위장불편", "보충제"],
        text="혈액응고 관련 약물을 복용 중이거나 특정 질환 관리가 필요한 경우에는 오메가-3 보충 전에 상담이 필요할 수 있다. 위장 불편과 트림, 제품 산패 문제도 실제 사용성에 영향을 준다. 품질 관리가 되는 제품을 고르는 것이 중요하다.", **common)

    source = "Helms et al. (2014) Contest Preparation"
    category = "physique_cutting"
    common = dict(source=source, category=category, year=2014, evidence_type="review", population="physique_athlete")
    add(subtopic="rate_of_loss", chunk_title="감량 속도", use_case="fat_loss",
        tags=["감량속도", "근손실방지", "피지크", "체중감소"],
        text="피지크 준비에서는 너무 빠른 감량이 근손실과 수행 저하를 부를 수 있으므로 감량 속도를 보수적으로 잡는 편이 좋다. 체중계 숫자보다 근력 유지와 컨디션을 같이 봐야 한다. 급격한 감량은 단기 체중 감소와 장기 성과를 혼동하게 만들 수 있다.", **common)
    add(subtopic="macro_priority", chunk_title="매크로 우선순위", use_case="fat_loss",
        tags=["매크로", "단백질우선", "탄수화물조절", "식단설계"],
        text="감량기에는 단백질을 우선 확보하고, 남은 에너지 안에서 탄수화물과 지방을 조절하는 접근이 실무적으로 많다. 탄수화물은 수행 유지와 직결되므로 너무 급격하게 줄이면 훈련 질이 흔들릴 수 있다. 개인의 선호와 훈련량에 맞는 균형이 중요하다.", **common)
    add(subtopic="training_during_cut", chunk_title="감량기 훈련 유지", use_case="fat_loss",
        tags=["감량기훈련", "근력유지", "볼륨조절", "회복"],
        text="감량기에는 무조건 운동량을 늘리기보다, 중요한 근력 자극을 유지하면서 회복 가능한 범위로 볼륨을 조정하는 편이 좋다. 식단 적자가 큰데 볼륨까지 과도하면 근육 유지가 어려워질 수 있다. 메인 리프트의 질을 지키는 것이 우선이다.", **common)
    add(subtopic="monitoring", chunk_title="모니터링 포인트", use_case="tracking",
        tags=["모니터링", "체중", "컨디션", "순응도"],
        text="감량기에는 체중 변화만 보지 말고 수면, 훈련 질, 배고픔, 집중력, 통증을 함께 확인해야 한다. 계획이 좋아도 순응도가 무너지면 지속되지 않는다. 그래서 피지크형 식단일수록 정교한 숫자보다 유지 가능한 구조가 더 중요하다.", **common)

    return items


def main() -> None:
    dataset = build_dataset()
    output_path = Path(__file__).resolve().parent.parent / "data" / "external_knowledge.json"
    output_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(dataset)} items to {output_path}")


if __name__ == "__main__":
    main()
