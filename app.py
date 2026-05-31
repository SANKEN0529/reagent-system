import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import io
import base64

# ========== 管理员配置 ==========
ADMIN_PASSWORD = "18110"

# Supabase 配置
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="实验室管理系统", page_icon="🧪", layout="wide")

# ========== 初始化状态 ==========
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

st.title("🧪 实验室综合管理系统")

# ========== 主菜单 ==========
menu = st.sidebar.radio("菜单", ["📋 试剂管理", "🔬 LCMS 送测", "⚛️ 核磁送测", "🛒 购买预约", "👑 管理员模式"])

# ========== 危险等级和存放要求选项 ==========
DANGER_LEVELS = ["无", "易燃", "腐蚀", "有毒", "易燃+有毒", "腐蚀+有毒", "易燃+腐蚀", "剧毒"]
STORAGE_REQUIREMENTS = ["无特殊要求", "阴凉干燥", "避光保存", "通风柜", "冰箱冷藏", "冷冻保存", "防潮", "密封保存"]

# 导出Excel函数（已隐藏ID）
def export_to_excel(data):
    df = pd.DataFrame(data)
    export_cols = ['name', 'cas', 'location', 'total', 'unit', 'date', 'danger_level', 'storage_requirement', 'remark']
    df = df[export_cols]
    df.columns = ['名称', 'CAS号', '位置', '总量', '单位', '登入日期', '危险等级', '存放要求', '备注']
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='试剂清单')
    return output.getvalue()

# ============================================================
# 1. 试剂管理
# ============================================================
if menu == "📋 试剂管理":
    st.header("📋 试剂管理")
    
    reagent_menu = st.radio("选择操作", ["查看所有", "添加试剂", "搜索试剂", "编辑/删除"], horizontal=True)
    
    # 查看所有（已隐藏ID）
    if reagent_menu == "查看所有":
        data = supabase.table('reagents').select('*').execute().data
        if data:
            df = pd.DataFrame(data)
            display_cols = ['name', 'cas', 'location', 'total', 'unit', 'date', 'danger_level', 'storage_requirement', 'remark']
            df_display = df[display_cols]
            df_display.columns = ['名称', 'CAS号', '位置', '总量', '单位', '登入日期', '危险等级', '存放要求', '备注']
            st.dataframe(df_display, use_container_width=True)
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
                    st.error("请填写完整信息")
    
    # 搜索试剂（已隐藏ID）
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
                df_result = pd.DataFrame(data)
                display_cols = ['name', 'cas', 'location', 'total', 'unit', 'date', 'danger_level', 'storage_requirement', 'remark']
                df_display = df_result[display_cols]
                df_display.columns = ['名称', 'CAS号', '位置', '总量', '单位', '登入日期', '危险等级', '存放要求', '备注']
                st.dataframe(df_display)
            else:
                st.warning("未找到")
    
    elif reagent_menu == "编辑/删除":
        data = supabase.table('reagents').select('*').execute().data
        if data:
            search_term = st.text_input("输入试剂名称或CAS号进行搜索")
            
            filtered_data = data
            if search_term:
                search_lower = search_term.lower()
                filtered_data = [r for r in data if search_lower in r['name'].lower() or search_lower in (r['cas'] or "").lower()]
            
            if not filtered_data:
                st.warning("未找到匹配的试剂")
            else:
                st.write(f"找到 {len(filtered_data)} 种试剂")
                options = {f"[ID:{r['id']}] {r['name']}": r for r in filtered_data}
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
                    
                    if st.form_submit_button("💾 保存修改"):
                        supabase.table('reagents').update({
                            'name': new_name, 'cas': new_cas, 'location': new_location,
                            'total': new_total, 'unit': new_unit,
                            'danger_level': new_danger, 'storage_requirement': new_storage,
                            'remark': new_remark
                        }).eq('id', r['id']).execute()
                        st.success("✅ 已保存")
                        st.rerun()
                
                st.markdown("---")
                if st.button("🗑️ 删除试剂", key=f"del_btn_{r['id']}", type="primary"):
                    st.session_state[f'delete_confirm_{r["id"]}'] = True
                
                if st.session_state.get(f'delete_confirm_{r["id"]}', False):
                    st.warning(f"⚠️ 确认删除「{r['name']}」？")
                    col_cfm, col_cnl = st.columns(2)
                    with col_cfm:
                        if st.button("✅ 确认删除"):
                            supabase.table('reagents').delete().eq('id', r['id']).execute()
                            st.session_state[f'delete_confirm_{r["id"]}'] = False
                            st.success("✅ 已删除")
                            st.rerun()
                    with col_cnl:
                        if st.button("❌ 取消"):
                            st.session_state[f'delete_confirm_{r["id"]}'] = False
                            st.rerun()
        else:
            st.info("暂无数据")

# ============================================================
# 2. LCMS 送测
# ============================================================
if menu == "🔬 LCMS 送测":
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
            st.info("暂无待测样品 🎉")
        else:
            st.subheader(f"📊 待测数量：{len(samples)} 个样品")
            
            for s in samples:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{s['sample_name']}**")
                    st.caption(f"提交人: {s['submitter']} | 时间: {s['submitted_at'][:16]}")
                    if s['notes']:
                        st.caption(f"备注: {s['notes']}")
                
                with col2:
                    if f'confirm_lcms_del_{s["id"]}' not in st.session_state:
                        st.session_state[f'confirm_lcms_del_{s["id"]}'] = False
                    
                    if not st.session_state[f'confirm_lcms_del_{s["id"]}']:
                        if st.button(f"🗑️ 删除", key=f"lcms_del_{s['id']}"):
                            st.session_state[f'confirm_lcms_del_{s["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"确认删除 {s['sample_name']}？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"确认", key=f"lcms_del_yes_{s['id']}"):
                                supabase.table('lcms_samples').delete().eq('id', s['id']).execute()
                                st.session_state[f'confirm_lcms_del_{s["id"]}'] = False
                                st.success("🗑️ 已删除")
                                st.rerun()
                        with col_b:
                            if st.button(f"取消", key=f"lcms_del_no_{s['id']}"):
                                st.session_state[f'confirm_lcms_del_{s["id"]}'] = False
                                st.rerun()
                st.divider()

# ============================================================
# 3. 核磁送测
# ============================================================
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
            st.info("暂无待测样品 🎉")
        else:
            h_count = len([s for s in samples if '氢谱' in s['nmr_type']])
            c_count = len([s for s in samples if '碳谱' in s['nmr_type']])
            
            col1, col2 = st.columns(2)
            col1.metric("氢谱", h_count)
            col2.metric("碳谱", c_count)
            st.divider()
            
            for s in samples:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{s['sample_name']}**")
                    st.caption(f"类型: {s['nmr_type']} | 溶剂: {s.get('solvent', '未指定')}")
                    st.caption(f"提交人: {s['submitter']} | 时间: {s['submitted_at'][:16]}")
                    if s['notes']:
                        st.caption(f"备注: {s['notes']}")
                
                with col2:
                    if f'confirm_nmr_del_{s["id"]}' not in st.session_state:
                        st.session_state[f'confirm_nmr_del_{s["id"]}'] = False
                    
                    if not st.session_state[f'confirm_nmr_del_{s["id"]}']:
                        if st.button(f"🗑️ 删除", key=f"nmr_del_{s['id']}"):
                            st.session_state[f'confirm_nmr_del_{s["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"确认删除 {s['sample_name']}？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"确认", key=f"nmr_del_yes_{s['id']}"):
                                supabase.table('nmr_samples').delete().eq('id', s['id']).execute()
                                st.session_state[f'confirm_nmr_del_{s["id"]}'] = False
                                st.success("🗑️ 已删除")
                                st.rerun()
                        with col_b:
                            if st.button(f"取消", key=f"nmr_del_no_{s['id']}"):
                                st.session_state[f'confirm_nmr_del_{s["id"]}'] = False
                                st.rerun()
                st.divider()

# ============================================================
# ============================================================
# 4. 购买预约（普通用户）
# ============================================================
elif menu == "🛒 购买预约":
    st.header("🛒 试剂购买预约")
    
    tab1, tab2 = st.tabs(["📝 登记购买需求", "✅ 查看购买记录"])
    
    with tab1:
        with st.form("purchase_form"):
            col1, col2 = st.columns(2)
            with col1:
                requester = st.text_input("申请人 *")
                reagent_name = st.text_input("试剂名称 *")
                cas = st.text_input("CAS号")
                specification = st.text_input("规格", placeholder="例如：500ml, 分析纯, 500g")
            with col2:
                supplier = st.text_input("商家名称")
                product_number = st.text_input("产品编号")
                price = st.number_input("价格 (元)", min_value=0.0, step=10.0, format="%.2f")
                notes = st.text_area("备注", placeholder="用途、紧急程度等")
            
            if st.form_submit_button("📤 提交购买预约"):
                if requester and reagent_name:
                    supabase.table('purchase_requests').insert({
                        'requester': requester,
                        'reagent_name': reagent_name,
                        'cas': cas,
                        'specification': specification,
                        'supplier': supplier,
                        'product_number': product_number,
                        'price': price,
                        'notes': notes,
                        'purchase_status': '无'
                    }).execute()
                    st.success(f"✅ 已提交购买预约：{reagent_name}")
                    st.balloons()
                else:
                    st.error("请填写申请人和试剂名称")
    
    with tab2:
        st.subheader("📋 购买记录")
        
        # 筛选状态
        filter_status = st.radio("筛选状态", ["全部", "无", "已购买"], horizontal=True)
        
        # 加载数据
        if filter_status == "全部":
            requests = supabase.table('purchase_requests').select('*').order('requested_at', desc=True).execute().data
        else:
            requests = supabase.table('purchase_requests').select('*').eq('purchase_status', filter_status).order('requested_at', desc=True).execute().data
        
        if not requests:
            st.info("暂无记录")
        else:
            st.caption(f"共 {len(requests)} 条记录")
            
            for req in requests:
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    st.write(f"**{req['reagent_name']}**")
                    details = []
                    if req.get('cas'):
                        details.append(f"CAS: {req['cas']}")
                    if req.get('specification'):
                        details.append(f"规格: {req['specification']}")
                    if req.get('supplier'):
                        details.append(f"商家: {req['supplier']}")
                    if req.get('product_number'):
                        details.append(f"货号: {req['product_number']}")
                    if req.get('price'):
                        details.append(f"¥{req['price']}")
                    st.caption(" | ".join(details))
                    st.caption(f"申请人: {req['requester']} | 时间: {req['requested_at'][:16]}")
                    if req.get('notes'):
                        st.caption(f"备注: {req['notes']}")
                
                with col2:
                    status = req.get('purchase_status', '无')
                    if status == "无":
                        st.markdown("🟡 **状态: 无**")
                    elif status == "已购买":
                        st.markdown("🟢 **状态: 已购买**")
                
                with col3:
                    if f'user_delete_confirm_{req["id"]}' not in st.session_state:
                        st.session_state[f'user_delete_confirm_{req["id"]}'] = False
                    
                    if not st.session_state[f'user_delete_confirm_{req["id"]}']:
                        if st.button(f"🗑️ 删除", key=f"user_del_{req['id']}"):
                            st.session_state[f'user_delete_confirm_{req["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"确认删除 {req['reagent_name']}？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ 确认", key=f"user_del_yes_{req['id']}"):
                                supabase.table('purchase_requests').delete().eq('id', req['id']).execute()
                                st.session_state[f'user_delete_confirm_{req["id"]}'] = False
                                st.success(f"🗑️ 已删除 {req['reagent_name']}")
                                st.rerun()
                        with col_b:
                            if st.button(f"❌ 取消", key=f"user_del_no_{req['id']}"):
                                st.session_state[f'user_delete_confirm_{req["id"]}'] = False
                                st.rerun()
                
                st.divider()

# ============================================================
# 5. 管理员模式
# ============================================================
elif menu == "👑 管理员模式":
    st.header("👑 管理员模式")
    
    if not st.session_state.admin_logged_in:
        password = st.text_input("请输入管理员密码", type="password")
        if st.button("登录"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("密码错误")
        st.stop()
    
    st.success("✅ 已登录管理员模式")
    
    admin_menu = st.radio("选择管理项目", ["LCMS 管理", "核磁管理", "购买预约管理", "数据导入导出", "系统设置"], horizontal=True)
    
    # LCMS 管理
    if admin_menu == "LCMS 管理":
        st.subheader("🔬 LCMS 所有记录")
        
        all_samples = supabase.table('lcms_samples').select('*').order('submitted_at', desc=True).execute().data
        
        if not all_samples:
            st.info("暂无记录")
        else:
            st.caption(f"共 {len(all_samples)} 条记录")
            
            if st.button("⚠️ 一键删除全部 LCMS 记录", type="primary"):
                st.session_state['confirm_delete_all_lcms'] = True
            
            if st.session_state.get('confirm_delete_all_lcms', False):
                st.warning("⚠️ 确认删除所有 LCMS 记录？此操作不可恢复！")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 确认删除全部"):
                        supabase.table('lcms_samples').delete().neq('id', 0).execute()
                        st.session_state['confirm_delete_all_lcms'] = False
                        st.success("已删除所有记录")
                        st.rerun()
                with col2:
                    if st.button("❌ 取消"):
                        st.session_state['confirm_delete_all_lcms'] = False
                        st.rerun()
            
            st.divider()
            
            for s in all_samples:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{s['sample_name']}**")
                    st.caption(f"提交人: {s['submitter']} | 时间: {s['submitted_at'][:16]} | 状态: {s.get('status', 'pending')}")
                    if s.get('notes'):
                        st.caption(f"备注: {s['notes']}")
                
                # 删除按钮（带二次确认）
                with col2:
                    if f'admin_lcms_del_confirm_{s["id"]}' not in st.session_state:
                        st.session_state[f'admin_lcms_del_confirm_{s["id"]}'] = False
                    
                    if not st.session_state[f'admin_lcms_del_confirm_{s["id"]}']:
                        if st.button(f"🗑️ 删除", key=f"admin_lcms_del_{s['id']}"):
                            st.session_state[f'admin_lcms_del_confirm_{s["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"确认删除 {s['sample_name']}？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ 确认", key=f"admin_lcms_del_yes_{s['id']}"):
                                supabase.table('lcms_samples').delete().eq('id', s['id']).execute()
                                st.session_state[f'admin_lcms_del_confirm_{s["id"]}'] = False
                                st.success(f"🗑️ 已删除 {s['sample_name']}")
                                st.rerun()
                        with col_b:
                            if st.button(f"❌ 取消", key=f"admin_lcms_del_no_{s['id']}"):
                                st.session_state[f'admin_lcms_del_confirm_{s["id"]}'] = False
                                st.rerun()
                st.divider()
    
       # 核磁管理
    elif admin_menu == "核磁管理":
        st.subheader("⚛️ 核磁所有记录")
        
        all_samples = supabase.table('nmr_samples').select('*').order('submitted_at', desc=True).execute().data
        
        if not all_samples:
            st.info("暂无记录")
        else:
            st.caption(f"共 {len(all_samples)} 条记录")
            
            if st.button("⚠️ 一键删除全部 核磁 记录", type="primary"):
                st.session_state['confirm_delete_all_nmr'] = True
            
            if st.session_state.get('confirm_delete_all_nmr', False):
                st.warning("⚠️ 确认删除所有核磁记录？此操作不可恢复！")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 确认删除全部"):
                        supabase.table('nmr_samples').delete().neq('id', 0).execute()
                        st.session_state['confirm_delete_all_nmr'] = False
                        st.success("已删除所有记录")
                        st.rerun()
                with col2:
                    if st.button("❌ 取消"):
                        st.session_state['confirm_delete_all_nmr'] = False
                        st.rerun()
            
            st.divider()
            
            for s in all_samples:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{s['sample_name']}**")
                    st.caption(f"类型: {s['nmr_type']} | 溶剂: {s.get('solvent', '未指定')}")
                    st.caption(f"提交人: {s['submitter']} | 时间: {s['submitted_at'][:16]} | 状态: {s.get('status', 'pending')}")
                    if s.get('notes'):
                        st.caption(f"备注: {s['notes']}")
                
                # 删除按钮（带二次确认）
                with col2:
                    if f'admin_nmr_del_confirm_{s["id"]}' not in st.session_state:
                        st.session_state[f'admin_nmr_del_confirm_{s["id"]}'] = False
                    
                    if not st.session_state[f'admin_nmr_del_confirm_{s["id"]}']:
                        if st.button(f"🗑️ 删除", key=f"admin_nmr_del_{s['id']}"):
                            st.session_state[f'admin_nmr_del_confirm_{s["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"确认删除 {s['sample_name']}？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ 确认", key=f"admin_nmr_del_yes_{s['id']}"):
                                supabase.table('nmr_samples').delete().eq('id', s['id']).execute()
                                st.session_state[f'admin_nmr_del_confirm_{s["id"]}'] = False
                                st.success(f"🗑️ 已删除 {s['sample_name']}")
                                st.rerun()
                        with col_b:
                            if st.button(f"❌ 取消", key=f"admin_nmr_del_no_{s['id']}"):
                                st.session_state[f'admin_nmr_del_confirm_{s["id"]}'] = False
                                st.rerun()
                st.divider()
    
       # 购买预约管理
    elif admin_menu == "购买预约管理":
        st.subheader("🛒 购买预约所有记录")
        
        # 搜索框和筛选
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search_keyword = st.text_input("🔍 搜索（试剂名称/CAS号/申请人/商家）", placeholder="输入关键字...", key="admin_purchase_search")
        with col_filter:
            filter_status = st.selectbox(
                "筛选状态", 
                ["全部", "无", "已购买"], 
                key="admin_purchase_filter"
            )
        
        # 加载所有数据
        all_requests = supabase.table('purchase_requests').select('*').order('requested_at', desc=True).execute().data
        
        # 应用筛选
        filtered_requests = all_requests
        if filter_status != "全部":
            filtered_requests = [r for r in filtered_requests if r.get('purchase_status', '无') == filter_status]
        
        # 应用搜索
        if search_keyword:
            keyword_lower = search_keyword.lower()
            filtered_requests = [
                r for r in filtered_requests
                if keyword_lower in r.get('reagent_name', '').lower()
                or keyword_lower in r.get('cas', '').lower()
                or keyword_lower in r.get('requester', '').lower()
                or keyword_lower in r.get('supplier', '').lower()
            ]
        
        if not filtered_requests:
            if search_keyword:
                st.info(f"未找到包含「{search_keyword}」的记录")
            else:
                st.info(f"暂无 {filter_status} 状态的记录" if filter_status != "全部" else "暂无记录")
        else:
            st.caption(f"共 {len(filtered_requests)} 条记录")
            
            for req in filtered_requests:
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    st.write(f"**{req['reagent_name']}**")
                    details = []
                    if req.get('cas'):
                        details.append(f"CAS: {req['cas']}")
                    if req.get('specification'):
                        details.append(f"规格: {req['specification']}")
                    if req.get('supplier'):
                        details.append(f"商家: {req['supplier']}")
                    if req.get('product_number'):
                        details.append(f"货号: {req['product_number']}")
                    if req.get('price'):
                        details.append(f"¥{req['price']}")
                    st.caption(" | ".join(details))
                    st.caption(f"申请人: {req['requester']} | 时间: {req['requested_at'][:16]}")
                    if req.get('notes'):
                        st.caption(f"备注: {req['notes']}")
                
                # 状态选择（无/已购买）
                with col2:
                    current_status = req.get('purchase_status', '无')
                    new_status = st.selectbox(
                        "状态",
                        ["无", "已购买"],
                        index=0 if current_status == "无" else 1,
                        key=f"admin_status_{req['id']}"
                    )
                    if new_status != current_status:
                        supabase.table('purchase_requests').update({'purchase_status': new_status}).eq('id', req['id']).execute()
                        st.rerun()
                
                # 已送达按钮（确认后删除）
                with col3:
                    if f'admin_deliver_confirm_{req["id"]}' not in st.session_state:
                        st.session_state[f'admin_deliver_confirm_{req["id"]}'] = False
                    
                    if not st.session_state[f'admin_deliver_confirm_{req["id"]}']:
                        if st.button(f"📦 已送达", key=f"admin_deliver_{req['id']}"):
                            st.session_state[f'admin_deliver_confirm_{req["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"确认 {req['reagent_name']} 已送达？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ 确认", key=f"admin_deliver_yes_{req['id']}"):
                                supabase.table('purchase_requests').delete().eq('id', req['id']).execute()
                                st.session_state[f'admin_deliver_confirm_{req["id"]}'] = False
                                st.success(f"📦 {req['reagent_name']} 已送达并删除")
                                st.rerun()
                        with col_b:
                            if st.button(f"❌ 取消", key=f"admin_deliver_no_{req['id']}"):
                                st.session_state[f'admin_deliver_confirm_{req["id"]}'] = False
                                st.rerun()
                
                # 删除按钮（确认后删除）
                with col4:
                    if f'admin_delete_confirm_{req["id"]}' not in st.session_state:
                        st.session_state[f'admin_delete_confirm_{req["id"]}'] = False
                    
                    if not st.session_state[f'admin_delete_confirm_{req["id"]}']:
                        if st.button(f"🗑️ 删除", key=f"admin_del_{req['id']}"):
                            st.session_state[f'admin_delete_confirm_{req["id"]}'] = True
                            st.rerun()
                    else:
                        st.warning(f"确认删除 {req['reagent_name']}？")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ 确认删除", key=f"admin_del_yes_{req['id']}"):
                                supabase.table('purchase_requests').delete().eq('id', req['id']).execute()
                                st.session_state[f'admin_delete_confirm_{req["id"]}'] = False
                                st.success(f"🗑️ 已删除 {req['reagent_name']}")
                                st.rerun()
                        with col_b:
                            if st.button(f"❌ 取消", key=f"admin_del_no_{req['id']}"):
                                st.session_state[f'admin_delete_confirm_{req["id"]}'] = False
                                st.rerun()
                
                st.divider()
                
           # 数据导入导出
    elif admin_menu == "数据导入导出":
        st.subheader("📊 数据导入导出")
        
        tab_export, tab_import = st.tabs(["📎 导出数据", "📂 导入数据"])
        
        # ========== 导出数据 ==========
        with tab_export:
            st.write("### 导出试剂清单")
            
            data = supabase.table('reagents').select('*').execute().data
            
            if data:
                st.info(f"共 {len(data)} 种试剂")
                
                df = pd.DataFrame(data)
                export_cols = ['name', 'cas', 'location', 'total', 'unit', 'date', 'danger_level', 'storage_requirement', 'remark']
                df = df[export_cols]
                df.columns = ['名称', 'CAS号', '位置', '总量', '单位', '登入日期', '危险等级', '存放要求', '备注']
                
                df['总量'] = df['总量'].apply(lambda x: int(x) if float(x).is_integer() else x)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='试剂清单')
                
                excel_data = output.getvalue()
                b64 = base64.b64encode(excel_data).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="试剂清单_{datetime.now().strftime("%Y%m%d")}.xlsx">📥 点击下载Excel文件</a>'
                st.markdown(href, unsafe_allow_html=True)
                
                st.success("导出完成！")
                st.subheader("预览（前5条）")
                st.dataframe(df.head(5))
            else:
                st.warning("暂无数据")
        
              # ========== 导入数据 ==========
        with tab_import:
            st.write("### 导入试剂清单")
            st.info("📌 导入说明：\n"
                    "- **必填列**：名称、位置、总量、单位\n"
                    "- **选填列**：CAS号、登入日期、危险等级、存放要求、备注\n"
                    "- 缺少选填列时会自动填入默认值\n"
                    "- 请使用「导出数据」功能生成的模板文件\n"
                    "- 如果导入失败，请先用导出功能生成新模板")
            
            if st.button("📥 下载导入模板"):
                template_df = pd.DataFrame({
                    '名称': ['示例试剂'],
                    'CAS号': ['64-17-5'],
                    '位置': ['A柜-1层'],
                    '总量': [5000],
                    '单位': ['ml'],
                    '登入日期': [datetime.now().strftime("%Y-%m-%d")],
                    '危险等级': ['无'],
                    '存放要求': ['无特殊要求'],
                    '备注': ['这是示例']
                })
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    template_df.to_excel(writer, index=False, sheet_name='模板')
                template_data = output.getvalue()
                b64 = base64.b64encode(template_data).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="导入模板.xlsx">📥 点击下载导入模板</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("选择 Excel 文件", type=["xlsx", "xls"])
            
            if uploaded_file is not None:
                try:
                    df_import = pd.read_excel(uploaded_file, dtype=str)
                    
                    # 改为预览将要导入的数据
                    st.subheader("📋 预览将要导入的数据")
                    st.dataframe(df_import.head())
                    
                    required_cols = ['名称', '位置', '总量', '单位']
                    missing_cols = [col for col in required_cols if col not in df_import.columns]
                    
                    if missing_cols:
                        st.error(f"缺少必要的列：{', '.join(missing_cols)}")
                        st.write("当前文件的列名：", list(df_import.columns))
                    else:
                        if st.button("✅ 确认导入"):
                            success_count = 0
                            error_count = 0
                            error_messages = []
                            
                            for idx, row in df_import.iterrows():
                                try:
                                    name = str(row.get('名称', '')).strip()
                                    if not name or name == 'nan':
                                        error_count += 1
                                        error_messages.append(f"第{idx+2}行：名称为空")
                                        continue
                                    
                                    location = str(row.get('位置', '')).strip()
                                    if not location or location == 'nan':
                                        error_count += 1
                                        error_messages.append(f"第{idx+2}行：位置为空")
                                        continue
                                    
                                    total_str = str(row.get('总量', '')).strip()
                                    if not total_str or total_str == 'nan':
                                        error_count += 1
                                        error_messages.append(f"第{idx+2}行：总量为空")
                                        continue
                                    
                                    import re
                                    total_match = re.search(r'[\d.]+', total_str)
                                    if total_match:
                                        total_val = float(total_match.group())
                                    else:
                                        error_count += 1
                                        error_messages.append(f"第{idx+2}行：总量格式错误")
                                        continue
                                    
                                    unit = str(row.get('单位', '')).strip()
                                    if not unit or unit == 'nan':
                                        error_count += 1
                                        error_messages.append(f"第{idx+2}行：单位为空")
                                        continue
                                    
                                    cas_val = str(row.get('CAS号', '')).strip()
                                    if cas_val == 'nan':
                                        cas_val = ""
                                    
                                    date_str = row.get('登入日期', '')
                                    if pd.isna(date_str) or str(date_str) == 'nan':
                                        date_str = datetime.now().strftime("%Y-%m-%d")
                                    else:
                                        date_str = str(date_str)[:10]
                                    
                                    danger_val = str(row.get('危险等级', '无')).strip()
                                    if danger_val == 'nan' or danger_val not in DANGER_LEVELS:
                                        danger_val = '无'
                                    
                                    storage_val = str(row.get('存放要求', '无特殊要求')).strip()
                                    if storage_val == 'nan' or storage_val not in STORAGE_REQUIREMENTS:
                                        storage_val = '无特殊要求'
                                    
                                    remark_val = str(row.get('备注', '')).strip()
                                    if remark_val == 'nan':
                                        remark_val = ""
                                    
                                    supabase.table('reagents').insert({
                                        'name': name,
                                        'cas': cas_val,
                                        'location': location,
                                        'total': total_val,
                                        'unit': unit,
                                        'date': date_str,
                                        'danger_level': danger_val,
                                        'storage_requirement': storage_val,
                                        'remark': remark_val
                                    }).execute()
                                    success_count += 1
                                    
                                except Exception as e:
                                    error_count += 1
                                    error_messages.append(f"第{idx+2}行 {row.get('名称', '未知')}: {str(e)[:50]}")
                            
                            st.success(f"✅ 导入完成！成功：{success_count} 条，失败：{error_count} 条")
                            if error_messages:
                                with st.expander("查看失败详情"):
                                    for msg in error_messages[:20]:
                                        st.write(f"- {msg}")
                            if success_count > 0:
                                st.rerun()
                except Exception as e:
                    st.error(f"读取文件失败：{e}")
                    st.write("请点击「下载导入模板」按钮，使用生成的模板文件填写数据")
    # ========== 系统设置 ==========
    elif admin_menu == "系统设置":
        st.subheader("系统设置")
        
        st.warning("⚠️ 以下操作不可恢复，请谨慎使用！")
        
        # 清空试剂数据
        with st.expander("🗑️ 清空试剂数据"):
            st.write("此操作将删除 **所有试剂数据**，不可恢复！")
            
            # 获取当前试剂数量
            reagent_count = len(supabase.table('reagents').select('*', count='exact').execute().data)
            st.write(f"当前共有 **{reagent_count}** 条试剂记录")
            
            if reagent_count > 0:
                # 确认删除
                if 'confirm_clear_reagents' not in st.session_state:
                    st.session_state.confirm_clear_reagents = False
                
                if not st.session_state.confirm_clear_reagents:
                    if st.button("🗑️ 清空所有试剂数据", type="primary"):
                        st.session_state.confirm_clear_reagents = True
                        st.rerun()
                else:
                    st.warning("⚠️ 确认要清空所有试剂数据吗？此操作不可恢复！")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ 确认清空"):
                            supabase.table('reagents').delete().neq('id', 0).execute()
                            st.session_state.confirm_clear_reagents = False
                            st.success("✅ 已清空所有试剂数据")
                            st.rerun()
                    with col2:
                        if st.button("❌ 取消"):
                            st.session_state.confirm_clear_reagents = False
                            st.rerun()
            else:
                st.info("暂无数据")
