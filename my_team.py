import random
import util
from capture_agents import CaptureAgent
from game import Directions
from util import nearest_point

def create_team(first_index, second_index, is_red,
                first='OffensiveReflexAgent', second='DefensiveReflexAgent', num_training=0):
    """
    Create a team of two agents
    """
    return [eval(first)(first_index), eval(second)(second_index)]

class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that choose score-maximizing actions
    """

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)

    def choose_action(self, game_state):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = game_state.get_legal_actions(self.index)

        values = [self.evaluate(game_state, a) for a in actions]

        max_value = max(values)
        best_actions = [a for a, v in zip(actions, values) if v == max_value]

        food_left = len(self.get_food(game_state).as_list())

        if food_left <= 2:
            best_dist = 9999
            best_action = None
            for action in actions:
                successor = self.get_successor(game_state, action)
                pos2 = successor.get_agent_position(self.index)
                dist = self.get_maze_distance(self.start, pos2)
                if dist < best_dist:
                    best_action = action
                    best_dist = dist
            return best_action

        return random.choice(best_actions)

    def get_successor(self, game_state, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = game_state.generate_successor(self.index, action)
        pos = successor.get_agent_state(self.index).get_position()
        if pos != nearest_point(pos):
            # Only half a grid position was covered
            return successor.generate_successor(self.index, action)
        else:
            return successor

    def evaluate(self, game_state, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.get_features(game_state, action)
        weights = self.get_weights(game_state, action)
        return features * weights

    def get_features(self, game_state, action):
        """
        Returns a counter of features for the state
        """
        features = util.Counter()
        successor = self.get_successor(game_state, action)
        features['successor_score'] = self.get_score(successor)
        return features

    def get_weights(self, game_state, action):
        """
        Normally, weights do not depend on the game state.  They can be either
        a counter or a dictionary.
        """
        return {'successor_score': 1.0}

class OffensiveReflexAgent(ReflexCaptureAgent):
    """
    An offensive agent that seeks to collect food strategically
    """
    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None
        self.escape_threshold = 3  # Distance to consider escaping from ghosts
        self.carried_food_weight = 10  # Bonus for carrying food
        self.total_food_weight = -50  # Encouragement to collect remaining food
        
    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)
        
    def choose_action(self, game_state):
        """
        Advanced action selection with multiple strategic considerations
        """
        actions = game_state.get_legal_actions(self.index)
        
        # Remove STOP action if possible
        if 'Stop' in actions:
            actions.remove('Stop')
        
        if not actions:
            return 'Stop'
        
        # Evaluate actions with advanced scoring
        values = [self.evaluate(game_state, a) for a in actions]
        max_value = max(values)
        best_actions = [a for a, v in zip(actions, values) if v == max_value]
        
        # If very few food dots left, prioritize returning home
        food_left = len(self.get_food(game_state).as_list())
        if food_left <= 2:
            best_dist = 9999
            best_action = None
            for action in actions:
                successor = self.get_successor(game_state, action)
                pos2 = successor.get_agent_position(self.index)
                dist = self.get_maze_distance(self.start, pos2)
                if dist < best_dist:
                    best_action = action
                    best_dist = dist
            return best_action
        
        return random.choice(best_actions)
    
    def get_features(self, game_state, action):
        """
        Extract advanced features for decision-making
        """
        features = util.Counter()
        successor = self.get_successor(game_state, action)
        my_state = successor.get_agent_state(self.index)
        my_pos = my_state.get_position()
        
        # Food collection features
        food_list = self.get_food(successor).as_list()
        features['successor_score'] = -len(food_list)  # Encourage eating food
        
        # Distance to nearest food
        if food_list:
            min_food_distance = min([self.get_maze_distance(my_pos, food) for food in food_list])
            features['distance_to_food'] = min_food_distance
        
        # Carried food bonus
        carried_food = game_state.get_agent_state(self.index).num_carrying
        features['carried_food'] = carried_food
        
        # Capsule proximity
        capsules = self.get_capsules(successor)
        if capsules:
            min_capsule_dist = min([self.get_maze_distance(my_pos, cap) for cap in capsules])
            features['capsule_proximity'] = min_capsule_dist
        
        # Enemy ghost detection and avoidance
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        ghosts = [a for a in enemies if not a.is_pacman and a.get_position() is not None]
        
        if ghosts:
            ghost_distances = [self.get_maze_distance(my_pos, ghost.get_position()) for ghost in ghosts]
            min_ghost_distance = min(ghost_distances)
            
            # Detailed ghost interaction
            features['ghost_distance'] = min_ghost_distance
            
            # Detect if ghosts are close and dangerous
            if min_ghost_distance < self.escape_threshold:
                # Check if ghosts are scared or not
                scared_ghosts = [g for g in ghosts if g.scared_timer > 0]
                
                if not scared_ghosts:
                    features['escape_factor'] = 1  # Need to escape
                else:
                    features['attack_scared_ghosts'] = 1  # Opportunity to attack
        
        # Proximity to home side (for returning food)
        home_distance = self.get_maze_distance(my_pos, self.start)
        features['home_distance'] = home_distance
        
        return features

    def get_weights(self, game_state, action):
        return {
            'successor_score': 100,  # Eating food is primary goal
            'distance_to_food': -1,  # Get closer to food
            'carried_food': self.carried_food_weight,  # Bonus for carrying food
            'capsule_proximity': -2,  # Slightly prefer being near power capsules
            'ghost_distance': 3,  # Avoid getting too close to ghosts
            'escape_factor': -500,  # Strong incentive to escape dangerous areas
            'attack_scared_ghosts': 50,  # Slight encouragement to attack scared ghosts
            'home_distance': -0.5  # Minor preference to stay somewhat close to home
        }

class DefensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free
    """

    def get_features(self, game_state, action):
        features = util.Counter()
        successor = self.get_successor(game_state, action)

        my_state = successor.get_agent_state(self.index)
        my_pos = my_state.get_position()

        # Determine if we are on defense
        features['on_defense'] = 1
        if my_state.is_pacman: features['on_defense'] = 0

        # Identify and track invaders
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        invaders = [a for a in enemies if a.is_pacman and a.get_position() is not None]
        
        # Number of invading Pacmen
        features['num_invaders'] = len(invaders)
        
        # Track closest food to our side
        our_food = self.get_food_you_are_defending(successor).as_list()
        if our_food:
            food_distances = [self.get_maze_distance(my_pos, food) for food in our_food]
            features['food_defense_distance'] = min(food_distances)
        
        # Compute distance to invaders
        if len(invaders) > 0:
            dists = [self.get_maze_distance(my_pos, a.get_position()) for a in invaders]
            features['invader_distance'] = min(dists)
            
            # Track which invader is closest to our food
            closest_invader = min(invaders, key=lambda a: min(self.get_maze_distance(a.get_position(), food) for food in our_food))
            features['threat_level'] = self.get_maze_distance(my_pos, closest_invader.get_position())
        
        # Discourage stopping and reversing
        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[game_state.get_agent_state(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def get_weights(self, game_state, action):
        return {
            'num_invaders': -1000,      # Strongly discourage multiple invaders
            'on_defense': 100,          # Prioritize staying on our side
            'invader_distance': -10,    # Get closer to invaders
            'stop': -100,               # Discourage stopping
            'reverse': -2,              # Slightly discourage reversing
            'food_defense_distance': -5,# Prefer being close to our food
            'threat_level': -20         # Respond more aggressively to direct threats
        }