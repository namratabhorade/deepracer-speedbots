import math

class PreviousState:
    steering_angle = -1
    steering_angle_2 = -1
    
    def is_unwanted_steering(self, steering_angle):
        if self.steering_angle != -1 and self.steering_angle_2 != -1 and steering_angle != - 1:
            current_direction = (steering_angle + 1) / abs(steering_angle + 1)
            ps1_direction = (self.steering_angle + 1) / abs(self.steering_angle + 1)
            ps2_direction = (self.steering_angle_2 + 1) / abs(self.steering_angle_2 + 1)
            return current_direction == ps2_direction and ps1_direction != ps2_direction
        return False

ps = PreviousState()

# Expected upcoming curve angle speed, value(1 - 4)
def get_speed_from_angle(angle, min_speed):
    speed = (4 - (angle*0.1)) * 10
    speed = abs((speed - (speed%5)) / 10)
    return max(speed, min_speed)

def reward_function(params):
    
    # Default params
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    steering_angle = round(params['steering_angle'], 0)
    speed = params['speed']
    steps = params['steps']
    progress = round(params['progress'], 2)
    all_wheels_on_track = params['all_wheels_on_track']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = round(params['heading'], 0)
    is_reversed = params['is_reversed']
    
    # Near Center in Percentage, value (0 - 100)
    near_center_per = round(((track_width/2) - distance_from_center) * 100 / (track_width/2), 0) 

    # Determine curve & direction
    upcoming_curve_direction = ''
    current_direction = 0
    future_direction = 0
    next_point = waypoints[closest_waypoints[1]]
    prev_point = waypoints[closest_waypoints[0]]
    future_track_length = 3
    if len(waypoints) > closest_waypoints[1] + future_track_length:
        future_point = waypoints[closest_waypoints[1] + future_track_length]
        current_point = waypoints[closest_waypoints[1]]
        future_direction = round(math.degrees(math.atan2(future_point[1] - current_point[1], future_point[0] - current_point[0])), 0)
        current_direction = round(math.degrees(math.atan2(current_point[1] - prev_point[1], current_point[0] - prev_point[0])), 0)
        upcoming_curve_angle = abs(future_direction - current_direction)
        if upcoming_curve_angle > 180:    
            upcoming_curve_angle = 360 - upcoming_curve_angle
    else:
        upcoming_curve_angle = 0
    is_track_straight = (upcoming_curve_angle == 0)
        
    min_speed = 1
    track_direction = math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0])
    track_direction = round(math.degrees(track_direction), 0)
    direction_diff_angle = abs(track_direction - heading)
    if direction_diff_angle > 180:
        direction_diff_angle = 360 - direction_diff_angle
    expected_curve_speed = get_speed_from_angle(upcoming_curve_angle, min_speed)
    
    progress_to_steps_ratio = round(3 * progress / max(steps, 1), 2)

    print("------------------------------------------------------------------")
    print("progress_to_steps_ratio: ", progress_to_steps_ratio)
    print("steps: ", steps)
    print("progress: ", progress)
    print("speed: ", speed)
    print("previous steering_angle: ", ps.steering_angle)
    print("steering_angle: ", steering_angle)
    print("is_track_straight: ", is_track_straight)
    print("upcoming_curve_direction: ", upcoming_curve_direction)
    print("upcoming_curve_angle: ", upcoming_curve_angle)
    print("expected_curve_speed: ", expected_curve_speed)
    print("near_center_per: ", near_center_per)
    print("direction_diff_angle: ", direction_diff_angle)
    print("ps.is_unwanted_steering: ", ps.is_unwanted_steering(steering_angle))
    print("[steering_angle, speed]: [", steering_angle,",",speed,"]")
    
    reward = 1e-5
    if is_reversed or not all_wheels_on_track or direction_diff_angle > 30 or near_center_per <= 0:
        print("xxxxxxxxxxxxxxxxxxxx")
        print("Penalize, Reward: ", reward)
        print("xxxxxxxxxxxxxxxxxxxx")
        return float(reward)
        
    print("--------------------")
    reward = (5 * near_center_per/100) + (3 * (100-direction_diff_angle)/100)
    reward = round(reward, 2)
    print("Initial reward: ", reward)
    
    # Reward perfect speed
    if speed == expected_curve_speed:
        reward += speed * near_center_per/100
        reward = round(reward, 2)
        print("1a) reward: ", reward)
    else:
        reward *= abs(1 - min(abs(expected_curve_speed - speed)/expected_curve_speed, 0.7))
        reward = round(reward, 2)
        print("1b) reward: ", reward)
        
    # Reward zero steering on straight tracks
    if is_track_straight and steering_angle == ps.steering_angle == 0:
        reward += speed/1.5
        reward = round(reward, 2)
        print("2a) reward: ", reward)
    elif ps.is_unwanted_steering(steering_angle):
        reward *= 0.5
        reward = round(reward, 2)
        print("2b) reward: ", reward)
        
    # Penalize hard turns
    if ps.steering_angle > -1 and abs(ps.steering_angle - steering_angle) > 10:
        reward *= 0.6
        reward = round(reward, 2)
        print("3a) reward: ", reward)
    
    # Reward driving in track direction
    if direction_diff_angle == 0:
        reward *= 1.2 + (100-direction_diff_angle)/100
        reward = round(reward, 2)
        print("4a) reward: ", reward)    
    # Penalize if not driving in track direction
    else:
        reward *= (100 - direction_diff_angle) / 100
        reward = round(reward, 2)
        print("4b) reward: ", reward)
        
    # Reward/penalize according to progress to steps ratio
    if progress_to_steps_ratio > 0:
        reward *= progress_to_steps_ratio
        reward = round(reward, 2)
        print("5a) reward: ", reward)
        
    # Reward track completion
    if progress < 100:
        reward += progress/10
        reward = round(reward, 2)
        print("6a) reward: ", reward)
    else:
        reward += progress
        reward = round(reward, 2)
        print("6b) reward: ", reward)

    reward = round(max(reward, 0.01), 2)
    print("--------------------")
    print("Final reward: ", reward)
    print("--------------------")
    
    ps.steering_angle_2 = ps.steering_angle
    ps.steering_angle = steering_angle
    return float(reward)
