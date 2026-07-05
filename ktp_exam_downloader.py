#!/usr/bin/env python3
"""
课堂派 章节测试题库下载器
Ketangpai Exam Downloader

从课堂派 API 拉取指定课程所有章节测试的题目、选项、正确答案和作答记录，
保存为 Markdown 题库文件，方便复习备考。
"""

import requests
import json
import time
import re
import sys
import os
import argparse
from datetime import datetime

__version__ = "1.0.0"


class KetangpaiClient:
    """课堂派 API 客户端"""

    BASE_URL = "https://openapiv5.ketangpai.com"

    def __init__(self, account: str, password: str):
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/json;charset=UTF-8",
        }
        self.account = account
        self.password = password
        self.token = None

    # ── 登录 ──────────────────────────────────────────────

    def login(self) -> dict:
        """登录课堂派，获取 token"""
        resp = self.session.post(
            f"{self.BASE_URL}/UserApi/login",
            json={
                "email": self.account,
                "password": self.password,
                "remember": "0",
                "type": "login",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("status") != 1:
            raise RuntimeError(f"登录失败: {data.get('message', '未知错误')}")
        self.token = data["data"]["token"]
        self.session.headers["token"] = self.token
        return data["data"]

    # ── 课程 ──────────────────────────────────────────────

    def get_course_list(self, semester: str, term: int) -> list:
        """获取学期课程列表"""
        resp = self.session.post(
            f"{self.BASE_URL}/CourseApi/semesterCourseList",
            json={
                "isstudy": 1,
                "search": "",
                "semester": semester,
                "term": term,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("status") != 1:
            raise RuntimeError(f"获取课程列表失败: {data.get('message')}")
        return data["data"]

    def find_course(self, keyword: str, semester: str, term: int) -> dict:
        """按关键词搜索课程"""
        courses = self.get_course_list(semester, term)
        for c in courses:
            if keyword in c.get("coursename", ""):
                return c
        print(f"\n未找到课程「{keyword}」，可用课程：")
        for c in courses:
            print(f"  - {c.get('coursename')} (ID: {c.get('id','')[:20]}...)")
        raise RuntimeError(f"未找到课程: {keyword}")

    # ── 章节测试 ──────────────────────────────────────────

    def get_chapter_tests(self, courseid: str) -> list:
        """获取课程下所有章节测试列表"""
        resp = self.session.post(
            f"{self.BASE_URL}/FutureV2/CourseMeans/getCourseContent",
            json={
                "contenttype": 6,
                "courseid": courseid,
                "courserole": 0,
                "desc": 3,
                "dirid": 0,
                "lessonlink": [],
                "limit": 50,
                "page": 1,
                "sort": [],
                "vtr_type": "",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("status") != 1:
            raise RuntimeError(f"获取章节列表失败: {data.get('message')}")
        return data["data"]["list"]

    # ── 题目 ──────────────────────────────────────────────

    def get_test_questions(self, testpaper_id: str, courseid: str) -> list:
        """获取某个测试的所有题目（含答案和作答记录）"""
        resp = self.session.post(
            f"{self.BASE_URL}/TestpaperApi/doSubjectList",
            json={
                "testpaperid": testpaper_id,
                "courseid": courseid,
                "reqtimestamp": int(time.time() * 1000),
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("status") != 1:
            raise RuntimeError(f"获取题目失败: {data.get('message')}")
        return data["data"]["lists"]

    # ── 其他 ──────────────────────────────────────────────

    @staticmethod
    def clean_html(html_text: str) -> str:
        """去除 HTML 标签"""
        return re.sub(r"<[^>]+>", "", html_text).strip()


def build_markdown(coursename: str, chapters: list, client: KetangpaiClient, courseid: str) -> str:
    """
    遍历所有章节，获取题目并生成 Markdown
    返回 Markdown 文本
    """
    md_lines = [
        f"# {coursename} — 章节测试题库\n",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"共 {len(chapters)} 个章节测试\n---\n",
    ]

    total_questions = 0
    total_done = 0
    total_score = 0.0

    for idx, chapter in enumerate(chapters, 1):
        title = chapter.get("title", "?")
        tp_id = chapter.get("testpaperid", chapter.get("id", ""))
        print(f"  [{idx}/{len(chapters)}] {title} ...", end=" ", flush=True)

        try:
            subjects = client.get_test_questions(tp_id, courseid)
            print(f"{len(subjects)} 题")
        except Exception as e:
            print(f"❌ {e}")
            md_lines.append(f"\n## {idx}. {title}\n\n*（获取失败: {e}）*\n")
            continue

        total_questions += len(subjects)
        md_lines.append(f"\n## {idx}. {title}\n共 {len(subjects)} 题\n")

        for i, subj in enumerate(subjects, 1):
            question = client.clean_html(subj.get("title", ""))
            q_type = subj.get("replenishtype", "?")
            score = subj.get("score", "0")
            my_score = subj.get("myscore", "")

            if my_score:
                total_score += float(my_score)
                total_done += 1

            score_display = f"{my_score}" if my_score else "未作答"
            md_lines.append(
                f"\n### 第{i}题 | {q_type} | {score}分 | 得分: {score_display}\n"
            )
            md_lines.append(f"{question}\n")

            options = subj.get("options", [])
            answer_ids = subj.get("answer", "").split("|") if subj.get("answer") else []
            my_answer_ids = subj.get("myanswer", "").split("|") if subj.get("myanswer") else []

            for opt in options:
                oid = opt.get("id", "")
                otext = client.clean_html(opt.get("title", ""))
                is_correct = oid in answer_ids
                is_mine = oid in my_answer_ids

                if is_correct and is_mine:
                    md_lines.append(f"- [x] **{otext}** ✅ ← 你的答案（正确）\n")
                elif is_correct:
                    md_lines.append(f"- [x] **{otext}** ✅ （正确答案）\n")
                elif is_mine:
                    md_lines.append(f"- [ ] ~~{otext}~~ ❌ ← 你的答案（错误）\n")
                else:
                    md_lines.append(f"- [ ] {otext}\n")

            explanation = client.clean_html(subj.get("explanation", ""))
            if explanation:
                md_lines.append(f"\n> 💡 解析: {explanation}\n")

        md_lines.append("\n---\n")

    # 统计摘要
    summary = (
        f"\n## 📊 统计摘要\n\n"
        f"| 项目 | 数值 |\n"
        f"|:---|---:|\n"
        f"| 章节数 | {len(chapters)} |\n"
        f"| 总题数 | {total_questions} |\n"
        f"| 已作答 | {total_done} |\n"
        f"| 总得分 | {total_score} |\n"
    )
    md_lines.append(summary)

    return "".join(md_lines)


def save_markdown(text: str, output_path: str):
    """保存 Markdown 到文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\n📄 已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="课堂派章节测试题库下载器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用示例:\n"
            "  %(prog)s -a 138xxxx -p your_pass -c 路基路面\n"
            "  %(prog)s -a 138xxxx -p your_pass -c 交通设计 -s 2025-2026 -t 2\n"
            "  %(prog)s --config config.json\n"
        ),
    )
    parser.add_argument("-a", "--account", help="课堂派账号（手机号/邮箱）")
    parser.add_argument("-p", "--password", help="课堂派密码")
    parser.add_argument("-c", "--course", help="课程名称关键词")
    parser.add_argument("-s", "--semester", default="2025-2026", help="学年，如 2025-2026")
    parser.add_argument("-t", "--term", type=int, default=2, help="学期 1 或 2")
    parser.add_argument("--config", help="配置文件路径（JSON 格式）")
    parser.add_argument("-o", "--output", help="输出目录（默认当前目录）")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    # ── 读取配置 ──────────────────────────────────────
    config = {}
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            config = json.load(f)

    account = args.account or config.get("account")
    password = args.password or config.get("password")
    course_keyword = args.course or config.get("course")
    semester = args.semester or config.get("semester", "2025-2026")
    term = args.term or config.get("term", 2)
    output_dir = args.output or config.get("output_dir") or os.getcwd()

    if not account or not password or not course_keyword:
        parser.print_help()
        print("\n❌ 错误: 必须提供账号、密码和课程名称关键词")
        print("   方式1: python ktp_exam_downloader.py -a 138xxxx -p pass -c 路基路面")
        print("   方式2: python ktp_exam_downloader.py --config config.json")
        sys.exit(1)

    # ── 执行 ──────────────────────────────────────────
    if not args.quiet:
        print(f"🔑 登录 {account} ...")

    client = KetangpaiClient(account, password)
    try:
        client.login()
        if not args.quiet:
            print(f"✅ 登录成功")

        # 查找课程
        if not args.quiet:
            print(f"🔍 搜索课程: {course_keyword} (学期 {semester} 第{term}学期)")
        course = client.find_course(course_keyword, semester, term)
        coursename = course["coursename"]
        courseid = course["id"]
        if not args.quiet:
            print(f"✅ 找到: {coursename}")

        # 获取章节测试
        if not args.quiet:
            print(f"📚 获取章节测试列表...")
        chapters = client.get_chapter_tests(courseid)
        if not args.quiet:
            print(f"✅ 共 {len(chapters)} 个章节测试\n")

        # 遍历获取题目 + 生成 Markdown
        md_text = build_markdown(coursename, chapters, client, courseid)

        # 保存
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", coursename)
        output_path = os.path.join(output_dir, f"{safe_name}_章节测试题库.md")
        save_markdown(md_text, output_path)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
