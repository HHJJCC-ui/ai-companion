# ================= 1. 导入必要的库 =================
import streamlit as st  # 导入 Streamlit 库，用于快速构建数据可视化 Web 应用
import os               # 导入 os 库，用于读取系统环境变量、操作文件路径等
from openai import OpenAI # 从 openai 库导入 OpenAI 类，DeepSeek API 兼容 OpenAI 格式，可直接用此 SDK
from datetime import datetime # 从 datetime 库导入 datetime 类，用于生成基于时间的唯一会话 ID
import json             # 导入 json 库，用于读写 JSON 格式的会话历史文件

# ================= 2. 页面基础配置 =================
# 注意：st.set_page_config 必须写在所有 Streamlit 命令的最前面！
st.set_page_config(
    page_title="hjc的AI应用",  # 设置浏览器标签页显示的标题
    page_icon="🚀",            # 设置浏览器标签页图标（支持 Emoji 表情）
    layout="wide",             # 设置页面布局模式："wide" 宽屏 / "centered" 居中
    initial_sidebar_state="expanded", # 设置侧边栏初始状态："expanded" 展开 / "collapsed" 收起
    menu_items={}              # 右上角菜单自定义（此处为空字典，不做自定义）
)


# --- 辅助函数定义区域 ---

# 定义生成会话标识的函数
def generate_session_id():
    """
    生成一个基于当前时间的唯一字符串ID
    格式例如：20260416123045
    """
    # 按 "年月日时分秒" 格式格式化当前时间并返回
    # 使用正确的 strftime 指令：%M 表示分钟，%S 表示秒，%m 表示月份
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")



# 定义保存会话信息的函数
def save_session_state():
    """
    将当前内存中的会话状态（昵称、性格、聊天记录）保存到本地 JSON 文件
    """
    # 只有当 st.session_state 中存在 current_session 时才执行保存
    if st.session_state.current_session:
        # 构建一个字典对象，存放所有需要保存的会话状态
        session_state = {
            "nick_name": st.session_state.nick_name,      # 保存伴侣昵称
            "nature": st.session_state.nature,            # 保存伴侣性格
            "current_session": st.session_state.current_session, # 保存当前会话ID
            "messages": st.session_state.messages,        # 保存聊天历史记录
        }
        # 检查 "session" 文件夹是否存在，不存在则创建
        if not os.path.exists("session"):
            os.mkdir("session") # 创建名为 "session" 的文件夹
        # 以写入模式打开 JSON 文件，文件名为当前会话ID
        with open(f"session/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            # 将 session_state 字典写入 JSON 文件，ensure_ascii=False 支持中文，indent=2 缩进格式化
            json.dump(session_state, f, ensure_ascii=False, indent=2)


# 定义创建新会话的函数
def create_session():
    """
    重置聊天记录，生成新的会话ID，并保存状态刷新页面
    """
    # 只有当聊天历史记录不为空时才执行（注意：此逻辑可能限制空会话创建，可按需调整）
    if st.session_state.messages:
        st.session_state.messages = []             # 清空聊天历史记录列表
        st.session_state.current_session = generate_session_id() # 生成新的会话ID
        save_session_state()                        # 保存这个新的空会话状态
        st.rerun()                                  # 重新运行 Streamlit 脚本，刷新页面

# 定义加载历史会话信息的列表函数
def load_session_history():
    session_list = [] # 初始化空列表，用于存放会话ID
    # 检查 "session" 文件夹是否存在
    if os.path.exists(f"session"):
        file_list = os.listdir("session") # 获取 "session" 文件夹下所有文件和文件夹名
        # 遍历文件列表
        for file in file_list:
            # 判断文件是否以 ".json" 结尾
            if file.endswith(".json"):
                session_list.append(file[:-5]) # 去掉文件后缀 ".json"，将会话ID加入列表
                session_list.sort(reverse=True) # 将会话列表按倒序排列（最新的在最上面）
    return session_list # 返回所有会话ID列表

#加载指定会话信息
def load_session(session_id):
    # 检查指定会话ID的JSON文件是否存在
    if os.path.exists(f"session/{session_id}.json"):
        # 以读取模式打开该JSON文件
        with open(f"session/{session_id}.json", "r", encoding="utf-8") as f:
            session_data = json.load(f) # 加载JSON文件内容到字典
            try:
                # 尝试从加载的字典中恢复各项会话状态
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_id
            except Exception as e:
                # 如果加载过程中出现任何错误，在界面上显示错误提示
                st.error(f"加载会话 {session_id} 失败：{e}")

#创建一个删除指定历史记录的函数
def delete_session(session_id):
    # 检查指定会话ID的JSON文件是否存在
    if os.path.exists(f"session/{session_id}.json"):
        try:
            os.remove(f"session/{session_id}.json") # 尝试删除该JSON文件
            st.success(f"会话 {session_id} 已删除") # 在界面上显示删除成功的提示
            # 如果删除的是当前正在使用的会话
            if session_id == st.session_state.current_session:
                st.session_state.messages = [] # 清空当前聊天历史记录列表
                st.session_state.nick_name = generate_session_id() # 重置昵称为新的时间戳
            st.rerun() # 删除会话后刷新页面显示最新历史记录
        except Exception as e:
            # 如果删除过程中出现任何错误，在界面上显示错误提示
            st.error(f"删除会话 {session_id} 失败：{e}")

# ================= 3. UI 界面元素 =================
# 创建页面大标题
st.title("AI智能伴侣")

# 添加页面 Logo（注意：路径需指向你本地的真实图片文件，否则会报错）
st.logo("🤖")

# ================= 4. 系统提示词（Prompt Engineering）=================
# 定义一个模板字符串，后续通过 %s 动态填入“昵称”和“性格”
system_prompt = """
你叫%s，现在是用户的真实伴侣，请完全代入伴侣角色。
规则：
1. 每次只回1条消息
2. 禁止任何场景或状态描述性文字
3. 匹配用户的语言
4. 回复简短，像微信聊天一样
5. 有需要的话可以用 ❤️ 🌸 等emoji表情
6. 用符合伴侣性格的方式对话
7. 回复的内容, 要充分体现伴侣的性格特征
伴侣性格：
- %s
你必须严格遵守上述规则来回复用户。
"""

# ================= 5. 会话状态初始化（Session State）=================
# Streamlit 每次交互都会重新运行整个脚本，使用 st.session_state 来持久化保存数据

# 检查 "messages" 是否在 st.session_state 中，不在则初始化为空列表（用于存放聊天历史）
if "messages" not in st.session_state:
    st.session_state.messages = []

# 检查 "nick_name" 是否在 st.session_state 中，不在则初始化为默认值 "小甜甜"
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小甜甜"

# 检查 "nature" 是否在 st.session_state 中，不在则初始化为默认值 "活泼开朗的东北姑娘"
if "nature" not in st.session_state:
    st.session_state.nature = "活泼开朗的东北姑娘"

# 检查 "current_session" 是否在 st.session_state 中，不在则生成初始会话ID
if "current_session" not in st.session_state:
    # 生成当前时间作为初始会话ID
    session_time = generate_session_id()
    # 将生成的ID保存到 st.session_state
    st.session_state.current_session = session_time

# ================= 6. 渲染历史聊天消息 =================
st.text(f"会话名称：{st.session_state.current_session}") # 在界面上显示当前会话名称
# 遍历会话状态中的消息列表，将历史对话逐条显示在界面上
for message in st.session_state.messages:
    # st.chat_message("role") 会根据角色（user/assistant）显示不同的气泡样式，然后写入消息内容
    st.chat_message(message["role"]).write(message["content"])

# ================= 7. 左侧侧边栏配置 =================
with st.sidebar:  # 使用上下文管理器，将以下组件包裹在侧边栏内显示
    # 创建 AI 控制面板的子标题
    st.subheader("AI控制面板")

    # 创建 "新建会话" 按钮，width="stretch" 让按钮占满侧边栏宽度，icon="🐷" 设置按钮图标
    if st.button("新建会话", width="stretch", icon="🐷"):
        # 点击按钮时，先保存当前会话的状态
        save_session_state()
        # 再调用 create_session 函数创建新会话
        create_session()

    # 创建 "历史会话" 子标题
    st.subheader("历史会话")
    # 调用 load_session_history 函数获取所有历史会话ID列表
    session_list = load_session_history()
    # 遍历每个会话ID
    for session in session_list:
        # 将一行分为两列，col1 占4份宽度，col2 占1份宽度
        col1, col2 = st.columns([4, 1])
        with col1: # 在第一列中
            # 创建会话加载按钮，按钮文字为会话ID，占满宽度，图标为文件夹
            # type根据是否为当前会话设置按钮颜色
            if st.button(session, width="stretch", icon="📂",type="primary" if session == st.session_state.current_session else "secondary"):
                st.session_state.current_session = session # 设置当前会话ID为选中的ID
                load_session(session) # 加载选中的会话数据
                st.rerun() # 加载会话后刷新页面显示对应聊天记录
        with col2: # 在第二列中
            # 创建删除按钮，无文字，占满宽度，图标为叉号，key 设置唯一值避免按钮冲突
            if st.button("", width="stretch", icon="❌", key=f"delete{session}"):
                delete_session(session) # 调用删除会话函数

    # 创建一个分割线，视觉上区分不同功能区域
    st.divider()

    # 创建 "伴侣信息" 子标题
    st.subheader("伴侣信息")

    # 1. 昵称输入框
    # 创建文本输入框，label为"昵称"，placeholder为提示文字，value回显当前会话中的昵称
    nick_name = st.text_input("昵称", placeholder="请输入伴侣的昵称", value=st.session_state.nick_name)
    # 在界面上显示用户当前输入的昵称
    st.write(f"你输入的昵称是：{nick_name}")

    # 如果输入框有内容（非空），更新会话状态中的昵称（实时生效）
    if nick_name:
        st.session_state.nick_name = nick_name

    # 2. 性格输入框（文本域，适合多行输入）
    # 创建文本域输入框，label为"性格"，placeholder为提示文字，value回显当前会话中的性格
    nature = st.text_area("性格", placeholder="请输入伴侣的性格特征", value=st.session_state.nature)
    # 在界面上显示用户当前输入的性格
    st.write(f"你输入的性格是：{nature}")

    # 如果输入框有内容（非空），更新会话状态中的性格（实时生效）
    if nature:
        st.session_state.nature = nature

# ================= 8. 核心聊天交互逻辑 =================
# 创建底部聊天输入框，将用户输入的内容赋值给 promat 变量
promat = st.chat_input("请输入你的问题:")

# 当用户输入了内容（即 promat 不为空字符串）时执行以下逻辑
if promat:
    # 1. 在界面上显示用户输入的消息（角色为 "user"）
    st.chat_message("user").write(promat)

    # 2. 将用户消息以字典形式追加到会话状态的历史记录列表中
    st.session_state.messages.append({"role": "user", "content": promat})

    # 3. 准备调用 AI 模型，初始化 OpenAI 客户端
    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'), # 从系统环境变量中读取 DEEPSEEK_API_KEY
        base_url="https://api.deepseek.com"          # 指定 DeepSeek 的 API 地址
    )

    # 4. 调用大模型获取流式响应
    response = client.chat.completions.create(
        model="deepseek-chat", # 指定使用的模型为 deepseek-chat
        messages=[
            # 注入系统提示词，动态填入当前的 昵称 和 性格
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            # 将之前的所有聊天记录作为上下文传递给大模型（* 用于解包列表）
            *st.session_state.messages
        ],
        stream=True # 启用流式输出，实现打字机效果
    )

    # 5. 处理流式响应并在界面上显示
    # 创建一个“空”的占位符组件，用于后续动态更新 AI 的回复内容
    response_message = st.empty()
    full_response = "" # 初始化空字符串，用于拼接完整的 AI 回复内容

    # 循环读取流式返回的每一个数据块 (chunk)
    for chunk in response:
        # 检查当前数据块是否包含有效内容（防止最后一个空包导致报错）
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content # 提取本次数据块中的增量文本内容
            full_response += content                 # 将增量内容拼接到完整回复字符串中
            # 在占位符位置实时更新显示 AI 回复（模拟打字机效果）
            response_message.chat_message("assistant").write(full_response)

    # 6. 将 AI 的完整回复以字典形式追加到历史记录中，以便下一轮对话携带上下文
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    #保存会话信息
    save_session_state()