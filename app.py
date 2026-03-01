import streamlit as st
import re


# ==========================================
# 1. 核心业务逻辑
# ==========================================
def extract_digits_and_amount(chunk):
    m1 = re.match(r'^([1-6]//[1-6])/(.+)$', chunk)
    m2 = re.match(r'^([1-6]/[1-6]+)/(.+)$', chunk)
    m4 = re.match(r'^([1-6]+)/(.+)$', chunk)

    if m1:
        raw_digits, amounts_str = m1.groups()
    elif m2:
        raw_digits, amounts_str = m2.groups()
    elif m4:
        raw_digits, amounts_str = m4.groups()
    else:
        return None, None

    amount_parts = amounts_str.split('/')
    try:
        amount = [float(part) for part in amount_parts if part.strip()]
        return raw_digits, amount
    except ValueError:
        return None, None


def add_to_results(digit_str, value):
    for d in digit_str:
        if d in st.session_state.results:
            st.session_state.results[d] += value


# ==========================================
# 2. 初始化状态
# ==========================================
if 'round_num' not in st.session_state:
    st.session_state.round_num = 1
if 'results' not in st.session_state:
    st.session_state.results = {str(i): 0.0 for i in range(1, 7)}
if 'logs' not in st.session_state:
    st.session_state.logs = []
# 用于绑定输入框的值，方便随时清空
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""


def log(msg):
    st.session_state.logs.insert(0, msg)


# ==========================================
# 3. 回调函数：处理解析并清空输入框
# ==========================================
def process_data():
    # 从 session_state 获取当前输入框的值
    input_str = st.session_state.input_text.strip()

    if not input_str:
        return

    log(f"--- 输入: {input_str} ---")
    # 使用 re.split()，| 代表“或”，\s+ 代表一个或多个空格
    chunks = re.split(r'///|\s+', input_str)

    # 过滤掉可能产生的空字符串（比如输入了两个连续空格的情况）
    chunks = [chunk for chunk in chunks if chunk.strip()]
    # chunks = input_str.split('///')
    for chunk in chunks:
        if not chunk.strip(): continue

        raw_digits_part, amount = extract_digits_and_amount(chunk)
        if raw_digits_part is None:
            log(f"⚠️ [跳过] 格式或金额无法识别: {chunk}")
            continue

        first_amount = amount[0] if len(amount) > 0 else None
        second_amount = amount[-1] if len(amount) > 1 else None

        # 执行分配算法
        if '//' in raw_digits_part:
            digits = raw_digits_part.split('//')
            if len(digits) == 2:
                add_to_results(digits[0], first_amount * (2 / 3))
                add_to_results(digits[1], first_amount * (1 / 3))
                if second_amount is not None:
                    add_to_results(digits[0], second_amount * (1 / 2))
                    add_to_results(digits[1], second_amount * (1 / 2))
        else:
            sub_parts = raw_digits_part.split('/')
            if len(sub_parts) == 2:
                d1 = sub_parts[0]
                d_others = sub_parts[1]
                if len(d1) == 1 and len(d_others) == 1:
                    add_to_results(d1, first_amount * (5 / 6))
                    add_to_results(d_others, first_amount * (1 / 6))
                elif len(d1) == 1 and len(d_others) >= 2:
                    add_to_results(d1, first_amount * (2 / 3))
                    share = (1 / 3) / len(d_others)
                    for d in d_others:
                        add_to_results(d, first_amount * share)

                if second_amount is not None:
                    n = 1 + len(d_others)
                    add_to_results(d1, second_amount / n)
                    for d in d_others:
                        add_to_results(d, second_amount / n)

            elif len(sub_parts) == 1:
                digits = sub_parts[0]
                n = len(digits)
                if n > 0:
                    share = first_amount / n
                    for d in digits:
                        add_to_results(d, share)

    log("✅ 累加成功！")


    # 【关键修改】处理完毕后，强制清空绑定的状态值
    st.session_state.input_text = ""


def reset_round():
    """清零并进入下一回合"""
    st.session_state.round_num += 1
    st.session_state.results = {str(i): 0.0 for i in range(1, 7)}
    st.session_state.logs = []
    st.session_state.input_text = ""


# ==========================================
# 4. UI 渲染界面
# ==========================================
st.set_page_config(page_title="金额分配解析系统", page_icon="💰", layout="centered")

st.title("💰 金额分配解析系统")
st.markdown(f"**当前回合: 第 {st.session_state.round_num} 回合**")

# --- 金额显示面板 ---
st.subheader("📊 当前累计金额")

# 保留优化手机端显示的 CSS，防止超大金额被截断
st.markdown("""
<style>
div[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;      /* 调整字体大小 */
    white-space: normal !important;    /* 允许文本自动换行 */
    word-wrap: break-word !important;  /* 强制打断换行 */
}
</style>
""", unsafe_allow_html=True)

mount_sum = 0
for i in range(1, 7):
    mount_sum += st.session_state.results[str(i)]

sorted_results = sorted(st.session_state.results.items(), key=lambda item: item[1], reverse=True)
for num, amt in sorted_results:
    st.metric(label=f"数字 {num}", value=f"{num}当前下注：{amt:.2f}\n预计输赢：{6 * amt - mount_sum:.2f}")

st.divider()

# --- 操作区 ---
# 【关键修改】绑定 key 为 "input_text"，并设置回车即触发 on_change 回调
st.text_input(
    "在此输入解析字符串:",
    key="input_text",
    on_change=process_data,
    placeholder="例如: 1//2/100///3/4/200/50"
)

col1, col2 = st.columns([1, 1])

with col1:
    # 按钮点击时触发 process_data 函数
    st.button("🚀 解析并累加", use_container_width=True, type="primary", on_click=process_data)

with col2:
    # 按钮点击时触发 reset_round 函数
    st.button("🔄 开启新回合 (清零)", use_container_width=True, on_click=reset_round)

# --- 日志区 ---
with st.expander("📝 操作日志 (点击展开/折叠)", expanded=True):
    for m in st.session_state.logs:
        st.text(m)

