import math


class PreviousState:
    steering_angle = -1
    progress_to_steps_ratio = 0


ps = PreviousState()


# Expected upcoming curve angle speed, value(1 - 4)
def get_speed_from_angle(angle):
    speed = (4 - (angle * 0.1)) * 10
    speed = abs((speed - (speed % 5)) / 10)
    return speed


# get absolute speed in continous action space, value (1, 1.5, 2, 2.5, ... ,4)
def get_speed_multiple_of_5(speed):
    speed = round(speed * 10, 0)
    speed = (speed - speed % 5) / 10
    return speed


def reward_function(params):
    # Default params
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    steering_angle = round(params['steering_angle'], 0)
    speed = params['speed']
    steps = params['steps']
    progress = round((params['progress'], 0))
    raw_progress = round(params['progress'], 2)
    all_wheels_on_track = params['all_wheels_on_track']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = round(params['heading'], 0)
    is_reversed = params['is_reversed']
    is_left_of_center = params['is_left_of_center']

    calculated_speed = get_speed_multiple_of_5(speed)
    progress_to_steps_ratio = round(max(raw_progress, 1) / max(steps, 1), 2)

    # Near Center in Percentage, value (0 - 100)
    near_center_per = round(((track_width / 2) - distance_from_center) * 100 / (track_width / 2), 0)

    # Determine curve & direction
    upcoming_curve_direction = ''
    current_direction = 0
    future_direction = 0
    next_point = waypoints[closest_waypoints[1]]
    prev_point = waypoints[closest_waypoints[0]]
    future_track_length = 7
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
    is_track_straight = (upcoming_curve_angle == 0)
    if is_track_straight:
        upcoming_curve_direction = ''

    track_direction = math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0])
    track_direction = round(math.degrees(track_direction), 0)
    direction_diff_angle = abs(track_direction - heading)
    if direction_diff_angle > 180:
        direction_diff_angle = 360 - direction_diff_angle

    expected_curve_speed = get_speed_from_angle(upcoming_curve_angle)
    correct_side_of_curve = False

    if (upcoming_curve_direction == 'left' and not is_left_of_center) or (
            upcoming_curve_direction == 'right' and is_left_of_center):
        correct_side_of_curve == True

    print("------------------------------------------------------------------")
    print("previous progress_to_steps_ratio: ", ps.progress_to_steps_ratio)
    print("progress_to_steps_ratio: ", progress_to_steps_ratio)
    print("steps: ", steps)
    print("raw_progress ", raw_progress)
    print("progress: ", progress)
    print("speed: ", speed)
    print("previous steering_angle: ", ps.steering_angle)
    print("steering_angle: ", steering_angle)
    print("is_left_of_center: ", is_left_of_center)
    print("is_track_straight: ", is_track_straight)
    print("upcoming_curve_direction: ", upcoming_curve_direction)
    print("correct_side_of_curve: ", correct_side_of_curve)
    print("upcoming_curve_angle: ", upcoming_curve_angle)
    print("expected_curve_speed: ", expected_curve_speed)
    print("calculated_speed: ", calculated_speed)
    print("near_center_per: ", near_center_per)
    print("direction_diff_angle: ", direction_diff_angle)

    reward = 1e-5
    if is_reversed or not all_wheels_on_track or direction_diff_angle > 30 or near_center_per <= 0:
        print("xxxxxxxxxxxxxxxxxxxx")
    print("Penalize, Reward: ", reward)
    print("xxxxxxxxxxxxxxxxxxxx")
    return float(reward)

    print("--------------------")
    reward = 5 * near_center_per / 100
    reward = round(reward, 2)
    print("Initial reward: ", reward)

    # Reward perfect speed
    if calculated_speed == expected_curve_speed:
        reward += calculated_speed * near_center_per / 100
        reward = round(reward, 2)
        print("1a) reward: ", reward)

    # Reward progress
    reward += progress / 10
    reward = round(reward, 2)
    print("2) reward: ", reward)

    # Reward for being on correct side of road before curve
    if not is_track_straight and correct_side_of_curve:
        reward += 2 + (10 * upcoming_curve_angle / 100)
        reward = round(reward, 2)
        print("3a) reward: ", reward)
    else:
        reward += 2 * near_center_per / 100
        reward = round(reward, 2)
        print("3b) reward: ", reward)

    # Penalize if not driving in track direction
    if direction_diff_angle > 0:
        reward *= (80 - direction_diff_angle) / 80
        reward = round(reward, 2)
        print("4a) reward: ", reward)

    # Reward when car takes correct turn during extreme curve
    if upcoming_curve_angle >= 35:
        reward = round(reward, 2)
        print("5a) reward: ", reward)
        reward += (5 * near_center_per / 100) / max(direction_diff_angle, 1)

    # Reward driving in track direction
    if direction_diff_angle == 0:
        reward *= (1.5 + near_center_per / 100)
        reward = round(reward, 2)
        print("6a) reward: ", reward)

    # Reward zero steering on straight tracks
    if is_track_straight and (steering_angle == ps.steering_angle == 0):
        reward += 3
        reward = round(reward, 2)
        print("7a) reward: ", reward)

    # Penalize hard turns
    if ps.steering_angle > -1 and abs(ps.steering_angle - steering_angle) > 10:
        reward *= 0.5
        reward = round(reward, 2)
        print("8a) reward: ", reward)

    # Reward low progress to steps ratio
    if ps.progress_to_steps_ratio > 0 and progress_to_steps_ratio > ps.progress_to_steps_ratio:
        reward += 15 * progress_to_steps_ratio
        reward = round(reward, 2)
        print("9a) reward: ", reward)

    # Reward low steps
    if raw_progress > 0 and steps > 0:
        reward *= 3 * raw_progress / steps
        reward = round(reward, 2)
        print("10a) reward: ", reward)

    # Reward track completion
    if progress == 100:
        reward += progress
        reward = round(reward, 2)
        print("11a) reward: ", reward)

    reward = round(max(reward, 0.01), 2)
    print("--------------------")
    print("Final reward: ", reward)
    print("--------------------")

    ps.steering_angle = steering_angle
    if progress_to_steps_ratio > ps.progress_to_steps_ratio:
        ps.progress_to_steps_ratio = round(progress_to_steps_ratio, 2)

    return float(reward)
