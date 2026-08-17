import csv
import random
from pathlib import Path
from collections import Counter

SEED = 42
PER_CATEGORY = 50 #rows generated per category 
TEST_FRACTION = 0.20 #20% of each category is held out for test.csv
random.seed(SEED)

CITIES = ["BLR", "MUM", "DEL", "HYD", "CHN", "PUN", "KOL", "GGN", "NOIDA", "AMD"]

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

def ref(n=6):
    return "".join(random.choices("0123456789", k=n))

MERCHANTS = {
    "Dining": ["SWIGGY", "ZOMATO", "DOMINOS", "MCDONALDS", "KFC", "PIZZA HUT", "BURGER KING", "CAFE COFFEE DAY", "STARBUCKS", "BARBEQUE NATION", "HALDIRAM", "SUBWAY", "FAASOS", "BEHROUZ BIRYANI", "CHAAYOS"],
    "Groceries": ["BLINKIT", "ZEPTO", "INSTAMART", "BIGBASKET", "DMART", "RELIANCE FRESH", "MORE SUPERMARKET", "SPENCERS", "NATURES BASKET", "STAR BAZAAR", "JIOMART GROCERY"],
    "Transportation": ["UBER INDIA", "OLA CABS", "RAPIDO", "IRCTC", "HP PETROL", "INDIAN OIL", "BHARAT PETROLEUM", "DELHI METRO", "BTMC", "NAMMA METRO", "REDBUS", "ABHIBUS", "FASTAG RECHARGE", "SHELL FUEL", "TSRTC", "METRO", "AUTO", "TAXI", "BIKE", "CAB"],
    "Utilities": ["BSES YAMUNA", "TATA POWER", "ADANI ELECTRICITY", "AIRTEL BROADBAND","JIO FIBER", "ACT FIBERNET", "MAHANAGAR GAS", "BWSSB WATER","TORRENT POWER", "VI POSTPAID", "BSNL BILL"],
    "Shopping": ["AMAZON PAY INDIA", "FLIPKART", "MYNTRA", "AJIO", "NYKAA", "ZARA", "H AND M", "RELIANCE TRENDS", "MEESHO", "SNAPDEAL", "TATA CLIQ", "WESTSIDE", "LIFESTYLE STORE"],
    "Entertainment": ["BOOKMYSHOW", "PVR CINEMAS", "INOX LEISURE", "CINEPOLIS", "WONDERLA", "PVR", "TICKETNEW", "PAYT INSIDER", "IMAGICA", "SNOW WORLD"],
    "Income": ["SALARY", "INTEREST", "DIVIDEND", "CASHBACK", "BONUS", "REIMBURSEMENT", "FREELANCE PAYMENT", "REFUND"],
    "Transfer": ["RIKHITHA REDDY", "SELF ACCOUNT", "MUTUAL FUND SIP", "PPF TRANSFER", "RD INSTALLMENT", "GROWN", "ZERODHA", "KUVERA"],"Healthcare": ["APOLLO PHARMACY", "1MG", "PHARMEASY", "NETMEDS", "FORTIS HOSPITAL", "MAX HEALTHCARE", "DR LAL PATHLABS", "PRACTO", "MANIPAL HOSPITAL", "MEDPLUS", "STAR HEALTH INSURANCE"],"Subscriptions": ["NETFLIX", "SPOTIFY", "AMAZON PRIME", "DISNEY HOTSTAR", "YOUTUBE PREMIUM", "CULT FIT", "LINKEDIN PREMIUM", "AUDIBLE", "SONYLIV", "ZEES", "APPLE ICLOUD"],
    "Housing": ["RENT", "HOME LOAN EMI", "SOCIETY MAINTENANCE", "NOBROKER RENT", "HOUSING SOCIETY DUES", "PROPERTY TAX", "FLAT MAINTENANCE"],
    "Uncategorized": ["ATM CASH WDL", "CHQ PAID", "MISC DEBIT", "BANK CHARGES","SERVICE CHARGE", "NEFT REF", "ADJUSTMENT ENTRY"],
}

EXPENSE_TEMPLATES = ["UPI/{m}/{ref}/PAYMENT", "UPI-{m}-ref", "POS {ref} {m}", "{m} {city}", "{m} ONLINE", "{m} PVT LTD"]
INCOME_TEMPLATES = ["NEFT CR-{m} {month}", "ACH CREDIT {m}", "IMPS {m} CREDIT", "{m} CREDIT SB AC {ref}", "UPI/{m}/CREDIT/{ref}"]
TRANSFER_TEMPLATES = ["UPI/{m}/{ref}", "IMPS TO {m}", "NEFT {m} XFER", "ACH DR {m} {ref}", "PHONEPE {m} {ref}"]
HOUSING_TEMPLATES = ["imps {m} {month}", "UPI/{m}/{ref}/PAYMENT", "POS {ref} {m}", "{m} PAYMENT {month}"]
UNCAT_TEMPLATES = ["{m} {ref}", "UPI/{ref}/NA", "Pos {ref} UNKNOWN MERCHANT", "{m}"]

TEMPLATE_GROUPS = {"Income": INCOME_TEMPLATES, "Transfer": TRANSFER_TEMPLATES, "Housing": HOUSING_TEMPLATES, "Uncategorized": UNCAT_TEMPLATES}

def render(category, merchant):
    template = random.choice(TEMPLATE_GROUPS.get(category, EXPENSE_TEMPLATES))
    return template.format(m=merchant, ref=ref(), city=random.choice(CITIES), month=random.choice(MONTHS))

def write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)    

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["description","category"])
        w.writerows(rows)

train_rows, test_rows, global_seen = [], [], set()
for category, merchants in MERCHANTS.items():
    rows, attempts = [], 0
    while len(rows) < PER_CATEGORY and attempts < PER_CATEGORY * 40:
        attempts += 1
        desc = render(category, random.choice(merchants))
        if desc.lower() in global_seen:
            continue
        global_seen.add(desc.lower())
        rows.append((desc,category))
    random.shuffle(rows)
    n_test = int(len(rows)*TEST_FRACTION)
    test_rows.extend(rows[:n_test])
    train_rows.extend(rows[n_test:])
    
random.shuffle(train_rows)
random.shuffle(test_rows)
write_csv("data/training.csv", train_rows)
write_csv("data/test.csv",test_rows)

overlap = {d.lower() for d, _ in train_rows} & {d.lower() for d, _ in test_rows}
print(f"training.csv {len(train_rows)} rows")
print(f"test.csv: {len(test_rows)} rows")
print(f"Overlap between them (MUST be 0); {len(overlap)}")
print("Test distribution: ", dict(Counter(c for _, c in test_rows)))
    