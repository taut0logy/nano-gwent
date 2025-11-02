import pygame
import sys
from core.game_state import GameState
from core.game_engine import GameEngine
from gui.game_gui import GameGUI
from gui.menu import GameMenu
from gui.config import SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Nano Gwent")
    
    icon = pygame.image.load('assets/images/icon.webp')
    pygame.display.set_icon(icon)
    
    menu = GameMenu(screen)
    clock = pygame.time.Clock()
    
    while True:
        game_config = menu.run()
        
        if game_config is None:
            break
        
        game_state = GameState()
        game_state.initialize()
        game_engine = GameEngine(game_state)
        
        player0_agent = None
        player1_agent = None
        player0_type = "Human"
        player1_type = "Human"
        
        if game_config['mode'] == 'human_vs_human':
            pass
        elif game_config['mode'] == 'human_vs_ai':
            agent_class = game_config['ai_agent']
            player1_agent = agent_class(1)
            player1_type = agent_class.__name__.replace('Agent', '')
        elif game_config['mode'] == 'ai_vs_ai':
            agent0_class = game_config['ai_agent_0']
            agent1_class = game_config['ai_agent_1']
            player0_agent = agent0_class(0)
            player1_agent = agent1_class(1)
            player0_type = agent0_class.__name__.replace('Agent', '')
            player1_type = agent1_class.__name__.replace('Agent', '')
        
        gui = GameGUI(screen, player0_type, player1_type)
        
        gui.last_round_number = 0
        gui.banner_state = None
        gui.banner_start_time = 0
        
        match_started = False
        first_render_done = False
        
        running = True
        
        while running:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif game_state.game_over:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        running = False
            
            # Render first to trigger the banner
            gui.render(game_state)
            
            if not first_render_done:
                first_render_done = True
            
            if not game_state.game_over:
                game_engine.check_auto_end_round()
            
            announcements_showing = gui.banner_state is not None
            
            # For AI vs AI, wait for initial banner to complete before starting
            if game_config['mode'] == 'ai_vs_ai' and not match_started:
                if first_render_done and gui.banner_state is None:
                    match_started = True
            
            can_make_move = not game_state.game_over and not announcements_showing
            if game_config['mode'] == 'ai_vs_ai':
                can_make_move = can_make_move and match_started
            
            if can_make_move:
                current_player_id = game_state.current_player
                
                if current_player_id == 0:
                    if player0_agent:
                        pygame.time.wait(500)
                        valid_actions = game_engine.get_valid_actions()
                        action = player0_agent.decide_action(game_state, valid_actions)
                        game_engine.execute_action(action)
                    else:
                        action = gui.handle_input(game_state)
                        if action:
                            valid_actions = game_engine.get_valid_actions()
                            if _is_action_valid(action, valid_actions):
                                game_engine.execute_action(action)
                                gui.selected_card = None
                
                elif current_player_id == 1:
                    if player1_agent:
                        pygame.time.wait(500)
                        valid_actions = game_engine.get_valid_actions()
                        action = player1_agent.decide_action(game_state, valid_actions)
                        game_engine.execute_action(action)
                    else:
                        action = gui.handle_input(game_state)
                        if action:
                            valid_actions = game_engine.get_valid_actions()
                            if _is_action_valid(action, valid_actions):
                                game_engine.execute_action(action)
                                gui.selected_card = None
            
            if game_state.game_over:
                gui.show_game_over(game_state)
            
            pygame.display.flip()
        
        if game_state.game_over:
            pygame.time.wait(2000)
    
    pygame.quit()
    sys.exit()

def _is_action_valid(action, valid_actions):
    for valid_action in valid_actions:
        if action.type == valid_action.type:
            if action.card is None and valid_action.card is None:
                return True
            if action.card and valid_action.card and action.card.id == valid_action.card.id:
                if action.target_row == valid_action.target_row:
                    return True
    return False

if __name__ == "__main__":
    main()
