import streamlit as st
from decimal import Decimal, ROUND_HALF_UP
import re
import html

st.set_page_config(
    page_title="Калькулятор НДС Онлайн",
    page_icon="💰",
    layout="centered"
)

st.markdown("""
<style>
.main {
    max-width: 900px;
}
.block-container {
    padding-top: 2rem;
}
.card {
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #ddd;
    margin-bottom: 15px;
}
.result-title {
    font-size: 20px;
    font-weight: 700;
}
.big-number {
    font-size: 28px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

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
    if n == 0:
        return ""
    result = []
    h = n // 100
    rest = n % 100

    if h:
        result.append(HUNDREDS[h])

    if 10 <= rest <= 19:
        result.append(TEENS[rest - 10])
    else:
        if rest // 10:
            result.append(TENS[rest // 10])
        if rest % 10:
            result.append((UNITS_FEMALE if female else UNITS_MALE)[rest % 10])

    return " ".join(result)


def integer_to_words(n):
    if n == 0:
        return "ноль"

    parts = []
    index = 0

    while n:
        triad = n % 1000
        if triad:
            one, few, many, female = SCALES[index]
            text = triad_to_words(triad, female)
            if index:
                text += " " + plural_form(triad, (one, few, many))
            parts.append(text)

        n //= 1000
        index += 1

    return " ".join(reversed(parts))


def money_to_text(amount):
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    rubles = int(amount)
    kopecks = int((amount - Decimal(rubles)) * 100)

    return (
        f"{rubles:,}".replace(",", " ")
        + f" ({integer_to_words(rubles).capitalize()}) "
        + plural_form(rubles, ("рубль", "рубля", "рублей"))
        + f" {kopecks:02d} "
        + plural_form(kopecks, ("копейка", "копейки", "копеек"))
    )


def parse_amount(value):
    value = value.replace(" ", "").replace("\u00A0", "").replace(",", ".")
    if not re.fullmatch(r"\d+(\.\d+)?", value):
        raise ValueError
    return Decimal(value)


st.title("💰 Калькулятор НДС Онлайн")
st.caption("Бесплатный сервис расчёта НДС с выводом суммы прописью")

amount_input = st.text_input(
    "Введите сумму",
    placeholder="Например: 100000,50"
)

mode = st.radio(
    "Режим расчёта",
    [
        "Начислить НДС сверху",
        "Выделить НДС из суммы"
    ],
    horizontal=True
)

if st.button("🧮 Рассчитать", use_container_width=True):

    try:
        amount = parse_amount(amount_input)
    except:
        st.error("Введите корректную сумму")
        st.stop()

    amount = amount.quantize(Decimal("0.01"))

    full_text = f"Исходная сумма:\n{amount_input}\n{money_to_text(amount)}"

    st.markdown("## 📄 Исходная сумма")

    st.text_area(
        "Результат",
        full_text,
        height=90
    )

    st.download_button(
        "📋 Скачать текст",
        full_text,
        file_name="nds_result.txt",
        use_container_width=True
    )

    st.markdown("## 📊 Расчёт НДС")

    all_results = [full_text]

    cols = st.columns(2)

    for i, rate in enumerate(RATES):

        if mode == "Выделить НДС из суммы":
            vat = amount * Decimal(rate) / (Decimal(100) + Decimal(rate))
        else:
            vat = amount * Decimal(rate) / Decimal(100)

        vat = vat.quantize(Decimal("0.01"))

        result = f"НДС {rate}%:\n{money_to_text(vat)}"
        all_results.append(result)

        with cols[i % 2]:
            st.info(result)

    st.markdown("## 📋 Полный результат")

    final = "\n\n".join(all_results)

    st.text_area(
        "Можно скопировать полностью",
        final,
        height=220
    )
