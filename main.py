from datetime import datetime
import os
import pytz
import requests
import yfinance as yf

# ---------------------------------------------------------
# 1. 환경 변수에서 텔레그램 정보 가져오기 (GitHub Secrets 연동)
# ---------------------------------------------------------
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


# ---------------------------------------------------------
# 2. 데이터 수집 함수
# ---------------------------------------------------------
def get_ticker_data(ticker_symbol):
    """yfinance를 이용해 현재가 및 전일 대비 변화량 수집"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="5d")

        if len(df) < 2:
            return None, None, None

        current_price = df["Close"].iloc[-1]
        prev_price = df["Close"].iloc[-2]

        change = current_price - prev_price
        pct_change = (change / prev_price) * 100

        return current_price, change, pct_change
    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")
        return None, None, None


def format_value(price, change, pct_change, is_yield=False):
    """상승/하락 아이콘(📈 / 📉) 및 문자열 포맷팅 (현재가 소수점 2자리 고정)"""
    if price is None:
        return "데이터 대기 중"

    # 상승: 📈, 하락: 📉
    if change >= 0:
        icon = "📈"
        sign = "+"
    else:
        icon = "📉"
        sign = ""  # 음수일 경우 기본 '-' 부호가 붙으므로 빈 문자열 처리

    if is_yield:  # 국채 수익률 (%)
        return f"{price:.2f}% ({icon} {sign}{change:.2f}, {sign}{pct_change:.2f}%)"
    else:  # 일반 가격 (소수점 2자리 포맷팅)
        return f"{price:,.2f} ({icon} {sign}{change:,.2f}, {sign}{pct_change:.2f}%)"


# ---------------------------------------------------------
# 3. 리포트 생성 함수
# ---------------------------------------------------------
def generate_report():
    utc_now = datetime.now(pytz.utc)
    kst_now = utc_now.astimezone(pytz.timezone("Asia/Seoul"))
    ny_now = utc_now.astimezone(pytz.timezone("America/New_York"))

    time_header = (
        f"🔔 [{kst_now.strftime('%H')}시 경제 리포트]\n"
        f"🇰🇷 KST:{kst_now.strftime('%H:%M')} | 🇺🇸 NY:{ny_now.strftime('%H:%M')}\n"
    )

    # 지수/환율
    usdkrw_p, usdkrw_c, usdkrw_pct = get_ticker_data("USDKRW=X")
    nasdaq_p, nasdaq_c, nasdaq_pct = get_ticker_data("^IXIC")
    sp500_p, sp500_c, sp500_pct = get_ticker_data("^GSPC")

    section_indices = (
        f"\n📊 지수/환율\n"
        f"원/달러: {format_value(usdkrw_p, usdkrw_c, usdkrw_pct)}\n"
        f"국내선물: 데이터 대기 중\n"
        f"나스닥: {format_value(nasdaq_p, nasdaq_c, nasdaq_pct)}\n"
        f"S&P500: {format_value(sp500_p, sp500_c, sp500_pct)}\n"
    )

    # 미 국채 수익률 (2년물 제외)
    us01y_p, us01y_c, us01y_pct = get_ticker_data("^IRX")
    us05y_p, us05y_c, us05y_pct = get_ticker_data("^FVX")
    us10y_p, us10y_c, us10y_pct = get_ticker_data("^TNX")
    us30y_p, us30y_c, us30y_pct = get_ticker_data("^TYX")

    section_bonds = (
        f"\n🏛️ 미 국채 수익률 (%)\n"
        f"1년물: {format_value(us01y_p, us01y_c, us01y_pct, is_yield=True)}\n"
        f"5년물: {format_value(us05y_p, us05y_c, us05y_pct, is_yield=True)}\n"
        f"10년물: {format_value(us10y_p, us10y_c, us10y_pct, is_yield=True)}\n"
        f"30년물: {format_value(us30y_p, us30y_c, us30y_pct, is_yield=True)}\n"
    )

    # 암호화폐 (비트코인, 이더리움, 테더 추가)
    btc_p, btc_c, btc_pct = get_ticker_data("BTC-USD")
    eth_p, eth_c, eth_pct = get_ticker_data("ETH-USD")
    usdt_p, usdt_c, usdt_pct = get_ticker_data("USDT-USD")

    section_crypto = (
        f"\n🌕 암호화폐\n"
        f"비트코인: {format_value(btc_p, btc_c, btc_pct)}\n"
        f"이더리움: {format_value(eth_p, eth_c, eth_pct)}\n"
        f"테더: {format_value(usdt_p, usdt_c, usdt_pct)}\n"
    )

    # 에너지/금속
    wti_p, wti_c, wti_pct = get_ticker_data("CL=F")
    gold_p, gold_c, gold_pct = get_ticker_data("GC=F")
    silver_p, silver_c, silver_pct = get_ticker_data("SI=F")
    copper_p, copper_c, copper_pct = get_ticker_data("HG=F")
    plat_p, plat_c, plat_pct = get_ticker_data("PL=F")
    pall_p, pall_c, pall_pct = get_ticker_data("PA=F")

    section_commodities = (
        f"\n🛢️ 에너지/금속\n"
        f"WTI유: {format_value(wti_p, wti_c, wti_pct)}\n"
        f"국제금: {format_value(gold_p, gold_c, gold_pct)}\n"
        f"실버: {format_value(silver_p, silver_c, silver_pct)}\n"
        f"구리: {format_value(copper_p, copper_c, copper_pct)}\n"
        f"플래티늄: {format_value(plat_p, plat_c, plat_pct)}\n"
        f"팔라듐: {format_value(pall_p, pall_c, pall_pct)}\n"
    )

    full_message = (
        time_header
        + section_indices
        + section_bonds
        + section_crypto
        + section_commodities
    )
    return full_message


# ---------------------------------------------------------
# 4. 텔레그램 전송 함수
# ---------------------------------------------------------
def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Telegram Bot Token or Chat ID is missing.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    response = requests.post(url, json=payload)
    print("Telegram Response:", response.json())


if __name__ == "__main__":
    message = generate_report()
    print(message)
    send_telegram_message(message)
