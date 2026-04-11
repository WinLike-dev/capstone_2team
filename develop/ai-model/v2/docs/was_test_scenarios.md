# WAS Test Scenarios

이 문서는 `v2` 기준으로 사용자 메시지 흐름에서 발생하는 WAS 연동 케이스를 시나리오 단위로 정리한 인덱스입니다.

처음 보는 팀원이면 아래 순서로 읽는 것을 추천합니다.

1. [was_api_contract.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_api_contract.md)
2. [was_team_test_checklist.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_team_test_checklist.md)
3. [was_team_curl_guide.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_team_curl_guide.md)
4. 아래 Mermaid 시나리오 파일

## 빠른 시작 문서

- [was_team_test_checklist.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_team_test_checklist.md)
  - WAS 팀이 실제로 무엇을 준비하고 무엇을 확인해야 하는지 정리한 체크리스트

- [was_team_curl_guide.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_team_curl_guide.md)
  - `/debug` 없이 `curl`로 `POST /chat`과 `POST /internal/events/profile-updated`를 테스트하는 실행 가이드

## 시나리오 목록

- [scenario_01_first_turn_initial_load.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_01_first_turn_initial_load.mmd)
  - 첫 메시지 초기 로드
  - 기대 WAS 호출: `GET /api/user/profile/{user_id}`, `GET /api/plan/today/{user_id}`

- [scenario_02_casual_or_fallback_no_write.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_02_casual_or_fallback_no_write.mmd)
  - 캐주얼 / fallback 메시지
  - 기대 WAS 호출: 활성 세션이면 추가 저장 없음

- [scenario_03_info_search_no_write.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_03_info_search_no_write.mmd)
  - 정보 질문
  - 기대 WAS 호출: 일반적으로 없음

- [scenario_04_care_no_write.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_04_care_no_write.mmd)
  - 공감 / 케어 메시지
  - 기대 WAS 호출: 일반적으로 없음

- [scenario_05_record_profile_update.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_05_record_profile_update.mmd)
  - 체중, 목표, persona 등 프로필 변경 메시지
  - 기대 WAS 호출: background write에서 `PUT /api/user/profile/{user_id}`

- [scenario_06_record_plan_check.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_06_record_plan_check.mmd)
  - 오늘 플랜 체크 완료 메시지
  - 기대 WAS 호출: `PUT /api/plan/check/{user_id}`

- [scenario_07_plan_create_proposal.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_07_plan_create_proposal.mmd)
  - 새 운동/식단 계획 생성 요청
  - 기대 WAS 호출: 즉시 저장 없음, `proposed_plan`만 세션에 유지

- [scenario_08_plan_modify_proposal.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_08_plan_modify_proposal.mmd)
  - 기존 계획 수정 요청
  - 기대 WAS 호출: `GET /api/workout-plan/full/{user_id}` 또는 `GET /api/diet-plan/full/{user_id}`

- [scenario_09_plan_approval_create.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_09_plan_approval_create.mmd)
  - 생성안 승인
  - 기대 WAS 호출: background write에서 `POST /api/plan/create/{user_id}`

- [scenario_10_plan_approval_update.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_10_plan_approval_update.mmd)
  - 수정안 승인
  - 기대 WAS 호출: background write에서 `PUT /api/plan/update/{user_id}`

- [scenario_11_profile_updated_next_turn_refresh.mmd](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios/scenario_11_profile_updated_next_turn_refresh.mmd)
  - WAS에서 프로필 변경 후 다음 턴 반영
  - 기대 WAS 호출: `POST /internal/events/profile-updated` 후 다음 턴에 `GET /api/user/profile/{user_id}`

## 같이 볼 핵심 포인트

- 첫 턴인지, 이미 열린 세션인지
- 승인 전후에 `session_id`를 같은 값으로 유지했는지
- WAS 저장은 응답 직후가 아니라 background task로 처리되는지
- 승인 성공 전에는 `proposed_plan`이 사라지지 않는지
- `selected_ai_persona`가 next-turn refresh에서 실제 반영되는지
