import streamlit as st
from num2words import num2words
import base64
import streamlit.components.v1 as components

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Калькулятор НДС Онлайн",
    page_icon="🧾",
    layout="centered"
)

# --- ФУНКЦИИ ---
def get_rubles_kopecks_text(amount):
    """Преобразует число в строку формата: 9 371 (Девять тысяч ...) рубль 51 копейка"""
    # Округляем и разбиваем на рубли и копейки
    amount_str = f"{amount:.2f}"
    rubles_str, kopecks_str = amount_str.split('.')
    rubles = int(rubles_str)
    kopecks = int(kopecks_str)

    # Правила склонения для рублей
    if rubles % 10 == 1 and rubles % 100 != 11:
        r_word = "рубль"
    elif 2 <= rubles % 10 <= 4 and not (12 <= rubles % 100 <= 14):
        r_word = "рубля"
    else:
        r_word = "рублей"

    # Правила склонения для копеек
    if kopecks % 10 == 1 and kopecks % 100 != 11:
        k_word = "копейка"
    elif 2 <= kopecks % 10 <= 4 and not (12 <= kopecks % 100 <= 14):
        k_word = "копейки"
    else:
        k_word = "копеек"

    # Получаем прописное значение
    if rubles == 0:
        r_text = "Ноль"
    else:
        r_text = num2words(rubles, lang='ru').capitalize()

    # Форматируем число с пробелами (9 371)
    formatted_rubles = f"{rubles:,}".replace(',', ' ')
    
    return f"{formatted_rubles} ({r_text}) {r_word} {kopecks:02d} {k_word}"

def generate_copy_button(text_to_copy):
    """Создает HTML/JS кнопку для надежного копирования в буфер обмена браузера"""
    # Кодируем текст в base64, чтобы избежать ошибок с переносами строк и кавычками в JS
    b64_text = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    
    html_code = f"""
    <div style="display: flex; justify-content: center; margin-top: 10px;">
        <button id="copy-btn" onclick="copyToClipboard()" style="
            background-color: #FF4B4B;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            font-family: sans-serif;
            font-weight: 600;
            transition: background-color 0.3s;
        ">
            📋 Скопировать полный расчёт
        </button>
    </div>

    <script>
    function copyToClipboard() {{
        // Декодируем текст из base64
        const text = decodeURIComponent(escape(window.atob('{b64_text}')));
        
        navigator.clipboard.writeText(text).then(function() {{
            const btn = document.getElementById('copy-btn');
            btn.innerText = '✅ Скопировано!';
            btn.style.backgroundColor = '#28a745';
            
            setTimeout(function() {{
                btn.innerText = '📋 Скопировать полный расчёт';
                btn.style.backgroundColor = '#FF4B4B';
            }}, 2500);
        }}).catch(function(err) {{
            console.error('Ошибка копирования: ', err);
        }});
    }}
    </script>
    """
    components.html(html_code, height=60)

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
st.title("🧾 Калькулятор НДС")
st.markdown("Быстрый расчет налога на добавленную стоимость с генерацией суммы прописью.")

# Блок ввода данных
with st.container():
    st.subheader("Параметры расчёта")
    col1, col2 = st.columns(2)
    
    with col1:
        # Разрешаем ввод текста для удобства (пользователи часто копируют суммы с пробелами)
        amount_input = st.text_input("Введите сумму (₽):", value="10000")
        try:
            # Очищаем строку от пробелов и меняем запятую на точку
            amount = float(amount_input.replace(' ', '').replace(',', '.'))
        except ValueError:
            st.error("Пожалуйста, введите корректное число.")
            amount = 0.0

    with col2:
        rate = st.selectbox("Ставка НДС:", [22, 10, 7, 5], format_func=lambda x: f"{x}%")

    mode = st.radio(
        "Режим расчёта:",
        options=["Начислить НДС (сумма без НДС)", "Выделить НДС (сумма с НДС)"],
        horizontal=True
    )

# --- МАТЕМАТИКА ---
if amount > 0:
    if mode == "Начислить НДС (сумма без НДС)":
        base_amount = amount
        vat_amount = amount * (rate / 100)
        total_amount = amount + vat_amount
        mode_title_base = "Сумма без НДС"
        mode_title_total = "Итоговая сумма (с НДС)"
    else:
        total_amount = amount
        vat_amount = amount * rate / (100 + rate)
        base_amount = total_amount - vat_amount
        mode_title_base = "Сумма без НДС"
        mode_title_total = "Исходная сумма (с НДС)"

    # --- ВЫВОД РЕЗУЛЬТАТОВ ---
    st.divider()
    st.subheader("Результаты")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric(mode_title_base, f"{base_amount:,.2f} ₽".replace(',', ' '))
    m_col2.metric("Сумма НДС", f"{vat_amount:,.2f} ₽".replace(',', ' '))
    m_col3.metric(mode_title_total, f"{total_amount:,.2f} ₽".replace(',', ' '))

    # Генерация прописных строк
    base_text = get_rubles_kopecks_text(base_amount)
    vat_text = get_rubles_kopecks_text(vat_amount)
    total_text = get_rubles_kopecks_text(total_amount)

    st.markdown("##### Суммы прописью:")
    st.info(f"**Сумма без НДС:** {base_text}\n\n**НДС ({rate}%):** {vat_text}\n\n**Сумма с НДС:** {total_text}")

    # --- БЛОК ПОЛНОГО РАСЧЕТА ---
    st.divider()
    st.subheader("Полный расчёт для копирования")
    
    full_report = (
        f"--- Детализация НДС ---\n"
        f"Ставка НДС: {rate}%\n"
        f"Сумма без НДС: {base_text}\n"
        f"Сумма НДС: {vat_text}\n"
        f"Итоговая сумма с НДС: {total_text}\n"
    )
    
    st.text_area("Текст расчёта (можно отредактировать):", value=full_report, height=150)
    
    # Кнопка копирования
    generate_copy_button(full_report)

else:
    st.info("Введите сумму больше нуля для начала расчёта.")
