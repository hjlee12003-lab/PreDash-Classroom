# 인증 및 배포 구조

## 구성과 요청 흐름
- `app.py`: Streamlit Secrets의 APP_PASSWORD와 공식 데이터 키를 읽습니다. 비밀번호가 없으면 앱 실행을 중단합니다. 비밀번호는 hmac.compare_digest로 비교하고 authorized를 세션에 기록합니다. 로그인 입력값은 성공 후 다음 실행에서 제거합니다.
- `predash/classroom.py`: 로그인 후 연결 설정에서 KIS 키·시크릿·계좌번호를 입력합니다. 잔고 조회 성공 시 해당 접속의 session_state에 자격정보와 KIS 객체를 보관합니다.
- `predash/kis.py`: 모의/실전 환경에 맞는 증권사 서버의 /oauth2/tokenP로 client_credentials 토큰을 발급받습니다. 토큰은 KIS 객체 메모리에 보관하고 만료 120초 전에 다시 발급합니다. API 조회에 Bearer 토큰과 appkey/appsecret을 사용합니다.
- 연결 해제는 세션을 지우고 앱 로그인 상태만 복원합니다. 로그아웃은 전체 세션을 지웁니다. 서버 메모리에서 참조를 제거하는 동작이며 증권사 토큰의 원격 폐기를 보장하지 않습니다.

## 비밀번호와 키 처리
APP_PASSWORD는 앱 공통 비밀번호이며 사용자별 계정·MFA·OAuth 로그인은 아닙니다. 현재 비밀번호 시도 횟수 제한은 없습니다. APP_PASSWORD와 공식 데이터 API 키는 Streamlit Settings → Secrets에만 설정하세요. KIS 키는 앱 연결 폼에서 접속 세션에 입력합니다. 저장소에 실제 키나 계좌정보를 올리지 마세요. Secrets의 공식 데이터 키는 서버 환경변수에 복사되어 제공기관 요청에 사용됩니다. GitHub 연결 인증은 별도이며 앱이 GitHub 토큰을 이용하지 않습니다.

## Streamlit 배포
1. Streamlit Community Cloud에서 Create app → Deploy a public app from GitHub를 선택합니다.
2. Repository: hjlee12003-lab/PreDash-Classroom, Branch: main, Main file path: app.py.
3. Advanced settings 또는 앱 Settings → Secrets에 .streamlit.example.toml의 항목을 입력합니다. APP_PASSWORD는 본인이 직접 정하세요. 키 미설정 항목은 빈 문자열로 둡니다.
4. 배포 후 비밀번호 미설정 차단 → 로그인 → 관심종목 → 연결 설정을 확인합니다. 모의 환경으로 먼저 잔고 조회 권한을 확인하세요.
5. APP_PASSWORD는 앱 내부 접근 제어입니다. Cloud 자체 비공개 공유 설정과는 별개입니다.

비밀번호와 API 키 원문은 채팅이나 README에 붙여 넣지 마세요.
