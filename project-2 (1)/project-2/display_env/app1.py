from flask import Flask, render_template, jsonify
import smbus2
import bme680
import RPi.GPIO as GPIO
import time
import threading
import csv
import joblib
import pickle
import sklearn

app = Flask(__name__)
app.static_folder = 'static'
GPIO.setmode(GPIO.BCM)
led_pin = 17
GPIO.setup(led_pin, GPIO.OUT)

# Configure BME680 sensor
i2c_address = 0x77  # BME680 sensor I2C address
bus = smbus2.SMBus(1)
sensor = bme680.BME680(i2c_addr=i2c_address)
sensor.set_temp_offset(0)

csv_file = open('sensor_data.csv', 'w')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Timestamp', 'Temperature', 'Humidity', 'Pressure', 'Gas'])

model = pickle.load(open('model.pkl','rb'))

@app.route('/')
def index():
    predicted_temperature = predict_temperature_spikes(data[-1, 1:])
    return render_template('index.html', predicted_temperature = predicted_temperature)

@app.route('/sensor_data')
def sensor_data():
    sensor.get_sensor_data()
    temperature = sensor.data.temperature
    humidity = sensor.data.humidity
    pressure = sensor.data.pressure
    gas = sensor.data.gas_resistance
    data = {
        'temperature': temperature,
        'humidity': humidity,
        'pressure': pressure,
        'gas': gas
    }
    return jsonify(data)
        
def monitor_sensor_data():
    while True:
        sensor.get_sensor_data()
        temperature = sensor.data.temperature
        humidity = sensor.data.humidity
        pressure = sensor.data.pressure
        gas = sensor.data.gas_resistance

        if temperature > 30:
            GPIO.output(led_pin, GPIO.HIGH)
        else:
            GPIO.output(led_pin, GPIO.LOW)

        # Save sensor data to CSV
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        csv_writer.writerow([timestamp, temperature, humidity, pressure, gas])
        csv_file.flush()  # Flush data to the file immediately

        time.sleep(1)
        
temperature_thread = threading.Thread(target=monitor_sensor_data)
temperature_thread.start()
    
@app.route('/shutdown', methods=['POST'])
def shutdown():
    csv_file.close()
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    return 'Server shutting down...'

@app.teardown_appcontext
def close_csv_file(error):
    csv_file.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
