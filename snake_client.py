import requests
import random
import json
import copy
import logging

class Game_model:
  server_url=""
  user={}
  players=[]
  req = requests.Session()
  game_map={}
  started_time=0

  def __init__(self,server_url,user_name):
    self.server_url = server_url
    self.user['name']=user_name
    self.user['snake']={}
    self.user['score']=0
    self.started_time=0
    self.game_map['walls']=[]
    self.game_map['walls_count']=0
    self.game_map['apples']=[]

  # basic snake control

  def birth_snake(self):
    direction = random.randint(1,4)
    flag = True
    while(flag):
      flag = False
      head_x = random.randint(20,80)
      head_y = random.randint(20,80)
      for player in self.players:
        snake_head = player['snake']['head']
        if abs(head_x - snake_head['x'])+abs(head_y - snake_head['y']) <= 15:
          flag = True
      for wall in self.game_map['walls']:
        if abs(head_x - wall['x'])+abs(head_y - wall['y']) <= 7:
          flag = True

    self.user['snake']['head'] = {'x':head_x,'y':head_y}

    if direction == 1:
      dir_x = 1
      dir_y = 0
    elif direction == 2:
      dir_x = 0
      dir_y = 1
    elif direction == 3:
      dir_x = -1
      dir_y = 0  
    elif direction == 4:
      dir_x = 0
      dir_y = -1   

    self.user['snake']['body'] = []
    for i in range(2):
      self.user['snake']['body'].append({'x':head_x+(i+1)*dir_x,'y':head_y+(i+1)*dir_y})

    self.user['snake']['len'] = 3

    print("snake birthed")

    res = self._upload_snake()
    if res == 0:
      return {'res':'suc','data':{'snake':self.user['snake']}}
    elif res == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}

      
  def move_snake(self,direction):
    snake = self.user['snake']
    
    if direction == 'n':
      mov_x=0
      mov_y=-1
    elif direction == 's':
      mov_x=0
      mov_y=1
    elif direction == 'w':
      mov_x=-1
      mov_y=0
    elif direction == 'e':
      mov_x=1
      mov_y=0

    snake_tail = copy.deepcopy(snake['body'][-1])

    for i in range(snake['len']-2,0,-1):
      snake['body'][i]=copy.deepcopy(snake['body'][i-1])

    snake['body'][0]=copy.deepcopy(snake['head'])

    snake['head']['x'] += mov_x
    snake['head']['y'] += mov_y

    print("moved success, direction = "+direction)

    res = self._upload_snake()

    if res == 'e':
      snake['len'] += 1
      self.user['score'] += 50*(0.95 ** self.game_map['walls_count'])
      snake['body'].append(snake_tail)
      self.game_map['walls_count'] += 10
      return {'res':'eat','data':{'pos':snake_tail,'socre':self.user['score']}}
    elif res == 'd':
      snake['len'] = -1
      return {'res':'die','data':{'socre':self.user['score']}}
    elif res == 0:
      return {'res':'suc','data':{}}
    elif res == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}


  def place_wall(self,direction):
    if direction == 'n':
      mov_x=0
      mov_y=-2
    elif direction == 's':
      mov_x=0
      mov_y=2
    elif direction == 'w':
      mov_x=-2
      mov_y=0
    elif direction == 'e':
      mov_x=2
      mov_y=0

    snake_h = self.user['snake']['head']
    if snake_h['x'] < 2 or  snake_h['x'] > 97 or snake_h['x'] <2 or snake_h['y'] > 97:
      return {'res':'fal','data':{}}

    wall = {'x':snake_h['x']+mov_x,'y':snake_h['y']+mov_y}
    self.game_map['walls'].append(wall)
    res = self._uploading_wall(wall)
    if res == 0:
      return {'res':'suc','data':{'wall':wall}}
    elif res == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}



  # communication process

  def join_game(self):
    url = self.server_url + "/join/" + self.user['name']
    print("joining game.")
    res = self.req.get(url)
    if res.status_code == 200:
      print("join success")
      self.user['uuid'] = res.text
      self.user['snake']={}
      self.user['score']=0
      self.started_time=0
      self.game_map['walls']=[]
      self.game_map['walls_count']=0
      self.game_map['apples']=[]
      return {'res':'suc','data':{'uuid':self.user['uuid']}}
    else:
      print("join fail")
      return {'res':'com_fai','data':{}}



  def wait_game_start(self):
    while(self.started_time == 0):
      res = self._get_status()
      if res == -1:
        return {'res':'over','data':{'socre':self.user['score']}}
      elif res == 2:
        return {'res':'com_fai','data':{}}

    return {'res':'start','data':{}}



  def sync_world(self):
    res = self._get_status()
    if res == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}

    res = self._update_score()
    if res == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}

    res = self._get_score()
    if res == -1 or self.started_time == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}

    res = self._get_snake()
    if res == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}

    res = self._get_walls()
    if res == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}

    res = self._get_apples()
    if res == -1:
      return {'res':'over','data':{'socre':self.user['score']}}
    elif res == 2:
      return {'res':'com_fai','data':{}}



  def _update_score(self):
    url = self.server_url + "/update/score"
    print("uploading score data")
    score_data={'data':{'score':self.user['score']}}
    res = self.req.post(url,json=score_data)
    if res.status_code == 200:
      if res.text == 'success':
        return 0
      elif res.text == 'over':
        return -1
    else:
      return 2
      

  def _upload_snake(self):
    url = self.server_url + "/update/snake"
    print("uploading snake data")
    snake_data = {}
    snake_data['head'] = self.user['snake']['head']
    snake_data['body'] = self.user['snake']['body']
    snake_data['len'] = self.user['snake']['len']
    print(snake_data)
    res = self.req.post(url,json=snake_data)
    if res.status_code == 200:
      if res.text == 'eat':
        return 'e'
      elif res.text == 'die':
        return 'd'
      elif res.text == 'success':
        return 0
      elif res.text == 'over':
        return -1
    else:
      return 2


  def _uploading_wall(self,wall):
    url = self.server_url + "/update/wall"
    print("uploading wall data")
    wall_data={}
    wall_data['wall']=wall
    res = self.req.post(url,json=wall_data)
    if res.status_code == 200:
      if res.text == 'success':
        self.game_map['walls_count'] -= 1
      elif res.text == 'over':
        return -1
    else:
      return 2


  def _get_status(self):
    url = self.server_url + "/get/status"
    if self.started_time == 0:
      url = self.server_url + "/get/statusfull"
    res = self.req.get(url)
    if res.status_code == 200:
      res_data = res.json()
      if res_data != None:
        self.started_time = res_data.get('time')
        if self.started_time == 0:
          self.players.clear()
          for player in res_data.get('player'):
            if player['uuid'] != self.user['uuid']:
              player['snake']={}
              player['score']=0
              self.players.append(player)
        return 0
      elif res.text == 'over':
        return -1
    else:
      return 2


  def _get_score(self):
    url = self.server_url + "/get/scores"
    res = self.req.get(url)
    if res.status_code == 200:
      res_data = res.json()
      if res_data != None and len(res_data) > 0:
        for player in res_data:
          [p for p in self.players if p['uuid'] == player['uuid']][0]['score'] = player['score']
        return 0
      elif res.text == 'over':
        return -1
    else:
      return 2


  def _get_snake(self):
    url = self.server_url + "/get/snakes"
    print("downloading snake data")
    res = self.req.get(url)
    if res.status_code == 200:
      snake_data = res.json()
      if snake_data != None:
        for snake in snake_data:
          player = [player for pl in self.players if pl['uuid'] == snake['uuid']][0]
          player['snake']['body'] = snake['body']
          player['snake']['len'] = snake['len']
          player['snake']['head'] = snake['head']
        return 0
      elif res.text == 'over':
        return -1
    else:
      return 2
    

  def _get_walls(self):
    url = self.server_url + "/get/walls"
    print("downloading wall data")
    res = self.req.get(url)
    if res.status_code == 200:
      walls_data = res.json()
      if walls_data != None and len(walls_data) > 0:
        for wall in walls_data:
          if self.game_map['walls'].conut(wall) > 0:
            continue
          self.game_map['walls'].append(wall)
        return 0
      elif res.text == 'empty':
        return 0
      elif res.text == 'over':
        return -1
    else:
      return 2


  def _get_apples(self): 
    url = self.server_url + "/get/apples"
    print("downloading apple data")
    res = self.req.get(url)
    if res.status_code == 200:
      apples_data = res.json()
      if apples_data != None and len(apples_data) > 0:
        self.game_map['apples'].clear()
        for apple in apples_data:
          self.game_map['apples'].append(apple)
        return 0
      elif res.text == 'empty':
        return 0
      elif res.text == 'over':
        return -1
    else:
      return 2
