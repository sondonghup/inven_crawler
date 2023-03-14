import requests
import argparse
from bs4 import BeautifulSoup as bs
from user_agent import generate_user_agent
import os


def crawl(category_list, page_num):
    """
    category_list : 카테고리 리스트, 크롤링 하고 싶은 게시글(댓글)의 카테고리
    page_num : 페이지 넘버
    """
    url = f"https://www.inven.co.kr/board/webzine/2097?iskin=maple&p{page_num}"

    header = {"User-Agent": generate_user_agent()}
    html = requests.get(url, headers=header)
    html = bs(html.text, "html.parser")
    posts = html.find_all("td", {"class": "tit"})

    for post in posts[5:]:  # 공지가 5개 고정인데 태그 값이 같아서 슬라이싱함
        post_category = (
            post.find("span", {"class": "category"}).text.replace("[", "").replace("]", "")
        )
        if post_category in category_list:
            post_info = post.find("a", {"class": "subject-link"})
            post_url = post_info["href"]
            post_url_code = post_url.split("/")[-1].split("?")[0]
            try:
                inven_comment_crawler(post_url_code)
            except Exception as e:
                with open("errors/error.tsv", "a", encoding="utf-8") as f:
                    f.write(f"{post_url}\t{e}\n")


def inven_comment_crawler(post_url_code):
    """
    post_url_code : 게시글 마다 고유한 포스트 url 코드이다
    title : 게시글 제목

    curl을 가져와서 converter로 돌려 headers, params 등등을 가져와서 request할때 같이 보내주었다.
    여기서 referer와 articlecode만 변경해주면서 크롤링
    """

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,de;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.inven.co.kr",
        "Referer": f"https://www.inven.co.kr/board/webzine/2097/{post_url_code}?iskin=maple",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }

    params = {
        "dummy": "1678809104039",
    }

    data = {
        "comeidx": "2097",
        "articlecode": f"{post_url_code}",
        "sortorder": "date",
        "act": "list",
        "out": "json",
        "replynick": "",
        "replyidx": "0",
        "uploadurl": "",
        "imageposition": "",
    }

    response = requests.post(
        "https://www.inven.co.kr/common/board/comment.json.php",
        params=params,
        headers=headers,
        data=data,
    )
    result = response.json()
    """
    name : 댓글 작성자
    comment : 댓글
    thumbs_up : 따봉 개수
    level : 댓글 작성자의 레벨
    """

    for comment_info in result["commentlist"][0]["list"]:
        name = comment_info["o_name"].replace("&amp;nbsp;", " ")
        comment = comment_info["o_comment"].replace("&amp;nbsp;", " ").replace("\n", " ")
        thumbs_up = comment_info["o_recommend"]
        level = comment_info["o_level"]
        with open("comments/comment.tsv", "a", encoding="utf-8") as f:
            f.write(f"{name}\t{comment}\t{thumbs_up}\t{level}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", default=1)
    parser.add_argument("-e", "--end", default=10)
    parser.add_argument("-g", "--category", default="이슈,기타")  # 카테고리

    """
    인벤 오픈 이슈 갤러리 카테고리 댓글을 크롤링 합니다.
    [유머]
    [이슈]
    [연예]
    [게임]
    [지식]
    [사진]
    [계층]
    [감동]
    [기타]
    """

    args = parser.parse_args()
    category_list = []
    category_list = args.category.split(",")

    if not os.path.exists("comments"):
        os.mkdir("comments")
    if not os.path.exists("errors"):
        os.mkdir("errors")

    for page_num in range(args.start, args.end, 1):
        crawl(category_list, page_num)
