import random
from capture_agents import CaptureAgent
from game import Directions
from util import nearest_point

def create_team(first_index, second_index, is_red, first='AdaptiveAgent', second='AdaptiveAgent', num_training=0):
    """
    Create a team of two agents.
    """
    return [eval(first)(first_index), eval(second)(second_index)]


class ReflexCaptureAgent(CaptureAgent):
    """
    A foundational agent with utility functions for other agents.
    """

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None
        self.last_positions = []
        self.loop_threshold = 5  # Detect loops

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        super().register_initial_state(game_state)
        self.last_positions = []

    def detect_loop(self, current_pos):
        """
        Detects loops based on recent positions.
        """
        self.last_positions.append(current_pos)
        if len(self.last_positions) > self.loop_threshold:
            self.last_positions.pop(0)

        # Detect loops when positions repeat
        if len(self.last_positions) == self.loop_threshold:
            unique_positions = set(self.last_positions)
            if len(unique_positions) <= 2:
                return True
        return False

    def navigate_to_target(self, game_state, target):
        """
        Navigate to the target using greedy distance minimization.
        """
        actions = game_state.get_legal_actions(self.index)
        best_action = None
        shortest_distance = float('inf')

        for action in actions:
            successor = game_state.generate_successor(self.index, action)
            successor_pos = successor.get_agent_position(self.index)
            dist = self.get_maze_distance(successor_pos, target)
            if dist < shortest_distance:
                best_action = action
                shortest_distance = dist

        return best_action or random.choice(actions)

    def get_closest_position(self, current_pos, positions):
        """
        Find the closest position from a list of positions.
        """
        return min(positions, key=lambda pos: self.get_maze_distance(current_pos, pos), default=None)

    def get_home_boundary_positions(self, game_state):
        """
        Get positions along the home boundary.
        """
        mid_width = game_state.data.layout.width // 2
        height = game_state.data.layout.height
        boundary_x = mid_width - 1 if self.red else mid_width
        return [(boundary_x, y) for y in range(height) if not game_state.has_wall(boundary_x, y)]

    def get_visible_ghosts(self, game_state):
        """
        Get positions of visible ghosts.
        """
        enemies = [game_state.get_agent_state(i) for i in self.get_opponents(game_state)]
        return [e.get_position() for e in enemies if not e.is_pacman and e.get_position() is not None]


import random
from capture_agents import CaptureAgent
from game import Directions
from util import nearest_point

def create_team(first_index, second_index, is_red, first='AdaptiveAgent', second='AdaptiveAgent', num_training=0):
    """
    Create a team of two agents.
    """
    return [eval(first)(first_index), eval(second)(second_index)]


class ReflexCaptureAgent(CaptureAgent):
    """
    A foundational agent with utility functions for other agents.
    """

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None
        self.last_positions = []
        self.loop_threshold = 5  # Detect loops

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        super().register_initial_state(game_state)
        self.last_positions = []

    def detect_loop(self, current_pos):
        """
        Detects loops based on recent positions.
        """
        self.last_positions.append(current_pos)
        if len(self.last_positions) > self.loop_threshold:
            self.last_positions.pop(0)

        # Detect loops when positions repeat
        if len(self.last_positions) == self.loop_threshold:
            unique_positions = set(self.last_positions)
            if len(unique_positions) <= 2:
                return True
        return False

    def navigate_to_target(self, game_state, target):
        """
        Navigate to the target using greedy distance minimization.
        """
        actions = game_state.get_legal_actions(self.index)
        best_action = None
        shortest_distance = float('inf')

        for action in actions:
            successor = game_state.generate_successor(self.index, action)
            successor_pos = successor.get_agent_position(self.index)
            dist = self.get_maze_distance(successor_pos, target)
            if dist < shortest_distance:
                best_action = action
                shortest_distance = dist

        return best_action or random.choice(actions)

    def get_closest_position(self, current_pos, positions):
        """
        Find the closest position from a list of positions.
        """
        return min(positions, key=lambda pos: self.get_maze_distance(current_pos, pos), default=None)

    def get_home_boundary_positions(self, game_state):
        """
        Get positions along the home boundary.
        """
        mid_width = game_state.data.layout.width // 2
        height = game_state.data.layout.height
        boundary_x = mid_width - 1 if self.red else mid_width
        return [(boundary_x, y) for y in range(height) if not game_state.has_wall(boundary_x, y)]

    def get_visible_ghosts(self, game_state):
        """
        Get positions of visible ghosts.
        """
        enemies = [game_state.get_agent_state(i) for i in self.get_opponents(game_state)]
        return [e.get_position() for e in enemies if not e.is_pacman and e.get_position() is not None]


class AdaptiveAgent(ReflexCaptureAgent):
    """
    An agent that dynamically switches between offensive and defensive modes.
    """

    def choose_action(self, game_state):
        """
        Decide on an action dynamically.
        """
        current_pos = game_state.get_agent_position(self.index)
        self.update_mode(game_state)

        ghosts = self.get_visible_ghosts(game_state)

        # Check if being chased and close to home
        if self.is_ghost_near(current_pos, ghosts) and self.is_close_to_home(game_state, current_pos):
            print(f"Agent {self.index}: Ghost chasing and close to home. Returning to base.")
            return self.return_to_base(game_state)

        if self.detect_loop(current_pos):
            print(f"Agent {self.index}: Detected a loop. Breaking it.")
            actions = game_state.get_legal_actions(self.index)
            if 'Stop' in actions:
                actions.remove('Stop')
            return random.choice(actions)

        if self.mode == 'offensive':
            return self.offensive_action(game_state)
        else:
            return self.defensive_action(game_state)

    def update_mode(self, game_state):
        """
        Update the mode dynamically based on the game state.
        """
        score = self.get_score(game_state)
        time_left = game_state.data.timeleft
        carrying = game_state.get_agent_state(self.index).num_carrying
        is_red_team = game_state.is_on_red_team(self.index)
        score_diff = score if is_red_team else -score

        # Switch mode based on score, carrying, and time
        if carrying >= 5 or (score_diff > 8 and time_left > 200):
            self.mode = 'defensive'
        elif time_left < 200 and score_diff > 0:
            self.mode = 'offensive'
        else:
            self.mode = 'offensive'

    def offensive_action(self, game_state):
        """
        Collect food while avoiding ghosts.
        """
        food_list = self.get_food(game_state).as_list()
        my_pos = game_state.get_agent_position(self.index)

        if not food_list:
            return self.return_to_base(game_state)

        ghosts = self.get_visible_ghosts(game_state)

        # If ghost nearby, retreat
        if self.is_ghost_near(my_pos, ghosts):
            print(f"Agent {self.index}: Ghost nearby! Retreating.")
            return self.retreat_from_ghosts(game_state, ghosts)

        # Default: collect food
        target = self.get_closest_position(my_pos, food_list)
        return self.navigate_to_target(game_state, target)

    def defensive_action(self, game_state):
        """
        Patrol the home boundary or chase invaders.
        """
        invaders = self.get_invaders(game_state)
        my_pos = game_state.get_agent_position(self.index)

        if invaders:
            closest_invader = self.get_closest_position(my_pos, invaders)
            return self.navigate_to_target(game_state, closest_invader)

        # Patrol home boundary
        boundary_positions = self.get_home_boundary_positions(game_state)
        target = self.get_closest_position(my_pos, boundary_positions)
        return self.navigate_to_target(game_state, target)

    def is_ghost_near(self, position, ghosts, threshold=3):
        """
        Check if a ghost is near the given position.
        """
        for ghost in ghosts:
            if self.get_maze_distance(position, ghost) <= threshold:
                return True
        return False

    def is_close_to_home(self, game_state, position, threshold=5):
        """
        Check if the agent is close to the home boundary.
        """
        home_positions = self.get_home_boundary_positions(game_state)
        for home_pos in home_positions:
            if self.get_maze_distance(position, home_pos) <= threshold:
                return True
        return False

    def retreat_from_ghosts(self, game_state, ghosts):
        """
        Move away from ghosts, and prioritize returning home if close.
        """
        my_pos = game_state.get_agent_position(self.index)
        if self.is_close_to_home(game_state, my_pos):
            return self.return_to_base(game_state)

        # Regular retreat logic
        actions = game_state.get_legal_actions(self.index)
        safest_action = None
        max_distance = -1

        for action in actions:
            successor = game_state.generate_successor(self.index, action)
            successor_pos = successor.get_agent_position(self.index)

            # Calculate the minimum distance to any ghost
            min_distance_to_ghost = min(
                [self.get_maze_distance(successor_pos, ghost) for ghost in ghosts],
                default=float('inf')
            )

            if min_distance_to_ghost > max_distance:
                max_distance = min_distance_to_ghost
                safest_action = action

        return safest_action or random.choice(actions)

    def get_invaders(self, game_state):
        """
        Identify positions of invaders in the home territory.
        """
        opponents = [game_state.get_agent_state(i) for i in self.get_opponents(game_state)]
        return [o.get_position() for o in opponents if o.is_pacman and o.get_position() is not None]

    def return_to_base(self, game_state):
        """
        Return to the closest position along the home boundary.
        """
        my_pos = game_state.get_agent_position(self.index)
        home_positions = self.get_home_boundary_positions(game_state)
        target = self.get_closest_position(my_pos, home_positions)
        return self.navigate_to_target(game_state, target)
