from selenium import webdriver
from selenium.webdriver.common.by import By
import sys
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from konlpy.tag import Okt
from collections import Counter, OrderedDict
import pandas as pd
import time

input_keyword = str(input("수집할 키워드를 입력하세요 : "))
input_pageNum = int(input("수집할 페이지 개수를 입력하세요 : "))

driver = webdriver.Chrome()
driver.maximize_window()
driver.get("https://www.naver.com")
time.sleep(1)
driver.find_element(By.XPATH, '//*[@id="query"]').send_keys(input_keyword)

driver.find_element(By.XPATH, '//*[@id="search_btn"]').click()
time.sleep(2)

driver.find_element(By.XPATH, '//a[@class="tab"][text()="뉴스"]').click()
time.sleep(2)
driver.minimize_window()


print(f"{input_keyword} 키워드 뉴스 검색 주소를 가져왔습니다.")
URL_BEFORE_KEYWORD = driver.current_url.replace(input_keyword, '')

# URL_BEFORE_KEYWORD = "https://search.naver.com/search.naver?where=news&sm=tab_pge&query="
URL_BEFORE_PAGE_NUM = "&sort=0&photo=0&field=0&pd=0&ds=&de=&cluster_rank=42&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so:r,p:all,a:all&start="

font_name = "Malgun Gothic"

# 주소 추출 함수
def get_link(input_keyword, input_pageNum):
    link = list()

    for page in range(input_pageNum):
        # 1 -> 11 -> 21 -> 31 ...
        currentPage = 1 + page * 10
        carwlingUrl = URL_BEFORE_KEYWORD + input_keyword + URL_BEFORE_PAGE_NUM + str(currentPage)

        response = requests.get(carwlingUrl)
        soup = BeautifulSoup(response.text, "lxml")

        # Class -> "." // ID -> "#"
        urlTag = soup.select(".news_tit")

        for url in urlTag:
            link.append(url["href"])

    print("뉴스 주소 추출 성공")
    return link

def get_article(url_link, file1):
    news_title_list = []
    news_content_list = []
    exist_url_link = []

    with open(file1, "w", encoding="utf8") as f:
        i = 1
        success_num = 0
        failed_num = 0
        print(f'총 {len(url_link)}개의 뉴스 기사가 검색되었습니다.')
        print("뉴스 기사 제목, 내용 추출을 시작합니다.")

        for url2 in url_link:
            article = Article(url2, language="ko")

            try:
                article.download()
                article.parse()
                success_num += 1
                print(f'{i}/{len(url_link)} 완료 ( •̀ㅂ•́)و  (성공: {success_num}, 실패: {failed_num})')
                i += 1
            except:
                failed_num += 1
                print(f'{i}/{len(url_link)} 실패 ヾ(｀ε´)ﾉ (성공: {success_num}, 실패: {failed_num})')
                i += 1
                continue

            news_title = article.title
            news_content = article.text

            news_title_list.append(news_title)
            news_content_list.append(news_content)
            exist_url_link.append(url2)

            f.write(news_title)
            f.write(news_content)

        f.close()
        print("뉴스 기사 제목, 내용 추출 완료")
        return news_title_list, news_content_list, exist_url_link

def topN_wordcount(news_title_list, news_content_list, topN_number):
    engine = Okt()
    topN_Dict_list = []

    for i in range(len(news_title_list)):
        nouns = []

        data = news_title_list[i] + ' ' + news_content_list[i]
        all_nouns = engine.nouns(data)
        nouns.extend([n for n in all_nouns if len(n) > 1])

        count = Counter(nouns)
        by_num = OrderedDict(sorted(count.items(), key=lambda t: t[1], reverse=True))

        word = [i for i in by_num.keys()]
        number = [i for i in by_num.values()]

        article_list = []

        for w, n in zip(word, number):
            final1 = f"{w}   {n}"
            article_list.append(final1)

        new_list = article_list[0:topN_number]

        topN_Dict = dict()
        for j in new_list:
            topN_Dict[j.split()[0]] = int(j.split()[1])
        topN_Dict_list.append(list(topN_Dict))
        print(f"{i}번째 데이터 처리 완료")

    print("데이터 처리 완료")

    return topN_Dict_list, article_list

def main(argv):
    file1 = "crawling1.txt"
    file2 = "wordcount_result.txt"
    topN_number = int(5)
    url_link = get_link(input_keyword, input_pageNum)
    news_title_list, news_content_list, exist_url_link = get_article(url_link, file1)
    topN_Dict_list, article_list = topN_wordcount(news_title_list, news_content_list, topN_number)

    # # 각 리스트의 길이 출력
    # print("news_title_list의 길이: ", len(news_title_list))
    # print("news_content_list의 길이: ", len(news_content_list))
    # print("exist_url_link의 길이: ", len(exist_url_link))
    # print("topN_Dict_list의 길이: ", len(topN_Dict_list))

    # 리스트들을 DataFrame으로 변환
    df = pd.DataFrame({
        '제목': news_title_list,
        '내용': news_content_list,
        '기사 URL': exist_url_link,
        '단어 5가지': topN_Dict_list
    })

    df['단어 5가지'] = df['단어 5가지'].apply(lambda x: ', '.join(x))

    # DataFrame 저장
    df.to_csv('selenium_naver_news.csv', index=False)
    print("all working's complete.")
    print(df)
if __name__ == '__main__':
    main(sys.argv)