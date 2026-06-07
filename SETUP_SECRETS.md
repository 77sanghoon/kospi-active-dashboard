# KOSPI Active Dashboard 설정 안내

현재 저장소에는 ETF 수집 코드와 GitHub Actions 자동 실행 파일이 올라가 있습니다. Google Sheets를 저장소로 쓰고, GitHub Actions가 매 영업일 오전 10시 KST에 데이터를 수집합니다.

## 현재 연결된 Google Sheet

스프레드시트 ID:

```text
18q9uz7pDLz9hHx7LJWMsSdt5qvhJAPZYTL1nFolKSmc
```

스프레드시트 URL:

```text
https://docs.google.com/spreadsheets/d/18q9uz7pDLz9hHx7LJWMsSdt5qvhJAPZYTL1nFolKSmc/edit
```

## GitHub Secrets 등록

GitHub 저장소에서 아래로 이동합니다.

```text
Settings > Secrets and variables > Actions > New repository secret
```

아래 2개를 등록합니다.

| Secret name | Value |
| --- | --- |
| `GOOGLE_SPREADSHEET_ID` | `18q9uz7pDLz9hHx7LJWMsSdt5qvhJAPZYTL1nFolKSmc` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google Cloud 서비스 계정 JSON 전체 내용 |

`GOOGLE_SERVICE_ACCOUNT_JSON`은 JSON 파일 내용을 그대로 붙여넣습니다. 파일을 저장소에 올리면 안 됩니다.

## Google Sheet 공유

서비스 계정 JSON 안에서 아래 항목을 찾습니다.

```json
"client_email": "...@...iam.gserviceaccount.com"
```

이 이메일 주소를 Google Sheet에 편집자로 공유합니다.

## 저장소 공개 전환

GitHub Free 계정에서는 private repository로 GitHub Pages를 사용할 수 없으므로, 저장소를 public으로 전환합니다.

```text
Settings > General > Danger Zone > Change repository visibility > Make public
```

주의: 저장소와 배포 URL을 아는 사람은 접근할 수 있습니다. Google 서비스 계정 JSON 같은 민감정보는 Secrets에만 있어야 하며, 저장소 파일로 커밋하면 안 됩니다.

## 검색 노출 줄이기

워크플로는 대시보드 배포 직전에 아래 설정을 자동으로 넣습니다.

- `dashboard/robots.txt`: 모든 검색엔진 크롤링 차단 요청
- `dashboard/index.html`: `noindex,nofollow,noarchive,nosnippet` 메타태그 삽입
- `dashboard/vercel.json`: Vercel 배포 시 `X-Robots-Tag` 헤더 적용

이 설정은 검색 노출을 줄이는 용도입니다. 완전한 비공개나 접근 제한은 아닙니다.

## GitHub Pages 설정

GitHub 저장소에서 아래로 이동합니다.

```text
Settings > Pages
```

Build and deployment의 Source를 `GitHub Actions`로 설정합니다.

## 수동 실행 테스트

GitHub 저장소에서 아래로 이동합니다.

```text
Actions > KOSPI Active Daily Collector > Run workflow
```

처음 테스트는 기본값으로 실행하면 됩니다. 성공하면 Google Sheet에 날짜별 시트와 요약 시트가 생기고, GitHub Pages 대시보드가 배포됩니다.

## Vercel 메모

Vercel로도 배포할 수 있도록 `vercel.json`의 검색 차단 헤더 설정은 준비되어 있습니다. 다만 매일 최신 데이터를 Vercel에 자동 배포하려면 Vercel 프로젝트 연결과 별도 배포 토큰 설정이 추가로 필요합니다.

## 자동 실행 시간

워크플로는 매주 월-금 오전 10시 KST에 자동 실행됩니다.

```text
0 1 * * 1-5 UTC = 한국시간 평일 10:00
```

## 주의

- PC가 꺼져 있어도 GitHub Actions 클라우드 러너에서 실행됩니다.
- Google Drive/Sheets ChatGPT 커넥터 권한과 GitHub Actions 서비스 계정 권한은 별개입니다.
- 서비스 계정 이메일이 시트 편집자로 공유되지 않으면 Actions가 실패합니다.
- Secrets가 등록되지 않으면 `Check cloud setup` 단계에서 실패합니다.
