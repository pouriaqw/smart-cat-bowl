from machine import Pin
import network
import time
import usocket as socket

# Wi-Fi Configuration
ssid = 'sarina'
password = 'sarinasa'

# Initialize the Wi-Fi station interface
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

print('Connecting to Wi-Fi...')
timeout = 30  # Set a timeout period (in seconds)
start_time = time.time()

while not station.isconnected():
    current_time = time.time()
    elapsed_time = current_time - start_time
    if elapsed_time > timeout:
        print('Failed to connect to Wi-Fi within the timeout period.')
        break
    print('Still connecting... ({:.1f} seconds elapsed)'.format(elapsed_time))
    time.sleep(1)

if station.isconnected():
    ip_address = station.ifconfig()[0]
    print('Connection successful')
    print('IP Address:', ip_address)
else:
    print('Connection failed. Check your SSID and password.')

# Pin setup for stepper motor
IN1 = Pin(5, Pin.OUT)
IN2 = Pin(4, Pin.OUT)
IN3 = Pin(0, Pin.OUT)
IN4 = Pin(2, Pin.OUT)

# Define the step sequence for the stepper motor (4-step sequence)
step_sequence = [
    [1, 0, 0, 1],
    [1, 0, 1, 0],
    [0, 1, 1, 0],
    [0, 1, 0, 1]
]

def step_motor(steps, delay, direction):
    if direction == 'backward':
        step_sequence.reverse()
    print("Starting motor with direction:", direction)
    for _ in range(steps):
        for step in step_sequence:
            IN1.value(step[0])
            IN2.value(step[1])
            IN3.value(step[2])
            IN4.value(step[3])
            time.sleep(delay)
    print("Motor sequence completed.")

def format_time():
    t = time.localtime()
    return "Time: {:02}:{:02}:{:02}".format(t[3], t[4], t[5])

def web_page(sleep_time=5, status="Ready", last_action_time="Time: --:--:--"):
    html = """<html>
    <head> 
        <title>ESP Web Server</title> 
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                background: #f4f4f9;
                margin: 0;
                padding: 0;
                color: #333;
                text-align: center;
            }}
            h1 {{
                color: #333;
                background: #e7f0ff;
                padding: 20px;
                border-bottom: 2px solid #ddd;
            }}
            .container {{
                max-width: 800px;
                margin: 20px auto;
                padding: 20px;
                background: #fff;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            p {{
                font-size: 1.2rem;
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                font-size: 20px;
                margin: 10px;
                cursor: pointer;
                transition: background-color 0.3s, transform 0.2s;
            }}
            .button:hover {{
                background-color: #0056b3;
                transform: scale(1.05);
            }}
            input[type="number"] {{
                font-size: 1.2rem;
                padding: 10px;
                margin: 10px 0;
                width: 100px;
                border: 2px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
            }}
            #progress-bar-container {{
                width: 100%;
                background-color: #ddd;
                border-radius: 25px;
                margin: 20px 0;
                overflow: hidden;
            }}
            #progress-bar {{
                width: 0%;
                height: 30px;
                background-color: #28a745;
                border-radius: 25px;
                transition: width 1s linear;
            }}
            #status {{
                font-size: 1.2rem;
                color: #28a745;
                margin-top: 20px;
                font-weight: bold;
            }}
            #last-action {{
                font-size: 1.2rem;
                color: #333;
                margin-top: 10px;
            }}
        </style>
        <script>
            function startProgress(duration) {{
                var bar = document.getElementById("progress-bar");
                var status = document.getElementById("status");
                bar.style.width = "0%";
                status.innerHTML = "";  // Clear previous status
                var step = 100 / duration;  // Calculate the step based on duration
                var width = 0;
                var interval = setInterval(function() {{
                    if (width >= 100) {{
                        clearInterval(interval);
                        status.innerHTML = "Complete";  // Update status once complete
                    }} else {{
                        width += step;
                        bar.style.width = width + "%";
                    }}
                }}, 1000);
            }}

            function handleSubmit(event) {{
                event.preventDefault();  // Prevent form submission
                var sleepTime = document.getElementById('sleep_time').value;

                // Confirmation dialog
                if (confirm("Are you sure you want to start the feeding sequence?")) {{
                    var totalDuration = 4 + parseInt(sleepTime);  // Total duration = 4s (2s forward + 2s backward) + sleep time
                    startProgress(totalDuration);  // Update progress bar duration

                    // Make a request to the server to start the motor actions
                    fetch('/start?sleep_time=' + sleepTime)
                    .then(response => response.text())
                    .then(data => {{
                        console.log("Motor action completed.");
                    }});
                }} else {{
                    console.log("Feeding sequence was canceled.");
                }}
            }}

            function updateStatus() {{
                fetch('/status')
                .then(response => response.text())
                .then(data => {{
                    var statusElement = document.getElementById("status");
                    var lastActionElement = document.getElementById("last-action");
                    var parts = data.split('|');
                    statusElement.innerHTML = parts[0];
                    lastActionElement.innerHTML = "Last action: " + parts[1];
                }});
            }}

            setInterval(updateStatus, 5000);  // Update status every 5 seconds
        </script>
    </head>
    <body> 
        <div class="container">
            <h1>Smart Cat Bowl</h1> 
            <p>Set the sleep time to fill the bowl:</p>
            <form onsubmit="handleSubmit(event);">
                <input type="number" id="sleep_time" name="sleep_time" min="1" max="20" value="{0}">
                <input type="submit" class="button" value="Start Feeding">
            </form>
            <div id="progress-bar-container">
                <div id="progress-bar"></div>
            </div>
            <div id="status">{1}</div>
            <div id="last-action">{2}</div>
        </div>
    </body>
    </html>""".format(sleep_time, status, last_action_time)
    return html

# Web server setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

print('Web server started. Waiting for connections...')

status = "Ready"
last_action_time = "Time: --:--:--"
sleep_time = 5  # Default sleep time

while True:
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    request = str(request)
    
    # Debug: Print the request for inspection
    print('Request received:', request)
    
    if '/start' in request:
        try:
            # Extract the sleep_time parameter from the request URL
            query_string = request.split(' ')[1]
            if '?' in query_string:
                params = query_string.split('?')[1].split('&')
                sleep_time_param = params[0].split('=')[1]
                sleep_time = int(sleep_time_param)
                if sleep_time < 1 or sleep_time > 20:
                    sleep_time = 5  # Default value if out of bounds
            print('Sleep time set to %d seconds' % sleep_time)

            # Execute the feeding sequence
            step_motor(25, 0.01, 'forward')
            time.sleep(sleep_time)  # Sleep for the specified time
            step_motor(25, 0.01, 'backward')
            step_motor(1,0.001, 'backward')

            # Update status and last action time
            status = "Motor action completed"
            last_action_time = format_time()

            response = "{}|{}".format(status, last_action_time)
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/plain\n')
            conn.send('Connection: close\n\n')
            conn.send(response)
        except Exception as e:
            print('Error parsing request:', e)
            conn.send('HTTP/1.1 500 Internal Server Error\n')
            conn.send('Content-Type: text/plain\n')
            conn.send('Connection: close\n\n')
            conn.send('Error: {}'.format(e))
    
    elif '/status' in request:
        # Provide status and last action time
        response = "{}|{}".format(status, last_action_time)
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/plain\n')
        conn.send('Connection: close\n\n')
        conn.send(response)
        
    else:
        # Serve the main page
        response = web_page(sleep_time=sleep_time, status=status, last_action_time=last_action_time)
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
    
    conn.close()

