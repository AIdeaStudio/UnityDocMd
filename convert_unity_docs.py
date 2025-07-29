import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

def get_physical_core_count():
    """
    获取CPU物理核心数
    """
    try:
        # 对于Windows
        if os.name == 'nt':
            return int(os.environ.get('NUMBER_OF_PROCESSORS', multiprocessing.cpu_count()))
    except:
        # 如果所有方法都失败，默认返回8核心
        return 8

def clean_content(soup, is_scripting_api=False):
    """
    从soup中移除不需要的元素
    """
    # 移除头部、尾部、侧边栏和其他导航元素
    for element in soup.find_all(["header", "footer", "nav", "aside", "script", "style"]):
        element.decompose()
    
    # 移除特定的div类或id，这些不是主要内容的一部分
    for element in soup.find_all("div", class_=["header-wrapper", "toolbar", "mobileLogo", 
                                               "master-wrapper", "sidebar", "footer-wrapper",
                                               "nextprev", "breadcrumbs", "search-form"]):
        element.decompose()
        
    # 移除特定id的div
    for element_id in ["header", "sidebar", "footer", "VersionNumber", "OtherVersionsContent",
                       "versionsSelectMobile", "otherVersionsLegend", "VersionSwitcherArrow",
                       "lang-switcher", "mobileSearchBtn", "ot-sdk-btn-container", "_leavefeedback", "_content"]:
        element = soup.find(id=element_id)
        if element:
            element.decompose()
            
    # 移除特定类的div
    for element_class in ["header-wrapper", "toolbar", "mobileLogo", "master-wrapper", 
                          "sidebar", "footer-wrapper", "nextprev", "breadcrumbs", 
                          "search-form", "toggle", "lang-list", "otherversionscontent",
                          "legendBox", "filler", "menu", "spacer", "more", "logo",
                          "version-switcher", "sidebar-version-switcher", "sidebar-search-form",
                          "ui-field-contain", "arrow", "lbl", "b", "tip", "icon", "tt"]:
        for element in soup.find_all("div", class_=element_class):
            element.decompose()
    
    # 对于Scripting API页面，移除反馈和建议表单
    if is_scripting_api:
        # 移除反馈和建议元素
        for element_class in ["scrollToFeedback", "suggest", "suggest-wrap", "suggest-success", 
                             "suggest-failed", "suggest-form", "loading"]:
            for element in soup.find_all("div", class_=element_class):
                element.decompose()
        
        # 移除与反馈相关的特定标签和输入
        for element in soup.find_all(["label", "input", "textarea", "button"], {"id": re.compile(r"suggest_.*")}):
            element.decompose()
            
        # 移除与反馈相关的特定链接和按钮
        for element in soup.find_all(["a", "button"], class_=["sbtn", "close", "cancel", "submit"]):
            # 仅当它们是反馈/建议系统的一部分时才移除
            if any(keyword in (element.get_text() or "") for keyword in ["Leave feedback", "Suggest a change", "Success!", "Submission failed", "Submit suggestion", "Cancel"]):
                element.decompose()

def clean_markdown(markdown_text):
    """
    通过移除额外的格式来清理markdown文本
    """
    # 移除多余的换行符
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
    
    # 移除前导/尾随空白字符
    markdown_text = markdown_text.strip()
    
    return markdown_text

def convert_html_links_to_md(markdown_text):
    """
    将markdown文本中的HTML链接转换为MD链接
    例如: [text](SomePage.html) -> [text](SomePage.md)
    """
    # 匹配HTML链接的正则表达式
    # 匹配格式: [text](SomePage.html) 或 [text](./SomePage.html) 或 [text](../SomePage.html)
    html_link_pattern = r'(\[([^\]]+)\]\([^)]*\.html(?:[^)]*)?\))'
    
    def replace_html_link(match):
        link_text = match.group(0)
        # 将.html替换为.md
        md_link = re.sub(r'\.html(?=[^)]*\))', '.md', link_text)
        return md_link
    
    # 替换所有HTML链接为MD链接
    markdown_text = re.sub(html_link_pattern, replace_html_link, markdown_text)
    
    return markdown_text

def convert_code_blocks_to_csharp(markdown_text):
    """
    将markdown文本中的代码块标签转换为CSHARP高亮
    例如: ``` 转换为 ```csharp
    同时确保结束标记正确
    """
    # 按行处理，更精确地控制转换
    lines = markdown_text.split('\n')
    new_lines = []
    in_code_block = False
    code_block_language = None
    
    for line in lines:
        stripped_line = line.strip()
        
        # 检查是否是代码块开始或结束标记
        if stripped_line.startswith('```'):
            if stripped_line == '```':
                # 没有语言标识的代码块标记
                if not in_code_block:
                    # 开始一个新的无语言标识的代码块
                    new_lines.append('```csharp')
                    in_code_block = True
                    code_block_language = 'csharp'
                else:
                    # 结束代码块
                    new_lines.append('```')
                    in_code_block = False
                    code_block_language = None
            else:
                # 有语言标识的代码块标记
                if not in_code_block:
                    # 开始一个新的有语言标识的代码块
                    new_lines.append(line)  # 保持原样
                    in_code_block = True
                    # 提取语言标识
                    lang = stripped_line[3:].strip()
                    code_block_language = lang if lang else None
                else:
                    # 结束代码块
                    new_lines.append('```')
                    in_code_block = False
                    code_block_language = None
        else:
            # 普通行
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def convert_single_file(args):
    """
    转换单个HTML文件为Markdown
    """
    html_file_path, output_dir, input_root = args
    try:
        # 读取HTML文件
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 判断是否为Scripting API页面
        is_scripting_api = "ScriptReference" in str(html_file_path)
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取主要内容
        content_wrap = soup.find('div', id='content-wrap')
        
        if not content_wrap:
            print(f"警告: 在 {html_file_path} 中未找到content-wrap")
            # 如果未找到content-wrap，回退到body
            content_wrap = soup.find('body')
        
        if content_wrap:
            # 通过移除不需要的元素来清理内容
            clean_content(content_wrap, is_scripting_api)
            
            # 查找content-wrap内的主要内容div
            content_block = content_wrap.find('div', class_='content')
            if content_block:
                # 处理表格以清理工具提示内容
                for table in content_block.find_all('table'):
                    for td in table.find_all('td'):
                        # 移除工具提示span但保留其文本内容
                        for tooltip in td.find_all('span', class_='tooltip'):
                            tooltip.unwrap()
                        for tooltip_text in td.find_all('span', class_='tooltiptext'):
                            tooltip_text.decompose()
                        for glossary_link in td.find_all('a', class_='tooltipGlossaryLink'):
                            glossary_link.decompose()
                        for more_info_link in td.find_all('a', class_='tooltipMoreInfoLink'):
                            more_info_link.decompose()
                
                # 使用markdownify转换为Markdown
                markdown_content = md(str(content_block), heading_style="ATX")
                
                # 清理markdown文本
                markdown_content = clean_markdown(markdown_content)
                
                # 转换HTML链接为MD链接
                markdown_content = convert_html_links_to_md(markdown_content)
                
                # 转换代码块为C#高亮
                markdown_content = convert_code_blocks_to_csharp(markdown_content)
                
                # 生成输出文件路径，保持目录结构
                relative_path = os.path.relpath(html_file_path, input_root)
                output_file_path = os.path.join(output_dir, relative_path)
                output_file_path = os.path.splitext(output_file_path)[0] + ".md"
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                
                # 将Markdown内容写入文件
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                return f"已转换 {html_file_path} 为 {output_file_path}"
            else:
                return f"错误: 在 {html_file_path} 中未找到内容块"
        else:
            return f"错误: 在 {html_file_path} 中未找到内容"
    except Exception as e:
        return f"转换 {html_file_path} 时出错: {str(e)}"

def batch_convert(input_dir, output_dir="output", max_workers=None):
    """
    使用并行处理将目录中的HTML文件批量转换为Markdown
    
    参数:
        input_dir (str): 包含要转换的HTML文件的目录
        output_dir (str): 保存Markdown文件的目录
        max_workers (int): 最大工作线程数。默认为CPU物理核心数
    """
    # 确保输入目录存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录 {input_dir} 不存在")
        return
    
    # 设置默认max_workers为CPU物理核心数
    if max_workers is None:
        max_workers = get_physical_core_count()
        print(f"使用 {max_workers} 个工作线程 (CPU物理核心数)")
    
    # 查找输入目录中的所有HTML文件
    html_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))
    
    print(f"找到 {len(html_files)} 个HTML文件，使用 {max_workers} 个线程进行转换")
    
    # 准备并行处理的参数
    args = [(html_file, output_dir, input_dir) for html_file in html_files]
    
    # 并行转换文件
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {executor.submit(convert_single_file, arg): arg[0] for arg in args}
        
        # 处理已完成的任务
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                print(result)
            except Exception as e:
                print(f"转换 {file} 时出错: {str(e)}")

def check_directories():
    """
    检查当前目录中是否存在Manual和ScriptReference目录
    """
    manual_dir = Path("Manual")
    script_ref_dir = Path("ScriptReference")
    
    manual_exists = manual_dir.exists() and manual_dir.is_dir()
    script_ref_exists = script_ref_dir.exists() and script_ref_dir.is_dir()
    
    return manual_exists, script_ref_exists

def convert_single_html_file(input_file, output_file=None):
    """
    转换单个HTML文件为Markdown
    
    参数:
        input_file (str): 输入HTML文件路径
        output_file (str): 输出Markdown文件路径，默认为输入文件名改为.md
    """
    import os
    import sys
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 {input_file} 不存在")
        return False
    
    # 设置输出文件路径
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".md"
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 调用现有的单文件转换函数
    result = convert_single_file((input_file, os.path.dirname(output_file), os.path.dirname(input_file)))
    
    if "已转换" in result:
        print(result)
        return True
    else:
        print(f"转换失败: {result}")
        return False

def main():
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 如果提供了命令行参数，认为是要转换单个文件
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        if convert_single_html_file(input_file, output_file):
            print("单文件转换完成!")
        else:
            print("单文件转换失败!")
        return
    
    # 检查所需目录是否存在
    manual_exists, script_ref_exists = check_directories()
    
    if not manual_exists and not script_ref_exists:
        print("错误: 当前目录中未找到 'Manual' 和 'ScriptReference' 目录")
        print("请将 'Manual' 和/或 'ScriptReference' 目录放置在当前文件夹中，然后重新运行脚本")
        return
    
    # 确定要转换的目录
    dirs_to_convert = []
    if manual_exists:
        dirs_to_convert.append(("Manual", "output-manual"))
    if script_ref_exists:
        dirs_to_convert.append(("ScriptReference", "output-script"))
    
    # 打印将要转换的内容
    print("将转换以下目录:")
    for src, dst in dirs_to_convert:
        print(f"  - {src} -> {dst}")
    
    # 请求用户确认
    response = input("\n是否开始转换? (y/n): ").strip().lower()
    if response not in ['y', 'yes']:
        print("转换已取消")
        return
    
    # 获取CPU物理核心数
    max_workers = get_physical_core_count()
    print(f"\n使用 {max_workers} 个工作线程 (CPU物理核心数)")
    
    # 执行转换
    for src_dir, output_dir in dirs_to_convert:
        print(f"\n正在转换 {src_dir} 到 {output_dir}...")
        try:
            batch_convert(src_dir, output_dir, max_workers)
            print(f"完成转换 {src_dir}")
        except Exception as e:
            print(f"转换 {src_dir} 时出错: {str(e)}")
    
    print("\n所有转换已完成!")

if __name__ == "__main__":
    main()