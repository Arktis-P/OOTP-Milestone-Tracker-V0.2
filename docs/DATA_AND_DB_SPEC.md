# OOTP Milestone Tracker V0.2 — Data & DB Specification

이 문서는 V0.2의 데이터 저장 구조와 DB 운영 원칙을 정의한다.

TODO보다 이 문서의 데이터 계약이 우선한다. 기능 구현 중 스키마/식별/transaction 정책을 바꿀 필요가 생기면 코드보다 이 문서를 먼저 수정한다.

---

# 1. 기본 원칙

1. **OOTP 원본은 입력 원본(Source of Truth)** 으로 취급한다.
2. 앱 DB는 원본을 해석·정규화한 **파생 데이터 저장소**다.
3. 서로 다른 OOTP 세이브는 절대 같은 DB에 혼합하지 않는다.
4. parser는 파일을 해석만 하고 DB를 직접 수정하지 않는다.
5. import service가 transaction과 저장 순서를 책임진다.
6. 동일 source를 반복 처리해도 중복 결과가 생기지 않아야 한다.
7. 원본이 변경되면 기존 파생 데이터를 안전하게 교체하거나, 안전하지 않으면 거부한다.
8. 사용자 수동 기록은 자동 import 데이터와 구분하되 같은 조회 모델에서 볼 수 있게 한다.

---

# 2. 사용자 데이터 위치

개발 중에는 프로젝트 로컬 경로를 사용할 수 있으나, 배포본은 사용자 데이터와 번들 데이터를 분리한다.

권장 Windows 구조:

```text
%APPDATA%/OOTP_Milestone_Tracker_V0.2/
├─ settings.json
├─ saves/
│  └─ {save_key}/
│     ├─ records.db
│     └─ reports/
├─ user_data/
│  ├─ korean_first_names.csv
│  ├─ korean_last_names.csv
│  └─ korean_names_pending.csv
└─ backups/
```

저장소/배포 bundle:

```text
data/
├─ milestones.csv
├─ streak_policies.json
├─ bundle_manifest.json
├─ korean_first_names.csv
└─ korean_last_names.csv
```

사용자 데이터는 앱 업데이트로 덮어쓰지 않는다.

---

# 3. Save Identity

## 목적
같은 PC에서 여러 OOTP 리그를 사용해도 기록이 섞이지 않게 한다.

## 권장 식별 방식

`save_key = stable hash(normalized absolute save path + league identity)`

가능하면 OOTP 내부의 안정적인 league ID를 함께 사용한다.

금지:
- 단순 폴더명만 사용
- 현재 시즌만 사용
- 팀명만 사용

## 세이브 전환

활성 세이브가 변경되면 다음을 함께 갱신한다.

- active DB connection
- boxscore path
- messages path
- import_export path
- current season context
- tracked team context
- dashboard/read models

기존 세이브 DB는 닫고 새 세이브 DB를 연다.

---

# 4. SQLite 운영 규칙

## 기본 설정

- SQLite
- `PRAGMA journal_mode=WAL`
- foreign keys enabled
- schema version 저장

## 연결 정책

- GUI widget이 직접 SQL을 실행하지 않는다.
- repository/service 계층을 통해 접근한다.
- background worker는 필요 시 별도 connection을 사용한다.
- connection을 thread 사이에서 무분별하게 공유하지 않는다.

## transaction 원칙

### 한 게임 import

한 게임에서 다음 항목은 가능한 한 단일 transaction에 포함한다.

1. game row
2. batting/pitching raw stats
3. affiliation update
4. season aggregate change
5. milestone events
6. streak updates
7. processed source status

중간 실패 시 전체 rollback한다.

### 한 뉴스 메시지 import

메시지 1개를 하나의 atomic unit으로 취급한다.

- 여러 이벤트가 생성되더라도 모두 성공 → commit
- 하나라도 실패 → 해당 메시지 전체 rollback
- 오류 상태만 별도로 기록 가능

### 레이팅 편집

DB보다 파일 출력 작업이 중심이므로 임시 파일 → 검증 → 원자 교체 순서를 사용한다.

---

# 5. Schema Version / Migration

DB에 다음 메타를 둔다.

```text
schema_version
created_at
app_version_created
app_version_last_opened
save_key
save_path_snapshot
```

원칙:

- 기존 사용자 DB를 삭제해서 새 버전을 맞추지 않는다.
- migration은 `N -> N+1` 식으로 누적한다.
- migration은 재실행되어도 안전해야 한다.
- destructive migration 전 backup 경로를 마련한다.
- migration 실패 시 version을 올리지 않는다.

---

# 6. 권장 핵심 테이블

실제 컬럼은 구현 과정에서 조정 가능하지만 책임은 유지한다.

## `players`

목적: 선수 identity의 중심.

주요 필드:

```text
id                  internal PK
ootp_player_id      nullable unique when known
first_name
last_name
display_name
is_temporary
created_at
updated_at
```

### 규칙
- `ootp_player_id`가 있으면 동일 선수 판별의 최우선 기준.
- 수동 선수는 `ootp_player_id = NULL`, `is_temporary = 1` 가능.
- 이름 약칭을 identity key로 사용하지 않는다.

## `teams`

```text
id
team_key
abbreviation
name
league
is_custom
```

## `player_team_affiliations`

선수와 팀의 시즌별 소속을 저장한다.

```text
player_id
team_id
season
source
first_seen
last_seen
```

## `games`

```text
id
season
ootp_game_id
game_date
home_team_id
away_team_id
game_type
source_id
source_hash
```

권장 unique:

```text
(season, ootp_game_id)
```

교차 시즌 game ID 재사용 가능성을 고려해 season을 포함한다.

## `batting_game_stats`

선수 1명 × 경기 1개의 원시/정규화 타격 stat.

## `pitching_game_stats`

선수 1명 × 경기 1개의 원시/정규화 투구 stat.

## `baseline_batting_stats`

stats TXT에서 가져온 시즌/통산 초기값.

## `baseline_pitching_stats`

동일.

### 중요
baseline은 박스스코어 누적치와 구분한다.

통산 계산은 개념적으로:

```text
career_current = imported_baseline + post-baseline_increment
```

동일 baseline snapshot을 갱신할 때 과거 값을 재가산하지 않는다.

## `milestone_events`

```text
id
policy_key
player_id nullable
team_id nullable
season
game_id nullable
event_date
scope
category
grade
value
threshold
source_type      auto/manual/message
source_ref
created_at
```

unique key는 이벤트 성격에 따라 정의하되 기본 목표는 같은 source에서 같은 policy 이벤트 중복 방지다.

## `manual_events`

CSV milestone 정책 밖의 자유 형식/특수 사건 보존이 필요할 경우 사용한다.

예:
- transfer
- injury
- contract

가능하면 read model에서 `milestone_events`와 통합해 보여준다.

## `streak_states`

진행 중 streak 상태.

```text
policy_key
subject_type
subject_id
season
start_date
last_date
current_value
metadata_json
```

## `streak_events`

완료/종료된 streak 기록.

## `processed_sources`

모든 import source의 중복/변경 판정 기반.

```text
source_type
source_id
path_snapshot
content_hash
mtime
size
status
processed_at
error_message
```

### hash 우선 원칙
파일 변경 판정은 가능하면 `content_hash`를 우선하고 mtime/size는 보조값으로 쓴다.

## `import_workflow_state`

UI가 재시작되어도 import 단계/결과를 복원할 수 있도록 한다.

권장 workflow:

- baseline_history
- latest_boxscores
- news_messages
- season_finalize

step:

- source_check
- analyze_classify
- review_results
- save
- confirm_result

outcome:

- completed
- partial_success
- failed
- cancelled

---

# 7. Source Fingerprint

## 목적

- 동일 파일 중복 처리 방지
- 수정 파일 감지
- 사용자가 파일을 복사/덮어쓰기 했을 때 변경 확인

## 권장값

```text
source_type
logical_source_id
content_hash
mtime
size
```

`logical_source_id` 예:

- boxscore: season + game id
- message: message number/source id
- stats snapshot: file type + season/context

## 상태 예

```text
new
processed
unchanged
changed_review_needed
excluded
error
```

---

# 8. Modified Boxscore 정책

가장 위험한 영역이므로 보수적으로 구현한다.

## 안전하게 교체 가능한 경우

- 최신 경기
- 이후 누적 이벤트를 재생할 필요가 없는 경우

처리:

1. 기존 source 결과 식별
2. 기존 game stats 제거
3. 해당 source가 만든 auto milestone 제거
4. 해당 source 영향 streak 되돌림/재계산
5. 새 source 저장
6. 누적 재계산
7. commit

## 안전하지 않은 경우

과거 경기를 수정하면 이후 경기의 threshold crossing 시점과 streak가 변할 수 있다.

전체 replay가 구현되기 전에는:

- DB 변경 전에 거부
- 이유 표시
- Advanced Tools의 season replay/recovery로 유도

---

# 9. Aggregate 계산 전략

초기 구현에서는 correctness를 우선한다.

권장:

- game stats를 normalized raw layer로 저장
- season/career 값을 필요 시 SQL aggregate 또는 명확한 summary table로 계산
- summary table을 쓰면 raw layer에서 재생성 가능해야 한다.

금지:

- 오직 누적값만 저장하고 원시 경기값을 버리는 구조
- 수정 import를 할 수 없는 irreversible aggregate

---

# 10. Player Merge

## Temporary player

수동 기록 시:

```text
D. Moon 같은 축약명만 받지 말고 가능한 한 full name 입력
```

임시 선수 생성 후 manual event를 연결한다.

## 확정 병합 조건

우선순위:

1. 명시적 OOTP player ID 일치
2. 사용자가 직접 선택한 merge
3. 이름 + 팀 + 시즌 등 높은 신뢰도의 복합 조건

동명이인 가능성이 있으면 자동 병합하지 않는다.

## 병합 시 이전 대상

- milestone events
- manual events
- streak refs
- affiliations
- localized name refs if player-specific mapping introduced later

병합 transaction이 실패하면 원상 복구한다.

---

# 11. Settings vs DB vs Policy 구분

## Settings

사용자/세이브별 환경값.

예:
- active save
- current season
- tracked teams
- MLB-only
- UI language
- qualification parameter override

## DB

실제 처리 결과와 세이브 상태.

예:
- players
- games
- stats
- milestone event
- processed source

## Policy

앱이 어떤 조건을 의미 있는 기록으로 판단할지에 대한 기준.

예:
- 30 HR
- OPS 1.0
- 30-30
- streak 유지 조건
- track_from

코드 상수로 흩어 넣지 않는다.

---

# 12. Backup / Reset

## Reset

현재 세이브 DB만 대상으로 한다.

삭제 전 최소 표시:

- DB path
- player count
- game count
- milestone count
- baseline 존재 여부
- processed source count

명시적 확인 없이 실행하지 않는다.

## Backup

최소한 다음 작업 전 backup을 고려한다.

- destructive migration
- full DB reset 직전 사용자 선택
- rating output overwrite

---

# 13. Validation DB

시즌 전체 replay를 검증할 때 운영 DB를 사용하지 않는다.

```text
validation/{save_key}/{timestamp}/validation.db
```

절차:

1. 빈 schema 생성
2. baseline 적용
3. 대상 시즌 boxscore 순차 import
4. messages 적용
5. finalize 필요 시 수행
6. 운영 DB와 count/hash/summary 비교
7. JSON report 생성

운영 DB는 read-only 비교 대상으로 취급한다.

---

# 14. 테스트 필수 항목

- WAL DB open/close
- schema migration
- foreign key
- save isolation
- duplicate source
- changed source
- transaction rollback
- temporary player merge
- baseline refresh no-double-count
- cross-season same game ID
- operating DB untouched by validation replay

---

# 15. 구현자가 판단하기 어려울 때의 우선순위

1. 원본 데이터 보존
2. 중복 방지
3. 잘못된 자동 병합 방지
4. rollback 가능성
5. 재계산 가능성
6. 성능

즉, V0.2 초기에는 약간 느리더라도 **틀린 기록을 조용히 저장하는 것보다 안전하게 거부하거나 다시 계산할 수 있는 구조**를 우선한다.
