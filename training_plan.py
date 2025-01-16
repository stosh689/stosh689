# training_plan.py

import datetime

# Training parameters
goal_distance = 12  # miles
goal_time = 2  # hours
goal_pace = goal_distance / goal_time  # miles per hour (6 mph)

# Weekly training plan (Days represent each day of the week, 1-7)
training_plan = {
    'Week 1-2': {
        'Day 1': '3 miles easy jog (4-5 mph)',
        'Day 2': 'Rest or cross-training',
        'Day 3': '4 miles steady jog (4.5 mph)',
        'Day 4': 'Rest or strength training',
        'Day 5': '3 miles easy jog',
        'Day 6': 'Rest or cross-training',
        'Day 7': '5 miles long run (comfortable pace)',
    },
    'Week 3-4': {
        'Day 1': '4 miles easy jog',
        'Day 2': 'Interval training: 1-minute fast run, 2-minute recovery (20-30 minutes)',
        'Day 3': 'Rest or cross-training',
        'Day 4': '5 miles steady jog (4.5 mph)',
        'Day 5': 'Strength training',
        'Day 6': '6 miles long run (comfortable pace)',
        'Day 7': 'Rest or active recovery',
    },
    'Week 5-6': {
        'Day 1': '4 miles jog (5 mph)',
        'Day 2': 'Interval training: 1-minute sprints at 7 mph, 2-minute recovery',
        'Day 3': 'Rest or cross-training',
        'Day 4': '5 miles tempo run at 5.5 mph',
        'Day 5': 'Strength training',
        'Day 6': '8 miles long run (focus on pacing)',
        'Day 7': 'Active recovery',
    },
    'Week 7-8': {
        'Day 1': '5 miles easy jog at 5 mph',
        'Day 2': 'Tempo run for 4 miles at 5.5 mph',
        'Day 3': 'Rest or cross-training',
        'Day 4': 'Interval training: 1-minute fast run at 6-7 mph, 2-minute recovery',
        'Day 5': 'Strength training',
        'Day 6': '10 miles long run at 5 mph',
        'Day 7': 'Active recovery',
    },
    'Goal Run': {
        'Day 1': f'Run {goal_distance} miles at {goal_pace} mph for {goal_time} hours',
    }
}

# Function to simulate a weekly schedule
def print_training_plan(week):
    print(f"\nTraining Plan: {week}\n")
    for day, activity in training_plan[week].items():
        print(f"{day}: {activity}")

# Function to calculate weekly mileage based on the training plan
def calculate_weekly_mileage(week):
    weekly_mileage = 0
    for day, activity in training_plan[week].items():
        # Extract miles from activities (assuming mileage is explicitly stated in the activities)
        if 'miles' in activity:
            miles = float(activity.split(' ')[0])
            weekly_mileage += miles
    return weekly_mileage

# Simulate and display the training plan
def simulate_training():
    for week in training_plan:
        print_training_plan(week)
        if week != 'Goal Run':
            weekly_mileage = calculate_weekly_mileage(week)
            print(f"Total weekly mileage for {week}: {weekly_mileage} miles\n")
        else:
            print("\nGoal Run: Complete 12 miles at 6 mph in 2 hours\n")

# Running the simulation
simulate_training()

