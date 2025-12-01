%%writefile app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# 設定頁面配置
st.set_page_config(page_title="台灣遺產稅快速試算", layout="wide")

# --- 初始化 Session State (讓輸入框有記憶功能) ---
# 這是修正「無法輸入」的關鍵：先定義好變數的初始狀態
if 'market_value' not in st.session_state:
    st.session_state.market_value = 8000
if 'ratio' not in st.session_state:
    st.session_state.ratio = 30
if 'tax_value' not in st.session_state:
    st.session_state.tax_value = int(8000 * 0.3)

# --- 連動計算函數 ---
# 只有當使用者動了「市價」或「比例」時，才去更新「課稅現值」
def update_tax_value():
    mv = st.session_state.market_value
    ra = st.session_state.ratio
    st.session_state.tax_value = int(mv * (ra / 100))

# --- 核心計算邏輯 (2024/2025 稅制) ---
def calculate_estate_tax(net_estate):
    if net_estate <= 0:
        return 0
    elif net_estate <= 50000000:
        return net_estate * 0.10
    elif net_estate <= 100000000:
        return net_estate * 0.15 - 2500000
    else:
        return net_estate * 0.20 - 7500000

# --- APP 介面設計 ---
st.title("📊 台灣遺產稅估算神器 (修正版)")
st.caption("已修正輸入框鎖定問題，現在您可以自由輸入數字了。")
st.markdown("---")

# 1. 左側欄：資產與負債輸入
with st.sidebar:
    st.header("1. 輸入資產資料")
    
    st.subheader("🏠 不動產 (房屋+土地)")
    st.info("遺產稅計算基礎為：房屋評定現值 + 土地公告現值")
    
    # 使用 key 和 on_change 來處理連動，避免輸入衝突
    st.number_input(
        "不動產「市價」總額 (萬)", 
        step=100, 
        key='market_value', 
        on_change=update_tax_value
    )
    
    st.slider(
        "公告現值佔市價比例預估 (%)", 
        10, 100, 
        key='ratio', 
        on_change=update_tax_value,
        help="移動此拉桿會自動更新下方的課稅現值"
    )
    
    # 這裡的 value 直接讀取 session_state，允許被手動修改
    real_estate_tax_value = st.number_input(
        "實際課稅現值 (萬) - 可手動修正", 
        key='tax_value',
        step=10,
        help="您可以直接在此輸入精確的公告現值，程式不會再鎖定它了"
    )

    st.subheader("📈 金融資產")
    # 移除 step 限制，讓輸入更自由
    stock_tw = st.number_input("台股部位 (萬)", value=8000, min_value=0)
    stock_us = st.number_input("美股/海外部位 (萬)", value=600, min_value=0)
    cash = st.number_input("現金/存款 (萬)", value=0, min_value=0)
    
    st.subheader("💸 負債與扣除額")
    debt = st.number_input("房貸/私人債務 (萬)", value=3000, min_value=0)
    
    st.subheader("👨‍👩‍👧 繼承人結構")
    has_spouse = st.checkbox("有配偶", value=True)
    num_children = st.number_input("子女如數", min_value=0, value=1, step=1)

# --- 2. 主畫面：計算過程與結果 ---

# A. 計算遺產總額 (課稅基礎)
total_assets_tax_base = real_estate_tax_value + stock_tw + stock_us + cash
total_assets_market = st.session_state.market_value + stock_tw + stock_us + cash 

# B. 計算免稅額與扣除額
exemption = 1333 # 免稅額
deduction_spouse = 553 if has_spouse else 0
deduction_children = 56 * num_children
deduction_funeral = 138
total_deductions = exemption + deduction_spouse + deduction_children + deduction_funeral + debt

# C. 計算淨額與稅金
net_taxable_estate = total_assets_tax_base - total_deductions
tax_payable = calculate_estate_tax(net_taxable_estate * 10000) / 10000 

# --- 儀表板顯示 ---

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="資產市價總額 (真實身價)", value=f"{total_assets_market} 萬")
with col2:
    st.metric(label="遺產稅課稅總額 (公告值)", value=f"{total_assets_tax_base} 萬", delta=f"與市價差額: {total_assets_market - total_assets_tax_base} 萬")
with col3:
    st.metric(label="扣除額合計 (含負債)", value=f"{total_deductions} 萬")

st.markdown("---")

st.subheader("📝 試算結果")

if net_taxable_estate > 0:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.error(f"預估應繳納遺產稅： {tax_payable:,.2f} 萬元")
        st.write(f"課稅淨額： {net_taxable_estate:,.2f} 萬元")
        
        if net_taxable_estate <= 5000:
            st.caption("目前適用稅率：10%")
        elif net_taxable_estate <= 10000:
            st.caption("目前適用稅率：15%")
        else:
            st.caption("目前適用稅率：20%")
            
    with c2:
        liquidity_gap = cash - tax_payable
        if liquidity_gap < 0:
            st.warning(f"⚠️ 現金流警示：\n帳上現金不足以繳稅！\n缺口約 {abs(liquidity_gap):.2f} 萬")
        else:
            st.success("✅ 現金流充足。")
else:
    st.success("恭喜！預估 **免繳** 遺產稅。")

st.markdown("---")
st.subheader("📊 資產結構分析")

df_assets = pd.DataFrame({
    '資產類別': ['不動產(課稅值)', '台股', '美股', '現金'],
    '金額': [real_estate_tax_value, stock_tw, stock_us, cash]
})

fig = px.pie(df_assets, values='金額', names='資產類別', title='課稅資產分佈圖', hole=0.4)
st.plotly_chart(fig, use_container_width=True)
