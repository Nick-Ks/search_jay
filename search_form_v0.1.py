import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from datetime import datetime
import logging
import os
import argparse
import re

def extract_form_urls(text, keyword):
    """텍스트에서 키워드가 포함된 URL 추출"""
    # 더 정확한 패턴 매칭을 위한 정규식
    patterns = [
        # https://forms.gle/xxxx 형식
        rf'https?://{keyword}/[A-Za-z0-9_-]+',
        # forms.gle/xxxx 형식
        rf'{keyword}/[A-Za-z0-9_-]+',
    ]
    
    urls = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        urls.extend(found)
    
    # URL 정제 및 정규화
    cleaned_urls = []
    seen_normalized = set()
    
    for url in urls:
        # 프로토콜이 없는 경우 추가
        if not url.startswith('http'):
            url = 'https://' + url
        
        # 정규화
        normalized = normalize_url(url)
        
        # 중복 체크 및 추가
        if normalized not in seen_normalized:
            seen_normalized.add(normalized)
            cleaned_urls.append(url)
    
    return cleaned_urls

def setup_argument_parser():
    """커맨드 라인 인자 파서 설정"""
    parser = argparse.ArgumentParser(description='Google Search Automation Tool')
    parser.add_argument('-k', '--keyword', type=str, default='',
                        help='검색 키워드 (선택사항)')
    parser.add_argument('-s', '--start', type=int, default=1,
                        help='시작 페이지 번호 (기본값: 1)')
    parser.add_argument('-c', '--cnt', type=int, default=1,
                        help='검색할 페이지 수 (기본값: 1)')
    parser.add_argument('-f', '--form', type=str, choices=['g', 'n'], default='g',
                        help='폼 유형 (g: forms.gle, n: naver.me, 기본값: g)')
    return parser

def get_form_type(form_code):
    """폼 코드를 실제 검색어로 변환"""
    form_types = {
        'g': 'forms.gle',
        'n': 'naver.me'
    }
    return form_types.get(form_code, 'forms.gle')

def normalize_url(url):
    """URL 정규화 (프로토콜 제거 및 끝부분 정리)"""
    url = url.lower()
    url = url.replace('https://', '').replace('http://', '')
    url = url.rstrip('.,')
    # URL 끝의 추가 문자 제거
    url = re.sub(r'[^A-Za-z0-9_/-].*$', '', url)
    return url

def setup_logging():
    """로깅 설정"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'search_{timestamp}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def setup_driver():
    """Selenium WebDriver 설정"""
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless=new')  # 새로운 headless 모드 사용
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logging.error(f"드라이버 설정 중 오류 발생: {str(e)}")
        raise

def extract_search_results(driver, keyword):
    """검색 결과에서 URL 추출"""
    logger = logging.getLogger(__name__)
    results = []
    try:
        logger.info("현재 페이지 URL: %s", driver.current_url)
        
        search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
        logger.info(f"총 {len(search_results)}개의 검색 결과 항목 발견")
        
        for idx, result in enumerate(search_results, 1):
            try:
                link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                title = result.find_element(By.CSS_SELECTOR, "h3").text
                try:
                    snippet = result.find_element(By.CSS_SELECTOR, "div.VwiC3b").text
                except NoSuchElementException:
                    snippet = "스니펫 없음"

                # 각 부분에서 폼 URL 추출
                url_forms = extract_form_urls(link, keyword)
                title_forms = extract_form_urls(title, keyword)
                snippet_forms = extract_form_urls(snippet, keyword)
                
                # 모든 폼 URL을 하나의 집합으로 합치기 (중복 제거)
                all_forms = set(url_forms + title_forms + snippet_forms)
                
                logger.info(f"\n검색결과 #{idx}")
                logger.info(f"URL: {link}")
                logger.info(f"제목: {title}")
                logger.info(f"스니펫: {snippet}")
                logger.info("발견된 폼 URL:")
                logger.info(f"- URL에서: {url_forms}")
                logger.info(f"- 제목에서: {title_forms}")
                logger.info(f"- 스니펫에서: {snippet_forms}")
                logger.info(f"- 중복 제거 후 총 개수: {len(all_forms)}")
                
                if all_forms:  # 폼 URL이 하나라도 발견된 경우
                    results.append({
                        'url': link,
                        'title': title,
                        'snippet': snippet,
                        'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'form_urls': list(all_forms),  # 발견된 모든 고유한 폼 URL
                        'form_urls_count': len(all_forms),  # 중복 제거된 폼 URL 개수
                        'url_forms': url_forms,  # URL에서 발견된 폼 URL
                        'title_forms': title_forms,  # 제목에서 발견된 폼 URL
                        'snippet_forms': snippet_forms  # 스니펫에서 발견된 폼 URL
                    })
                    logger.info("결과 수집됨\n")
                else:
                    logger.info("폼 URL 미발견으로 제외됨\n")
                    
            except NoSuchElementException as e:
                logger.error(f"결과 #{idx} 처리 중 요소를 찾을 수 없음: {str(e)}")
            except Exception as e:
                logger.error(f"결과 #{idx} 처리 중 오류 발생: {str(e)}")
                
    except Exception as e:
        logger.error(f"결과 추출 중 오류 발생: {str(e)}")
    
    logger.info(f"최종 수집된 결과 수: {len(results)}")
    return results

def has_next_page(driver):
    """다음 페이지 존재 여부 확인"""
    try:
        next_button = driver.find_element(By.ID, "pnnext")
        return True
    except NoSuchElementException:
        return False

def go_to_next_page(driver):
    """다음 페이지로 이동"""
    try:
        next_button = driver.find_element(By.ID, "pnnext")
        next_button.click()
        time.sleep(random.uniform(2, 4))  # 페이지 로딩 대기
        return True
    except Exception as e:
        logging.error(f"다음 페이지 이동 중 오류 발생: {str(e)}")
        return False

def go_to_specific_page(driver, start_page):
    """특정 페이지로 직접 이동"""
    if start_page > 1:
        try:
            current_url = driver.current_url
            if 'start=' in current_url:
                new_url = current_url.split('start=')[0] + f'start={((start_page-1)*10)}'
            else:
                new_url = current_url + f'&start={((start_page-1)*10)}'
            
            driver.get(new_url)
            time.sleep(random.uniform(2, 4))
            return True
        except Exception as e:
            logging.error(f"특정 페이지 이동 중 오류 발생: {str(e)}")
            return False
    return True

def save_results(results, filename):
    """결과를 CSV 파일로 저장"""
    df = pd.DataFrame(results)
    
    # form_urls 리스트를 문자열로 변환
    if 'form_urls' in df.columns:
        df['form_urls'] = df['form_urls'].apply(lambda x: '\n'.join(x) if x else '')
        df['url_forms'] = df['url_forms'].apply(lambda x: '\n'.join(x) if x else '')
        df['title_forms'] = df['title_forms'].apply(lambda x: '\n'.join(x) if x else '')
        df['snippet_forms'] = df['snippet_forms'].apply(lambda x: '\n'.join(x) if x else '')
    
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    logging.info(f"{len(results)}개의 결과를 {filename}에 저장함")

def search_google(keyword, form_type, page_count, start_page):
    """구글 검색 수행"""
    logger = logging.getLogger(__name__)
    driver = setup_driver()
    all_results = []
    current_page = start_page
    end_page = start_page + page_count - 1
    
    try:
        logger.info("Google 검색 페이지로 이동")
        # 구글 검색 페이지로 이동
        driver.get("https://www.google.com")
        time.sleep(random.uniform(1, 2))

        logger.info(f"현재 페이지 제목: {driver.title}")


        # 검색어 입력
        search_query = f'"{form_type}"'
        if keyword:
            search_query = f'{keyword} {search_query}'
        logger.info(f"검색어: {search_query}")
        
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(random.uniform(2, 3))


        # 시작 페이지로 이동
        if not go_to_specific_page(driver, start_page):
            logger.error(f"시작 페이지({start_page})로 이동 실패")
            return all_results
            
        logger.info(f"검색 시작: 키워드='{keyword}'")
        logger.info(f"페이지 범위: {start_page} ~ {end_page}")
        
        while current_page <= end_page:
            logger.info(f"현재 페이지: {current_page}")
            
            # form_type으로 URL 추출
            results = extract_search_results(driver, form_type)
            for result in results:
                result['page_number'] = current_page
            all_results.extend(results)
            
            if current_page < start_page + page_count - 1:
                if not has_next_page(driver) or not go_to_next_page(driver):
                    logger.info("마지막 페이지 도달")
                    break
            
            current_page += 1
            time.sleep(random.uniform(2, 4))
            
    except Exception as e:
        logger.error(f"검색 중 오류 발생: {str(e)}")
    finally:
        driver.quit()
    
    return all_results

def main():
    # 인자 파서 설정 및 파싱
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # 로깅 설정
    logger = setup_logging()
    
    # 폼 타입 변환
    form_type = get_form_type(args.form)
    
    logger.info(f"\n검색 설정:")
    logger.info(f"- 검색 키워드: {args.keyword}")
    logger.info(f"- 시작 페이지: {args.start}")
    logger.info(f"- 검색할 페이지 수: {args.cnt}")
    logger.info(f"- 폼 유형: {form_type}")
    
    # 검색 실행 (키워드와 폼유형 분리 전달)
    results = search_google(args.keyword, form_type, args.cnt, args.start)
    
    # 최종 결과 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    final_filename = f'results_{args.form}_{timestamp}.csv'
    save_results(results, final_filename)
    
    # 검색 결과 요약 출력
    logger.info("\n검색 완료 요약:")
    logger.info(f"- 총 수집된 결과 수: {len(results)}")
    logger.info(f"- 결과 저장 파일: {final_filename}")

if __name__ == "__main__":
    main()
