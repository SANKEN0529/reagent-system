import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 从 secrets 读取密钥
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="试剂管理系统", page_icon="🧪")
st.title("🧪 实验室试剂管理系统")

menu = st.sidebar.radio("菜单", ["查看所有", "添加试剂", "搜索试剂", "低库存提醒", "编辑/删除"])

if menu == "查看所有":
    data = supabase.table('reagents').select('*').execute().data
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
        st.caption(f"共 {len(data)} 种试剂")
    else:
        st.info("暂无数据")

elif menu == "添加试剂":
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("试剂名称 *")
            cas = st.text_input("CAS号")
            location = st.text_input("存放位置 *")
        with col2:
            total = st.number_input("总量 *", min_value=0.0, step=0.1)
            unit = st.text_input("单位", "g")
            date = st.date_input("登入日期", datetime.now())
        remark = st.text_input("备注")

        if st.form_submit_button("✅ 添加"):
            if name and location and total > 0:
                supabase.table('reagents').insert({
                    'name': name, 'cas': cas, 'location': location,
                    'total': total, 'unit': unit, 'date': str(date), 'remark': remark
                }).execute()
                st.success(f"✅ 已添加 {name}")
                st.balloons()
            else:
                st.error("请填写完整信息")

elif menu == "搜索试剂":
    keyword = st.text_input("输入关键字（名称/CAS号/位置）")
    if keyword:
        data = supabase.table('reagents').select('*').ilike('name', f'%{keyword}%').execute().data
        if not data:
            data = supabase.table('reagents').select('*').ilike('cas', f'%{keyword}%').execute().data
        if not data:
            data = supabase.table('reagents').select('*').ilike('location', f'%{keyword}%').execute().data
        if data:
            st.success(f"找到 {len(data)} 条结果")
            st.dataframe(pd.DataFrame(data))
        else:
            st.warning("未找到")

elif menu == "低库存提醒":
    threshold = st.slider("库存阈值", 0, 100, 10)
    data = supabase.table('reagents').select('*').lt('total', threshold).execute().data
    if data:
        st.warning(f"⚠️ 以下 {len(data)} 种试剂低于 {threshold}")
        st.dataframe(pd.DataFrame(data))
    else:
        st.success(f"✅ 所有试剂库存充足")

elif menu == "编辑/删除":
    data = supabase.table('reagents').select('*').execute().data
    if data:
        options = {f"[{d['id']}] {d['name']}": d for d in data}
        selected = st.selectbox("选择试剂", list(options.keys()))
        r = options[selected]

        new_total = st.number_input("新总量", value=float(r['total']))
        if st.button("更新总量"):
            supabase.table('reagents').update({'total': new_total}).eq('id', r['id']).execute()
            st.success("已更新")
            st.rerun()

        if st.button("删除试剂", type="primary"):
            supabase.table('reagents').delete().eq('id', r['id']).execute()
            st.success("已删除")
            st.rerun()
    else:
        st.info("暂无数据")