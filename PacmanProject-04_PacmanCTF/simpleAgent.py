# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions, Actions
import game
from qlearningAgents import ApproximateQAgent

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, thirdIndex, isRed,
               first = 'myAgent', second = 'myDAgent', third = 'myAgent'):
  """
  This function should return a list of three agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  print firstIndex, secondIndex, thirdIndex
  return [eval(first)(firstIndex), eval(second)(secondIndex), eval(third)(thirdIndex)]

##########
# Agents #
##########



class myAgent(ApproximateQAgent):
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.myFlagPos = self.getFlagsYouAreDefending(gameState)[0]
        self.depth = 1
    def getAction(self, gameState):
        self.observationHistory.append(gameState)
        myState = gameState.getAgentState(self.index)
        myPos = myState.getPosition()
        if myPos != util.nearestPoint(myPos):
          # We're halfway from one position to the next
              return gameState.getLegalActions(self.index)[0]
        else:
              return self.chooseAction(gameState)
    def chooseAction(self, gameState):
        actions = gameState.getLegalActions(self.index)
      
        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [self.getFeatures1(gameState, a)*self.getWeights1(gameState, a) for a in actions]
        # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
        
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        legalActions = gameState.getLegalActions(self.index)
        action = None
        if util.flipCoin(self.epsilon):
            action = random.choice(legalActions)
        else:
            action = self.value(gameState, self.index, -float("inf"), float("inf"))[1]
        self.doAction(gameState,action)
#        return random.choice(bestActions)
        return action
    def getFeatures1(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        foodList = self.getFood(successor).asList()    
        features['successorScore'] = -len(foodList)#self.getScore(successor)

        # Compute distance to the nearest food

        if len(foodList) > 0: # This should always be True,  but better safe than sorry
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
          features['distanceToFood'] = minDistance
        return features

    def getWeights1(self, gameState, action):
        return {'successorScore': 100, 'distanceToFood': -1}


    def value(self, state, index, a, b):
        mindex = index % 6
        if index >= self.depth * 6 or state.isOver():
            return (self.getValue(state), "Stop")
        if mindex in self.getTeam(state) and state.getAgentState(mindex).configuration:
            v = (-float('Inf'), "Stop")
            for way in state.getLegalActions(mindex):
                k = (self.value(state.generateSuccessor(mindex, way), index + 1, a, b)[0],way)
                if k[0] >= v[0]:
                    v = k
                a= max(a, k[0])
                if b < a:
                    break
            return v
        elif mindex in self.getOpponents(state) and state.getAgentState(mindex).configuration:
            v = (float('Inf'), "Stop")
            for way in state.getLegalActions(mindex):
                k = (self.value(state.generateSuccessor(mindex, way), index + 1, a, b)[0], way)
                if k[0] < v[0]:
                    v = k
                b = min(b, k[0])
                if b < a:
                    break
            return v
        else:
          return self.value(state, index+1, a, b)

    def getSuccessor(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        return successor
    def getFeatures(self, state, action):
        features = util.Counter()
        myState = state.getAgentState(self.index)
        successor = state.generateSuccessor(self.index, action)
        newState = successor.getAgentState(self.index)
        features['successorScore'] = self.getScore(successor)
        foodList = self.getFood(successor).asList()    
        features['has-food'] = len(foodList)
        myPos = int(myState.getPosition()[0]), int(myState.getPosition()[1])
        newPos = int(newState.getPosition()[0]), int(newState.getPosition()[1])
        
        if len(foodList) > 0:
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
          features['distanceToFood'] = minDistance
        if features["has-food"]:
          features["goAttack"] = 1
        if state.getAgentDistances():
          features["eat-pacman"] = min([min(state.getAgentDistances()[i],successor.getAgentDistances()[i]) for i in self.getOpponents(successor)])
        features["own-flag"]=float(myState.ownFlag or newState.ownFlag)
        caps = self.getCapsules(state)
        if caps:
          features['get-caps'] = min([self.getMazeDistance(newPos, i) for i in caps])

        flag = self.getFlags(state)
        if flag:
          features['get-flag'] = self.getMazeDistance(newPos, flag[0])
        critical_index = self.getOwnFlagOpponent(state)
        if critical_index:
          critical_pos = state.getAgentState(critical_index).getPosition()
          if critical_pos:
            features["critical-point"] = self.getMazeDistance(newPos, critical_pos)
          else:
            features["critical-point"] = self.getMazeDistance(newPos, self.myFlagPos)
        features["bias"] = 1.0
        features.divideAll(3.1415926**3.1415926**3.1415926)
        return features

    def getQValue(self, state, action):
        return self.getWeights()*self.getFeatures(state, action)


    def update(self, state, action, nextState, reward):
        f = self.getFeatures(state, action)
        qmax = self.computeValueFromQValues(nextState)
        q = self.getQValue(state, action)
        for i in f.keys():
            self.weights[i] += self.alpha*(reward + self.discount * qmax - q) * f[i]

class myDAgent(ApproximateQAgent):
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.myFlagPos = self.getFlagsYouAreDefending(gameState)[0]
        self.depth = 1
    def getAction(self, gameState):
        self.observationHistory.append(gameState)
        myState = gameState.getAgentState(self.index)
        myPos = myState.getPosition()
        if myPos != util.nearestPoint(myPos):
          # We're halfway from one position to the next
              return gameState.getLegalActions(self.index)[0]
        else:
              return self.chooseAction(gameState)
    def chooseAction(self, gameState):
        actions = gameState.getLegalActions(self.index)
      
        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [self.getFeatures1(gameState, a)*self.getWeights1(gameState, a) for a in actions]
        # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
        
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        legalActions = gameState.getLegalActions(self.index)
        action = None
        if util.flipCoin(self.epsilon):
            action = random.choice(legalActions)
        else:
            action = self.value(gameState, self.index, -float("inf"), float("inf"))[1]
        self.doAction(gameState,action)
#        return random.choice(bestActions)
        return action
    def getFeatures1(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        
        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()
        
        # Computes whether we're on defense (1) or offense (0)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0

        # Computes distance to invaders we can see
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
          dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
          features['invaderDistance'] = min(dists)

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def getWeights1(self, gameState, action):
        return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}

    def value(self, state, index, a, b):
        mindex = index % 6
        if index >= self.depth * 6 or state.isOver():
            return (self.getValue(state), "Stop")
        if mindex in self.getTeam(state) and state.getAgentState(mindex).configuration:
            v = (-float('Inf'), "Stop")
            for way in state.getLegalActions(mindex):
                k = (self.value(state.generateSuccessor(mindex, way), index + 1, a, b)[0],way)
                if k[0] >= v[0]:
                    v = k
                a= max(a, k[0])
                if b < a:
                    break
            return v
        elif mindex in self.getOpponents(state) and state.getAgentState(mindex).configuration:
            v = (float('Inf'), "Stop")
            for way in state.getLegalActions(mindex):
                k = (self.value(state.generateSuccessor(mindex, way), index + 1, a, b)[0], way)
                if k[0] < v[0]:
                    v = k
                b = min(b, k[0])
                if b < a:
                    break
            return v
        else:
          return self.value(state, index+1, a, b)

    
    def getSuccessor(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        return successor
    def getFeatures(self, state, action):
        features = util.Counter()        
        myState = state.getAgentState(self.index)
        successor = state.generateSuccessor(self.index, action)
        newState = successor.getAgentState(self.index)
        features['successorScore'] = self.getScore(successor)
        foodList = self.getFood(successor).asList()    
        features['has-food'] = len(foodList)
        myPos = int(myState.getPosition()[0]), int(myState.getPosition()[1])
        newPos = int(newState.getPosition()[0]), int(newState.getPosition()[1])
        
        if len(foodList) > 0:
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
          features['distanceToFood'] = minDistance
        if not myState.isPacman:
          features["Defending"]=1

        if state.getAgentDistances():
          features["eat-pacman"] = min([min(state.getAgentDistances()[i],successor.getAgentDistances()[i]) for i in self.getOpponents(successor)])

        critical_index = self.getOwnFlagOpponent(state)
        if critical_index:
          critical_pos = state.getAgentState(critical_index).getPosition()
          if critical_pos:
            features["critical-point"] = self.getMazeDistance(newPos, critical_pos)
          else:
            features["critical-point"] = self.getMazeDistance(newPos, self.myFlagPos)
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
          dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
          features['invaderDistance'] = min(dists)

        features["bias"] = 1.0
        features.divideAll(3.1415926**3.1415926**3.1415926)
        return features

    def getQValue(self, state, action):
        return self.getWeights()*self.getFeatures(state, action)


    def update(self, state, action, nextState, reward):
        f = self.getFeatures(state, action)
        qmax = self.computeValueFromQValues(nextState)
        q = self.getQValue(state, action)
        for i in f.keys():
            self.weights[i] += self.alpha*(reward + self.discount * qmax - q) * f[i]



