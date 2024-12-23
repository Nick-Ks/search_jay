# Google Forms URL Collector

구글 검색을 통해 forms.gle 또는 naver.me 형식의 URL을 수집하는 도구입니다.

## 설치 방법

### 1. Python 설치 확인
```bash
python --version  # Python 3.7 이상이어야 합니다
```

### 2. Chrome 및 ChromeDriver 설치

#### RHEL/Rocky Linux/CentOS
```bash
# EPEL 저장소 추가
sudo dnf install epel-release

# Chrome 저장소 추가
sudo tee /etc/yum.repos.d/google-chrome.repo << 'EOF'
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
EOF

# Chrome 설치
sudo dnf install google-chrome-stable

# Chromium 및 ChromeDriver 설치
sudo dnf install chromium chromedriver
```

#### Ubuntu/Debian
```bash
# Chrome 설치
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

# Chromium 및 ChromeDriver 설치
sudo apt-get install chromium-browser chromium-chromedriver
```

### 3. Python 패키지 설치
```bash
# 필요한 패키지 설치
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용법
```bash
python script.py [-k KEYWORD] [-s START] [-c COUNT] [-f FORM]
```

### 파라미터 설명
- `-k, --keyword`: 검색할 키워드 (선택사항)
- `-s, --start`: 시작 페이지 번호 (기본값: 1)
- `-c, --cnt`: 검색할 페이지 수 (기본값: 1)
- `-f, --form`: 폼 유형 (g: forms.gle, n: naver.me, 기본값: g)

### 사용 예시

1. 기본 검색 (forms.gle, 1페이지)
```bash
python script.py
```

2. 키워드와 함께 검색
```bash
python script.py -k "설문조사"
```

3. naver.me 3페이지부터 2페이지 검색
```bash
python script.py -f n -s 3 -c 2
```

4. forms.gle 2페이지부터 5페이지 검색
```bash
python script.py -s 2 -c 5
```

## 결과 파일

- 검색 결과는 CSV 파일로 저장됩니다.
- 파일명 형식: `results_{폼유형}_{타임스탬프}.csv`
- 결과 파일에는 다음 정보가 포함됩니다:
  - url: 검색 결과 URL
  - title: 검색 결과 제목
  - snippet: 검색 결과 스니펫
  - form_urls: 발견된 모든 고유한 폼 URL
  - form_urls_count: 발견된 폼 URL 개수
  - url_forms: URL에서 발견된 폼 URL
  - title_forms: 제목에서 발견된 폼 URL
  - snippet_forms: 스니펫에서 발견된 폼 URL
  - page_number: 검색 결과 페이지 번호

## 로그

- 실행 중 발생하는 모든 로그는 `logs` 디렉토리에 저장됩니다.
- 로그 파일명 형식: `search_{타임스탬프}.log`

## 주의사항

1. 구글의 검색 정책에 따라 너무 많은 요청을 보내면 일시적으로 검색이 차단될 수 있습니다.
2. 안정적인 실행을 위해 페이지 수를 적절히 조절하여 사용하시기 바랍니다.
3. 네트워크 상태에 따라 검색 결과가 달라질 수 있습니다.
