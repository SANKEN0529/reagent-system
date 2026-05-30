import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import io
import base64

# 从 secrets 读取密钥
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="试剂管理系统", page_icon="🧪", layout="wide")
st.title("🧪 实验室试剂管理系统")

# 危险等级选项
DANGER_LEVELS = ["无", "易燃", "腐蚀", "有毒", "易燃+有毒", "腐蚀+有毒", "易燃+腐蚀", "剧毒"]

# 存放要求选项
STORAGE_REQUIREMENTS = ["无特殊要求", "阴凉干燥", "避光保存", "通风柜", "冰箱冷藏", "冷冻保存", "防潮", "密封保存"]

# 导出Excel函数
def export_to_excel(data):
    df = pd.DataFrame(data)
    # 选择要导出的列
    export_cols = ['id', 'name', 'cas', 'location', 'total', 'unit', 'date', 'danger_level', 'storage_requirement', 'remark']
    df = df[export_cols]
    df.columns = ['ID', '名称', 'CAS号', '位置', '总量', '单位', '登入日期', '危险等级', '存放要求', '备注']
    
    # 转换为Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='试剂清单')
    return output.getvalue()

menu = st.sidebar.radio("菜单", ["查看所有", "添加试剂", "搜索试剂", "编辑/删除", "📎 导出Excel"])

# ========== 查看所有 ==========
if menu == "查看所有":
    st.header("📋 试剂清单")
    data = supabase.table('reagents').select('*').execute().data
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        st.caption(f"共 {len(data)} 种试剂")
        
        # 统计不同危险等级的数量
        st.subheader("📊 统计信息")
        col1, col2 = st.columns(2)
        with col1:
            danger_counts = df['danger_level'].value_counts() if 'danger_level' in df.columns else {}
            st.write("**危险等级分布：**")
            for level, count in danger_counts.items():
                st.write(f"- {level}: {count} 种")
        with col2:
            storage_counts = df['storage_requirement'].value_counts() if 'storage_requirement' in df.columns else {}
            st.write("**存放要求分布：**")
            for req, count in storage_counts.items():
                st.write(f"- {req}: {count} 种")
    else:
        st.info("暂无数据")

# ========== 添加试剂 ==========
elif menu == "添加试剂":
    st.header("➕ 添加新试剂")
    with st.form("add_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("试剂名称 *")
            cas = st.text_input("CAS号")
            location = st.text_input("存放位置 *")
        with col2:
            total = st.number_input("总量 *", min_value=0, step=1, format="%d")
            unit = st.text_input("单位 *", placeholder="例如：g, ml, 瓶, 支")
            date = st.date_input("登入日期", datetime.now())
        with col3:
            danger_level = st.selectbox("危险等级", DANGER_LEVELS)
            storage_requirement = st.selectbox("存放要求", STORAGE_REQUIREMENTS)
        remark = st.text_area("备注", placeholder="纯度、厂家、注意事项等")
        
        if st.form_submit_button("✅ 添加"):
            if name and location and unit and total > 0:
                supabase.table('reagents').insert({
                    'name': name, 'cas': cas, 'location': location,
                    'total': total, 'unit': unit, 'date': str(date),
                    'danger_level': danger_level, 'storage_requirement': storage_requirement,
                    'remark': remark
                }).execute()
                st.success(f"✅ 已添加 {name}")
                st.balloons()
            else:
                st.error("请填写完整信息（名称、位置、单位、总量）")

# ========== 搜索试剂 ==========
elif menu == "搜索试剂":
    st.header("🔍 搜索试剂")
    search_type = st.radio("搜索方式", ["按名称", "按CAS号", "按位置", "按危险等级"], horizontal=True)
    keyword = st.text_input("请输入关键字")
    
    if keyword:
        if search_type == "按名称":
            data = supabase.table('reagents').select('*').ilike('name', f'%{keyword}%').execute().data
        elif search_type == "按CAS号":
            data = supabase.table('reagents').select('*').ilike('cas', f'%{keyword}%').execute().data
        elif search_type == "按位置":
            data = supabase.table('reagents').select('*').ilike('location', f'%{keyword}%').execute().data
        else:  # 按危险等级
            data = supabase.table('reagents').select('*').ilike('danger_level', f'%{keyword}%').execute().data
        
        if data:
            st.success(f"找到 {len(data)} 条结果")
            st.dataframe(pd.DataFrame(data))
        else:
            st.warning("未找到")

# ========== 编辑/删除 ==========
elif menu == "编辑/删除":
    st.header("✏️ 编辑或删除试剂")
    data = supabase.table('reagents').select('*').execute().data
    if data:
        options = {f"[{d['id']}] {d['name']}": d for d in data}
        selected = st.selectbox("选择试剂", list(options.keys()))
        r = options[selected]
        
        with st.form("edit_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("名称", r['name'])
                new_cas = st.text_input("CAS号", r['cas'] or "")
                new_location = st.text_input("位置", r['location'])
            with col2:
                new_total = st.number_input("总量", value=int(r['total']), step=1)
                new_unit = st.text_input("单位", r['unit'])
                new_danger = st.selectbox("危险等级", DANGER_LEVELS, index=DANGER_LEVELS.index(r.get('danger_level', '无')) if r.get('danger_level') in DANGER_LEVELS else 0)
            with col3:
                new_storage = st.selectbox("存放要求", STORAGE_REQUIREMENTS, index=STORAGE_REQUIREMENTS.index(r.get('storage_requirement', '无特殊要求')) if r.get('storage_requirement') in STORAGE_REQUIREMENTS else 0)
                new_remark = st.text_area("备注", r['remark'] or "")
            
            col_save, col_delete = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 保存修改"):
                    supabase.table('reagents').update({
                        'name': new_name, 'cas': new_cas, 'location': new_location,
                        'total': new_total, 'unit': new_unit,
                        'danger_level': new_danger, 'storage_requirement': new_storage,
                        'remark': new_remark
                    }).eq('id', r['id']).execute()
                    st.success("✅ 已保存")
                    st.rerun()
            with col_delete:
                if st.form_submit_button("🗑️ 删除", type="primary"):
                    supabase.table('reagents').delete().eq('id', r['id']).execute()
                    st.success("✅ 已删除")
                    st.rerun()
    else:
        st.info("暂无数据")

# ========== 导出Excel ==========
elif menu == "📎 导出Excel":
    st.header("📎 导出试剂清单")
    data = supabase.table('reagents').select('*').execute().data
    
    if data:
        st.info(f"共 {len(data)} 种试剂，点击下方按钮导出Excel文件")
        
        # 预览
        st.subheader("预览（前5条）")
        st.dataframe(pd.DataFrame(data).head(5))
        
        # 导出按钮
        excel_data = export_to_excel(data)
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="试剂清单_{datetime.now().strftime("%Y%m%d")}.xlsx">📥 点击下载Excel文件</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        st.success("导出完成！")
    else:
        st.warning("暂无数据，请先添加试剂")
