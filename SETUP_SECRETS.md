# KOSPI Active Dashboard 설정 안내

현재 저장소에는 ETF 수집 코드와 GitHub Actions 자동 실행 파일이 올라가 있습니다. 남은 작업은 Google 서비스 계정과 GitHub Secrets 연결입니다.

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
