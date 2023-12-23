import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import mplcursors
from scipy import interpolate
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
def get_departure_cities():
    conn = sqlite3.connect('AirTickets.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Departure_city FROM Flights")
    cities = cursor.fetchall()
    conn.close()
    return [city[0] for city in cities]
def get_destination_cities():
    conn = sqlite3.connect('AirTickets.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Destination_city FROM Flights")
    cities = cursor.fetchall()
    conn.close()
    return [city[0] for city in cities]

departure_cities = get_departure_cities()
destination_cities = get_destination_cities()

# Функция для получения рейсов
def fetch_flights(departure_city, destination_city, departure_date, business_trip_days):
    departure_date_str = departure_date.strftime('%Y-%m-%d')
    response = requests.get(f'http://localhost:5000/api/flights?departure_city={departure_city}&destination_city={destination_city}&departure_date={departure_date_str}&business_trip_days={business_trip_days}')
    return response

# Функция для отображения рейсов и кнопок прогнозирования
def show_flights(flights_data, response_data):
    alternative_results = response_data.get('alternative_results')

    if alternative_results == 0:
        st.success("Найдены следующие рейсы:")
        for index, (outbound_flight, return_flight, total_price, waiting_days, outbound_departure_time, outbound_arrival_time, return_departure_time, return_arrival_time) in enumerate(flights_data):
            flight_info = "<hr>"
            flight_info += f"Билет {index + 1}:\n"
            flight_info += f"Туда: {outbound_flight[1]} -> {outbound_flight[2]}, {outbound_flight[3]} - {outbound_flight[4]}, Время вылета: {outbound_departure_time}, Время прилета: {outbound_arrival_time}, Авиакомпания: {outbound_flight[5]}, Цена: {outbound_flight[6]} руб.\n"
            flight_info += "<hr>"
            flight_info += f"Обратно: {return_flight[1]} -> {return_flight[2]}, {return_flight[3]} - {return_flight[4]}, Время вылета: {return_departure_time}, Время прилета: {return_arrival_time}, Авиакомпания: {return_flight[5]}, Цена: {return_flight[6]} руб.\n"
            flight_info += f"Общая стоимость: {total_price} руб.\n"
            flight_info += f"Дни ожидания: {waiting_days} дней\n"
            st.write(flight_info, unsafe_allow_html=True)

            if st.button(f"Прогноз цены на билеты {index + 1}", key=f"button_{index + 1}"):
                fetch_and_plot_price_forecast(outbound_flight[1], outbound_flight[2], return_flight[1],
                                              return_flight[2], f"Прогноз цены на билеты {index + 1}")

    elif alternative_results == 1:
        st.warning("Не удалось найти точно подходящие билеты, но вот некоторые альтернативы:")
        for index, (outbound_flight, return_flight, total_price, waiting_days, outbound_departure_time, outbound_arrival_time, return_departure_time, return_arrival_time) in enumerate(flights_data):
            flight_info = "<hr>"
            flight_info += f"Альтернативный билет {index + 1}:\n"
            flight_info += f"Туда: {outbound_flight[1]} -> {outbound_flight[2]}, {outbound_flight[3]} - {outbound_flight[4]}, Время вылета: {outbound_departure_time}, Время прилета: {outbound_arrival_time}, Авиакомпания: {outbound_flight[5]}, Цена: {outbound_flight[6]} руб.\n"
            flight_info += "<hr>"  # Добавляем горизонтальную линию в качестве разделителя
            flight_info += f"Обратно: {return_flight[1]} -> {return_flight[2]}, {return_flight[3]} - {return_flight[4]}, Время вылета: {return_departure_time}, Время прилета: {return_arrival_time}, Авиакомпания: {return_flight[5]}, Цена: {return_flight[6]} руб.\n"
            flight_info += f"Общая стоимость: {total_price} руб.\n"
            flight_info += f"Дни ожидания: {waiting_days} дней\n"
            st.write(flight_info, unsafe_allow_html=True)

    elif alternative_results == 2:
        st.error("Рейсы не найдены. Попробуйте другие даты или направления.")
def fetch_and_plot_price_forecast(departure_city_outbound, destination_city_outbound, departure_city_return,
                                  destination_city_return, title):
    price_response_outbound = requests.get(
        f'http://localhost:5000/api/price_forecast?departure_city={departure_city_outbound}&destination_city={destination_city_outbound}')
    price_response_return = requests.get(
        f'http://localhost:5000/api/price_forecast?departure_city={departure_city_return}&destination_city={destination_city_return}')

    if price_response_outbound.status_code == 200 and price_response_return.status_code == 200:
        price_data_outbound = price_response_outbound.json()
        price_data_return = price_response_return.json()

        flight_info_list_outbound = [f"Из {departure_city_outbound} в {destination_city_outbound}" for _ in
                                     range(len(price_data_outbound))]
        flight_info_list_return = [f"Из {departure_city_return} в {destination_city_return}" for _ in
                                   range(len(price_data_return))]

        plot_price_forecast_with_prediction(price_data_outbound, flight_info_list_outbound, price_data_return,
                                            flight_info_list_return, title)
    else:
        st.error("Ошибка при получении данных о ценах")
def plot_price_forecast_with_prediction(price_data_outbound, flight_data_outbound, price_data_return, flight_data_return, title, inflation_rate=0.05):
    df_outbound = pd.DataFrame(price_data_outbound, columns=["Дата", "Цена"])
    df_outbound['Дата'] = pd.to_datetime(df_outbound['Дата'], format='%d.%m.%Y')
    df_outbound = df_outbound.sort_values(by='Дата')

    df_return = pd.DataFrame(price_data_return, columns=["Дата", "Цена"])
    df_return['Дата'] = pd.to_datetime(df_return['Дата'], format='%d.%m.%Y')
    df_return = df_return.sort_values(by='Дата')

    last_date_outbound = df_outbound['Дата'].iloc[-1]
    last_date_return = df_return['Дата'].iloc[-1]

    prediction_dates_outbound = pd.date_range(start=last_date_outbound, periods=180, freq='D')
    prediction_dates_return = pd.date_range(start=last_date_return, periods=180, freq='D')

    linear_interp_outbound = interpolate.interp1d(df_outbound['Дата'].map(datetime.toordinal), df_outbound['Цена'], fill_value='extrapolate')
    linear_interp_return = interpolate.interp1d(df_return['Дата'].map(datetime.toordinal), df_return['Цена'], fill_value='extrapolate')

    predicted_prices_outbound = linear_interp_outbound([date.toordinal() for date in prediction_dates_outbound])
    predicted_prices_return = linear_interp_return([date.toordinal() for date in prediction_dates_return])

    df_prediction_outbound = pd.DataFrame({'Дата': prediction_dates_outbound, 'Цена': predicted_prices_outbound})
    df_prediction_return = pd.DataFrame({'Дата': prediction_dates_return, 'Цена': predicted_prices_return})

    df_prediction_outbound['Цена'] = df_prediction_outbound['Цена'] * (1 + inflation_rate)
    df_prediction_return['Цена'] = df_prediction_return['Цена'] * (1 + inflation_rate)

    # Устанавливаем минимальное значение для цены
    min_price = 0
    df_prediction_outbound['Цена'] = df_prediction_outbound['Цена'].clip(lower=min_price)
    df_prediction_return['Цена'] = df_prediction_return['Цена'].clip(lower=min_price)

    hovertext_outbound = [f'Дата: {date.strftime("%d.%m.%Y")}, Цена: {price:.2f}, {flight_info}' for date, price, flight_info in zip(df_outbound['Дата'], df_outbound['Цена'], flight_data_outbound)]
    hovertext_return = [f'Дата: {date.strftime("%d.%m.%Y")}, Цена: {price:.2f}, {flight_info}' for date, price, flight_info in zip(df_return['Дата'], df_return['Цена'], flight_data_return)]

    fig_outbound = go.Figure()
    fig_outbound.add_trace(go.Scatter(x=df_outbound['Дата'], y=df_outbound['Цена'], mode='lines+markers', name='Фактическая цена', hovertext=hovertext_outbound, hoverinfo="text+x+y"))
    fig_outbound.add_trace(go.Scatter(x=df_prediction_outbound['Дата'], y=df_prediction_outbound['Цена'], mode='lines+markers', name='Прогноз с учетом инфляции', hoverinfo="text+x+y"))

    fig_return = go.Figure()
    fig_return.add_trace(go.Scatter(x=df_return['Дата'], y=df_return['Цена'], mode='lines+markers', name='Фактическая цена', hovertext=hovertext_return, hoverinfo="text+x+y"))
    fig_return.add_trace(go.Scatter(x=df_prediction_return['Дата'], y=df_prediction_return['Цена'], mode='lines+markers', name='Прогноз с учетом инфляции', hoverinfo="text+x+y"))

    fig_outbound.update_layout(title=f'Прогноз цены на билет туда: {title}', xaxis_title='Дата', yaxis_title='Цена (руб)', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="white")
    fig_return.update_layout(title=f'Прогноз цены на билет обратно: {title}', xaxis_title='Дата', yaxis_title='Цена (руб)', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="white")

    st.plotly_chart(fig_outbound, use_container_width=True)
    st.plotly_chart(fig_return, use_container_width=True)

def main():
    st.markdown("""
        <style>
        .header {
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
            padding: 10px;
            text-align: center;
        }
        .subheader {
            color: #ffffff;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<div class="header">Микросервис для прогнозирования стоимости авиабилетов</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Добро пожаловать в наш сервис</div>', unsafe_allow_html=True)

    with st.form("input_form"):
        departure_city = st.selectbox("Город вылета",  departure_cities)
        destination_city = st.selectbox("Город назначения", destination_cities)
        departure_date = st.date_input("Дата вылета", datetime.today())
        business_trip_days = st.slider("Количество командировочных дней", 1, 3, 1)
        submit_button = st.form_submit_button("Найти рейсы")

    if submit_button:
        response = fetch_flights(departure_city, destination_city, departure_date, business_trip_days)
        if response.status_code == 200:
            response_data = response.json()
            st.session_state['flights_data'] = response_data['flights']
            st.session_state['response_data'] = response_data
        else:
            st.error("Ошибка при получении данных")

    if 'flights_data' in st.session_state:
        show_flights(st.session_state['flights_data'], st.session_state['response_data'])

if __name__ == "__main__":
    main()