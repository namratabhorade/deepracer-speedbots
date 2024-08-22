import math


class Curve:
    upcoming_curve_direction = ''
    upcoming_curve_angle = 0
    is_track_straight = True
    is_correct_side_of_curve = False


class PreviousState:
    steering_angle_1 = -1
    steering_angle_2 = -1
    best_steps = -1
    total_steps = -1
    avg_steps = -1
    iteration = 0
    max_progress = -1

    # Determine unwanted steering
    def is_unwanted_steering(self, params):
        steering_angle = round(params['steering_angle'], 0)
        if self.steering_angle_1 != -1 and self.steering_angle_2 != -1:
            sign_0 = steering_angle / abs(steering_angle) if steering_angle != 0 else 1.0
            sign_1 = self.steering_angle_1 / abs(self.steering_angle_1) if self.steering_angle_1 != 0 else 1.0
            sign_2 = self.steering_angle_2 / abs(self.steering_angle_2) if self.steering_angle_2 != 0 else 1.0
            if sign_0 != sign_1 and sign_0 == sign_2:
                return True
        return False


ps = PreviousState()


# Expected upcoming curve angle and direction
def get_curve_details(params, length):
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    is_left_of_center = params['is_left_of_center']
    curve = Curve()
    curve.upcoming_curve_direction = ''
    prev_point = waypoints[closest_waypoints[0]]
    if len(waypoints) > closest_waypoints[1] + length:
        future_point = waypoints[closest_waypoints[1] + length]
        current_point = waypoints[closest_waypoints[1]]
        future_direction = round(
            math.degrees(math.atan2(future_point[1] - current_point[1], future_point[0] - current_point[0])), 0)
        current_direction = round(
            math.degrees(math.atan2(current_point[1] - prev_point[1], current_point[0] - prev_point[0])), 0)
        curve.upcoming_curve_angle = abs(future_direction - current_direction)
        curve.upcoming_curve_direction = 'left' if current_direction < future_direction else 'right'
        if current_direction == future_direction:
            curve.upcoming_curve_direction = ''
        if curve.upcoming_curve_angle > 180:
            curve.upcoming_curve_angle = 360 - curve.upcoming_curve_angle
    else:
        curve.upcoming_curve_angle = 0
    curve.is_track_straight = (curve.upcoming_curve_angle <= 15)

    if curve.upcoming_curve_angle > 0 and ((curve.upcoming_curve_direction == 'left' and not is_left_of_center) or (
            curve.upcoming_curve_direction == 'right' and is_left_of_center)):
        curve.is_correct_side_of_curve = True
    return curve


# Expected upcoming curve angle expected speed, value(1 - 4)
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
    is_reversed = params['is_reversed']
    is_left_of_center = params['is_left_of_center']

    # Near Center in Percentage, value (0 - 100)
    near_center_per = round(((track_width / 2) - distance_from_center) * 100 / (track_width / 2), 0)

    # Progress to steps ratio x 3, Higher = better
    progress_to_steps_ratio = round(3 * progress / max(steps, 1), 2)

    # Determine curve & direction
    track_length_to_consider = 5
    curve = get_curve_details(params, track_length_to_consider)
    direction_diff_angle = get_direction_diff_angle(params)
    expected_curve_speed = get_speed_from_angle(curve.upcoming_curve_angle)

    print("------------------------------------------------------------------")
    print("progress_to_steps_ratio:", progress_to_steps_ratio)
    print("progress:", progress)
    print("steps:", steps)
    print("ps.best_steps:", ps.best_steps)
    print("ps.avg_steps:", ps.avg_steps)
    print("ps.iteration:", ps.iteration)
    print("ps.max_progress:", ps.max_progress)
    print("near_center_per:", near_center_per)
    print("direction_diff_angle:", direction_diff_angle)
    print("curve.is_track_straight:", curve.is_track_straight)
    print("curve.upcoming_curve_angle:", curve.upcoming_curve_angle)
    print("curve.is_correct_side_of_curve:", curve.is_correct_side_of_curve)
    print("[ps1, ps2, steering_angle]: [", ps.steering_angle_2, ",", ps.steering_angle_1, ",", steering_angle, "]")
    print("ps.is_unwanted_steering:", ps.is_unwanted_steering(params))
    print("[steering_angle, speed]: [", steering_angle, ",", speed, "]")
    print("[speed, expected_curve_speed]: [", speed, ",", expected_curve_speed, "]")
    print("curve.upcoming_curve_angle + direction_diff_angle:", curve.upcoming_curve_angle + direction_diff_angle)

    if is_reversed or direction_diff_angle > 80 or near_center_per <= 0:
        reward = 1e-5
        print("xxxxxxxxxxxxxxxxxxxx")
        print("Penalize, Reward:", reward)
        print("xxxxxxxxxxxxxxxxxxxx")
        return float(reward)

    print("--------------------")
    initial_reward = (speed + 4 * near_center_per / 100) * progress_to_steps_ratio 
    initial_reward = round(initial_reward, 2)
    print("Initial reward:", initial_reward)

    reward = initial_reward

    if curve.is_track_straight:
        # Heavily Reward consistent zero steering on straight track
        if steering_angle == ps.steering_angle_1 == ps.steering_angle_2 == 0:
            reward += speed * 3
            reward = round(abs(reward), 2)
            print("2a1) reward:", reward)
        # Reward zero steering on straight track
        if steering_angle == 0:
            reward += speed * 2
            reward = round(abs(reward), 2)
            print("2a2) reward:", reward)
        # Punish harder if steering on straight track
        if steering_angle != 0:
            reward *= (35 - abs(steering_angle)) / 35
            reward = round(abs(reward), 2)
            print("2a3) reward:", reward)
    else:
        # Punish higher direction_diff_angle on strong curves
        if curve.upcoming_curve_angle + direction_diff_angle > 55:
            reward *= 0.5 * (60 - direction_diff_angle) / 60
            reward = round(abs(reward), 2)
            print("2b1) reward:", reward)
    
    # Reward/penalize according to progress to steps ratio
    if progress < 100:
        reward += reward * progress / 10 * (progress_to_steps_ratio ** 10)
        reward = round(abs(reward), 2)
        print("4a) reward:", reward)
    else:
        reward += progress_to_steps_ratio * 10000
        reward = round(abs(reward), 2)
        print("4b) reward:", reward)
    
        ps.iteration += 1
        if ps.avg_steps == -1:
            ps.avg_steps = steps
            ps.total_steps = steps
        else:
            ps.total_steps += steps
            ps.avg_steps = round(ps.total_steps / ps.iteration, 0)
        if ps.best_steps == -1 or ps.best_steps > steps:
            ps.best_steps = steps

    if progress == 100:
        reward += ((progress_to_steps_ratio ** 5) * 2000)
        reward = round(max(reward, 96000), 2)
        print("4a) reward:", reward)
        ps.iteration += 1
        if ps.avg_steps == -1:
            ps.avg_steps = steps
            ps.total_steps = steps
        else:
            ps.total_steps += steps
            ps.avg_steps = round(ps.total_steps / ps.iteration, 0)
        if ps.best_steps == -1 or ps.best_steps > steps:
            ps.best_steps = steps

    reward = round(max(reward, 0.01), 2)
    print("--------------------")
    print("Final reward:", reward)
    print("--------------------")

    ps.steering_angle_2 = ps.steering_angle_1
    ps.steering_angle_1 = steering_angle
    if ps.max_progress < progress:
        ps.max_progress = progress

    return reward
