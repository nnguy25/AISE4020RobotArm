def replay_motion_from_file(filename: str):
    # Load recorded angles from file
    try:
        with open(filename, "r") as f:
            positions = [eval(line.strip()) for line in f.readlines()]
        print(f"Loaded {len(positions)} positions from {filename}")
    except FileNotFoundError:
        print(f"File {filename} not found. Make sure you recorded this quadrant.")
        exit(1)

    # Move to neutral position
    mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=30)
    time.sleep(2)

    # Replay the recorded motion smoothly
    print("Replaying recorded motion smoothly...")
    for pos in positions:
        mc.sync_send_angles(pos, 80)
        time.sleep(0.05)

    print("Motion complete!")
    mc.release_all_servos()