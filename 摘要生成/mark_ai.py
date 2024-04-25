import os
from loguru import logger
from pprint import pprint
import frontmatter
import pangu
import random
from http import HTTPStatus

# 此处填写你从阿里云灵积模型服务获得的 key。注意不要泄露该 key，更稳妥的方法是用另外的方法将其写到环境变量中。
os.environ['DASHSCOPE_API_KEY'] = "sk-edabe02ebfb74fcc9103f0e566399924"

# 这条导入语句要写在赋环境变量之后
from dashscope import Generation


def tree(filepath, ignore_dir_names=None, ignore_file_names=None):
    """返回两个列表，第一个列表为 filepath 下全部文件的完整路径, 第二个为对应的文件名"""
    if ignore_dir_names is None:
        ignore_dir_names = []
    if ignore_file_names is None:
        ignore_file_names = []
    ret_list = []
    if isinstance(filepath, str):
        if not os.path.exists(filepath):
            logger.error("路径不存在: " + filepath)
            return None, None
        elif os.path.isfile(filepath) and os.path.basename(filepath) not in ignore_file_names:
            return [filepath], [os.path.basename(filepath)]
        elif os.path.isdir(filepath) and os.path.basename(filepath) not in ignore_dir_names:
            for file in os.listdir(filepath):
                fullfilepath = os.path.join(filepath, file)
                if os.path.isfile(fullfilepath) and os.path.basename(fullfilepath) not in ignore_file_names:
                    ret_list.append(fullfilepath)
                if os.path.isdir(fullfilepath) and os.path.basename(fullfilepath) not in ignore_dir_names:
                    ret_list.extend(tree(fullfilepath, ignore_dir_names, ignore_file_names)[0])
    return ret_list, [os.path.basename(p) for p in ret_list]


# 定义一个函数call_with_messages，用于传入一段Markdown格式的文章，并返回文章的概要
def call_with_messages(content):
    # 定义一个消息列表，用于传入文章概要生成器
    messages = [{'role': 'system',
                 'content': '你是文章提纲生成器，我将会输入一段 Markdown 格式的文章，你需要解析输入的文章，理解其中的意思，最后给出它的概要，可以多一些，但是内容在200字以内。'},
                {'role': 'user', 'content': content}]
    # 实例化一个Generation对象
    gen = Generation()
    # 调用Generation对象的call方法，传入参数Models.qwen_turbo，messages，seed，result_format
    response = gen.call(
        Generation.Models.qwen_turbo,
        messages=messages,
        seed=random.randint(1, 10000),  # set the random seed, optional, default to 1234 if not set
        result_format='message',  # set the result to be "message" format.
    )
    # 判断请求状态码是否为200
    if response.status_code == HTTPStatus.OK:
        # 打印请求状态码
        logger.debug(response)
        # 打印概要
        logger.info(response.output.choices[0].message.content)
        # 返回概要
        return response.output.choices[0].message.content
    else:
        # 抛出异常
        raise RuntimeError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))


# 定义一个函数，从一个md文件中生成AI摘要
def gen_ai_abstract_from_one_md_file(md_path):
    # 加载md文件
    md = frontmatter.load(md_path)
    # 如果md文件中没有ai或者YOU_NEED_TO_ADD_ABSTRACT_MANUALLY，则尝试生成摘要
    if 'ai' not in md and 'YOU_NEED_TO_ADD_ABSTRACT_MANUALLY' not in md:
        try:
            # 使用pangu库对文本进行拼接
            abstract = pangu.spacing_text(call_with_messages(md.content))
            # 将摘要添加到md文件中
            md.content = '{% tip info %}AI摘要：' + abstract + '{% endtip %}' + '\n' + md.content
            # md['ai'] = abstract
            md['YOU_NEED_TO_ADD_ABSTRACT_MANUALLY'] = False
        except RuntimeError as e:
            logger.error(e)
            logger.error('你需要自行添加摘要')
            # 将YOU_NEED_TO_ADD_ABSTRACT_MANUALLY添加到md文件中
            md['YOU_NEED_TO_ADD_ABSTRACT_MANUALLY'] = True
        # 将md文件保存
        frontmatter.dump(md, md_path)
    else:
        logger.info('已添加，跳过')


if __name__ == '__main__':
    ROOT_PATH = r'D:\Desktop\hexo-old\source\_posts'
    file_lists = list(zip(*tree(ROOT_PATH)))
    for file_tuple in file_lists:
        if file_tuple[1].endswith('.md'):
            logger.info('当前处理文件：' + file_tuple[1])
            gen_ai_abstract_from_one_md_file(file_tuple[0])
