import math
import time


class PreviousState:
    start_time = -1
    steering_angle_1 = -1
    steering_angle_2 = -1
    best_steps = -1
    best_time = -1

    # Determine unwanted steering
    def is_unwanted_steering(self, params):
        steering_angle = round(params['steering_angle'], 0)
        if self.steering_angle_1 > -1 and self.steering_angle_2 > -1:
            sign_0 = steering_angle / abs(steering_angle) if steering_angle > 0 else 1
            sign_1 = ps.steering_angle_1 / abs(ps.steering_angle_1) if ps.steering_angle_1 > 0 else 1
            sign_2 = ps.steering_angle_2 / abs(ps.steering_angle_2) if ps.steering_angle_2 > 0 else 1
            if sign_0 != sign_1 and sign_0 == sign_2:
                return True
        return False


ps = PreviousState()


# Expected upcoming curve angle speed, value(1 - 4)
def get_speed_from_angle(angle):
    speed = (4 - (angle * 0.1)) * 10
    speed = abs((speed - (speed % 5)) / 10)
    return max(speed, 1)


# get direction difference angle between two points
def get_curve_between_two_points(params, prev_waypoint, next_waypoint):
    heading = round(params['heading'], 0)
    track_direction = math.atan2(next_waypoint[1] - prev_waypoint[1], next_waypoint[0] - prev_waypoint[0])
    track_direction = round(math.degrees(track_direction), 0)
    curve_angle = abs(track_direction - heading)
    if curve_angle > 180:
        curve_angle = 360 - curve_angle
    return curve_angle


# get direction difference angle between current waypoint and next
def get_direction_diff_angle(params):
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    next_waypoint = waypoints[closest_waypoints[1]]
    prev_waypoint = waypoints[closest_waypoints[0]]
    return get_curve_between_two_points(params, prev_waypoint, next_waypoint)


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
    is_reversed = params['is_reversed']

    # Near Center in Percentage, value (0 - 100)
    near_center_per = round(((track_width / 2) - distance_from_center) * 100 / (track_width / 2), 0)

    # Higher = better
    progress_to_steps_ratio = round(3 * progress / max(steps, 1), 2)

    # Determine curve & direction
    upcoming_curve_direction = ''
    prev_point = waypoints[closest_waypoints[0]]
    future_track_length = 5
    if len(waypoints) > closest_waypoints[1] + future_track_length:
        future_point = waypoints[closest_waypoints[1] + future_track_length]
        current_point = waypoints[closest_waypoints[1]]
        future_direction = round(
            math.degrees(math.atan2(future_point[1] - current_point[1], future_point[0] - current_point[0])), 0)
        current_direction = round(
            math.degrees(math.atan2(current_point[1] - prev_point[1], current_point[0] - prev_point[0])), 0)
        upcoming_curve_angle = abs(future_direction - current_direction)
        upcoming_curve_direction = 'left' if current_direction < future_direction else 'right'
        if upcoming_curve_angle > 180:
            upcoming_curve_angle = 360 - upcoming_curve_angle
    else:
        upcoming_curve_angle = 0
    is_track_straight = (upcoming_curve_angle <= 15)
    if is_track_straight:
        upcoming_curve_direction = ''

    direction_diff_angle = get_direction_diff_angle(params)
    expected_curve_speed = get_speed_from_angle(upcoming_curve_angle)

    if ps.start_time < 0:
        ps.start_time = time.time()
    time_taken = round(time.time() - ps.start_time, 3)

    print("------------------------------------------------------------------")
    print("progress:", progress)
    print("time_taken:", time_taken)
    print("best time_taken:", ps.best_time)
    print("steps:", steps)
    print("best steps:", ps.best_steps)
    print("progress_to_steps_ratio:", progress_to_steps_ratio)
    print("steering_angle:", steering_angle)
    print("previous steering_angle 1:", ps.steering_angle_1)
    print("previous steering_angle 2:", ps.steering_angle_2)
    print("is_track_straight:", is_track_straight)
    print("upcoming_curve_direction:", upcoming_curve_direction)
    print("upcoming_curve_angle:", upcoming_curve_angle)
    print("near_center_per:", near_center_per)
    print("direction_diff_angle:", direction_diff_angle)
    print("ps.is_unwanted_steering:", ps.is_unwanted_steering(params))
    print("[steering_angle, speed]: [", steering_angle, ",", speed, "]")
    print("[speed, expected_curve_speed]: [", speed, ",", expected_curve_speed, "]")

    reward = 1e-5
    if is_reversed or not all_wheels_on_track or direction_diff_angle > 75 or near_center_per <= 0:
        print("xxxxxxxxxxxxxxxxxxxx")
        print("Penalize, Reward:", reward)
        print("xxxxxxxxxxxxxxxxxxxx")
        return float(reward)

    print("--------------------")
    reward = 1 + speed + 10 * progress_to_steps_ratio
    reward = round(reward, 2)
    print("Initial reward:", reward)

    # Reward higher speed in track direction
    if direction_diff_angle <= 30:
        reward += speed
        reward = round(reward, 2)
        print("1a) reward:", reward)
    # Penalize if not driving in track direction
    elif direction_diff_angle > 50:
        reward *= (100 - direction_diff_angle) / 100
        reward = round(reward, 2)
        print("1b) reward:", reward)
    else:
        reward -= speed
        reward = round(reward, 2)
        print("1c) reward:", reward)

    if is_track_straight:
        # Reward zero steering on straight tracks
        if steering_angle == ps.steering_angle_1 == 0:
            reward += speed * 1.5
            reward = round(reward, 2)
            print("2a1) reward:", reward)
        # Penalize unwanted steering
        elif ps.is_unwanted_steering(params):
            reward *= 0.5
            reward = round(reward, 2)
            print("2a2) reward:", reward)

    # Penalize less then expected speed
    if speed < expected_curve_speed:
        reward *= 0.5
        reward = round(reward, 2)
        print("3a) reward:", reward)

    # Penalize steering at all steps
    if steering_angle != 0:
        reward *= (80 - abs(steering_angle)) / 80
        reward = round(abs(reward), 2)
        print("4a) reward:", reward)

        # Punish harder if steering on straight track
        if is_track_straight:
            reward *= (50 - abs(steering_angle)) / 50
            reward = round(abs(reward), 2)
            print("4a1) reward:", reward)

    # Reward track completion
    if progress < 100:
        reward += progress / 5
        reward = round(reward, 2)
        print("5a) reward:", reward)

    if progress == 100:
        reward += 3 * (progress ** 2) / steps
        reward = round(reward, 2)
        print("6a) reward:", reward)

        # Reward if previous record is broken
        if steps < ps.best_steps:
            reward += progress
            reward = round(reward, 2)
            print("6a1) reward:", reward)

        if ps.best_steps == -1 or ps.best_steps > steps:
            ps.best_steps = steps

        # Reset Timer
        if ps.best_time < 0 or ps.best_time > time_taken:
            ps.best_time = time_taken
        ps.start_time = -1

    # Reward/penalize according to progress to steps ratio
    if progress_to_steps_ratio > 0:
        reward *= progress_to_steps_ratio
        reward = round(reward, 2)
        print("7a) reward:", reward)

    # Reward/penalize according to time taken
    if time_taken > 0:
        reward *= (20 * progress / 100) / time_taken
        reward = round(reward, 2)
        print("8a) reward:", reward)

    reward = round(max(reward, 1), 2)
    print("--------------------")
    print("Final reward:", reward)
    print("--------------------")

    ps.steering_angle_2 = ps.steering_angle_1
    ps.steering_angle_1 = steering_angle
    return float(reward)
