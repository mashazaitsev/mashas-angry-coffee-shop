from cmu_graphics import *
import math
import random

'''
Masha's Angry Coffee Shop:
A survival game where you play as the coffee shop owner being chased by angry customers. 
Click customers within throwing range to hit them with coffee. Survive 4 rounds of increasing 
difficulty to win.

Key Features:
1) Backtracking pathfinding (Customer.findPath, Customer.passages)
Every customer runs a recursive backtracking algorithm over the walkable grid to chase the player.
Moves are sorted by Manhattan distance so customers head toward the player first, backtracking
only if they are blocked. Customers remember their current path so the backtracking search doesn't
rerun every frame (self.path, self.pathIndex) so the algorithm only reruns when a path is completed or
invalidated. Without this feature, the game would hit a timeout at every frame.

2) Custom walkable grid matching the visual background
The cafe background is overlaid on a 15x16 grid with a hardcoded app.walkable list. Both the player
and customers are constrained to walkable cells only, so no one walks through tables, counters or
walls (with some exceptions to give customers and player enough space to move).

3) Multi-screen app with a reusable Button class
Start screen and game screen are handled through runAppWithScreens, with a Button class that stores
(position,text,onClickFn) and handles its own click detection and drawing.

4) Increasing difficulty across 4 rounds 
Each round increases customer count and speed. With every round, more customers are allowed to spawn
closer to the player, making evasion harder. Round 4 is the final boss round.

5) Coffee projectile system with throw range
Clicking a customer within throw-range spawns a Coffee object that tracks the customer's moving
position in real time. The customer is only removed when the coffee actually reaches them.

Grading Shortcut:
Click 'START GAME' on the start screen to begin. During gameplay, click the 'Skip to final round'
button (top-right) to jump directly to Round 4 with full difficulty and full health, so you can see the
endgame state without playing through rounds 1-3.
Press R at any time during gameplay to restart from Round 1.
'''

class Player:
    def __init__(self,startCx,startCy,radius,speed):
        self.startCx=startCx
        self.startCy=startCy
        self.cx=startCx
        self.cy=startCy
        self.radius=radius
        self.speed=speed
        
    def reset(self):
        self.cx=self.startCx
        self.cy=self.startCy
            
    def draw(self, app):
        cellWidth,cellHeight=getCellSize(app)
        w=cellWidth*1.1
        h=cellHeight*2.9
        drawImage(app.ownerUrl,self.cx-w/2, self.cy-h/2, width=w, height=h)
        
    def move(self,dx,dy,app):
        newCx=self.cx+dx*self.speed
        newCy=self.cy+dy*self.speed
        
        row,col=getCell(app,newCx,newCy)    
        if isLegal(app,row,col,set()):
            self.cx=newCx
            self.cy=newCy
    
       
class Customer:
    def __init__(self,cx,cy,radius,speed,url):
        self.cx=cx
        self.cy=cy
        self.radius=radius
        self.speed=speed
        self.url=url
        
        self.path=None
        self.pathIndex=0
        
        self.targeted=False
    
    def moveToward(self,player,app): #steps along the paths.
        if self.path is None or self.pathIndex>=len(self.path):
            self.path= self.findPath(app, self.cx, self.cy, player.cx, player.cy)
            self.pathIndex=1 
            if self.path is None or len(self.path)<2:
                self.path=None
                return
        nextRow,nextCol=self.path[self.pathIndex]
        targetCx,targetCy=getCellCenter(app,nextRow,nextCol)
        dx,dy=targetCx-self.cx, targetCy-self.cy
        d=(dx**2+dy**2)**0.5
        
        if d<self.speed:
            self.cx, self.cy=targetCx, targetCy
            self.pathIndex+=1
        elif d!=0:
            self.cx+=self.speed*dx/d
            self.cy+=self.speed*dy/d
            
    def wasClicked(self,mouseX,mouseY):
        return distance(self.cx,self.cy,mouseX,mouseY)<=self.radius
        
    def touchesPlayer(self,player):
        return distance(self.cx,self.cy,player.cx,player.cy)<=self.radius+player.radius
    
    def draw(self, app):
        cellWidth,cellHeight=getCellSize(app)
        w=cellWidth
        h=cellHeight*2.9
        drawImage(self.url, self.cx, self.cy, width=w, height=h, align='center')
    
    def isInThrowRange(self, player, throwRange):
        return distance(self.cx, self.cy, player.cx, player.cy)<= throwRange
    
    def findPath(self,app,startCx,startCy,goalCx,goalCy): 
        startRow,startCol=getCell(app,startCx,startCy)
        goalRow,goalCol=getCell(app,goalCx,goalCy)
        if not isLegal(app,startRow,startCol,set()):
            return None
        if not isLegal(app,goalRow,goalCol,set()):
            return None
        visited={(startRow,startCol)}
        return self.passages(app,startRow,startCol,goalRow,goalCol,[],visited)

    
    def passages(self,app,row,col,ownersRow,ownersCol,result,visited): #visited is a set.
        if (row,col)==(ownersRow,ownersCol): 
            return result + [(row,col)]
        
        moves=[]
        for drow,dcol in [(0,1),(1,0),(-1,0),(0,-1)]:
            newDist= abs((row+drow)-ownersRow)+abs((col+dcol)-ownersCol)
            moves.append((newDist,drow,dcol))
        moves.sort() 
        
        for _,drow,dcol in moves: 
            newrow,newcol= row+drow, col+dcol
            if isLegal(app, newrow, newcol, visited):
                newResult= result+[(row,col)]
                newVisited= visited|{(newrow,newcol)}
                solution= self.passages(app,newrow,newcol,ownersRow,ownersCol,newResult,newVisited)
                if solution!= None:
                    return solution
        return None

class Coffee:
    def __init__(self,startCx,startCy,target,speed):
        self.cx=startCx
        self.cy=startCy
        self.target=target
        self.speed=speed
    
    def update(self): 
        dx= self.target.cx-self.cx
        dy=self.target.cy-self.cy
        d=(dx**2+dy**2)**0.5
        if d<=self.speed: 
            self.cx, self.cy= self.target.cx, self.target.cy
            return True
        self.cx+= self.speed*dx/d
        self.cy+= self.speed*dy/d
        return False
    
    def draw(self,app):
        size=40
        drawImage(app.coffeeUrl,self.cx,self.cy,width=size,height=size,align='center')

class Button:
    def __init__(self,left,top,width,height,color,text,onClickFn,textSize):
        self.left=left
        self.top=top
        self.width=width
        self.height=height
        self.color=color
        self.text=text
        self.onClickFn=onClickFn
        self.textSize=textSize
    
    def handleClick(self,mouseX,mouseY):
        left,right= self.left, self.left+self.width
        top,bottom=self.top, self.top+self.height
        if (left<=mouseX<=right) and (top<=mouseY<=bottom):
            self.onClickFn()
    
    def draw(self):
        drawRect(self.left,self.top, self.width, self.height, fill=self.color,borderWidth=4 ,border='maroon')
        cx,cy=self.left+self.width/2,self.top+self.height/2
        drawLabel(self.text, cx, cy, bold=True, font='monospace',fill='maroon',size=self.textSize)


def onAppStart(app):
    app.cafewidth=840
    app.cafeheight=490
    app.margin=app.topmargin=35
    app.titleheight=100
    app.width=app.cafewidth+2*app.margin
    app.height=app.cafeheight+app.margin+app.topmargin+app.titleheight
    
    app.stepsPerSecond=8
    app.maxRounds=4
    app.maxHealth=5
    
    app.playerRadius=20
    app.playerSpeed=15
    
    app.startCustomerCount=10
    app.startCustomerSpeed=2
    app.customerRadius=15
    app.minSpawnDistance=200
    
    app.rows = 15
    app.cols = 16
    app.boardLeft = app.margin
    app.boardTop = app.titleheight+app.margin
    app.boardWidth = app.cafewidth
    app.boardHeight = app.cafeheight
    app.cellBorderWidth = 1
    
    app.startUrl='cmu://1166394/46625098/coffee+shop+exterior.png'
    
    app.heartUrl='cmu://1166394/46609409/heart.png'
    app.heartwidth=40
    app.heartheight=40
    
    app.coffeeUrl='cmu://1166394/46622702/coffee+splash.png'
    app.coffeeSpeed=60
    app.throwRange=app.width/3
    
    app.ownerUrl='cmu://1166394/46609658/owner.png'
    app.customerUrls=['cmu://1166394/46609770/customer1.png',
    'cmu://1166394/46609773/customer7.png','cmu://1166394/46609782/customer2.png',
    'cmu://1166394/46609788/customer8.png','cmu://1166394/46609792/customer3.png',
    'cmu://1166394/46609797/customer9.png','cmu://1166394/46609800/customer4.png',
    'cmu://1166394/46609806/customer10.png','cmu://1166394/46609810/customer5.png',
    'cmu://1166394/46609815/customer11.png','cmu://1166394/46609819/customer6.png']
    
    playerStartRow, playerStartCol=7,14 #True Cells
    app.playerStartCx, app.playerStartCy= getCellCenter(app,playerStartRow,playerStartCol)
    
    app.walkable=[False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,
                False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,
                False,True,True,False,False,False,False,False,False,False,False,False,False,False,False,False,
                False,True,True,True,True,True,True,True,True,True,True,True,True,False,True,False,
                False,False,False,True,False,True,True,True,True,True,True,True,True,True,True,False,
                False,True,False,True,False,False,True,True,True,True,True,True,True,True,True,False,
                False,True,False,True,False,False,False,True,True,True,True,True,True,True,True,False,
                False,True,False,True,False,False,False,True,True,True,True,True,True,True,True,False,
                False,True,False,True,False,False,False,True,True,True,True,True,True,True,True,False,
                True,True,False,True,False,False,False,True,True,True,True,True,True,True,True,False,
                True,True,True,True,False,False,False,True,True,True,True,True,True,True,True,False,
                True,True,True,True,False,True,True,True,True,True,True,True,False,False,True,False,
                False,False,True,True,False,True,True,False,True,False,False,False,False,False,False,False,
                False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,
                False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,]
    
    resetApp(app)
    initializeButtons(app)

def initializeButtons(app):
    def startGame():
        setActiveScreen('game')
        
    def skipToLastRound():
        while app.round<app.maxRounds:
            advanceRound(app)
    
    app.startButton= Button(
        left=app.width/2-90,
        top=app.height/2,
        width=190,
        height=50,
        color='white',
        text='START GAME',
        onClickFn=startGame,
        textSize=30)
        
    app.skipButton=Button(
        left=app.width-200,
        top=10,
        width=180,
        height=22,
        color='white',
        text='Skip to final round',
        onClickFn=skipToLastRound,
        textSize=14)

##################
# Start Screen
##################
def start_redrawAll(app):
    drawImage(app.startUrl, 0,0, width=app.width,height=app.height)
    drawLabel("Welcome to Masha's Angry Coffee Shop",app.width/2,app.height/7,size=36,bold=True,fill='white')
    
    boxWidth=300
    boxHeight=200
    boxLeft=app.width/2-boxWidth/2
    boxTop=app.height-boxHeight*1.2
    
    drawRect(boxLeft, boxTop, boxWidth, boxHeight, fill='pink',opacity=95)
    drawLabel('How to Play', app.width/2,boxTop+boxHeight*0.10,size=18,bold=True,fill='maroon')
    drawLabel('The customers are out to get you!', app.width/2,boxTop+boxHeight*0.2,size=14,bold=True,fill='maroon')
    drawLabel('Use arrow keys to escape them.',app.width/2,boxTop+boxHeight*0.35,size=14,fill='maroon',bold=True)
    drawLabel('Click nearby customers to throw coffee &',app.width/2,boxTop+boxHeight*0.5,size=14,bold=True,fill='maroon')
    drawLabel('make them disappear',app.width/2,boxTop+boxHeight*0.57,size=14,bold=True,fill='maroon')
    drawLabel('Survive 4 rounds with 5 hearts to win!',app.width/2,boxTop+boxHeight*0.7,size=14,bold=True,fill='maroon')
    drawLabel('Anytime a customer runs in to you,',app.width/2,boxTop+boxHeight*0.85,size=14,bold=True,fill='maroon')
    drawLabel('you lose one heart.',app.width/2,boxTop+boxHeight*0.92,size=14,bold=True,fill='maroon')
    app.startButton.draw()

def start_onMousePress(app,mouseX,mouseY):
    app.startButton.handleClick(mouseX,mouseY)

##################
# Game Screen
##################
def resetApp(app):
    app.health=app.maxHealth
    
    app.url='cmu://1166394/46511145/Screenshot+2026-04-17+at+3.18.27 PM.png'
    app.round=1
    app.gameOver=False
    
    app.customerCount=app.startCustomerCount
    app.customerSpeed=app.startCustomerSpeed
    
    app.player=Player(app.playerStartCx,app.playerStartCy,app.playerRadius,app.playerSpeed)
    app.customers=makeCustomers(app,app.customerCount,app.customerSpeed)
    
    app.coffees=[]

def makeCustomers(app,count,speed): 
    walkableCells=[]
    for row in range(app.rows):
        for col in range(app.cols):
            if app.walkable[row*app.cols+col]:
                walkableCells.append((row,col))
    random.shuffle(walkableCells)
    
    closeSpawnLimit=(app.round-1)*2
    closeMinDistance=80
    
    customers=[]
    closeCount=0
    for row,col in walkableCells:
        if len(customers)>= count:
            break
        cx,cy=getCellCenter(app,row,col)
        d= distance(cx,cy,app.player.cx,app.player.cy)
        
        if d >= app.minSpawnDistance:
            url=random.choice(app.customerUrls)
            customers.append(Customer(cx,cy,app.customerRadius,speed,url))
        elif closeCount< closeSpawnLimit and d>= closeMinDistance:
            url=random.choice(app.customerUrls)
            customers.append(Customer(cx,cy,app.customerRadius,speed,url))
            closeCount+=1
    return customers

def advanceRound(app): 
    app.round+=1
    if app.round>app.maxRounds:
        app.gameOver=True
    else:
        app.customerCount=math.ceil(app.customerCount*1.1)
        app.customerSpeed*=1.4
        
        app.player.reset()
        app.customers=makeCustomers(app,app.customerCount,app.customerSpeed)

def game_onKeyPress(app,key):
    if key=='r':
        resetApp(app)

def game_onKeyHold(app,keys):
    if app.gameOver:
        return
    if 'up' in keys:
        app.player.move(0,-1,app)
    if 'down' in keys:
        app.player.move(0,1,app)
    if 'left' in keys:
        app.player.move(-1,0,app)
    if 'right' in keys:
        app.player.move(1,0,app)


def game_onStep(app):
    if app.gameOver:
        return
    
    stillFlying=[]
    for coffee in app.coffees:
        if coffee.update():
            if coffee.target in app.customers:
                app.customers.remove(coffee.target)
        else:
            stillFlying.append(coffee)
    app.coffees=stillFlying
    
    survivors=[]
    for customer in app.customers:
        customer.moveToward(app.player, app)
        if customer.touchesPlayer(app.player):
            app.health-=1
            if app.health<=0:
                app.gameOver=True
                return 
        else:
            survivors.append(customer)
    app.customers=survivors
    
    if len(app.customers)==0:
        advanceRound(app)

def game_onMousePress(app,mouseX,mouseY):
    if app.gameOver:
        return
    
    app.skipButton.handleClick(mouseX, mouseY)
    
    for customer in app.customers:
        if customer.wasClicked(mouseX, mouseY) and not customer.targeted:
            if not customer.isInThrowRange(app.player,app.throwRange):
                return
            customer.targeted=True
            coffee=Coffee(app.player.cx,app.player.cy,customer,speed=app.coffeeSpeed)
            app.coffees.append(coffee)
            return

def game_redrawAll(app):
    drawRect(0,0,app.width,app.height,fill=rgb(255,235,240))
    
    drawImage(app.url,app.margin,app.titleheight+app.topmargin,width=app.cafewidth,height=app.cafeheight)
    drawHeader(app)
    app.player.draw(app) 
    
    for customer in app.customers:
        customer.draw(app)
        
    app.skipButton.draw()
    
    drawHearts(app)
    
    for coffee in app.coffees:
        coffee.draw(app)
        
    drawLabel('Press arrow keys to move, r to restart',app.width/2,app.height-app.margin/2,
                size=16,font='monospace',bold=True)

    if app.gameOver:
        drawGameOver(app)

def drawHearts(app):
    heartSpacing=35
    heartSize=40
    heartY=app.titleheight+app.margin/3
    for i in range(app.health):
        heartX=(app.boardLeft+app.boardWidth)-heartSize/2-(app.maxHealth-1-i)*heartSpacing
        drawImage(app.heartUrl, heartX-heartSize/2, heartY-heartSize/2, width=app.heartwidth, height=app.heartheight)

def drawGameOver(app):
    drawRect(0,0,app.width,app.height,fill='maroon',opacity=40)
    drawLabel('Game Over!',app.width/2,app.height/2-15,size=50, bold=True,fill='white',font='monospace')
    if app.health<=0:
        drawLabel('Better luck next time!', app.width/2,app.height/2+20,size=24,fill='white',font='monospace',bold=True)
    else:
        drawLabel('You finished all 4 rounds!',app.width/2,app.height/2+20,size=24,fill='white',font='monospace',bold=True)
            
def drawHeader(app):
    drawLabel("Masha's Angry Coffee Shop",app.width/2,(app.titleheight+app.margin)/2-10,size=45,font='monospace',
    bold=True,fill='maroon')
    drawLabel(f'Round {app.round}/{app.maxRounds}',app.margin,app.titleheight+app.margin/2,size=25,bold=True,
    align='left',font='monospace')
    drawLabel(f'Customers left: {len(app.customers)}',app.margin*6,app.titleheight+app.margin/2,
    size=20,align='left',font='monospace',bold=True)

############
# Math Helper Function
############
def distance(x0,y0,x1,y1):
    return ((x1-x0)**2+(y1-y0)**2)**0.5
    
############
# Grid/Coordinate Helper Functions
############

def getCellSize(app):
    cellWidth = app.boardWidth / app.cols
    cellHeight = app.boardHeight / app.rows
    return (cellWidth, cellHeight)
    
def getCell(app,cx,cy):
    cellWidth,cellHeight=getCellSize(app)
    col=math.floor((cx-app.boardLeft)/cellWidth)
    row=math.floor((cy-app.boardTop)/cellHeight)
    return row,col

def getCellCenter(app,row,col):
    cellWidth,cellHeight=getCellSize(app)
    cx= app.boardLeft + col*cellWidth + cellWidth/2
    cy= app.boardTop + row*cellHeight+ cellHeight/2
    return cx,cy

############
# Backtracking Helper Function
############

def isLegal(app,row,col,visited): 
    if row<0 or row>=app.rows:
        return False
    if col<0 or col>=app.cols:
        return False
    if not app.walkable[row*app.cols+col]:
        return False
    if (row,col) in visited:
        return False
    return True


def main():
    runAppWithScreens(initialScreen='start')

main()
