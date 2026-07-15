# DummyDataGenerator

기존 SQLite 데이터베이스의 스키마(테이블, 컬럼, PK, FK, UNIQUE 제약)를 자동으로 읽어서
[Faker](https://faker.readthedocs.io/)로 그럴듯한 더미 데이터를 생성/삽입하는 CLI 툴입니다.

## 요구 사항

- Python 3.9 이상 (개발/테스트는 Python 3.14 기준)
- 대상 SQLite `.db` 파일 (테이블이 이미 만들어져 있어야 함 — 이 툴은 스키마를 생성하지 않고, 기존 스키마를 읽어 데이터만 채웁니다)

## 설치

1. 저장소 루트로 이동합니다.
2. 가상환경을 활성화합니다. (이미 `.venv`가 있다면 바로 활성화)

   ```powershell
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```

   ```bash
   # bash / Git Bash
   source .venv/Scripts/activate
   ```

3. 의존성을 설치합니다.

   ```bash
   pip install -r requirements.txt
   ```

## 빠른 시작

```bash
# 1. 스키마 확인 (테이블/컬럼/PK/FK/UNIQUE 목록 출력)
python -m dummydatagen --db path/to.db --list-tables

# 2. 모든 테이블에 기본 10개씩 더미 데이터 삽입
python -m dummydatagen --db path/to.db

# 3. 결과가 걱정되면 먼저 --dry-run으로 생성될 SQL만 확인
python -m dummydatagen --db path/to.db --rows 100 --dry-run
```

## 사용법 예시

```bash
# 모든 테이블에 100개씩 삽입
python -m dummydatagen --db path/to.db --rows 100

# 테이블별로 개수 지정 (지정하지 않은 테이블은 0개)
python -m dummydatagen --db path/to.db --rows users=50,posts=200,comments=500

# 재현 가능한 결과 (같은 seed면 항상 같은 데이터)
python -m dummydatagen --db path/to.db --rows 100 --seed 42

# 실제로 삽입하지 않고 생성될 INSERT SQL만 확인 (DB 변경 없음)
python -m dummydatagen --db path/to.db --rows 100 --dry-run

# 특정 테이블만 채우기 (나머지는 건드리지 않음)
python -m dummydatagen --db path/to.db --rows 100 --tables users,posts

# 스키마만 확인하고 종료
python -m dummydatagen --db path/to.db --list-tables

# 한국어 더미 데이터 (이름, 주소 등이 한국어로 생성됨)
python -m dummydatagen --db path/to.db --rows 100 --locale ko_KR

# 상세 로그 (테이블별 처리 진행 상황 출력)
python -m dummydatagen --db path/to.db --rows 100 -v
```

## CLI 옵션

| 옵션 | 필수 | 설명 |
|---|---|---|
| `--db PATH` | 예 | 대상 SQLite 파일 경로 |
| `--rows N` 또는 `--rows table=N,table2=M` | 아니오 (기본값 `10`) | 전체 테이블 기본 행 수 또는 테이블별 개수 |
| `--tables t1,t2` | 아니오 (기본: 전체) | 지정한 테이블만 채움 |
| `--seed INT` | 아니오 | 재현 가능한 랜덤 시드 |
| `--dry-run` | 아니오 | INSERT 실행 없이 SQL만 출력 |
| `--locale LOCALE` | 아니오 (기본 `en_US`) | Faker locale (예: `ko_KR`, `ja_JP`) |
| `--list-tables` | 아니오 | 스키마 요약만 출력하고 종료 |
| `-v`, `--verbose` | 아니오 | 처리 중인 테이블/행 수를 로그로 출력 |

## 동작 방식

1. `PRAGMA table_info` / `PRAGMA foreign_key_list` / `PRAGMA index_list`로 스키마를 읽습니다.
2. FK 의존성을 위상 정렬해 부모 테이블부터 채웁니다 (순환 참조가 있으면 에러 메시지를 출력하고 종료).
3. 컬럼 이름(`email`, `name`, `phone`, `created_at` 등)에 따라 적절한 Faker 값을 매핑하고,
   이름으로 매핑되지 않으면 SQLite 컬럼 타입(affinity)에 따라 값을 생성합니다.
4. FK 컬럼은 이미 생성된 부모 테이블의 실제 PK 값 중에서 랜덤하게 선택합니다.
5. `INTEGER PRIMARY KEY` 컬럼은 값 생성 없이 SQLite의 자동 증가(rowid)에 위임합니다.
6. 전체 작업은 하나의 트랜잭션으로 처리되어, 중간에 실패하면 전부 롤백됩니다. `--dry-run`도 항상 롤백됩니다.

## 제약 사항 (v1 범위 밖)

- 복합(다중 컬럼) UNIQUE/PK 조합의 완전한 유일성 보장은 지원하지 않습니다 (단일 컬럼 UNIQUE만 지원).
- SQLite 외 다른 DB는 지원하지 않습니다.
- CHECK 제약 파싱, 확률적 NULL 생성은 지원하지 않습니다.
- 부모 테이블에 행이 없는 상태로 자식 테이블(NOT NULL FK)만 채우려 하면 에러가 발생합니다 — 부모 테이블을 먼저 채워야 합니다.

## 테스트

```bash
pytest
```
