target_speed = 40
prev_speed_error = 0
delta = 1
accu_speed_error = 0.0
Kp = 0.1
Kd = 0.05
Ki = 0.01

KPH = 45
kph_error = target_speed - KPH
speed_error_der = (kph_error - prev_speed_error) / delta
prev_speed_error = kph_error
accu_speed_error += kph_error * delta
pid_value = (Kp * kph_error) + (Kd * speed_error_der) + (Ki * accu_speed_error)
delta = delta + 1

print(pid_value)