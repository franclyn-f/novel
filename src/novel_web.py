from langchain_community.chat_models.tongyi import ChatTongyi
import streamlit as st
from novel_chapter import get_file_content, get_content, save_content
from novel_chapter import get_chapter_title_prompt, get_chapter_prompt


def split_string_by_length(string, length):
    return [string[i:i+length] for i in range(0, len(string), length)]


def content_callback(content):
    for item in split_string_by_length(str(content), 35):
        st.text(item)


def start():
    print("start")
    summary_file_name = "checkpoint/summary.txt"
    chapter_file_name = "checkpoint/chapter_num.txt"
    summary = get_file_content(summary_file_name)
    chapter_num = get_file_content(chapter_file_name)
    if chapter_num == "":
        chapter_num = 0
    else:
        chapter_num = int(chapter_num)

    while True:
        chapter_title_prompt = get_chapter_title_prompt(summary, chapter_num)
        llm = ChatTongyi()
        # llm.model_name = "qwen-plus"
        llm.model_name = "qwen1.5-72b-chat"
        llm.streaming = True
        llm.model_kwargs = {"temperature": "0.3"}
        # print("---------------------------------- prompt begin --------------------------------------")
        # print(chapter_title_prompt)
        # print("---------------------------------- prompt end --------------------------------------")
        title_info = get_content(llm, chapter_title_prompt, content_callback)
        chapter_content = ""
        print("----------------------------------- chapter begin -----------------------------------")
        for cnt in range(1, 101):
            chapter_prompt = get_chapter_prompt(title_info, chapter_content, chapter_num + 1, summary, cnt)
            # print("----------------------------- chapter prompt begin ------------------------------")
            # print(chapter_prompt)
            # print("----------------------------- chapter prompt end ------------------------------")
            content = get_content(llm, chapter_prompt, content_callback)
            chapter_content = chapter_content + content
            if len(chapter_content) > 2500:
                chapter_summary_prompt = ""
                if len(summary) > 0:
                    chapter_summary_prompt = f"""
                            以下是这篇小说前面部分内容的总结:
                            {summary}
    
                            """
                chapter_summary_prompt += f"""
                        以下是一篇小说中的最新一章的内容，请你将这篇小说之前的内容与现在这一章节的内容结合，给出整体的总结，总结之后的字数控制在两千字
                        以内,总结请至少分为三个部分
                        第一部分为主角以及与主角相关的人物名称、身份信息以及与主角之间的关系
                        第二部分为主角以及主角相关的角色的技能或者特点（包括长处和短处）
                        第三部分为主角过往经历的总结
                        请注意只根据现有内容进行总结，不要捏造事实，不要带入将来可能进行展开的情节
    
                        {chapter_content}
                        """
                # print("----------------------------------- summary_prompt begin -----------------------------------")
                # print(chapter_summary_prompt)
                # print("----------------------------------- summary_prompt end -----------------------------------")
                summary = get_content(llm, chapter_summary_prompt, content_callback)
                # print("----------------------------------- summary begin -----------------------------------")
                # print(summary)
                # print("----------------------------------- summary end -----------------------------------")
                break
        print("----------------------------------- chapter end -----------------------------------")
        chapter_num += 1
        save_content(chapter_content, f"novels/{chapter_num}.txt")
        save_content(chapter_num, chapter_file_name)
        save_content(summary, summary_file_name)


if __name__ == "__main__":
    st.button("开始", on_click=start)