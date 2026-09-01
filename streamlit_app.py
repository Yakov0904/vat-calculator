import streamlit as st
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

st.set_page_config(
    page_title="Калькулятор НДС",
    page_icon="💰",
    layout="centered"
)

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
    ("миллиард", "миллиарда", "миллиардов", False),
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

    words = []
    h = n // 100
    rest = n % 100

    if h:
        words.append(HUNDREDS[h])

    if 10 <= rest <= 19:
        words.append(TEENS[rest - 10])
        return " ".join(words)

    t = rest // 10
    u = rest % 10

    if t:
        words.append(TENS[t])

    if u:
        words.append((UNITS_FEMALE if female else UNITS_MALE)[u])

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


def parse_amount(text):
    text = text.strip().replace(" ", "").replace("\u00A0", "")
    text = text.replace(",", ".")

    if not re.fullmatch(r"[+-]?\d+(\.\d+)?", text):
        raise ValueError

    return Decimal(text)


st.title("💰 Онлайн калькулятор НДС")
st.write("Расчёт НДС с переводом суммы в пропись.")

amount_text = st.text_input("Введите сумму", placeholder="Например: 100000,50")

mode = st.radio(
    "Режим расчёта",
    [
        "Рассчитать НДС от суммы",
        "Выделить НДС из суммы с НДС"
    ]
)

if st.button("🧮 Рассчитать", type="primary"):

    try:
        amount = parse_amount(amount_text)
        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    except:
        st.error("Введите корректную сумму")
        st.stop()

    st.subheader("Введённая сумма")

    input_result = money_to_text(amount)

    st.code(
        f"{amount_text}\n{input_result}",
        language=None
    )

    st.download_button(
        "📋 Скачать результат",
        f"{amount_text}\n{input_result}",
        file_name="nds_result.txt"
    )

    st.subheader("Результаты НДС")

    for rate in RATES:

        if mode.startswith("Выделить"):
            vat = amount * Decimal(rate) / (Decimal(100) + Decimal(rate))
        else:
            vat = amount * Decimal(rate) / Decimal(100)

        vat = vat.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        result = f"НДС {rate}%: {money_to_text(vat)}"

        st.text_area(
            f"НДС {rate}%",
            result,
            height=70
        )
