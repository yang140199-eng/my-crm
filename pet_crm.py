import streamlit as st
import pandas as pd
import os
import json

# ===================== 【1. 核心引擎】 =====================
BASE_DIR = r"E:\桌面"
JSON_DB = os.path.join(BASE_DIR, "crm_database.json")

DB_COLUMNS = [
    "客户编号", "公司名字", "网站", "国家", "公司地址", "公司电话", "公司邮箱",
    "联系人明细", "Facebook", "Linkedin", "Ins", "YouTube", "其他社媒",
    "客户类型", "客户等级", "合作意向", "公司规模", "主营产品",
    "海关数据分析", "Whois验证", "决策人直接联系方式", "社媒活跃状况", "内部备注"
]

def ensure_list(val):
    if isinstance(val, list): return val
    if isinstance(val, str) and val.strip():
        try:
            res = json.loads(val)
            return res if isinstance(res, list) else []
        except: return []
    return []

def render_full_link(text):
    if not text or not isinstance(text, str) or text in ["---", "N/A"]: return "---"
    clean_text = text.strip()
    if clean_text.startswith(("http", "www.")):
        link = clean_text if clean_text.startswith("http") else f"https://{clean_text}"
        return f'<a href="{link}" target="_blank" style="color: #2563eb; word-break: break-all; font-weight: 600;">{clean_text}</a>'
    return clean_text

def get_next_customer_id():
    if st.session_state.data.empty:
        return "C0001"
    ids = st.session_state.data["客户编号"].str.extract(r'C(\d+)').dropna()
    if ids.empty:
        return "C0001"
    max_num = ids[0].astype(int).max()
    next_num = max_num + 1
    return f"C{next_num:04d}"

if 'data' not in st.session_state:
    if os.path.exists(JSON_DB):
        try:
            df = pd.read_json(JSON_DB, dtype={"客户编号": str}).fillna("")
            for col in ["联系人明细", "其他社媒"]:
                if col in df.columns: df[col] = df[col].apply(ensure_list)
            st.session_state.data = df[DB_COLUMNS]
        except:
            st.session_state.data = pd.DataFrame(columns=DB_COLUMNS)
    else:
        st.session_state.data = pd.DataFrame(columns=DB_COLUMNS)

for key in ['page', 'edit_id', 'temp_row', 'sort_col', 'sort_ascending', 'delete_confirm']:
    if key not in st.session_state:
        if key == 'page': st.session_state[key] = 'list'
        elif key == 'sort_col': st.session_state[key] = "客户编号"
        elif key == 'sort_ascending': st.session_state[key] = True
        elif key == 'delete_confirm': st.session_state[key] = False
        else: st.session_state[key] = None

def sync_all():
    df_save = st.session_state.data.copy()
    for col in ["联系人明细", "其他社媒"]:
        df_save[col] = df_save[col].apply(lambda x: json.dumps(x, ensure_ascii=False))
    df_save.to_json(JSON_DB, orient="records", force_ascii=False, indent=4)
    st.toast("💾 变更已同步", icon="✔️")

# ===================== 【2. UI 样式表】 =====================
st.set_page_config(page_title="CRM System", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f1f5f9; }
    .main-card {
        background: white; padding: 24px; border-radius: 10px;
        border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 17px; font-weight: 800; color: #0f172a;
        margin-bottom: 20px; padding-bottom: 8px; border-bottom: 2px solid #3b82f6; width: fit-content;
    }
    .field-label { color: #1e293b; font-size: 13px; font-weight: 700; margin-bottom: 6px; margin-top: 12px; }
    .field-value {
        background: #f8fafc; padding: 12px 14px; border-radius: 8px;
        font-size: 15px; color: #000000; border: 1px solid #cbd5e1;
        min-height: 42px; line-height: 1.5;
    }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        border: 2px solid #475569 !important; border-radius: 8px !important; background-color: #ffffff !important;
    }
    input, textarea { color: #000000 !important; font-size: 15px !important; font-weight: 500 !important; }
    .data-cell { padding: 12px 6px; font-size: 14px; border-bottom: 1px solid #e2e8f0; color: #000000; }
</style>
""", unsafe_allow_html=True)

# ===================== 【3. 侧边栏】 =====================
with st.sidebar:
    st.markdown("<h2 style='color:#0f172a;'>管理系统</h2>", unsafe_allow_html=True)
    if st.button("📊 数据总览", use_container_width=True):
        st.session_state.page = 'list'; st.rerun()
    if st.button("➕ 新增记录", type="primary", use_container_width=True):
        new_id = get_next_customer_id()
        st.session_state.temp_row = {col: "" for col in DB_COLUMNS}
        st.session_state.temp_row.update({
            "客户编号": new_id,
            "联系人明细": [],
            "其他社媒": [],
            "客户等级": "B-重点",
            "合作意向": "中"
        })
        st.session_state.edit_id = new_id; st.session_state.page = 'detail'; st.rerun()

# ===================== 【4. 列表展示页】 =====================
if st.session_state.page == 'list':
    st.title("数据列表")
    search = st.text_input("", placeholder="🔍 输入关键词搜索...", label_visibility="collapsed")
    df_show = st.session_state.data.copy()
    if search:
        df_show = df_show[df_show.astype(str).apply(lambda x: x.str.contains(search, case=False).any(), axis=1)]

    if st.session_state.sort_col:
        rank_map = {"A-顶级": 1, "B-重点": 2, "C-普通": 3, "D-潜伏": 4}
        def custom_sort_key(series):
            return series.apply(lambda x: (1 if str(x).strip() in ["", "---"] else 0,
                                           rank_map.get(x, 99) if st.session_state.sort_col == "客户等级" else str(x).lower()))
        df_show = df_show.sort_values(by=st.session_state.sort_col, ascending=st.session_state.sort_ascending, key=custom_sort_key)

    RATIO = [1.5, 3.5, 2, 2, 1]
    h = st.columns(RATIO)
    cols = [("🆔 编号", "客户编号"), ("🏢 公司名称", "公司名字"), ("📍 国家", "国家"), ("📦 产品", "主营产品"), ("🏷️ 等级", "客户等级")]
    for i, (label, key) in enumerate(cols):
        is_active = st.session_state.sort_col == key
        icon = " 🔼" if (is_active and st.session_state.sort_ascending) else (" 🔽" if is_active else "")
        if h[i].button(f"{label}{icon}", key=f"h_{key}", use_container_width=True):
            if st.session_state.sort_col == key: st.session_state.sort_ascending = not st.session_state.sort_ascending
            else: st.session_state.sort_col = key; st.session_state.sort_ascending = True
            st.rerun()

    for idx, row in df_show.iterrows():
        r = st.columns(RATIO)
        with r[0]:
            if st.button(f"{row['客户编号']}", key=f"row_{row['客户编号']}_{idx}"):
                st.session_state.edit_id = row['客户编号']; st.session_state.temp_row = None; st.session_state.page = 'detail'; st.rerun()
        r[1].markdown(f'<div class="data-cell"><b>{row["公司名字"] or "---"}</b></div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="data-cell">{row["国家"] or "---"}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="data-cell">{str(row["主营产品"])[:12] if row["主营产品"] else "---"}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="data-cell" style="text-align:center;">`{row["客户等级"] or "B-重点"}`</div>', unsafe_allow_html=True)

# ===================== 【5. 详细信息页（终极无错版）】 =====================
elif st.session_state.page == 'detail':
    is_new = st.session_state.temp_row is not None
    if is_new:
        curr = st.session_state.temp_row
        edit_mode = True
    else:
        target_res = st.session_state.data[st.session_state.data['客户编号'] == st.session_state.edit_id]
        if not target_res.empty:
            curr = target_res.iloc[0].to_dict()
        else:
            st.error("❌ 未找到该客户记录，可能已被删除")
            st.session_state.page = 'list'
            st.rerun()

    t1, t2, t3 = st.columns([6, 2, 1])
    t1.markdown(f"### 🏢 {curr['公司名字'] or '新记录'} <span style='font-size:16px; color:#64748b;'>#{curr['客户编号']}</span>", unsafe_allow_html=True)
    if not is_new: edit_mode = t2.toggle("🔓 开启编辑模式", value=False)
    if t3.button("⬅️ 返回", use_container_width=True): st.session_state.page = 'list'; st.rerun()

    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("<div class='main-card'><div class='section-title'>📌 业务基础资料</div>", unsafe_allow_html=True)
        for label, key in [("客户编号", "客户编号"), ("公司名字", "公司名字"), ("官方网站", "网站"), ("所属国家", "国家"), ("公司地址", "公司地址"), ("固定电话", "公司电话"), ("通用邮箱", "公司邮箱")]:
            st.markdown(f"<div class='field-label'>{label}</div>", unsafe_allow_html=True)
            if edit_mode:
                curr[key] = st.text_input(label, curr.get(key, ""), label_visibility="collapsed", key=f"in_{key}", disabled=(key=="客户编号" and not is_new))
            else:
                val = render_full_link(curr.get(key)) if key == "网站" else (curr.get(key) or "---")
                st.markdown(f"<div class='field-value'>{val}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-title' style='margin-top:25px;'>🌐 社媒信息</div>", unsafe_allow_html=True)
        s_row1 = st.columns(2)
        with s_row1[0]:
            st.markdown("<div class='field-label'>Facebook</div>", unsafe_allow_html=True)
            if edit_mode: curr["Facebook"] = st.text_input("FB", curr.get("Facebook",""), label_visibility="collapsed", key="ed_fb")
            else: st.markdown(f"<div class='field-value'>{render_full_link(curr.get('Facebook'))}</div>", unsafe_allow_html=True)
        with s_row1[1]:
            st.markdown("<div class='field-label'>Linkedin</div>", unsafe_allow_html=True)
            if edit_mode: curr["Linkedin"] = st.text_input("LI", curr.get("Linkedin",""), label_visibility="collapsed", key="ed_li")
            else: st.markdown(f"<div class='field-value'>{render_full_link(curr.get('Linkedin'))}</div>", unsafe_allow_html=True)

        s_row2 = st.columns(2)
        with s_row2[0]:
            st.markdown("<div class='field-label'>Ins</div>", unsafe_allow_html=True)
            if edit_mode: curr["Ins"] = st.text_input("IN", curr.get("Ins",""), label_visibility="collapsed", key="ed_ins")
            else: st.markdown(f"<div class='field-value'>{render_full_link(curr.get('Ins'))}</div>", unsafe_allow_html=True)
        with s_row2[1]:
            st.markdown("<div class='field-label'>YouTube</div>", unsafe_allow_html=True)
            if edit_mode: curr["YouTube"] = st.text_input("YT", curr.get("YouTube",""), label_visibility="collapsed", key="ed_yt")
            else: st.markdown(f"<div class='field-value'>{render_full_link(curr.get('YouTube'))}</div>", unsafe_allow_html=True)

        st.markdown("<div class='field-label'>其他渠道 (TikTok等)</div>", unsafe_allow_html=True)
        other_df = pd.DataFrame(ensure_list(curr.get("其他社媒", [])), columns=["平台名称", "账号/链接"])
        if edit_mode:
            curr["其他社媒"] = st.data_editor(other_df, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_other").to_dict('records')
        else:
            if not other_df.empty: st.dataframe(other_df, use_container_width=True, hide_index=True)
            else: st.markdown("<div class='field-value'>暂无记录</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("<div class='main-card'><div class='section-title'>🔬 背调详细分析</div>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            st.markdown(f"<div class='field-label'>等级</div>", unsafe_allow_html=True)
            opts = ["A-顶级", "B-重点", "C-普通", "D-潜伏"]
            if edit_mode:
                lv = curr.get("客户等级", "B-重点")
                idx = opts.index(lv) if lv in opts else 1
                curr["客户等级"] = st.selectbox("L", opts, index=idx, label_visibility="collapsed")
            else:
                st.markdown(f"<div class='field-value'>{curr.get('客户等级')}</div>", unsafe_allow_html=True)
        with b2:
            st.markdown(f"<div class='field-label'>类型</div>", unsafe_allow_html=True)
            types = ["品牌方", "渠道商", "终端客户", "零售商"]
            if edit_mode:
                tv = curr.get("客户类型", "品牌方")
                idx = types.index(tv) if tv in types else 0
                curr["客户类型"] = st.selectbox("T", types, index=idx, label_visibility="collapsed")
            else:
                st.markdown(f"<div class='field-value'>{curr.get('客户类型') or '---'}</div>", unsafe_allow_html=True)

        b3, b4 = st.columns(2)
        with b3:
            st.markdown(f"<div class='field-label'>意向度</div>", unsafe_allow_html=True)
            if edit_mode:
                intent_opts = ["低", "中", "高"]
                intent_val = curr.get("合作意向", "中")
                safe_val = intent_val if intent_val in intent_opts else "中"
                curr["合作意向"] = st.select_slider("I", options=intent_opts, value=safe_val, label_visibility="collapsed")
            else:
                st.markdown(f"<div class='field-value'>{curr.get('合作意向')}</div>", unsafe_allow_html=True)
        with b4:
            st.markdown(f"<div class='field-label'>规模</div>", unsafe_allow_html=True)
            if edit_mode: curr["公司规模"] = st.text_input("S", curr.get("公司规模",""), label_visibility="collapsed")
            else: st.markdown(f"<div class='field-value'>{curr.get('公司规模') or '---'}</div>", unsafe_allow_html=True)

        for label, key, h in [("主营产品", "主营产品", 60), ("海关贸易数据", "海关数据分析", 80), ("Whois所有权", "Whois验证", 60), ("决策人直接联系方式", "决策人直接联系方式", 60), ("活跃状况", "社媒活跃状况", 60), ("内部备注", "内部备注", 100)]:
            st.markdown(f"<div class='field-label'>{label}</div>", unsafe_allow_html=True)
            if edit_mode: curr[key] = st.text_area(label, curr.get(key, ""), height=h, label_visibility="collapsed", key=f"ta_{key}")
            else: st.markdown(f"<div class='field-value' style='min-height:60px; white-space:pre-wrap;'>{curr.get(key) or '---'}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='main-card'><div class='section-title'>👥 联系人决策链</div>", unsafe_allow_html=True)
    con_df = pd.DataFrame(ensure_list(curr.get("联系人明细", [])), columns=["姓名", "职位", "电话/WhatsApp", "Email"])
    if edit_mode:
        curr["联系人明细"] = st.data_editor(con_df, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_con").to_dict('records')
    else:
        if not con_df.empty: st.dataframe(con_df, use_container_width=True, hide_index=True)
        else: st.info("暂无联系人记录")
    st.markdown("</div>", unsafe_allow_html=True)

    if edit_mode:
        st.divider()
        cs, cd, _ = st.columns([1,1,4])
        if cs.button("💾 保存档案", type="primary", use_container_width=True):
            save_row = {k: curr.get(k, "") for k in DB_COLUMNS}
            if is_new:
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([save_row])], ignore_index=True)
            else:
                mask = st.session_state.data["客户编号"] == curr["客户编号"]
                st.session_state.data.loc[mask] = pd.Series(save_row)
            sync_all()
            st.session_state.page = 'list'
            st.rerun()

        if not is_new:
            if cd.button("🗑️ 删除记录", use_container_width=True):
                st.session_state.delete_confirm = True
                st.rerun()

            if st.session_state.delete_confirm:
                st.warning(f"⚠️ 确认删除客户：{curr['客户编号']} - {curr['公司名字']}？不可恢复！")
                col1, col2 = st.columns(2)
                if col1.button("✅ 确认删除", use_container_width=True):
                    st.session_state.data = st.session_state.data[st.session_state.data["客户编号"] != curr["客户编号"]]
                    sync_all()
                    st.session_state.delete_confirm = False
                    st.session_state.page = 'list'
                    st.rerun()
                if col2.button("❌ 取消", use_container_width=True):
                    st.session_state.delete_confirm = False
                    st.rerun()