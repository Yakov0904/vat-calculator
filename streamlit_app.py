import streamlit as st
import streamlit.components.v1 as components
from decimal import Decimal, ROUND_HALF_UP
import re

st.set_page_config(
    page_title="Калькулятор НДС Онлайн",
    page_icon="💰",
    layout="centered"
)

# ---------- СТИЛЬ ----------
st.markdown("""
<style>
.block-container {
    max-width: 900px;
    padding-top: 2rem;
}
h1 {
    text-align: center;
}
.card {
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #dddddd;
    margin: 10px 0;
}
.result {
    font-size: 18px;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)


# ---------- ЛОГИКА ----------

UNITS_MALE = ["", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
UNITS_FEMALE = ["", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
TEENS = ["десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать",
         "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"]
TENS = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят",
        "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
HUNDREDS = ["", "сто", "двести", "триста", "четыреста", "пятьсот",
            "шестьсот", "семьсот", "восемьсот", "девятьсот"]

SCALES = [
    ("", "", "", False),
    ("тысяча", "тысячи", "тысяч", True),
    ("миллион", "миллиона", "миллионов", False),
    ("миллиард", "миллиарда", "миллиардов", False)
]

RATES = [22, 10, 7, 5]


def plural_form(n, forms):
    n = abs(n) % 100
    if 11 <= n <= 19:
        return forms[2]
    n %= 10
    if n == 1:
        return forms[0]
    if 2 <= n <= 4:
        return forms[1]
    return forms[2]


def triad_to_words(n, female=False):
    words = []
    h = n // 100
    rest = n % 100

    if h:
        words.append(HUNDREDS[h])

    if 10 <= rest <= 19:
        words.append(TEENS[rest - 10])
    else:
        if rest // 10:
            words.append(TENS[rest // 10])
        if rest % 10:
            words.append((UNITS_FEMALE if female else UNITS_MALE)[rest % 10])

    return " ".join(words)


def integer_to_words(n):
    if n == 0:
        return "ноль"

    parts = []
    index = 0

    while n:
        triad = n % 1000
        if triad:
            one, few, many, female = SCALES[index]
            txt = triad_to_words(triad, female)
            if index:
                txt += " " + plural_form(triad, (one, few, many))
            parts.append(txt)

        n //= 1000
        index += 1

    return " ".join(reversed(parts))


def money_to_text(amount):
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    rub = int(amount)
    kop = int((amount - Decimal(rub)) * 100)

    return (
        f"{rub:,}".replace(",", " ")
        + f" ({integer_to_words(rub).capitalize()}) "
        + plural_form(rub, ("рубль", "рубля", "рублей"))
        + f" {kop:02d} "
        + plural_form(kop, ("копейка", "копейки", "копеек"))
    )


def parse_amount(value):
    value = value.replace(" ", "").replace(",", ".")
    if not re.fullmatch(r"\d+(\.\d+)?", value):
        raise ValueError
    return Decimal(value)


def copy_button(text, key):
    import base64

    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")

    components.html(
        f"""
        <html>
        <body style="margin:0;">
        <button id="copy_{key}"
        style="
        width:130px;
        height:38px;
        padding:5px 10px;
        border-radius:8px;
        border:1px solid #888;
        background:white;
        cursor:pointer;
        font-size:14px;">
        📋 Копировать
        </button>

        <script>
        const btn = document.getElementById("copy_{key}");

        btn.onclick = async function() {{
            const text = decodeURIComponent(escape(atob("{encoded}")));

            try {{
                await navigator.clipboard.writeText(text);
            }} catch(e) {{
                const area = document.createElement("textarea");
                area.value = text;
                document.body.appendChild(area);
                area.select();
                document.execCommand("copy");
                area.remove();
            }}

            btn.innerHTML = "✅ Скопировано";
            setTimeout(() => btn.innerHTML="📋 Копировать", 1500);
        }};
        </script>
        </body>
        </html>
        """,
        height=45,
    )


# ---------- ИНТЕРФЕЙС ----------

st.title("💰 Калькулятор НДС Онлайн")
st.caption("Бесплатный сервис расчёта НДС с суммой прописью")

amount_input = st.text_input(
    "Введите сумму",
    placeholder="Например: 100000,50"
)

mode = st.radio(
    "Режим расчёта",
    ["Начислить НДС", "Выделить НДС из суммы"],
    horizontal=True
)

if st.button("🧮 Рассчитать", use_container_width=True):

    try:
        amount = parse_amount(amount_input)
    except:
        st.error("Введите корректную сумму")
        st.stop()

    amount = amount.quantize(Decimal("0.01"))

    source = f"Исходная сумма:\n{amount_input}\n{money_to_text(amount)}"

    st.subheader("📄 Исходная сумма")
    st.text_area(" ", source, height=90)
    copy_button(source, "source")

    st.subheader("📊 Результаты")

    total = [source]

    for rate in RATES:
        if mode == "Выделить НДС из суммы":
            vat = amount * Decimal(rate) / (Decimal(100)+Decimal(rate))
        else:
            vat = amount * Decimal(rate) / Decimal(100)

        vat = vat.quantize(Decimal("0.01"))

        result = f"НДС {rate}%:\n{money_to_text(vat)}"
        total.append(result)

        with st.container():
            st.info(result)
            copy_button(result, str(rate))

    full = "\n\n".join(total)

    st.subheader("📋 Полный расчёт")
    st.text_area(" ", full, height=220)
    copy_button(full, "all")
