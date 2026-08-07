# OOTP Milestone Tracker V0.2 — Implementation TODO

이 문서는 V0.2를 처음부터 재구현하기 위한 **작업 순서 + 기능 명세 + 동작 계약**이다.

다음 작업자는 체크박스를 단순 작업 목록으로만 보지 말고, 각 항목의 **목적 / 입력 / 처리 / 출력 / 완료 조건**을 구현 계약으로 사용한다.

## 공통 원칙

- 구현 순서는 **데이터 기반 → 파서 → 집계 → 마일스톤 → 최소 UI → 분석 기능 → 자동화 → 파워유저 기능 → 운영 안정성** 순서를 따른다.
- 기능을 UI부터 만들지 않는다. 핵심 로직은 GUI와 독립된 `core/` 계층에 먼저 구현하고 테스트한다.
- OOTP 원본 파일은 가능한 한 **읽기 전용 입력**으로 취급한다.
- 동일 입력을 여러 번 처리해도 결과가 중복되지 않는 **멱등성**을 기본 요구사항으로 둔다.
- 한 세이브의 데이터가 다른 세이브와 섞이지 않도록 **세이브별 DB 분리**를 기본 구조로 한다.
- 마일스톤 기준, 연속 기록 기준, 예측 시작 기준 등은 코드에 흩어 넣지 않고 외부 정책 파일로 관리한다.
- DB 구조와 정책 파일의 기준은 [`docs/DATA_AND_DB_SPEC.md`](docs/DATA_AND_DB_SPEC.md)를 우선 참조한다.
- 마일스톤/연속 기록/예측 규칙은 [`docs/RULES_AND_POLICIES.md`](docs/RULES_AND_POLICIES.md)를 우선 참조한다.

---

# Phase 0. 프로젝트 기반

## [x] 0.1 프로젝트 스캐폴딩

### 기능
애플리케이션의 기본 디렉터리와 실행 진입점을 만든다.

### 권장 구조

```text
/
├─ main.py
├─ core/
│  ├─ config/
│  ├─ db/
│  ├─ parser/
│  ├─ stats/
│  ├─ milestone/
│  ├─ streak/
│  ├─ prediction/
│  ├─ import_workflow/
│  └─ validation/
├─ gui/
│  ├─ theme/          # UI 디자인 시스템, 컬러 팔레트, 큐티 스타일시트(QSS)
│  ├─ views/
│  ├─ widgets/
│  └─ workers/        # QThread 기반 비동기 워커
├─ data/
├─ docs/
├─ tests/
└─ build.py
```

### GUI 기술 스택 및 UX 설계 원칙
- **GUI 프레임워크**: PySide6 기반 네이티브 데스크톱 앱 (QSS 및 Fluent UI 스타일 적용).
- **디자인 시스템 & UX**:
  - 모던 다크 테마 중심의 플루이드 카드 디자인 (Windows 11 스타일 사이드바 내비게이션).
  - 마일스톤 등급(Common, Rare, Epic, Legendary)별 시각적 글로우 배지 및 진행률 프로그레스 바.
  - 야구 스탯 데이터 표의 고속 필터링, 정렬 및 드릴다운(Drill-down) 지원.
- **백그라운드 & 알림**:
  - 파일 파싱 및 DB I/O는 `gui/workers/`의 `QThread`로 비동기 처리하여 메인 스레드 프리징 완벽 차단.
  - 시스템 트레이 백그라운드 상주 및 경기 마일스톤 실시간 토스트 알림 팝업.

### 완료 조건
- `python main.py`가 오류 없이 최소 창 또는 CLI bootstrap까지 실행된다.
- core 모듈이 GUI 없이 import 가능하다.

## [x] 0.2 설정 모델 및 경로 관리

### 기능
OOTP 설치/세이브 위치, 현재 시즌, 추적 팀, import 옵션 등 앱 전체 설정을 저장한다.

### 동작
- 설정 파일은 사용자 데이터 영역에 둔다.
- 저장소에는 `settings.example.json`만 포함한다.
- 설정에서 활성 세이브를 선택하면 boxscore / messages / import_export 등 파생 경로를 자동 계산한다.
- 존재하지 않는 경로는 앱 시작 시 즉시 실패시키지 말고 readiness 상태로 보고한다.

### 완료 조건
- 설정 load/save 테스트가 있다.
- 세이브를 바꾸면 파생 경로와 DB 경로가 함께 변경된다.

---

# Phase 1. 데이터베이스와 핵심 데이터 모델

## [x] 1.1 세이브별 SQLite DB 생성

### 기능
각 OOTP 리그/세이브의 기록을 별도 SQLite DB에 저장한다.

### 동작
- 세이브 식별자는 안정적인 save path + league identity 기반으로 만든다.
- DB는 `WAL` 모드를 사용한다.
- schema version을 저장하고 migration 경로를 마련한다.
- DB 파일 삭제 없이 schema upgrade가 가능해야 한다.

### 필수 엔티티
- saves / metadata
- teams
- players
- player_team_affiliations
- games
- batting_game_stats
- pitching_game_stats
- season_stats / career baselines
- milestone_events
- streak_state / streak_events
- import_sources / processed_sources
- import_workflow_state
- manual_events

### 완료 조건
- 빈 DB 생성 테스트
- schema 재실행 테스트
- 세이브 A/B의 데이터 격리 테스트

## [x] 1.2 선수 식별 및 병합 규칙

### 기능
OOTP 파일마다 이름 표현이 달라도 동일 선수를 최대한 같은 선수로 연결한다.

### 동작
- OOTP의 안정적인 player_id가 있으면 항상 최우선 키로 사용한다.
- ID가 없는 임시 수동 선수는 별도 temporary identity를 가진다.
- 이후 stats/boxscore에서 확정 player_id가 들어오면 수동 선수 기록을 확정 선수로 병합한다.
- 이름만으로 자동 병합할 때는 충돌 가능성이 있으므로 보수적으로 처리한다.

### 완료 조건
- 동일 약칭 선수가 여러 명이어도 기록이 섞이지 않는다.
- 수동 선수 → 확정 선수 병합 시 기존 이벤트가 보존된다.

---

# Phase 2. OOTP 데이터 파싱

## [x] 2.1 player batting/pitching stats TXT 파서

### 기능
기존 리그의 과거 시즌·통산 수치를 baseline으로 가져온다.

### 입력
- `player_batting_stats.txt`
- `player_pitching_stats.txt`

### 처리
- 선수 ID, 시즌, 팀, 주요 counting/rate stat을 읽는다.
- 현재 시즌 snapshot과 과거 시즌 데이터를 구분한다.
- 통산 누적 baseline을 별도로 저장한다.

### 출력
- 선수 목록
- 시즌 기록
- 통산 baseline
- 팀 소속 정보

### 완료 조건
- 박스스코어가 0건이어도 선수 시즌/통산 화면을 구성할 수 있다.

## [x] 2.2 박스스코어 HTML 파서

### 기능
경기별 타격·투구·팀 정보를 읽어 현재 시즌 기록의 주 데이터로 사용한다.

### 처리 대상
- 경기 ID
- 경기 날짜
- 홈/원정 팀
- 선수별 타격 line
- 선수별 투구 line
- 타격/투구 notes
- 특수 기록 판정에 필요한 이벤트 정보

### 완료 조건
- fixture HTML을 기준으로 deterministic parse 결과를 얻는다.
- parser는 DB에 직접 쓰지 않는다. 파싱 결과 객체만 반환한다.

## [x] 2.3 특수 이벤트 파싱

### 기능
단순 누적 숫자로 찾기 어려운 기록을 박스스코어 notes에서 추출한다.

### 우선 대상
- 사이클링 히트
- 그랜드슬램
- 완투
- 완봉
- 노히터
- 퍼펙트 게임
- 홀드 등 OOTP 표기에 의존하는 값

### 완료 조건
- 각 특수 이벤트 fixture가 최소 1개 이상 있다.

---

# Phase 3. Import 파이프라인과 통계 집계

## [x] 3.1 baseline import workflow

### 기능
stats TXT를 최초/갱신/시즌 중간 모드로 가져온다.

### 모드
- `first_time`: 새 세이브 최초 구성
- `refresh`: 기존 baseline 갱신
- `mid_season`: 시즌 중 snapshot 보완

### 동작
- 분석/미리보기 후 저장한다.
- 저장은 transaction으로 묶는다.
- GUI에서는 worker thread로 실행할 수 있도록 core API를 분리한다.

## [x] 3.2 박스스코어 import

### 기능
새 경기 파일을 가져와 게임/통계/마일스톤/연속 기록을 갱신한다.

### 처리 순서
1. source fingerprint 계산
2. 파싱
3. game identity 확인
4. 중복/변경 여부 판단
5. 원본 game stats 저장
6. 시즌 누적 계산
7. 마일스톤 판정
8. streak 갱신
9. processed source 상태 저장
10. commit

### 완료 조건
- 같은 파일 2회 import 시 결과가 증가하지 않는다.
- 실패 시 해당 경기 처리 전체가 rollback 된다.

## [x] 3.3 수정 박스스코어 재가져오기

### 기능
이미 처리한 최신 경기 파일이 수정됐을 때 기존 결과를 안전하게 교체한다.

### 동작
- source hash가 달라졌는지 확인한다.
- 기존 game stats + 자동 milestone + streak 결과를 한 transaction에서 제거/재생한다.
- 역사적 누적 재생이 안전하지 않은 과거 경기 수정은 거부하고 사용자에게 이유를 보여준다.

## [x] 3.4 라이브 자동 스캔/감시 (Live Auto-Watch)

### 기능
OOTP 세이브 디렉터리(`boxscores/`, `news/`)의 파일 생성을 백그라운드에서 감시하고 새 경기 완료 시 자동 import를 수행한다.

### 동작
- watchdog 기반의 File System Watcher 모듈 구현.
- 게임 실행 중 새 박스스코어 생성 시 무중단 자동 감지 및 백그라운드 파싱/마일스톤 갱신.
- 트레이 핑/알림 UI를 통해 신규 달성된 마일스톤 즉시 팝업 안내.

### 완료 조건
- 라이브 감시 On/Off 토글이 가능하고, 새 파일 생성 시 자동 import 및 UI 신규 이벤트 알림이 동작한다.

---

# Phase 4. 마일스톤 엔진 — 제품의 핵심

## [x] 4.1 정책 파일 로더

### 기능
`data/milestones.csv` 또는 동등한 정책 파일에서 마일스톤 정의를 읽는다.

### 필드 예
- category
- key
- label
- scope
- stat
- threshold
- direction
- grade
- track_from
- near_n
- description_template

### 완료 조건
- 코드 수정 없이 기준 숫자를 변경할 수 있다.

## [x] 4.2 경기 마일스톤

### 기능
한 경기에서 달성되는 기록을 자동 판정한다.

### 우선 구현
- 타자: 안타, 홈런, 타점, 도루
- 투수: 탈삼진
- 특수: 사이클, 그랜드슬램, 완투, 완봉, 노히터, 퍼펙트

### 동작
- 같은 stat의 여러 threshold를 동시에 넘으면 정책에 따라 최상위 기록 중심으로 저장한다.
- 같은 경기/선수/정책 key는 중복 생성하지 않는다.

## [x] 4.3 시즌 누적 마일스톤

### 기능
시즌 누적값이 threshold를 crossing하는 순간 이벤트를 생성한다.

### 예
- 150/200 안타
- 20/30/40 홈런
- 100 타점
- 20/30 승
- 100/200 탈삼진
- 세이브, 홀드, 이닝 등

### 핵심 규칙
`previous < threshold <= current` 형태의 crossing을 기본으로 한다.

## [x] 4.4 통산 마일스톤

### 기능
baseline + 앱이 import한 이후 기록을 결합해 통산 threshold crossing을 판정한다.

### 중요
- baseline을 매 import마다 중복 합산하지 않는다.
- 통산 첫 출장/첫 안타/첫 홈런 같은 0→1 기록도 지원한다.

## [x] 4.5 시즌 복합 기록

### 기능
둘 이상의 stat 조합으로 기록을 판정한다.

### 예
- 20-20
- 30-30
- 40-40
- 50-50

## [x] 4.6 시즌 비율 기록 최종 판정

### 기능
타율/OBP/SLG/OPS/ERA처럼 시즌 종료 시 qualification이 필요한 기록을 최종 판정한다.

### 동작
- 시즌 중 실시간 누적 기록과 분리한다.
- 최소 타석/이닝 자격 기준을 settings 또는 policy에서 읽는다.
- 사용자가 시즌 finalize를 실행했을 때 한 번 판정한다.

## [x] 4.7 팀 마일스톤

### 기능
팀 단위 기록을 판정한다.

### 우선 대상
- 선발 전원 안타
- 선발 전원 타점
- 선발 전원 득점
- 팀 노히터
- 팀 퍼펙트
- 시즌 팀 승수

---

# Phase 5. 최소 사용 가능한 UI(MVP)

## [x] 5.1 앱 셸 / 내비게이션

### 권장 페이지
Records
1. Dashboard
2. Achievement Records
3. Player Stats
4. Achievement Predictions
5. Streak Records

Data Management
6. Record Import Center
7. Manual Records
8. Rating Editor

Settings
9. Settings
10. Advanced Tools

초기 MVP에서는 1, 2, 3, 6, 9만 먼저 실제 구현하고 나머지는 placeholder여도 된다.

## [x] 5.2 Settings

### 기능
- OOTP save root 선택
- 활성 세이브 선택
- 현재 시즌
- 추적 팀
- MLB-only 여부
- 파생 경로 확인
- 데이터 readiness 표시

## [x] 5.3 Record Import Center

### 기능
모든 import 작업의 진입점을 한 곳에 둔다.

### 최소 흐름
`Source Check → Analyze → Review → Save → Result`

### 대상
- baseline history
- latest boxscores
- 추후 news messages
- season finalize

## [x] 5.4 Achievement Records

### 기능
자동/수동으로 저장된 모든 이벤트를 조회한다.

### 필터
- 시즌
- 선수/팀
- 이벤트 유형
- 중요도
- 자동/수동 source

### 내보내기 & 공유 (Export & Share)
- 마일스톤 달성 카드를 고화질 이미지(PNG) 또는 세련된 HTML 카드로 내보내기/복사.
- 커뮤니티(FM/OOTP 야구 커뮤니티 등)에 공유하기 용이하도록 마일스톤 요약 텍스트 자동 복사 기능 제공.

## [x] 5.5 Player Stats

### 기능
추적 팀 선수를 중심으로 시즌/통산 기록을 본다.

### UI
- 선수 목록
- 타격/투구 구분
- 시즌/통산 토글
- 경기별 drill-down
- 최근 milestone 요약

## [x] 5.6 Dashboard

### 기능
앱을 켰을 때 현재 데이터 상태와 중요한 기록을 압축해서 보여준다.

### 카드
- 최근 마일스톤
- 데이터 준비 상태
- 마지막 import
- 빠른 import 액션
- 이후 phase에서 prediction / streak 카드 추가

---

# Phase 6. 기록 달성 예측

## [x] 6.1 예측 모델

### 기능
현재 속도라면 시즌/통산 마일스톤에 언제 또는 어느 정도 확률로 접근할지 보여준다.

### 최소 계산 정보
- current value
- target
- remaining
- season pace
- recent-window pace(데이터 충분할 때)
- projected additional
- 계산 근거

### 규칙
- `track_from`: 너무 먼 목표는 목록에 올리지 않는다.
- `near_n`: 목표에 매우 가까운 항목을 강조한다.
- 선수 개인 출전/등판량과 팀 경기 수를 혼동하지 않는다.

## [x] 6.2 Prediction UI

### 기능
임박/추적 중인 목표를 정렬하고 선수 상세로 이동한다.

---

# Phase 7. 연속 기록(Streak)

## [x] 7.1 streak policy 로더

정책 파일에서 streak 종류와 유지/종료 조건을 읽는다.

## [x] 7.2 streak tracker

### 기능
박스스코어 import마다 현재 streak를 연장하거나 종료한다.

### 저장
- active state
- start date
- current length/value
- end date
- final length/value

## [x] 7.3 Streak Center

### 기능
- 진행 중 기록
- 최근 종료 기록
- 시즌/선수/팀/유형 필터
- CSV export

## [x] 7.4 Dashboard/Player integration

- 대시보드 진행 중 streak 카드
- 선수 상세에 해당 선수의 active streak 표시

---

# Phase 8. 수동 기록과 선수 보완

## [ ] 8.1 통합 수동 기록 폼

### 지원
- 마일스톤
- 수상
- 이적
- 부상
- 포스트시즌
- 기타 역사적 사건

### 요구
자동 이벤트와 동일한 조회 모델에 저장하되 `source=manual`을 명시한다.

## [ ] 8.2 수동 선수 등록

### 기능
아직 DB에 없는 선수를 풀 네임으로 임시 생성하고 이벤트를 기록한다.

### 후속 병합
stats/boxscore에서 확정 player_id가 확인되면 기존 이벤트를 병합한다.

---

# Phase 9. OOTP 뉴스 메시지 자동화

## [ ] 9.1 messageN.txt 스캐너

### 기능
OOTP 뉴스 폴더에서 메시지 파일을 수집하고 source fingerprint를 저장한다.

## [ ] 9.2 messages.dat 날짜 해석기

### 기능
확인된 OOTP 버전의 메시지 날짜 metadata를 읽는다.

### 안전 규칙
확인되지 않은 버전/필드는 추측해서 쓰지 않는다. unsupported 상태로 남기고 텍스트 스캔은 계속한다.

## [ ] 9.3 메시지 분류/파싱

### 우선 지원
- 트레이드
- FA
- 계약 연장
- 부상
- MVP
- 사이영상
- 신인왕
- 월간상
- 올스타
- Great Glove
- Platinum Stick
- 디비전 우승
- 월드시리즈 우승
- 명예의 전당

## [ ] 9.4 검토/승인 UI

상태:
- new
- date_missing
- changed_review_needed
- already_applied
- excluded
- error

사용자가 승인한 메시지만 저장한다.

## [ ] 9.5 메시지 단위 원자 저장

한 메시지에서 여러 이벤트가 생기더라도 모두 성공해야 commit한다.
실패 시 해당 메시지만 rollback하고 error 상태를 저장한다.

---

# Phase 10. 커스텀 팀 / 확장팀

## [ ] 10.1 tracked teams

- 기본 MLB 팀
- 사용자 선택 추적 팀

## [ ] 10.2 custom team registration

- 약칭
- 팀명
- 선택적 league 정보

stats export의 affiliation을 이용해 선수를 커스텀 팀에 연결한다.

---

# Phase 11. 레이팅 편집

## [ ] 11.1 roster parser

MLB/KBO roster export를 읽되 통계 DB와 강하게 결합하지 않는다.

## [ ] 11.2 일괄 편집

### 기능
- 대상 필터
- 변경 전후 preview
- diff
- mod roster 출력

### 안전
- 원본 직접 수정 금지
- 기존 출력 backup
- duplicate player ID 방지
- 필터 밖 선수 변경 방지
- 부분 실패 rollback

---

# Phase 12. 로컬라이제이션

## [ ] 12.1 UI 한국어/English

모든 UI 문구는 translation layer를 통과한다.
언어 변경은 settings에 저장한다.

## [ ] 12.2 선수 이름 한글 매핑

### 파일
- korean_last_names.csv
- korean_first_names.csv
- korean_names_pending.csv

### 기능
- import 중 미등록 이름 pending 수집
- 자동 추천
- 사용자 수정
- 사용자 매핑 우선

UI 언어와 선수명 한글 표시는 독립 설정으로 유지한다.

---

# Phase 13. 번들 정책 업데이트

## [ ] 13.1 bundle manifest

앱 업데이트로 새 milestone/name seed/policy가 추가됐을 때 사용자 파일에 안전하게 병합한다.

### 규칙
- 사용자 수정값 덮어쓰기 금지
- 신규 key만 자동 병합
- 충돌은 사용자 검토 대상으로 남김

---

# Phase 14. Advanced Tools / 복구 도구

## [ ] 14.1 개별 박스스코어 재import

선택 파일 1개를 복구 목적으로 다시 처리한다.

## [ ] 14.2 Spring Training 제거

스프링 트레이닝 경기를 명시적으로 찾아 운영 기록에서 제거한다.

## [ ] 14.3 Regular Season recovery

삭제/누락 이후 boxscore source를 다시 스캔해 빠진 정규시즌 경기를 복구한다.

## [ ] 14.4 Season isolation validation

### 기능
운영 DB를 수정하지 않고 별도 validation DB에 시즌 전체를 replay한다.

### 결과
- 게임 수
- 이벤트 수
- excluded/error 수
- 운영 DB와의 차이
- JSON report

## [ ] 14.5 현재 세이브 DB 초기화

삭제 전 DB summary와 대상 경로를 표시하고 명시적 확인을 요구한다.

---

# Phase 15. 배포 / 품질

## [ ] 15.1 테스트 계층

필수 테스트:
- parser fixtures
- DB migration
- import idempotency
- milestone crossing
- composite milestones
- ratio qualification
- streak extend/end
- prediction math
- manual-player merge
- modified-source reimport
- message save rollback
- save isolation

## [ ] 15.2 Windows 배포

- PyInstaller build
- 사용자 데이터는 `%APPDATA%/OOTP_Milestone_Tracker_V0.2/` 등 별도 영역
- exe 교체 후 DB/settings/user CSV 유지

## [ ] 15.3 E2E acceptance flow

최종적으로 아래 흐름이 실제 세이브 fixture에서 끊김 없이 동작해야 한다.

```text
새 설치
→ 언어/세이브 설정
→ baseline stats import
→ boxscore import
→ 선수 시즌/통산 기록 표시
→ 마일스톤 자동 생성
→ Achievement Records 조회
→ Prediction 생성
→ Streak 갱신
→ 추가 boxscore import
→ 중복 없이 누적
→ 뉴스 스캔/검토/승인
→ 수동 기록 추가
→ 앱 재시작
→ 모든 데이터 유지
```

---

# 구현 우선순위 요약

## P0 — 반드시 먼저
- 설정/경로
- 세이브별 DB
- stats parser
- boxscore parser
- import idempotency
- 시즌/통산 집계
- 경기/시즌/통산 마일스톤
- Settings / Import Center / Achievement Records / Player Stats

## P1 — 핵심 제품 완성
- Dashboard
- Prediction
- Streak
- Manual Records
- 커스텀 팀
- 시즌 ratio finalize

## P2 — 자동화/파워유저
- 뉴스 메시지 자동화
- 레이팅 편집
- 선수명 한글화
- UI 다국어

## P3 — 운영 안정화
- bundle update
- 수정 source recovery
- season validation
- DB reset
- 배포/업데이트 보존

---

# 작업자가 반드시 읽을 문서

1. [`docs/DATA_AND_DB_SPEC.md`](docs/DATA_AND_DB_SPEC.md) — DB 구조, 세이브 분리, transaction, source fingerprint, migration 원칙
2. [`docs/RULES_AND_POLICIES.md`](docs/RULES_AND_POLICIES.md) — 마일스톤/streak/prediction 기준과 정책 파일 작성 원칙

기능을 구현하다 위 문서와 충돌하는 임시 설계가 필요하면 코드에 바로 박아 넣지 말고, 먼저 문서를 갱신해 새 계약을 명시한다.
