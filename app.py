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

st.set_page_config(page_title="实验室管理系统", page_icon="🧪", layout="wide")
st.title("🧪 实验室综合管理系统")

# 危险等级选项
DANGER_LEVELS = ["无", "易燃", "腐蚀", "有毒", "易燃+有毒", "腐蚀+有毒", "易燃+腐蚀", "剧毒"]

# 存放要求选项
STORAGE_REQUIREMENTS = ["无特殊要求", "阴凉干燥", "避光保存", "通风柜", "冰箱冷藏", "冷冻保存", "防潮", "密封保存"]

# 导出Excel函数
def export_to_excel(data):
    df = pd.DataFrame(data)
    export_cols = ['id', 'name', 'cas', 'location', 'total', 'unit', 'date', 'danger_level', 'storage_requirement', 'remark']
    df = df[export_cols]
    df.columns = ['ID', '名称', 'CAS号', '位置', '总量', '单位', '登入日期', '危险等级', '存放要求', '备注']
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='试剂清单')
    return output.getvalue()

# 初始化确认状态
if 'confirm_delete_reagent' not in st.session_state:
    st.session_state.confirm_delete_reagent = {}
if 'confirm_lcms' not in st.session_state:
    st.session_state.confirm_lcms = {}
if 'confirm_nmr' not in st.session_state:
    st.session_state.confirm_nmr = {}

menu = st.sidebar.radio("菜单", ["📋 试剂管理", "🔬 LCMS 送测", "⚛️ 核磁送测", "📎 导出Excel"])

# ========== 试剂管理 ==========
if menu == "📋 试剂管理":
    st.header("📋 试剂管理")
    
    reagent_menu = st.radio("选择操作", ["查看所有", "添加试剂", "搜索试剂", "编辑/删除"], horizontal=True)
    
    # 查看所有
    if reagent_menu == "查看所有":
        data = supabase.table('reagents').select('*').execute().data
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            st.caption(f"共 {len(data)} 种试剂")
            
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
    
    # 添加试剂
    elif reagent_menu == "添加试剂":
        with st.form("add_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("试剂名称 *")
                cas = st.text_input("CAS号 *", placeholder="例如：64-17-5")
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
                if name and cas and location and unit and total > 0:
                    supabase.table('reagents').insert({
                        'name': name, 'cas': cas, 'location': location,
                        'total': total, 'unit': unit, 'date': str(date),
                        'danger_level': danger_level, 'storage_requirement': storage_requirement,
                        'remark': remark
                    }).execute()
                    st.success(f"✅ 已添加 {name}")
                    st.balloons()
                else:
                    st.error("请填写完整信息（名称、CAS号、位置、单位、总量）")
    
    # 搜索试剂
    elif reagent_menu == "搜索试剂":
        search_type = st.radio("搜索方式", ["按名称", "按CAS号", "按位置", "按危险等级"], horizontal=True)
        keyword = st.text_input("请输入关键字")
        
        if keyword:
            if search_type == "按名称":
                data = supabase.table('reagents').select('*').ilike('name', f'%{keyword}%').execute().data
            elif search_type == "按CAS号":
                data = supabase.table('reagents').select('*').ilike('cas', f'%{keyword}%').execute().data
            elif search_type == "按位置":
                data = supabase.table('reagents').select('*').ilike('location', f'%{keyword}%').execute().data
            else:
                data = supabase.table('reagents').select('*').ilike('danger_level', f'%{keyword}%').execute().data
            
            if data:
                st.success(f"找到 {len(data)} 条结果")
                st.dataframe(pd.DataFrame(data))
            else:
                st.warning("未找到")
    
    # 编辑/删除
    elif reagent_menu == "编辑/删除":
        data = supabase.table('reagents').select('*').execute().data
        if data:
            search_term = st.text_input("输入试剂名称或CAS号进行搜索", placeholder="例如：乙醇 或 64-17-5")
            
            filtered_data = data
            if search_term:
                search_lower = search_term.lower()
                filtered_data = [
                    r for r in data 
                    if search_lower in r['name'].lower() 
                    or search_lower in (r['cas'] or "").lower()
                ]
            
            if not filtered_data:
                st.warning("未找到匹配的试剂")
            else:
                st.write(f"找到 {len(filtered_data)} 种试剂")
                
                options = {}
                for r in filtered_data:
                    label = f"[ID:{r['id']}] {r['name']}"
                    if r.get('cas'):
                        label += f" (CAS:{r['cas']})"
                    label += f" - 库存:{r['total']}{r['unit']}"
                    options[label] = r
                
                selected_label = st.selectbox("选择试剂", list(options.keys()))
                r = options[selected_label]
                
                st.divider()
                st.subheader(f"当前编辑：{r['name']}")
                
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
                            # 修改确认
                            if 'confirm_save' not in st.session_state:
                                st.session_state.confirm_save = False
                            if not st.session_state.confirm_save:
                                st.warning("⚠️ 确认修改？再次点击保存按钮确认")
                                if st.form_submit_button("⚠️ 确认保存修改"):
                                    supabase.table('reagents').update({
                                        'name': new_name, 'cas': new_cas, 'location': new_location,
                                        'total': new_total, 'unit': new_unit,
                                        'danger_level': new_danger, 'storage_requirement': new_storage,
                                        'remark': new_remark
                                    }).eq('id', r['id']).execute()
                                    st.session_state.confirm_save = True
                                    st.success("✅ 已保存")
                                    st.rerun()
                            else:
                                st.session_state.confirm_save = False
                    
                    with col_delete:
                        if st.form_submit_button("🗑️ 删除", type="primary"):
                            if f'confirm_del_{r["id"]}' not in st.session_state:
                                st.session_state[f'confirm_del_{r["id"]}'] = False
                            if not st.session_state[f'confirm_del_{r["id"]}']:
                                st.warning(f"⚠️ 确认删除 {r['name']}？再次点击删除按钮确认")
                                if st.form_submit_button("⚠️ 确认删除试剂"):
                                    supabase.table('reagents').delete().eq('id', r['id']).execute()
                                    st.session_state[f'confirm_del_{r["id"]}'] = True
                                    st.success("✅ 已删除")
                                    st.rerun()
                            else:
                                st.session_state[f'confirm_del_{r["id"]}'] = False
        else:
            st.info("暂无数据")

# ========== LCMS 送测 ==========
elif menu == "🔬 LCMS 送测":
    st.header("🔬 LCMS 送测登记")
    
    tab1, tab2 = st.tabs(["📝 登记样品", "✅ 管理待测样品"])
    
    with tab1:
        with st.form("lcms_form"):
            col1, col2 = st.columns(2)
            with col1:
                submitter = st.text_input("你的名字 *")
                sample_name = st.text_input("样品名称 *")
            with col2:
                notes = st.text_area("备注", placeholder="分子量范围、溶剂等")
            
            if st.form_submit_button("📤 提交 LCMS"):
                if submitter and sample_name:
                    supabase.table('lcms_samples').insert({
                        'submitter': submitter,
                        'sample_name': sample_name,
                        'notes': notes
                    }).execute()
                    st.success("✅ 已提交")
                    st.balloons()
                else:
                    st.error("请填写姓名和样品名称")
    
    with tab2:
        samples = supabase.table('lcms_samples').select('*').eq('status', 'pending').order('submitted_at').execute().data
        
        if not samples:
            st.info("暂无待测 LCMS 样品 🎉")
        else:
            st.subheader(f"📊 待测数量：{len(samples)} 个样品")
            
            for s in samples:
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{s['sample_name']}**")
                    st.caption(f"提交人: {s['submitter']} | 时间: {s['submitted_at'][:16]}")
                    if s['notes']:
                        st.caption(f"备注: {s['notes']}")
                with col3:
                    if f'confirm_lcms_{s["id"]}' not in st.session_state:
                        st.session_state[f'confirm_lcms_{s["id"]}'] = False
                    
                    if not st.session_state[f'confirm_lcms_{s["id"]}']:
                        if st.button(f"✅ 测完", key=f"lcms_{s['id']}"):
                            st.session_state[f'confirm_lcms_{s["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"⚠️ 确认 {s['sample_name']} 已测完？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ 确认", key=f"confirm_lcms_yes_{s['id']}"):
                                supabase.table('lcms_samples').update({'status': 'completed'}).eq('id', s['id']).execute()
                                st.session_state[f'confirm_lcms_{s["id"]}'] = False
                                st.success(f"✅ {s['sample_name']} 已完成")
                                st.rerun()
                        with col_b:
                            if st.button(f"❌ 取消", key=f"confirm_lcms_no_{s['id']}"):
                                st.session_state[f'confirm_lcms_{s["id"]}'] = False
                                st.rerun()
                st.divider()

# ========== 核磁送测 ==========
elif menu == "⚛️ 核磁送测":
    st.header("⚛️ 核磁送测登记")
    
    tab1, tab2 = st.tabs(["📝 登记样品", "✅ 管理待测样品"])
    
    with tab1:
        with st.form("nmr_form"):
            col1, col2 = st.columns(2)
            with col1:
                submitter = st.text_input("你的名字 *")
                sample_name = st.text_input("样品名称 *")
                nmr_type = st.selectbox("核磁类型 *", ["氢谱", "碳谱", "氢谱+碳谱", "二维谱"])
            with col2:
                solvent = st.selectbox("氘代试剂", ["CDCl3", "DMSO-d6", "MeOD", "D2O", "丙酮-d6", "其他"])
                notes = st.text_area("备注", placeholder="浓度、特殊要求等")
            
            if st.form_submit_button("📤 提交核磁"):
                if submitter and sample_name:
                    supabase.table('nmr_samples').insert({
                        'submitter': submitter,
                        'sample_name': sample_name,
                        'nmr_type': nmr_type,
                        'solvent': solvent if solvent != "其他" else "",
                        'notes': notes
                    }).execute()
                    st.success("✅ 已提交")
                    st.balloons()
                else:
                    st.error("请填写姓名和样品名称")
    
    with tab2:
        samples = supabase.table('nmr_samples').select('*').eq('status', 'pending').order('submitted_at').execute().data
        
        if not samples:
            st.info("暂无待测核磁样品 🎉")
        else:
            h_count = len([s for s in samples if '氢谱' in s['nmr_type']])
            c_count = len([s for s in samples if '碳谱' in s['nmr_type']])
            
            col1, col2 = st.columns(2)
            col1.metric("氢谱", h_count)
            col2.metric("碳谱", c_count)
            
            st.divider()
            
            for s in samples:
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{s['sample_name']}**")
                    st.caption(f"类型: {s['nmr_type']} | 溶剂: {s.get('solvent', '未指定')}")
                    st.caption(f"提交人: {s['submitter']} | 时间: {s['submitted_at'][:16]}")
                    if s['notes']:
                        st.caption(f"备注: {s['notes']}")
                with col3:
                    if f'confirm_nmr_{s["id"]}' not in st.session_state:
                        st.session_state[f'confirm_nmr_{s["id"]}'] = False
                    
                    if not st.session_state[f'confirm_nmr_{s["id"]}']:
                        if st.button(f"✅ 测完", key=f"nmr_{s['id']}"):
                            st.session_state[f'confirm_nmr_{s["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"⚠️ 确认 {s['sample_name']} 已测完？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ 确认", key=f"confirm_nmr_yes_{s['id']}"):
                                supabase.table('nmr_samples').update({'status': 'completed'}).eq('id', s['id']).execute()
                                st.session_state[f'confirm_nmr_{s["id"]}'] = False
                                st.success(f"✅ {s['sample_name']} 已完成")
                                st.rerun()
                        with col_b:
                            if st.button(f"❌ 取消", key=f"confirm_nmr_no_{s['id']}"):
                                st.session_state[f'confirm_nmr_{s["id"]}'] = False
                                st.rerun()
                st.divider()

# ========== 导出Excel ==========
elif menu == "📎 导出Excel":
    st.header("📎 导出试剂清单")
    data = supabase.table('reagents').select('*').execute().data
    
    if data:
        st.info(f"共 {len(data)} 种试剂，点击下方按钮导出Excel文件")
        
        st.subheader("预览（前5条）")
        st.dataframe(pd.DataFrame(data).head(5))
        
        excel_data = export_to_excel(data)
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="试剂清单_{datetime.now().strftime("%Y%m%d")}.xlsx">📥 点击下载Excel文件</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        st.success("导出完成！")
    else:
        st.warning("暂无数据，请先添加试剂")
