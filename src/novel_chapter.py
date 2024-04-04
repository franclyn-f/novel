from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage

import os
# 需要设置真实使用的key
os.environ["DASHSCOPE_API_KEY"] = ""


def get_file_content(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        return "\n".join(file.readlines())

def get_content(llm, prompt: str):
    res = llm.stream([HumanMessage(content=prompt)], streaming=True)
    content = ""
    last = ""
    for r in res:
        resp = last + str(r).replace("content='", "")[:-1]
        if resp.count("response_metadata") != 0:
            continue
        for item in resp.split("\\n")[0:-1]:
            content = content + item + "\n"
            print(item)
        last = resp.split("\\n")[-1]
    content = content + last + "\n"
    print(last)
    return content


def save_content(content, file_name):
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(str(content) + "\n")
        file.flush()


def get_chapter_title_prompt(summary, completed_chapter_num):
    prompt = """
    你是一位优秀的网文作者，擅长写玄幻小说，现在你需要写一篇玄幻小说，讲述一个少年逆天改命的故事，
    请为主角起一个听起来比较真实而好听的名字，不要跟有名的角色重名，全文大概100万字，其中每章大概2500-3000字，
    现在需要你将章节的标题给出，请注意如果现在还没有章节标题，请输出第一个章节的标题，如果已经存在章节标题，请
    给出现在已经存在的最新章节的下一个章节对应的标题，注意只输出一个章节的标题与对应的序号，不要输出多余的内容
    """
    if len(summary) > 0:
        prompt = f"""{prompt}

        以下是这篇小说之前内容的总结：
        {summary}
        """
    chapter_title_prompt = prompt
    if completed_chapter_num > 0:
        chapter_title_prompt = f"""{chapter_title_prompt}

        目前已经写了{completed_chapter_num}个章节，请你继续给出下一个章节的标题
        """
    return chapter_title_prompt


def get_chapter_prompt(title_info, chapter_content, chapter_num):
    prompt = "你是一位优秀的网文作者，擅长写玄幻小说，现在你需要写一篇玄幻小说，讲述一个少年逆天改命的故事"
    if len(summary) > 0:
        prompt = f"""{prompt}

        以下是这篇小说之前内容的总结：
        {summary}
        """
    chapter_prompt = f"""
    {prompt}

    以下是最新章节的标题
    {title_info}

    请你根据现有故事情节以及最新章节的标题对内容进行续写，每一章节分为100小节，现在继续续写第{chapter_num}章的第{cnt}小节，
    请注意每一章的字数保持在2500字以上，每一章节的每小节在500字以上，请对每个小节增加细节描写，多对人物的语言、动作进行刻画，表明
    角色的性格以及角色之间的关系，并且对周围的环境也进行细致的刻画，请注意在开始的时候需要增加对世界观的描述，对这个世界的势力划分，
    人们的追求等有一个初步的描述
                    """
    if len(chapter_content) > 0:
        chapter_prompt = f"""{chapter_prompt}

        下面是这一章节已经有的续写内容：
        {chapter_content}
        """
    return chapter_prompt


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
    print("---------------------------------- prompt begin --------------------------------------")
    print(chapter_title_prompt)
    print("---------------------------------- prompt end --------------------------------------")
    title_info = get_content(llm, chapter_title_prompt)
    chapter_content = ""
    print("----------------------------------- chapter begin -----------------------------------")
    for cnt in range(1, 101):
        chapter_prompt = get_chapter_prompt(title_info, chapter_content, chapter_num + 1)
        print("----------------------------- chapter prompt begin ------------------------------")
        print(chapter_prompt)
        print("----------------------------- chapter prompt end ------------------------------")
        content = get_content(llm, chapter_prompt)
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
            print("----------------------------------- summary_prompt begin -----------------------------------")
            print(chapter_summary_prompt)
            print("----------------------------------- summary_prompt end -----------------------------------")
            summary = get_content(llm, chapter_summary_prompt)
            print("----------------------------------- summary begin -----------------------------------")
            print(summary)
            print("----------------------------------- summary end -----------------------------------")
            break
    print("----------------------------------- chapter end -----------------------------------")
    chapter_num += 1
    save_content(chapter_content, f"novels/{chapter_num}.txt")
    save_content(chapter_num, chapter_file_name)
    save_content(summary, summary_file_name)




