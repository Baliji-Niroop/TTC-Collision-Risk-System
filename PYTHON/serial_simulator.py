import time

distance = 40
closing_speed = 15

while True:

    distance = distance - (closing_speed/3.6)*0.5
    
    if distance <= 0:
        distance = 40
        
    ttc = distance / (closing_speed/3.6)
    
    if ttc > 3:
        risk = 0
    elif ttc > 1.5:
        risk = 1
    else:
        risk = 2

    with open("live_data.txt","w") as f:
        f.write(f"{distance:.2f},{ttc:.2f},{risk}")
    
    time.sleep(0.3)