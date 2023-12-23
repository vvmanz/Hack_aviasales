from flask import Flask, jsonify, request
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
@app.route('/api/flights')
def api_flights():
    conn = sqlite3.connect('AirTickets.db')
    cursor = conn.cursor()

    departure_city = request.args.get('departure_city')
    destination_city = request.args.get('destination_city')
    departure_date_str = request.args.get('departure_date')
    business_trip_days = int(request.args.get('business_trip_days'))

    departure_date = datetime.strptime(departure_date_str, '%Y-%m-%d').strftime('%d.%m.%Y')

    cursor.execute("""
        SELECT * FROM Flights WHERE Departure_city=? AND Destination_city=? AND Date_departure=?
        """, (departure_city, destination_city, departure_date))
    outbound_flights = cursor.fetchall()

    return_date = (datetime.strptime(departure_date, '%d.%m.%Y') + timedelta(days=business_trip_days)).strftime(
        '%d.%m.%Y')
    cursor.execute("""
        SELECT * FROM Flights WHERE Departure_city=? AND Destination_city=? AND Date_departure=?
        """, (destination_city, departure_city, return_date))
    return_flights = cursor.fetchall()

    if not outbound_flights or not return_flights:
        response_data = {'flights': [], 'alternative_results': 2}  # Результаты не найдены
    else:
        # Создание всех возможных комбинаций билетов туда и обратно с временем прилета и вылета
        flight_combinations = []
        for outbound_flight in outbound_flights:
            for return_flight in return_flights:
                total_price = outbound_flight[6] + return_flight[6]
                waiting_days = (datetime.strptime(return_flight[3], '%d.%m.%Y') - datetime.strptime(outbound_flight[4],
                                                                                                    '%d.%m.%Y')).days - 1
                outbound_departure_time = outbound_flight[4]
                outbound_arrival_time = outbound_flight[5]
                return_departure_time = return_flight[8]
                return_arrival_time = return_flight[9]
                flight_combinations.append((outbound_flight, return_flight, total_price, waiting_days,
                                            outbound_departure_time, outbound_arrival_time, return_departure_time,
                                            return_arrival_time))

        # Сортировка комбинаций по стоимости и дням ожидания
        sorted_combinations = sorted(flight_combinations, key=lambda x: (x[2], x[3]))

        if not sorted_combinations:
            response_data = {'flights': [], 'alternative_results': 1}  # Альтернативные билеты могут подойти, но не подходят по одному из критериев
        else:
            response_data = {'flights': sorted_combinations, 'alternative_results': 0}  # Результаты найдены

    conn.close()
    return jsonify(response_data)

@app.route('/api/price_forecast')
def api_price_forecast():
    departure_city = request.args.get('departure_city')
    destination_city = request.args.get('destination_city')

    conn = sqlite3.connect('AirTickets.db')
    cursor = conn.cursor()

    cursor.execute("""
           SELECT Date_departure, Price FROM Flights 
           WHERE Departure_city=? AND Destination_city=?
       """, (departure_city, destination_city))
    print('Запрос отправлен')
    price_data = cursor.fetchall()
    print(price_data)
    conn.close()
    return jsonify(price_data)

if __name__ == '__main__':
    app.run(debug=True)