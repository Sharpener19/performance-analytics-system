import psycopg2

# Connecting to the database
conn = psycopg2.connect(
    host="localhost",        # your Postgres host
    database="esmo",   # your DB name
    user="username",         # your DB user
    password="verygoodpassword" # your DB password
)
cursor = conn.cursor()

roles = ['Top', 'Jungle', 'Mid', 'Bot', 'Support']

# gets or creates player, if player is new then prompts user to enter country
def get_or_create_player(name):
    cursor.execute("SELECT player_id FROM players WHERE player_name = %s;", (name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        country = input(f"New player '{name}' detected. Enter country: ")
        cursor.execute(
            "INSERT INTO players (player_name, country) VALUES (%s,%s) RETURNING player_id;",
            (name, country)
        )
        conn.commit()
        return cursor.fetchone()[0]

# gets the next game_id
def get_next_game_id():
    cursor.execute("SELECT MAX(game_id) FROM game_stats;")
    result = cursor.fetchone()[0]
    return 1 if result is None else result + 1

# inserts a single match, data entry (10 players)
def insert_match():
    print("\n--- New Match ---")
    season_id = int(input("Enter season_id: "))
    phase = input("Competition phase (Regular Season/Playoffs): ")
    team_win = input("Winning team name: ")
    team_lose = input("Losing team name: ")

    game_id = get_next_game_id()
    print(f"Assigned game_id = {game_id}")

    print("\nEnter 10 lines of player data:")
    print("Format for non-junglers: Name Champion K D A")
    print("Format for junglers: Name Champion K D A Drakes Rams Bosses Steals")

    for i in range(10):
        role = roles[i % 5]
        team_name = team_win if i < 5 else team_lose
        win = True if i < 5 else False

        while True:
            try:
                data = input(f"Player {i+1} ({role}): ").strip().split()

                # Check if jungler stats are formatted correctly
                if role.lower() == 'jungle' and len(data) != 9:
                    print(f"Error: Jungle player must have 9 fields (Name Champion K D A Drakes Rams Bosses Steals). Please retype this line.")
                    continue  # Retry this player
                elif role.lower() != 'jungle' and len(data) != 5:
                    print(f"Error: {role} player must have 5 fields (Name Champion K D A). Please retype this line.")
                    continue  # Retry this player

                # Parse values
                player_name = data[0]
                champion = data[1]
                kills = int(data[2])
                deaths = int(data[3])
                assists = int(data[4])

                player_id = get_or_create_player(player_name)

                # Insert into game_stats
                cursor.execute("""
                    INSERT INTO game_stats (
                        player_id, season_id, team_name, role, champion_name,
                        kills, deaths, assists, win, game_id, competition_phase
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING game_stat_id
                """, (player_id, season_id, team_name, role, champion, kills, deaths, assists, win, game_id, phase))
                game_stat_id = cursor.fetchone()[0]

                # Jungle objectives
                if role.lower() == 'jungle':
                    drakes = int(data[5])
                    rams = int(data[6])
                    bosses = int(data[7])
                    steals = int(data[8])
                    cursor.execute("""
                        INSERT INTO jungle_stats (
                            game_stat_id, drakes_secured, rams_secured, bosses_secured, objectives_stolen
                        ) VALUES (%s,%s,%s,%s,%s)
                    """, (game_stat_id, drakes, rams, bosses, steals))

                break

            except ValueError:
                print("Error: K/D/A and objective values must be integers. Please retype this line.")
            except Exception as e:
                print(f"Unexpected error: {e}. Please retype this line.")

    conn.commit()
    print(f"Match inserted successfully! game_id = {game_id}\n")

# Main loop
while True:
    insert_match()
    cont = input("Add another match? (y/n): ").lower()
    if cont != 'y':
        break

cursor.close()
conn.close()
