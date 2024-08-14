import math


class PreviousState:
    steering_angle_1 = -1
    steering_angle_2 = -1

    def is_unwanted_steering(self, params):
        steering_angle = round(params['steering_angle'], 0)
        if self.steering_angle_1 != -1 and self.steering_angle_2 != -1:
            current_direction = (steering_angle + 1) / abs(steering_angle + 1)
            ps1_direction = (self.steering_angle_1 + 1) / abs(self.steering_angle_1 + 1)
            ps2_direction = (self.steering_angle_2 + 1) / abs(self.steering_angle_2 + 1)
            return current_direction == ps2_direction and ps1_direction != ps2_direction
        return False


# Expected upcoming curve angle speed, value(1 - 4)
def get_speed_from_angle(angle, min_speed):
    speed = (4 - (angle * 0.1)) * 10
    speed = abs((speed - (speed % 5)) / 10)
    return max(speed, min_speed)


# get curve from future track length
def get_curve_from_length(params, future_track_length):
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    upcoming_curve_angle = 0
    # Determine curve & direction
    prev_point = waypoints[closest_waypoints[0]]
    if len(waypoints) > closest_waypoints[1] + future_track_length:
        current_point = waypoints[closest_waypoints[1]]
        future_point = waypoints[closest_waypoints[1] + future_track_length]
        future_direction = round(
            math.degrees(math.atan2(future_point[1] - current_point[1], future_point[0] - current_point[0])), 0)
        current_direction = round(
            math.degrees(math.atan2(current_point[1] - prev_point[1], current_point[0] - prev_point[0])), 0)
        upcoming_curve_angle = abs(future_direction - current_direction)
        if upcoming_curve_angle > 180:
            upcoming_curve_angle = 360 - upcoming_curve_angle
    return upcoming_curve_angle


# get difference between current heading and track
def get_direction_diff_angle(params):
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = round(params['heading'], 0)
    next_point = waypoints[closest_waypoints[1]]
    prev_point = waypoints[closest_waypoints[0]]
    track_direction = math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0])
    track_direction = round(math.degrees(track_direction), 0)
    direction_diff_angle = abs(track_direction - heading)
    if direction_diff_angle > 180:
        direction_diff_angle = 360 - direction_diff_angle
    return direction_diff_angle


# Average of upcoming angles based on length
def get_avg_curve_from_length(params, future_track_length):
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    avg_angle = 0
    for x in range(future_track_length):
        if len(waypoints) > closest_waypoints[1] + future_track_length:
            avg_angle = (avg_angle + get_curve_from_length(params, x + 1)) / x + 1
            print(x + 1, ",avg_angle:", avg_angle)
    return avg_angle


ps = PreviousState()


def reward_function(params):
    # Default params
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    steering_angle = round(params['steering_angle'], 0)
    speed = params['speed']
    steps = params['steps']
    progress = round(params['progress'], 2)
    all_wheels_on_track = params['all_wheels_on_track']
    is_reversed = params['is_reversed']

    min_speed = 1
    future_track_length = 10

    # Near Center in Percentage, value (0 - 100)
    near_center_per = round(((track_width / 2) - distance_from_center) * 100 / (track_width / 2), 0)

    # Progress to steps ratio, higher the better
    progress_to_steps_ratio = round(1.5 * progress / max(steps, 1), 2)

    # Determine curve & direction
    upcoming_curve_angle = get_avg_curve_from_length(params, future_track_length)
    is_track_straight = (upcoming_curve_angle == 0)
    direction_diff_angle = get_direction_diff_angle(params)
    expected_curve_speed = get_speed_from_angle(upcoming_curve_angle, min_speed)

    print("------------------------------------------------------------------")
    print("progress_to_steps_ratio:", progress_to_steps_ratio)
    print("steps:", steps)
    print("progress:", progress)
    print("speed:", speed)
    print("previous steering_angle:", ps.steering_angle_1)
    print("steering_angle:", steering_angle)
    print("is_track_straight:", is_track_straight)
    print("upcoming_curve_angle:", upcoming_curve_angle)
    print("expected_curve_speed:", expected_curve_speed)
    print("near_center_per:", near_center_per)
    print("direction_diff_angle:", direction_diff_angle)
    print("ps.is_unwanted_steering:", ps.is_unwanted_steering(steering_angle))
    print("[steering_angle, speed]: [", steering_angle, ",", speed, "]")

    reward = 1e-5
    if is_reversed or not all_wheels_on_track or direction_diff_angle > 60 or near_center_per <= 0:
        print("xxxxxxxxxxxxxxxxxxxx")
        print("Penalize, Reward:", reward)
        print("xxxxxxxxxxxxxxxxxxxx")
        return float(reward)

    print("--------------------")
    reward = 4 + progress / 10
    reward = round(reward, 2)
    print("Initial reward:", reward)

    # Reward perfect speed
    if speed == expected_curve_speed:
        reward += speed
        reward = round(reward, 2)
        print("1a) reward:", reward)
    else:
        reward *= abs(1 - min(abs(expected_curve_speed - speed) / expected_curve_speed, 0.7))
        reward = round(reward, 2)
        print("1b) reward:", reward)

    # Reward zero steering on straight tracks
    if is_track_straight and steering_angle == 0:
        reward += speed
        reward = round(reward, 2)
        print("2a) reward:", reward)

    # Penalize unwanted steering
    if ps.is_unwanted_steering(steering_angle):
        reward *= 0.5
        reward = round(reward, 2)
        print("3a) reward:", reward)

    # Penalize hard turns
    if ps.steering_angle_1 > -1 and abs(ps.steering_angle_1 - steering_angle) > 20:
        reward *= 0.6
        reward = round(reward, 2)
        print("4a) reward:", reward)

    # Reward driving in track direction
    if direction_diff_angle <= 10:
        reward *= 1 + (3 * (100 - direction_diff_angle) / 100)
        reward = round(reward, 2)
        print("5a) reward:", reward)
    # Penalize if not driving in track direction
    else:
        reward *= (100 - direction_diff_angle) / 100
        reward = round(reward, 2)
        print("5b) reward:", reward)

    # Reward/penalize according to progress to steps ratio
    if progress_to_steps_ratio > 0:
        reward *= progress_to_steps_ratio
        reward = round(reward, 2)
        print("6a) reward:", reward)

    # Reward track completion
    if progress < 100:
        reward += progress / 10
        reward = round(reward, 2)
        print("7a) reward:", reward)
    else:
        reward += 2 * progress
        reward = round(reward, 2)
        print("8b) reward:", reward)

    reward = round(max(reward, 0.01), 2)
    print("--------------------")
    print("Final reward:", reward)
    print("--------------------")

    ps.steering_angle_2 = ps.steering_angle_1
    ps.steering_angle_1 = steering_angle
    return float(reward)
